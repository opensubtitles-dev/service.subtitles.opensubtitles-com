"""SPIKE: pure-Python AAC audio extraction from Matroska (MKV) -> ADTS (.aac).

Stdlib only, Python 3.6 compatible, streaming reads (no whole-file load - MKV
films are GBs). Proves the no-ffmpeg fallback rung for the most common film
container (docs/audio_extraction_matrix.md).

Covers: EBML varint ids/sizes, unknown-size segments, Tracks/TrackEntry
(TrackNumber, CodecID A_AAC*, CodecPrivate = AudioSpecificConfig), Clusters,
SimpleBlock AND BlockGroup/Block, all three lacing modes (Xiph, fixed, EBML).
"""
import struct
import sys
import time

# element ids we care about (raw, with length marker bits)
EBML_HEADER = 0x1A45DFA3
SEGMENT = 0x18538067
TRACKS = 0x1654AE6B
TRACK_ENTRY = 0xAE
TRACK_NUMBER = 0xD7
CODEC_ID = 0x86
CODEC_PRIVATE = 0x63A2
CLUSTER = 0x1F43B675
SIMPLE_BLOCK = 0xA3
BLOCK_GROUP = 0xA0
BLOCK = 0xA1

UNKNOWN_SIZE = -1


def _read_vint(f, keep_marker):
    """Reads one EBML varint. keep_marker=True for element IDs."""
    first = f.read(1)
    if not first:
        return None, 0
    b = first[0]
    length = 8 - b.bit_length() + 1 if b else 8
    length = next((i + 1 for i in range(8) if b & (0x80 >> i)), 8)
    rest = f.read(length - 1)
    if len(rest) != length - 1:
        return None, 0
    value = b if keep_marker else b & (0xFF >> length)
    for byte in rest:
        value = (value << 8) | byte
    if not keep_marker:
        # all-ones payload means "unknown size"
        if value == (1 << (7 * length)) - 1:
            return UNKNOWN_SIZE, length
    return value, length


def _read_element(f):
    """Returns (id, size, header_len) or (None, ...) at EOF."""
    eid, id_len = _read_vint(f, keep_marker=True)
    if eid is None:
        return None, 0, 0
    size, size_len = _read_vint(f, keep_marker=False)
    if size is None:
        return None, 0, 0
    return eid, size, id_len + size_len


def _parse_tracks(f, end):
    """Returns (aac_track_number, AudioSpecificConfig) or (None, None)."""
    while f.tell() < end:
        eid, size, _ = _read_element(f)
        if eid is None:
            break
        if eid != TRACK_ENTRY:
            f.seek(size, 1)
            continue
        entry_end = f.tell() + size
        number, codec, private = None, "", b""
        while f.tell() < entry_end:
            ceid, csize, _ = _read_element(f)
            if ceid is None:
                break
            payload_at = f.tell()
            if ceid == TRACK_NUMBER:
                number = int.from_bytes(f.read(csize), "big")
            elif ceid == CODEC_ID:
                codec = f.read(csize).decode("latin1").strip("\x00")
            elif ceid == CODEC_PRIVATE:
                private = f.read(csize)
            else:
                f.seek(csize, 1)
            f.seek(payload_at + csize)
        if codec.startswith("A_AAC") and number is not None and len(private) >= 2:
            return number, private
        f.seek(entry_end)
    return None, None


def _block_frames(data, want_track):
    """Splits a (Simple)Block payload into frames for want_track, or []."""
    # track number is a vint at the start of the block payload
    b = data[0]
    tlen = next((i + 1 for i in range(8) if b & (0x80 >> i)), 8)
    track = b & (0xFF >> tlen)
    for byte in data[1:tlen]:
        track = (track << 8) | byte
    if track != want_track:
        return []
    pos = tlen + 2                      # skip 2-byte relative timecode
    flags = data[pos]; pos += 1
    lacing = (flags >> 1) & 0x3
    if lacing == 0:                     # no lacing: one frame
        return [data[pos:]]
    count = data[pos] + 1; pos += 1
    sizes = []
    if lacing == 2:                     # fixed: equal split
        each = (len(data) - pos) // count
        sizes = [each] * count
    elif lacing == 1:                   # Xiph: 255-run coded, last implicit
        for _ in range(count - 1):
            sz = 0
            while True:
                v = data[pos]; pos += 1
                sz += v
                if v != 255:
                    break
            sizes.append(sz)
        sizes.append(len(data) - pos - sum(sizes))
    else:                               # EBML: first absolute vint, rest signed deltas
        b0 = data[pos]
        l0 = next((i + 1 for i in range(8) if b0 & (0x80 >> i)), 8)
        first = b0 & (0xFF >> l0)
        for byte in data[pos + 1:pos + l0]:
            first = (first << 8) | byte
        pos += l0
        sizes = [first]
        for _ in range(count - 2):
            bd = data[pos]
            ld = next((i + 1 for i in range(8) if bd & (0x80 >> i)), 8)
            delta = bd & (0xFF >> ld)
            for byte in data[pos + 1:pos + ld]:
                delta = (delta << 8) | byte
            delta -= (1 << (7 * ld - 1)) - 1        # signed vint bias
            pos += ld
            sizes.append(sizes[-1] + delta)
        sizes.append(len(data) - pos - sum(sizes))
    frames = []
    for sz in sizes:
        frames.append(data[pos:pos + sz])
        pos += sz
    return frames


def _adts_header(asc, frame_len):
    aot = (asc[0] >> 3) & 0x1F
    freq_idx = ((asc[0] & 7) << 1) | (asc[1] >> 7)
    channels = (asc[1] >> 3) & 0xF
    flen = frame_len + 7
    hdr = bytearray(7)
    hdr[0] = 0xFF
    hdr[1] = 0xF1
    hdr[2] = ((aot - 1) << 6) | (freq_idx << 2) | (channels >> 2)
    hdr[3] = ((channels & 3) << 6) | (flen >> 11)
    hdr[4] = (flen >> 3) & 0xFF
    hdr[5] = ((flen & 7) << 5) | 0x1F
    hdr[6] = 0xFC
    return bytes(hdr)


def extract(path_in, path_out):
    frames_out = 0
    with open(path_in, "rb") as f, open(path_out, "wb") as out:
        track, asc = None, None
        # top level: EBML header then Segment
        while True:
            eid, size, _ = _read_element(f)
            if eid is None:
                break
            if eid != SEGMENT:
                f.seek(size, 1)
                continue
            seg_end = None if size == UNKNOWN_SIZE else f.tell() + size
            while seg_end is None or f.tell() < seg_end:
                ceid, csize, _ = _read_element(f)
                if ceid is None:
                    break
                if ceid == TRACKS:
                    track, asc = _parse_tracks(f, f.tell() + csize)
                    if track is None:
                        raise SystemExit("no AAC audio track found")
                elif ceid == CLUSTER and track is not None:
                    cl_end = None if csize == UNKNOWN_SIZE else f.tell() + csize
                    while cl_end is None or f.tell() < cl_end:
                        beid, bsize, _ = _read_element(f)
                        if beid is None:
                            break
                        if beid == SIMPLE_BLOCK:
                            for frame in _block_frames(f.read(bsize), track):
                                out.write(_adts_header(asc, len(frame)))
                                out.write(frame)
                                frames_out += 1
                        elif beid == BLOCK_GROUP:
                            g_end = f.tell() + bsize
                            while f.tell() < g_end:
                                geid, gsize, _ = _read_element(f)
                                if geid is None:
                                    break
                                if geid == BLOCK:
                                    for frame in _block_frames(f.read(gsize), track):
                                        out.write(_adts_header(asc, len(frame)))
                                        out.write(frame)
                                        frames_out += 1
                                else:
                                    f.seek(gsize, 1)
                        elif bsize == UNKNOWN_SIZE:
                            break        # cannot skip unknown-size child safely
                        else:
                            f.seek(bsize, 1)
                elif csize == UNKNOWN_SIZE:
                    break
                else:
                    f.seek(csize, 1)
            break
    return frames_out


if __name__ == "__main__":
    t0 = time.time()
    n = extract(sys.argv[1], sys.argv[2])
    print(f"extracted {n} AAC frames in {time.time() - t0:.2f}s")
