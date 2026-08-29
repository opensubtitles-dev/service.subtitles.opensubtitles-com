"""SPIKE: pure-Python AAC audio extraction from MP4 -> ADTS (.aac).
Stdlib only, Python 3.6 compatible. Proves the no-ffmpeg fallback rung."""
import struct, sys, time

def boxes(buf, start, end):
    off = start
    while off + 8 <= end:
        size, btype = struct.unpack(">I4s", buf[off:off+8]); hdr = 8
        if size == 1:
            size = struct.unpack(">Q", buf[off+8:off+16])[0]; hdr = 16
        elif size == 0:
            size = end - off
        yield btype.decode("latin1"), off + hdr, off + size
        off += size

def find(buf, path, start, end):
    t = path[0]
    for btype, s, e in boxes(buf, start, end):
        if btype == t:
            return (s, e) if len(path) == 1 else find(buf, path[1:], s, e)
    return None

def extract(path_in, path_out):
    with open(path_in, "rb") as f:
        data = f.read()
    moov = find(data, ["moov"], 0, len(data))
    assert moov, "no moov"
    # find the audio trak (mp4a sample entry)
    audio = None
    for btype, s, e in boxes(data, *moov):
        if btype != "trak":
            continue
        stsd = find(data, ["mdia", "minf", "stbl", "stsd"], s, e)
        if stsd and b"mp4a" in data[stsd[0]:stsd[1]]:
            audio = (s, e); break
    assert audio, "no mp4a track"
    stbl = find(data, ["mdia", "minf", "stbl"], *audio)
    stsd = find(data, ["stsd"], *stbl)
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
    assert asc and len(asc) >= 2, "no AudioSpecificConfig"
    aot = (asc[0] >> 3) & 0x1F
    freq_idx = ((asc[0] & 7) << 1) | (asc[1] >> 7)
    channels = (asc[1] >> 3) & 0xF

    def table(name, s, e, per, skip=12):
        seg = data[s+skip:e]
        n = struct.unpack(">I", data[s+8:s+12])[0]
        return seg, n
    stsz_s, stsz_e = find(data, ["stsz"], *stbl)
    sample_size = struct.unpack(">I", data[stsz_s+4:stsz_s+8])[0]
    count = struct.unpack(">I", data[stsz_s+8:stsz_s+12])[0]
    sizes = ([sample_size]*count if sample_size else
             list(struct.unpack(">%dI" % count, data[stsz_s+12:stsz_s+12+4*count])))
    co = find(data, ["stco"], *stbl) or find(data, ["co64"], *stbl)
    is64 = data[co[0]-4:co[0]] == b"co64"
    cn = struct.unpack(">I", co[0]+4 and data[co[0]+4:co[0]+8])[0]
    fmt = ">%dQ" % cn if is64 else ">%dI" % cn
    offsets = list(struct.unpack(fmt, data[co[0]+8:co[0]+8+(8 if is64 else 4)*cn]))
    stsc_s, stsc_e = find(data, ["stsc"], *stbl)
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

t0 = time.time()
n = extract(sys.argv[1], sys.argv[2])
print(f"extracted {n} AAC frames in {time.time()-t0:.2f}s")
