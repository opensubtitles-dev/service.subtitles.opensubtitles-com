"""Android audio extraction via the NDK media stack, through ctypes.

PROBE-VERIFIED (docs/audio_extraction_matrix.md): Kodi's Android Python can
dlopen the SYSTEM library libmediandk.so (only writable files are barred by
W^X), and every symbol used here resolves on real Kodi 21.3 / API 31. The
NDK media APIs exist since API 21, so old boxes are covered too.

Two rungs, no binaries anywhere:

  extract_aac(src, dst)     demux the AAC track of ANY container Android can
                            read (MKV/MP4/TS/AVI...) -> ADTS. No decoding.
  transcode(src, dst, ...)  decode ANY codec the device knows (AC3/DTS/EAC3
                            on most boxes) -> pick one channel (C-speed
                            strided copy) -> AMediaCodec AAC encode at 24k,
                            source sample rate -> ADTS. ffmpeg-rung parity.

Both raise AndroidAudioError with an honest, path-free message on failure so
the caller can fall through to the next rung.
"""
import ctypes
import os
import struct

TIMEOUT_US = 10000
ENCODER_MIME = b"audio/mp4a-latm"
TARGET_BITRATE = 24000
BUFFER_FLAG_CODEC_CONFIG = 2
BUFFER_FLAG_END_OF_STREAM = 4
INFO_OUTPUT_FORMAT_CHANGED = -2
INFO_TRY_AGAIN_LATER = -1
INFO_OUTPUT_BUFFERS_CHANGED = -3

_SAMPLE_RATES = (96000, 88200, 64000, 48000, 44100, 32000, 24000, 22050,
                 16000, 12000, 11025, 8000, 7350)


class AndroidAudioError(Exception):
    pass


class _BufferInfo(ctypes.Structure):
    _fields_ = [("offset", ctypes.c_int32), ("size", ctypes.c_int32),
                ("presentationTimeUs", ctypes.c_int64),
                ("flags", ctypes.c_uint32)]


def _lib():
    try:
        lib = ctypes.CDLL("libmediandk.so")
    except OSError as e:
        raise AndroidAudioError(f"libmediandk.so unavailable ({type(e).__name__})")
    p = ctypes.POINTER
    lib.AMediaExtractor_new.restype = ctypes.c_void_p
    lib.AMediaExtractor_setDataSourceFd.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                                    ctypes.c_int64, ctypes.c_int64]
    lib.AMediaExtractor_getTrackCount.restype = ctypes.c_size_t
    lib.AMediaExtractor_getTrackCount.argtypes = [ctypes.c_void_p]
    lib.AMediaExtractor_getTrackFormat.restype = ctypes.c_void_p
    lib.AMediaExtractor_getTrackFormat.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    lib.AMediaExtractor_selectTrack.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    lib.AMediaExtractor_readSampleData.restype = ctypes.c_ssize_t
    lib.AMediaExtractor_readSampleData.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                                   ctypes.c_size_t]
    lib.AMediaExtractor_getSampleTime.restype = ctypes.c_int64
    lib.AMediaExtractor_getSampleTime.argtypes = [ctypes.c_void_p]
    lib.AMediaExtractor_advance.restype = ctypes.c_bool
    lib.AMediaExtractor_advance.argtypes = [ctypes.c_void_p]
    lib.AMediaExtractor_delete.argtypes = [ctypes.c_void_p]
    lib.AMediaFormat_getString.restype = ctypes.c_bool
    lib.AMediaFormat_getString.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                           p(ctypes.c_char_p)]
    lib.AMediaFormat_getInt32.restype = ctypes.c_bool
    lib.AMediaFormat_getInt32.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                          p(ctypes.c_int32)]
    lib.AMediaFormat_getBuffer.restype = ctypes.c_bool
    lib.AMediaFormat_getBuffer.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                           p(ctypes.c_void_p), p(ctypes.c_size_t)]
    lib.AMediaFormat_new.restype = ctypes.c_void_p
    lib.AMediaFormat_setString.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                           ctypes.c_char_p]
    lib.AMediaFormat_setInt32.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                          ctypes.c_int32]
    lib.AMediaFormat_delete.argtypes = [ctypes.c_void_p]
    lib.AMediaCodec_createDecoderByType.restype = ctypes.c_void_p
    lib.AMediaCodec_createDecoderByType.argtypes = [ctypes.c_char_p]
    lib.AMediaCodec_createEncoderByType.restype = ctypes.c_void_p
    lib.AMediaCodec_createEncoderByType.argtypes = [ctypes.c_char_p]
    lib.AMediaCodec_configure.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                          ctypes.c_void_p, ctypes.c_void_p,
                                          ctypes.c_uint32]
    lib.AMediaCodec_start.argtypes = [ctypes.c_void_p]
    lib.AMediaCodec_stop.argtypes = [ctypes.c_void_p]
    lib.AMediaCodec_delete.argtypes = [ctypes.c_void_p]
    lib.AMediaCodec_dequeueInputBuffer.restype = ctypes.c_ssize_t
    lib.AMediaCodec_dequeueInputBuffer.argtypes = [ctypes.c_void_p, ctypes.c_int64]
    lib.AMediaCodec_getInputBuffer.restype = p(ctypes.c_uint8)
    lib.AMediaCodec_getInputBuffer.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                                               p(ctypes.c_size_t)]
    lib.AMediaCodec_queueInputBuffer.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                                                 ctypes.c_int64, ctypes.c_size_t,
                                                 ctypes.c_uint64, ctypes.c_uint32]
    lib.AMediaCodec_dequeueOutputBuffer.restype = ctypes.c_ssize_t
    lib.AMediaCodec_dequeueOutputBuffer.argtypes = [ctypes.c_void_p,
                                                    p(_BufferInfo), ctypes.c_int64]
    lib.AMediaCodec_getOutputBuffer.restype = p(ctypes.c_uint8)
    lib.AMediaCodec_getOutputBuffer.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                                                p(ctypes.c_size_t)]
    lib.AMediaCodec_releaseOutputBuffer.argtypes = [ctypes.c_void_p, ctypes.c_size_t,
                                                    ctypes.c_bool]
    lib.AMediaCodec_getOutputFormat.restype = ctypes.c_void_p
    lib.AMediaCodec_getOutputFormat.argtypes = [ctypes.c_void_p]
    return lib


def _fmt_str(lib, fmt, key):
    out = ctypes.c_char_p()
    if lib.AMediaFormat_getString(fmt, key, ctypes.byref(out)) and out.value:
        return out.value.decode("latin1")
    return ""


def _fmt_int(lib, fmt, key, default=0):
    out = ctypes.c_int32()
    if lib.AMediaFormat_getInt32(fmt, key, ctypes.byref(out)):
        return int(out.value)
    return default


def _open_audio_track(lib, src):
    """Returns (extractor, fd, track_index, track_format). Caller cleans up."""
    ex = lib.AMediaExtractor_new()
    if not ex:
        raise AndroidAudioError("AMediaExtractor_new failed")
    fd = os.open(src, os.O_RDONLY)
    status = lib.AMediaExtractor_setDataSourceFd(ex, fd, 0, os.fstat(fd).st_size)
    if status != 0:
        os.close(fd)
        lib.AMediaExtractor_delete(ex)
        raise AndroidAudioError(f"extractor rejected the source (status {status})")
    for idx in range(lib.AMediaExtractor_getTrackCount(ex)):
        fmt = lib.AMediaExtractor_getTrackFormat(ex, idx)
        mime = _fmt_str(lib, fmt, b"mime")
        if mime.startswith("audio/"):
            return ex, fd, idx, fmt, mime
        lib.AMediaFormat_delete(fmt)
    os.close(fd)
    lib.AMediaExtractor_delete(ex)
    raise AndroidAudioError("no audio track in the source")


def _adts(asc_aot, freq_idx, channels, frame_len):
    flen = frame_len + 7
    hdr = bytearray(7)
    hdr[0] = 0xFF
    hdr[1] = 0xF1
    hdr[2] = ((asc_aot - 1) << 6) | (freq_idx << 2) | (channels >> 2)
    hdr[3] = ((channels & 3) << 6) | (flen >> 11)
    hdr[4] = (flen >> 3) & 0xFF
    hdr[5] = ((flen & 7) << 5) | 0x1F
    hdr[6] = 0xFC
    return bytes(hdr)


def extract_aac(src, dst):
    """Demux the AAC track of any Android-readable container to ADTS.

    Returns frames written. Raises AndroidAudioError when the audio track is
    not AAC (use transcode()) or the container is unreadable."""
    lib = _lib()
    ex, fd, idx, fmt, mime = _open_audio_track(lib, src)
    try:
        if mime not in ("audio/mp4a-latm", "audio/aac"):
            raise AndroidAudioError(f"audio track is {mime}, not AAC - transcode instead")
        data_p = ctypes.c_void_p()
        size = ctypes.c_size_t()
        if not lib.AMediaFormat_getBuffer(fmt, b"csd-0", ctypes.byref(data_p),
                                          ctypes.byref(size)) or size.value < 2:
            raise AndroidAudioError("no AAC codec config (csd-0) on the track")
        asc = ctypes.string_at(data_p, size.value)
        aot = (asc[0] >> 3) & 0x1F
        freq_idx = ((asc[0] & 7) << 1) | (asc[1] >> 7)
        channels = (asc[1] >> 3) & 0xF

        lib.AMediaExtractor_selectTrack(ex, idx)
        cap = 1 << 20
        buf = ctypes.create_string_buffer(cap)
        frames = 0
        with open(dst, "wb") as out:
            while True:
                n = lib.AMediaExtractor_readSampleData(ex, buf, cap)
                if n < 0:
                    break
                out.write(_adts(aot, freq_idx, channels, n))
                out.write(buf.raw[:n])
                frames += 1
                if not lib.AMediaExtractor_advance(ex):
                    break
        return frames
    finally:
        lib.AMediaFormat_delete(fmt)
        lib.AMediaExtractor_delete(ex)
        os.close(fd)


def _drain(lib, codec, info, on_output, timeout=TIMEOUT_US):
    """Pulls every ready output buffer from codec into on_output(bytes)."""
    while True:
        oidx = lib.AMediaCodec_dequeueOutputBuffer(codec, ctypes.byref(info), timeout)
        if oidx == INFO_OUTPUT_FORMAT_CHANGED or oidx == INFO_OUTPUT_BUFFERS_CHANGED:
            continue
        if oidx < 0:
            return False
        # codec-config buffers (CSD) are format data, not audio frames -
        # wrapping one in ADTS litters the stream with an undecodable frame
        if info.size > 0 and not (info.flags & BUFFER_FLAG_CODEC_CONFIG):
            osize = ctypes.c_size_t()
            optr = lib.AMediaCodec_getOutputBuffer(codec, oidx, ctypes.byref(osize))
            on_output(ctypes.string_at(
                ctypes.addressof(optr.contents) + info.offset, info.size))
        eos = bool(info.flags & BUFFER_FLAG_END_OF_STREAM)
        lib.AMediaCodec_releaseOutputBuffer(codec, oidx, False)
        if eos:
            return True


def transcode(src, dst, progress=None, duration_s=0):
    """Decode any device-supported audio codec, reduce to mono, re-encode as
    24k AAC at the SOURCE sample rate, write ADTS. Parity with the ffmpeg rung.

    No resampling on purpose: Kodi's Android Python ships without audioop
    (verified on-device), and none is needed - the upload size is set by the
    24k bitrate alone and the server's ASR resamples anyway. Multichannel PCM
    is reduced by taking channel 0 (a strided memoryview copy - C speed)."""
    lib = _lib()
    ex, fd, idx, fmt, mime = _open_audio_track(lib, src)
    decoder = encoder = None
    enc_fmt = None
    try:
        src_rate = _fmt_int(lib, fmt, b"sample-rate", 48000)
        src_ch = max(1, _fmt_int(lib, fmt, b"channel-count", 2))

        decoder = lib.AMediaCodec_createDecoderByType(mime.encode())
        if not decoder:
            raise AndroidAudioError(f"no decoder for {mime} on this device")
        lib.AMediaCodec_configure(decoder, fmt, None, None, 0)
        lib.AMediaCodec_start(decoder)

        if src_rate not in _SAMPLE_RATES:
            # ADTS can only express the standard rates - snap to the nearest
            src_rate = min(_SAMPLE_RATES, key=lambda r: abs(r - src_rate))
        enc_fmt = lib.AMediaFormat_new()
        lib.AMediaFormat_setString(enc_fmt, b"mime", ENCODER_MIME)
        lib.AMediaFormat_setInt32(enc_fmt, b"sample-rate", src_rate)
        lib.AMediaFormat_setInt32(enc_fmt, b"channel-count", 1)
        lib.AMediaFormat_setInt32(enc_fmt, b"bitrate", TARGET_BITRATE)
        lib.AMediaFormat_setInt32(enc_fmt, b"aac-profile", 2)   # AAC-LC
        encoder = lib.AMediaCodec_createEncoderByType(ENCODER_MIME)
        if not encoder:
            raise AndroidAudioError("no AAC encoder on this device")
        lib.AMediaCodec_configure(encoder, enc_fmt, None, None, 1)  # 1 = encode
        lib.AMediaCodec_start(encoder)

        lib.AMediaExtractor_selectTrack(ex, idx)
        cap = 1 << 20
        sample_buf = ctypes.create_string_buffer(cap)
        info = _BufferInfo()
        freq_idx = _SAMPLE_RATES.index(src_rate)
        out = open(dst, "wb")
        frames = [0]
        enc_pts = [0]

        def write_encoded(chunk):
            out.write(_adts(2, freq_idx, 1, len(chunk)))
            out.write(chunk)
            frames[0] += 1

        def feed_encoder(pcm, eos=False):
            # feed 16k mono PCM into the encoder in input-buffer sized bites
            pos = 0
            while pos < len(pcm) or eos:
                iidx = lib.AMediaCodec_dequeueInputBuffer(encoder, TIMEOUT_US)
                if iidx < 0:
                    _drain(lib, encoder, info, write_encoded)
                    continue
                isize = ctypes.c_size_t()
                iptr = lib.AMediaCodec_getInputBuffer(encoder, iidx, ctypes.byref(isize))
                take = min(isize.value, len(pcm) - pos)
                if take > 0:
                    ctypes.memmove(iptr, pcm[pos:pos + take], take)
                flag = BUFFER_FLAG_END_OF_STREAM if (eos and pos + take >= len(pcm)) else 0
                lib.AMediaCodec_queueInputBuffer(encoder, iidx, 0, take,
                                                 enc_pts[0], flag)
                enc_pts[0] += (take // 2) * 1000000 // src_rate
                pos += take
                if flag:
                    return
                _drain(lib, encoder, info, write_encoded, timeout=0)

        def on_pcm(raw):
            # channel 0 only - a strided memoryview copy runs at C speed
            if src_ch > 1:
                mono = bytes(memoryview(raw).cast("h")[0::src_ch])
            else:
                mono = raw
            feed_encoder(mono)

        extractor_done = False
        decoder_done = False
        while not decoder_done:
            if not extractor_done:
                iidx = lib.AMediaCodec_dequeueInputBuffer(decoder, TIMEOUT_US)
                if iidx >= 0:
                    n = lib.AMediaExtractor_readSampleData(ex, sample_buf, cap)
                    if n < 0:
                        lib.AMediaCodec_queueInputBuffer(
                            decoder, iidx, 0, 0, 0, BUFFER_FLAG_END_OF_STREAM)
                        extractor_done = True
                    else:
                        isize = ctypes.c_size_t()
                        iptr = lib.AMediaCodec_getInputBuffer(decoder, iidx,
                                                              ctypes.byref(isize))
                        ctypes.memmove(iptr, sample_buf.raw, n)
                        pts = lib.AMediaExtractor_getSampleTime(ex)
                        lib.AMediaCodec_queueInputBuffer(decoder, iidx, 0, n,
                                                         max(pts, 0), 0)
                        lib.AMediaExtractor_advance(ex)
                        if progress and duration_s and pts > 0:
                            pct = min(70, 5 + int(pts / 1000000 / duration_s * 65))
                            progress.update(pct, "Extracting audio (device decoder)...")
                            if progress.iscanceled():
                                raise AndroidAudioError("cancelled")
            decoder_done = _drain(lib, decoder, info, on_pcm,
                                  timeout=0 if not extractor_done else TIMEOUT_US)
        feed_encoder(b"", eos=True)
        _drain(lib, encoder, info, write_encoded, timeout=200000)
        out.close()
        if not frames[0]:
            raise AndroidAudioError("device codecs produced no audio")
        return frames[0]
    finally:
        for codec in (decoder, encoder):
            if codec:
                try:
                    lib.AMediaCodec_stop(codec)
                except Exception:
                    pass
                lib.AMediaCodec_delete(codec)
        if enc_fmt:
            lib.AMediaFormat_delete(enc_fmt)
        lib.AMediaFormat_delete(fmt)
        lib.AMediaExtractor_delete(ex)
        os.close(fd)
