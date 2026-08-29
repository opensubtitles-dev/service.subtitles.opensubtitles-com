"""Windows audio extraction via Media Foundation, through ctypes.

The Windows analog of android_audio.py: no binaries, no installs - the
SourceReader decodes whatever MF reads (MP4/AAC everywhere, MKV since
Windows 10, AC3 since 8) and the SinkWriter's AAC encoder + auto-inserted
resampler produce a small .m4a. Raw COM vtable calls via ctypes; validated
on real Windows by the audio-matrix CI workflow.

Size note: MF's AAC encoder floor is 12000 bytes/s (96 kbps) - a 2 h film
lands ~84 MB mono, inside the server's 100 MB cap but far above the ffmpeg
rung's 21 MB. Acceptable; this rung is for machines with nothing else.
"""
import ctypes
import os
from ctypes import wintypes

CO_E_ALREADYINITIALIZED = -2147417850
MF_VERSION = 0x00020070
MF_SOURCE_READER_FIRST_AUDIO_STREAM = 0xFFFFFFFD
MF_SOURCE_READER_ANY_STREAM = 0xFFFFFFFE
MF_SOURCE_READERF_ENDOFSTREAM = 0x2


class WindowsAudioError(Exception):
    pass


class GUID(ctypes.Structure):
    _fields_ = [("d1", ctypes.c_uint32), ("d2", ctypes.c_uint16),
                ("d3", ctypes.c_uint16), ("d4", ctypes.c_ubyte * 8)]

    def __init__(self, text=None):
        super().__init__()
        if text:
            part = text.strip("{}").split("-")
            self.d1 = int(part[0], 16)
            self.d2 = int(part[1], 16)
            self.d3 = int(part[2], 16)
            rest = bytes.fromhex(part[3] + part[4])
            for i, b in enumerate(rest):
                self.d4[i] = b


MF_MT_MAJOR_TYPE = GUID("48eba18e-f8c9-4687-bf11-0a74c9f96a8f")
MF_MT_SUBTYPE = GUID("f7e34c9a-42e8-4714-b74b-cb29d72c35e5")
MF_MT_AUDIO_NUM_CHANNELS = GUID("37e48bf5-645e-4c5b-89de-ada9e29b696a")
MF_MT_AUDIO_SAMPLES_PER_SECOND = GUID("5faeeae7-0290-4c31-9e8a-c534f68d9dba")
MF_MT_AUDIO_BITS_PER_SAMPLE = GUID("f2deb57f-40fa-4764-aa33-ed4f2d1ff669")
MF_MT_AUDIO_AVG_BYTES_PER_SECOND = GUID("1aab75c8-cfef-451c-ab95-ac034b8e1731")
MFMediaType_Audio = GUID("73647561-0000-0010-8000-00aa00389b71")
MFAudioFormat_PCM = GUID("00000001-0000-0010-8000-00aa00389b71")
MFAudioFormat_AAC = GUID("00001610-0000-0010-8000-00aa00389b71")

_ole32 = None
_mfplat = None
_mfreadwrite = None


def _com(obj, index, restype, *argtypes):
    """Calls vtable slot `index` on COM pointer `obj`."""
    vtbl = ctypes.cast(obj, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
    proto = ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)
    return proto(vtbl[index])


def _check(hr, what):
    if hr < 0:
        raise WindowsAudioError(f"{what} failed (hr=0x{hr & 0xFFFFFFFF:08X})")


def _release(obj):
    if obj:
        try:
            _com(obj, 2, ctypes.c_ulong)(obj)
        except Exception:
            pass


def _startup():
    global _ole32, _mfplat, _mfreadwrite
    try:
        _ole32 = ctypes.windll.ole32
        _mfplat = ctypes.windll.mfplat
        _mfreadwrite = ctypes.windll.mfreadwrite
    except (AttributeError, OSError) as e:
        raise WindowsAudioError(f"Media Foundation unavailable ({type(e).__name__})")
    hr = _ole32.CoInitializeEx(None, 0x2)      # COINIT_APARTMENTTHREADED
    if hr < 0 and hr != CO_E_ALREADYINITIALIZED and hr != 1:  # S_FALSE = 1
        _check(hr, "CoInitializeEx")
    _check(_mfplat.MFStartup(MF_VERSION, 0), "MFStartup")


def _make_type(settings):
    """IMFMediaType with the given (guid_key, kind, value) attributes set."""
    mt = ctypes.c_void_p()
    _check(_mfplat.MFCreateMediaType(ctypes.byref(mt)), "MFCreateMediaType")
    for key, kind, value in settings:
        if kind == "guid":       # IMFAttributes::SetGUID = vtable 24
            hr = _com(mt, 24, ctypes.c_long, ctypes.POINTER(GUID),
                      ctypes.POINTER(GUID))(mt, ctypes.byref(key), ctypes.byref(value))
        else:                    # IMFAttributes::SetUINT32 = vtable 21
            hr = _com(mt, 21, ctypes.c_long, ctypes.POINTER(GUID),
                      ctypes.c_uint32)(mt, ctypes.byref(key), value)
        _check(hr, "media type attribute")
    return mt


def transcode(src, dst, progress=None):
    """Decode via SourceReader, encode 96k mono AAC into .m4a via SinkWriter.

    Returns bytes written. The SinkWriter auto-inserts the resampler DSP for
    the rate/channel conversion, so any PCM the decoder yields is accepted."""
    _startup()
    reader = ctypes.c_void_p()
    writer = ctypes.c_void_p()
    try:
        _check(_mfreadwrite.MFCreateSourceReaderFromURL(
            ctypes.c_wchar_p(os.path.abspath(src)), None, ctypes.byref(reader)),
            "open source")

        # ask the reader for decoded PCM (native rate/channels)
        pcm = _make_type([(MF_MT_MAJOR_TYPE, "guid", MFMediaType_Audio),
                          (MF_MT_SUBTYPE, "guid", MFAudioFormat_PCM)])
        # IMFSourceReader::SetCurrentMediaType = vtable 7
        _check(_com(reader, 7, ctypes.c_long, ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p)(
            reader, MF_SOURCE_READER_FIRST_AUDIO_STREAM, None, pcm),
            "decode to PCM (no audio decoder for this codec?)")
        _release(pcm)

        if os.path.exists(dst):
            os.unlink(dst)
        _check(_mfreadwrite.MFCreateSinkWriterFromURL(
            ctypes.c_wchar_p(os.path.abspath(dst)), None, None,
            ctypes.byref(writer)), "create sink writer")

        aac = _make_type([(MF_MT_MAJOR_TYPE, "guid", MFMediaType_Audio),
                          (MF_MT_SUBTYPE, "guid", MFAudioFormat_AAC),
                          (MF_MT_AUDIO_NUM_CHANNELS, "u32", 1),
                          (MF_MT_AUDIO_SAMPLES_PER_SECOND, "u32", 44100),
                          (MF_MT_AUDIO_BITS_PER_SAMPLE, "u32", 16),
                          (MF_MT_AUDIO_AVG_BYTES_PER_SECOND, "u32", 12000)])
        stream = ctypes.c_uint32()
        # IMFSinkWriter::AddStream = vtable 3
        _check(_com(writer, 3, ctypes.c_long, ctypes.c_void_p,
                    ctypes.POINTER(ctypes.c_uint32))(writer, aac,
                    ctypes.byref(stream)), "add AAC stream (encoder present?)")
        _release(aac)

        # the reader's ACTUAL output type becomes the writer's input type
        current = ctypes.c_void_p()
        # IMFSourceReader::GetCurrentMediaType = vtable 6
        _check(_com(reader, 6, ctypes.c_long, ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_void_p))(
            reader, MF_SOURCE_READER_FIRST_AUDIO_STREAM, ctypes.byref(current)),
            "read PCM type")
        # IMFSinkWriter::SetInputMediaType = vtable 4
        _check(_com(writer, 4, ctypes.c_long, ctypes.c_uint32, ctypes.c_void_p,
                    ctypes.c_void_p)(writer, stream.value, current, None),
            "set writer input (resampler unavailable?)")
        _release(current)

        # IMFSinkWriter::BeginWriting = vtable 5
        _check(_com(writer, 5, ctypes.c_long)(writer), "begin writing")

        read_sample = _com(reader, 9, ctypes.c_long, ctypes.c_uint32,
                           ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32),
                           ctypes.POINTER(ctypes.c_uint32),
                           ctypes.POINTER(ctypes.c_longlong),
                           ctypes.POINTER(ctypes.c_void_p))
        write_sample = _com(writer, 6, ctypes.c_long, ctypes.c_uint32,
                            ctypes.c_void_p)
        while True:
            if progress and progress.iscanceled():
                raise WindowsAudioError("cancelled")
            actual = ctypes.c_uint32()
            flags = ctypes.c_uint32()
            ts = ctypes.c_longlong()
            sample = ctypes.c_void_p()
            _check(read_sample(reader, MF_SOURCE_READER_FIRST_AUDIO_STREAM, 0,
                               ctypes.byref(actual), ctypes.byref(flags),
                               ctypes.byref(ts), ctypes.byref(sample)),
                   "read sample")
            if flags.value & MF_SOURCE_READERF_ENDOFSTREAM:
                _release(sample)
                break
            if sample:
                _check(write_sample(writer, stream.value, sample), "write sample")
                _release(sample)

        # IMFSinkWriter::Finalize = vtable 11
        _check(_com(writer, 11, ctypes.c_long)(writer), "finalize")
        size = os.path.getsize(dst)
        if not size:
            raise WindowsAudioError("encoder produced no output")
        return size
    finally:
        _release(writer)
        _release(reader)
        try:
            _mfplat.MFShutdown()
        except Exception:
            pass
