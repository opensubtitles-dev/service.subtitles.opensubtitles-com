"""Pure-Python audio track extraction (MP4/MOV and Matroska) -> ADTS .aac.

Stdlib only, Python 3.6 compatible. The no-external-tool rung of the audio
ladder (docs/audio_extraction_matrix.md): extracts the AAC track WITHOUT
decoding, so it works where nothing can be executed (Android, iOS/tvOS) and
feeds afconvert on macOS for MKV sources. Only AAC tracks are supported -
that is inherent (extraction without decode).

extract_audio_track(path_in, path_out) -> frames written; raises
UnsupportedSource when the container/codec cannot be handled.
"""
import os
import struct
import sys
import time


class UnsupportedSource(Exception):
    """Container unreadable or no extractable AAC track."""

import struct, sys, time

def _mp4_boxes(buf, start, end):
    off = start
    while off + 8 <= end:
        size, btype = struct.unpack(">I4s", buf[off:off+8]); hdr = 8
        if size == 1:
            size = struct.unpack(">Q", buf[off+8:off+16])[0]; hdr = 16
        elif size == 0:
            size = end - off
        yield btype.decode("latin1"), off + hdr, off + size
        off += size

def _mp4_find(buf, path, start, end):
    t = path[0]
    for btype, s, e in _mp4_boxes(buf, start, end):
        if btype == t:
            return (s, e) if len(path) == 1 else _mp4_find(buf, path[1:], s, e)
    return None

def extract_mp4(path_in, path_out):
    with open(path_in, "rb") as f:
        data = f.read()
    moov = _mp4_find(data, ["moov"], 0, len(data))
    if not moov:
        raise UnsupportedSource("no moov box")
    # find the audio trak (mp4a sample entry)
    audio = None
    for btype, s, e in _mp4_boxes(data, *moov):
        if btype != "trak":
            continue
        stsd = _mp4_find(data, ["mdia", "minf", "stbl", "stsd"], s, e)
        if stsd and b"mp4a" in data[stsd[0]:stsd[1]]:
            audio = (s, e); break
    if not audio:
        raise UnsupportedSource("no AAC (mp4a) audio track")
    stbl = _mp4_find(data, ["mdia", "minf", "stbl"], *audio)
    stsd = _mp4_find(data, ["stsd"], *stbl)
    # AudioSpecificConfig from esds
    esds_pos = data.find(b"esds", stsd[0], stsd[1])
    # walk esds descriptors to DecoderSpecificInfo (tag 5)
    p = esds_pos + 8  # skip 'esds' + version/flags
    asc = None
    endp = stsd[1]
    while p < endp:
        tag = data[p]; p += 1
        ln = 0
        while True:
            b = data[p]; p += 1
            ln = (ln << 7) | (b & 0x7F)
            if not b & 0x80: break
        if tag == 5:
            asc = data[p:p+ln]; break
        if tag == 3: p += 3      # ES descriptor header
        elif tag == 4: p += 13   # DecoderConfig header
        else: p += ln
    if not (asc and len(asc) >= 2):
        raise UnsupportedSource("no AudioSpecificConfig")
    aot = (asc[0] >> 3) & 0x1F
    freq_idx = ((asc[0] & 7) << 1) | (asc[1] >> 7)
    channels = (asc[1] >> 3) & 0xF

    def table(name, s, e, per, skip=12):
        seg = data[s+skip:e]
        n = struct.unpack(">I", data[s+8:s+12])[0]
        return seg, n
    stsz_s, stsz_e = _mp4_find(data, ["stsz"], *stbl)
    sample_size = struct.unpack(">I", data[stsz_s+4:stsz_s+8])[0]
    count = struct.unpack(">I", data[stsz_s+8:stsz_s+12])[0]
    sizes = ([sample_size]*count if sample_size else
             list(struct.unpack(">%dI" % count, data[stsz_s+12:stsz_s+12+4*count])))
    co = _mp4_find(data, ["stco"], *stbl) or _mp4_find(data, ["co64"], *stbl)
    is64 = data[co[0]-4:co[0]] == b"co64"
    cn = struct.unpack(">I", co[0]+4 and data[co[0]+4:co[0]+8])[0]
    fmt = ">%dQ" % cn if is64 else ">%dI" % cn
    offsets = list(struct.unpack(fmt, data[co[0]+8:co[0]+8+(8 if is64 else 4)*cn]))
    stsc_s, stsc_e = _mp4_find(data, ["stsc"], *stbl)
    sn = struct.unpack(">I", data[stsc_s+4:stsc_s+8])[0]
    stsc = [struct.unpack(">III", data[stsc_s+8+i*12:stsc_s+20+i*12]) for i in range(sn)]

    out = open(path_out, "wb")
    si = 0
    for ci, chunk_off in enumerate(offsets, start=1):
        per_chunk = 0
        for first, spc, _sd in reversed(stsc):
            if ci >= first:
                per_chunk = spc; break
        pos = chunk_off
        for _ in range(per_chunk):
            if si >= len(sizes): break
            sz = sizes[si]; frame = data[pos:pos+sz]
            flen = sz + 7
            hdr = bytearray(7)
            hdr[0] = 0xFF; hdr[1] = 0xF1
            hdr[2] = ((aot - 1) << 6) | (freq_idx << 2) | (channels >> 2)
            hdr[3] = ((channels & 3) << 6) | (flen >> 11)
            hdr[4] = (flen >> 3) & 0xFF
            hdr[5] = ((flen & 7) << 5) | 0x1F
            hdr[6] = 0xFC
            out.write(bytes(hdr)); out.write(frame)
            pos += sz; si += 1
    out.close()
    return si



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


_MKV_AUDIO = {
    "A_AAC": ("aac", ".aac"),
    "A_AC3": ("raw", ".ac3"),
    "A_EAC3": ("raw", ".eac3"),
    "A_MPEG/L3": ("raw", ".mp3"),
    "A_DTS": ("raw", ".dts"),
    "A_FLAC": ("flac", ".flac"),
}
# "raw" tracks are self-framing elementary streams that survive plain
# concatenation of their block frames; afconvert on macOS reads raw
# AC3/EAC3/MP3/FLAC directly (measured, docs/audio_extraction_matrix.md).


def _mkv_kind(codec):
    for known, spec in _MKV_AUDIO.items():
        if codec == known or codec.startswith(known + "/"):
            return spec[0]
    return None


def _parse_tracks(f, end):
    """Returns (track_number, codec_id, CodecPrivate) of the first
    extractable audio track, or (None, "", b"")."""
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
        if number is not None and _mkv_kind(codec):
            if _mkv_kind(codec) == "aac" and len(private) < 2:
                pass        # AAC without ASC cannot be ADTS-framed - skip it
            else:
                return number, codec, private
        f.seek(entry_end)
    return None, "", b""


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


def extract_mkv(path_in, path_out):
    frames_out = 0
    with open(path_in, "rb") as f, open(path_out, "wb") as out:
        track, codec, private = None, "", b""
        kind, asc = "aac", b""
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
                    track, codec, private = _parse_tracks(f, f.tell() + csize)
                    if track is None:
                        raise UnsupportedSource("no extractable audio track found")
                    kind = _mkv_kind(codec)
                    if kind == "aac":
                        asc = private
                    elif kind == "flac":
                        # CodecPrivate IS the complete fLaC stream header
                        out.write(private)
                elif ceid == CLUSTER and track is not None:
                    cl_end = None if csize == UNKNOWN_SIZE else f.tell() + csize
                    while cl_end is None or f.tell() < cl_end:
                        beid, bsize, _ = _read_element(f)
                        if beid is None:
                            break
                        if beid == SIMPLE_BLOCK:
                            for frame in _block_frames(f.read(bsize), track):
                                if kind == "aac":
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
                                        if kind == "aac":
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




def probe_extension(path_in):
    """Extension the extracted track will need (".aac", ".ac3", ...).

    afconvert on macOS TRUSTS the file extension (measured) - callers must
    name the output correctly or conversion fails on a perfectly good stream.
    """
    with open(path_in, "rb") as f:
        head = f.read(12)
    if head[:4] != b"\x1aE\xdf\xa3":
        return ".aac"                     # MP4 family always yields ADTS
    # cheap Tracks scan for the codec id
    with open(path_in, "rb") as f:
        while True:
            eid, size, _ = _read_element(f)
            if eid is None:
                break
            if eid == SEGMENT:
                seg_end = None if size == UNKNOWN_SIZE else f.tell() + size
                while seg_end is None or f.tell() < seg_end:
                    ceid, csize, _ = _read_element(f)
                    if ceid is None:
                        break
                    if ceid == TRACKS:
                        _n, codec, _p = _parse_tracks(f, f.tell() + csize)
                        for known, spec in _MKV_AUDIO.items():
                            if codec == known or codec.startswith(known + "/"):
                                return spec[1]
                        return ".aac"
                    if csize == UNKNOWN_SIZE:
                        break
                    f.seek(csize, 1)
                break
            f.seek(size, 1)
    return ".aac"


def extract_audio_track(path_in, path_out):
    """Extracts the AAC track of an MP4/MOV or MKV file to ADTS.

    Returns the number of frames written; raises UnsupportedSource for
    non-AAC audio or unknown containers. Never decodes - CPU cost is I/O."""
    with open(path_in, "rb") as f:
        head = f.read(12)
    if head[:4] == b"\x1aE\xdf\xa3":
        return extract_mkv(path_in, path_out)
    if head[4:8] in (b"ftyp", b"moov", b"mdat", b"wide", b"free"):
        return extract_mp4(path_in, path_out)
    raise UnsupportedSource("unrecognized container")
