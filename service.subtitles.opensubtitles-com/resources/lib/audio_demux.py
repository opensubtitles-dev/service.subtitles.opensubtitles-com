"""Pure-Python audio track extraction (MP4/MOV and Matroska).

Stdlib only, Python 3.6 compatible. The no-external-tool rung of the audio
ladder (docs/audio_extraction_matrix.md): extracts the audio track WITHOUT
decoding, so it works where nothing can be executed (Android, iOS/tvOS) and
feeds afconvert on macOS for MKV sources. Outputs by codec: AAC -> ADTS,
AC3/EAC3/MP3/DTS -> raw elementary stream, FLAC -> native, Opus -> Ogg
re-encapsulation (RFC 7845, pure stdlib), little-endian integer PCM -> WAV.

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
AUDIO_ELEM = 0xE1
SAMPLING_FREQ = 0xB5
CHANNELS_ELEM = 0x9F
BIT_DEPTH = 0x6264
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
    "A_OPUS": ("opus", ".ogg"),
    "A_PCM/INT/LIT": ("pcm", ".wav"),
}
# "raw" tracks are self-framing elementary streams that survive plain
# concatenation of their block frames; afconvert on macOS reads raw
# AC3/EAC3/MP3/FLAC directly (measured, docs/audio_extraction_matrix.md).
# "opus" packets are NOT self-framing - they get Ogg re-encapsulation
# (_OggOpusWriter); "pcm" little-endian integer samples get a WAV header.
# A_PCM/INT/BIG (big-endian) is deliberately absent: exact-key match only.


def _mkv_kind(codec):
    for known, spec in _MKV_AUDIO.items():
        if codec == known or codec.startswith(known + "/"):
            return spec[0]
    return None


def _parse_tracks(f, end):
    """Returns (track_number, codec_id, CodecPrivate, audio_params) of the
    first extractable audio track, or (None, "", b"", {}). audio_params holds
    sampling rate / channels / bit depth from the Audio element (PCM needs
    them for the WAV header)."""
    while f.tell() < end:
        eid, size, _ = _read_element(f)
        if eid is None:
            break
        if eid != TRACK_ENTRY:
            f.seek(size, 1)
            continue
        entry_end = f.tell() + size
        number, codec, private = None, "", b""
        audio = {}
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
            elif ceid == AUDIO_ELEM:
                a_end = f.tell() + csize
                while f.tell() < a_end:
                    aeid, asize, _ = _read_element(f)
                    if aeid is None:
                        break
                    a_at = f.tell()
                    raw = f.read(asize)
                    if aeid == SAMPLING_FREQ and len(raw) in (4, 8):
                        audio["rate"] = int(struct.unpack(
                            ">f" if len(raw) == 4 else ">d", raw)[0])
                    elif aeid == CHANNELS_ELEM:
                        audio["channels"] = int.from_bytes(raw, "big")
                    elif aeid == BIT_DEPTH:
                        audio["bit_depth"] = int.from_bytes(raw, "big")
                    f.seek(a_at + asize)
            else:
                f.seek(csize, 1)
            f.seek(payload_at + csize)
        if number is not None and _mkv_kind(codec):
            kind = _mkv_kind(codec)
            if kind == "aac" and len(private) < 2:
                pass        # AAC without ASC cannot be ADTS-framed - skip it
            elif kind == "opus" and len(private) < 19:
                pass        # Opus needs the OpusHead CodecPrivate verbatim
            elif kind == "pcm" and not audio.get("rate"):
                pass        # PCM without a sampling rate cannot be WAV-framed
            else:
                return number, codec, private, audio
        f.seek(entry_end)
    return None, "", b"", {}


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


# --- Ogg Opus re-encapsulation ---------------------------------------------
# Opus packets in MKV are not self-framing; players need them inside Ogg
# (RFC 7845). Pure stdlib: Ogg page framing + the Ogg CRC-32 (poly 0x04C11DB7,
# init 0, no reflection, no final xor - NOT zlib.crc32).

_OGG_CRC_TABLE = []


def _ogg_crc(data):
    if not _OGG_CRC_TABLE:
        for i in range(256):
            r = i << 24
            for _ in range(8):
                r = ((r << 1) ^ 0x04C11DB7) & 0xFFFFFFFF if r & 0x80000000 \
                    else (r << 1) & 0xFFFFFFFF
            _OGG_CRC_TABLE.append(r)
    crc = 0
    for b in data:
        crc = ((crc << 8) & 0xFFFFFFFF) ^ _OGG_CRC_TABLE[((crc >> 24) & 0xFF) ^ b]
    return crc


# TOC-byte frame durations in ms*10 (RFC 6716 §3.1): configs 0-11 SILK
# {10,20,40,60}, 12-15 hybrid {10,20}, 16-31 CELT {2.5,5,10,20}
_OPUS_FRAME_MS10 = ([100, 200, 400, 600] * 3 +
                    [100, 200] * 2 +
                    [25, 50, 100, 200] * 4)


def _opus_samples(packet):
    """Decoded 48 kHz sample count of one Opus packet, from the TOC byte."""
    if not packet:
        return 0
    toc = packet[0]
    ms10 = _OPUS_FRAME_MS10[toc >> 3]
    code = toc & 0x3
    if code == 0:
        frames = 1
    elif code in (1, 2):
        frames = 2
    else:
        frames = packet[1] & 0x3F if len(packet) > 1 else 0
    return frames * ms10 * 48 // 10


class _OggOpusWriter:
    """Writes Opus packets into a minimal, spec-valid Ogg Opus stream."""

    def __init__(self, out, opus_head):
        self._out = out
        self._serial = 0x4F535355          # 'OSSU', arbitrary fixed serial
        self._seq = 0
        self._granule = 0
        self._pending = []                 # packets for the current page
        self._pending_lace = 0
        try:
            self._preskip = struct.unpack("<H", opus_head[10:12])[0]
        except Exception:
            self._preskip = 0
        self._page(opus_head, header_type=0x02, granule=0)
        tags = b"OpusTags" + struct.pack("<I", 4) + b"kodi" + struct.pack("<I", 0)
        self._page(tags, header_type=0x00, granule=0)

    def _page(self, packet, header_type, granule):
        self._flush()
        self._emit([packet], header_type, granule)

    def _emit(self, packets, header_type, granule):
        lacing = bytearray()
        body = bytearray()
        for p in packets:
            n = len(p)
            while n >= 255:
                lacing.append(255)
                n -= 255
            lacing.append(n)
            body += p
        hdr = bytearray(b"OggS")
        hdr += bytes([0, header_type])
        hdr += struct.pack("<q", granule)
        hdr += struct.pack("<I", self._serial)
        hdr += struct.pack("<I", self._seq)
        hdr += b"\x00\x00\x00\x00"         # CRC placeholder
        hdr.append(len(lacing))
        hdr += lacing
        page = bytes(hdr) + bytes(body)
        crc = _ogg_crc(page)
        page = page[:22] + struct.pack("<I", crc) + page[26:]
        self._out.write(page)
        self._seq += 1

    def _flush(self, header_type=0x00):
        if self._pending:
            self._emit(self._pending, header_type, self._granule + self._preskip)
            self._pending = []
            self._pending_lace = 0

    def add(self, packet):
        lace = len(packet) // 255 + 1
        if self._pending and self._pending_lace + lace > 255:
            self._flush()
        self._pending.append(packet)
        self._pending_lace += lace
        self._granule += _opus_samples(packet)
        if self._pending_lace >= 200:      # keep pages comfortably small
            self._flush()

    def close(self):
        # EOS page always emitted - carries the remaining packets, or is a
        # valid zero-packet page when everything already flushed
        self._emit(self._pending, 0x04, self._granule + self._preskip)
        self._pending = []
        self._pending_lace = 0


def _wav_header(data_len, rate, channels, bit_depth):
    block = channels * bit_depth // 8
    return (b"RIFF" + struct.pack("<I", 36 + data_len) + b"WAVE" +
            b"fmt " + struct.pack("<IHHIIHH", 16, 1, channels, rate,
                                  rate * block, block, bit_depth) +
            b"data" + struct.pack("<I", data_len))


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
    ogg = None
    pcm_len = 0
    with open(path_in, "rb") as f, open(path_out, "wb") as out:
        track, codec, private = None, "", b""
        kind, asc, audio = "aac", b"", {}

        def emit(frame):
            nonlocal frames_out, pcm_len
            if kind == "aac":
                out.write(_adts_header(asc, len(frame)))
                out.write(frame)
            elif kind == "opus":
                ogg.add(frame)
            elif kind == "pcm":
                out.write(frame)
                pcm_len += len(frame)
            else:
                out.write(frame)
            frames_out += 1

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
                    track, codec, private, audio = _parse_tracks(f, f.tell() + csize)
                    if track is None:
                        raise UnsupportedSource("no extractable audio track found")
                    kind = _mkv_kind(codec)
                    if kind == "aac":
                        asc = private
                    elif kind == "flac":
                        # CodecPrivate IS the complete fLaC stream header
                        out.write(private)
                    elif kind == "opus":
                        ogg = _OggOpusWriter(out, private)
                    elif kind == "pcm":
                        # placeholder header; real sizes patched on close
                        out.write(_wav_header(0, audio.get("rate", 48000),
                                              audio.get("channels", 2) or 2,
                                              audio.get("bit_depth", 16) or 16))
                elif ceid == CLUSTER and track is not None:
                    cl_end = None if csize == UNKNOWN_SIZE else f.tell() + csize
                    while cl_end is None or f.tell() < cl_end:
                        beid, bsize, _ = _read_element(f)
                        if beid is None:
                            break
                        if beid == SIMPLE_BLOCK:
                            for frame in _block_frames(f.read(bsize), track):
                                emit(frame)
                        elif beid == BLOCK_GROUP:
                            g_end = f.tell() + bsize
                            while f.tell() < g_end:
                                geid, gsize, _ = _read_element(f)
                                if geid is None:
                                    break
                                if geid == BLOCK:
                                    for frame in _block_frames(f.read(gsize), track):
                                        emit(frame)
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
        if ogg is not None:
            ogg.close()
        if kind == "pcm" and frames_out:
            out.seek(0)
            out.write(_wav_header(pcm_len, audio.get("rate", 48000),
                                  audio.get("channels", 2) or 2,
                                  audio.get("bit_depth", 16) or 16))
    if track is None:
        raise UnsupportedSource("no Tracks element found (truncated file?)")
    if not frames_out:
        raise UnsupportedSource("audio track contained no frames")
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
                        _n, codec, _p, _a = _parse_tracks(f, f.tell() + csize)
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
