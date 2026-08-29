"""Platform audio engines - everything testable WITHOUT the platform.

The Android/Windows engines are validated on real systems (emulator + CI);
these tests cover their pure logic so a regression is caught by any local
pytest run, not only by the next device campaign."""
import ctypes
import struct
import sys
from unittest.mock import patch, MagicMock

import pytest


# --- android_audio ---------------------------------------------------------

def test_android_adts_header_matches_spec():
    from resources.lib.android_audio import _adts, _SAMPLE_RATES
    hdr = _adts(2, _SAMPLE_RATES.index(48000), 1, 100)
    assert len(hdr) == 7
    assert hdr[0] == 0xFF and (hdr[1] & 0xF0) == 0xF0          # syncword
    assert (hdr[1] & 0x08) == 0                                 # MPEG-4
    flen = ((hdr[3] & 0x03) << 11) | (hdr[4] << 3) | (hdr[5] >> 5)
    assert flen == 107                                          # frame + header
    profile = (hdr[2] >> 6) & 0x3
    assert profile == 1                                         # AAC-LC (aot 2 - 1)


def test_android_sample_rate_snapping():
    from resources.lib.android_audio import _SAMPLE_RATES
    # the transcode path snaps odd rates to the nearest ADTS-expressible one
    assert min(_SAMPLE_RATES, key=lambda r: abs(r - 47999)) == 48000
    assert min(_SAMPLE_RATES, key=lambda r: abs(r - 11000)) == 11025


def test_android_lib_failure_is_controlled():
    from resources.lib import android_audio
    with patch.object(ctypes, "CDLL", side_effect=OSError("nope")):
        with pytest.raises(android_audio.AndroidAudioError):
            android_audio._lib()


# --- windows_audio ---------------------------------------------------------

def test_windows_guid_parsing_roundtrip():
    from resources.lib.windows_audio import GUID
    g = GUID("73647561-0000-0010-8000-00aa00389b71")
    assert g.d1 == 0x73647561
    assert g.d2 == 0x0000
    assert g.d3 == 0x0010
    assert bytes(g.d4) == bytes.fromhex("800000aa00389b71")


def test_windows_check_raises_with_hresult():
    from resources.lib.windows_audio import _check, WindowsAudioError
    _check(0, "fine")                    # S_OK passes
    _check(1, "s_false")                 # S_FALSE passes
    with pytest.raises(WindowsAudioError) as e:
        _check(-2147024809, "bad param")  # E_INVALIDARG
    assert "0x80070057" in str(e.value)


def test_windows_startup_unavailable_off_windows():
    from resources.lib import windows_audio
    # off-Windows there is no ctypes.windll - must be a controlled error
    if not hasattr(ctypes, "windll"):
        with pytest.raises(windows_audio.WindowsAudioError):
            windows_audio._startup()


# --- transcriber ladder fallbacks -----------------------------------------

def test_android_rung_falls_back_to_ndk_demux(tmp_path):
    """NDK transcode failing (no decoder on device) must fall through to the
    NDK AAC demux, not abort."""
    from resources.lib import transcriber
    from resources.lib import android_audio

    out_holder = {}

    def fake_extract(src, dst):
        with open(dst, "wb") as f:
            f.write(b"\xff\xf1" + b"\x00" * 100)
        out_holder["dst"] = dst
        return 1

    with patch.object(transcriber, "_profile_dir", return_value=str(tmp_path)), \
         patch.object(android_audio, "transcode",
                      side_effect=android_audio.AndroidAudioError("no decoder")), \
         patch.object(android_audio, "extract_aac", side_effect=fake_extract):
        result = transcriber.extract_android("/video/x.mkv")
    assert result == out_holder["dst"]


def test_android_rung_caps_demuxed_track(tmp_path):
    from resources.lib import transcriber
    from resources.lib import android_audio

    def fat_extract(src, dst):
        with open(dst, "wb") as f:
            f.seek(transcriber.MAX_UPLOAD_BYTES)
            f.write(b"x")
        return 1

    with patch.object(transcriber, "_profile_dir", return_value=str(tmp_path)), \
         patch.object(android_audio, "transcode",
                      side_effect=android_audio.AndroidAudioError("no decoder")), \
         patch.object(android_audio, "extract_aac", side_effect=fat_extract):
        with pytest.raises(transcriber.TranscriptionError):
            transcriber.extract_android("/video/x.mkv")


def test_windows_rung_falls_back_to_pydemux(tmp_path):
    """MF failing (codec/feature gap) must fall through to pydemux inside the
    run_transcription dispatch."""
    import xbmc
    from resources.lib import transcriber
    from resources.lib import windows_audio

    src = tmp_path / "movie.mkv"
    src.write_bytes(b"\x1aE\xdf\xa3" + b"\x00" * 100)

    caps = {"ffmpeg": "", "encode_x_realtime": None}
    calls = []

    def fake_pydemux(path):
        calls.append(path)
        out = tmp_path / "out.aac"
        out.write_bytes(b"\xff\xf1" + b"\x00" * 50)
        return str(out)

    def windows_only(cond):
        return "Windows" in cond

    with patch.object(transcriber, "get_capabilities", return_value=caps), \
         patch.object(xbmc, "getCondVisibility", side_effect=windows_only), \
         patch.object(windows_audio, "transcode",
                      side_effect=windows_audio.WindowsAudioError("no MF")), \
         patch.object(transcriber, "extract_pydemux", side_effect=fake_pydemux), \
         patch.object(transcriber, "_profile_dir", return_value=str(tmp_path)), \
         patch.object(transcriber, "MockTranscriptionClient") as mock_client, \
         patch("resources.lib.transcriber.xbmcgui.DialogProgress",
               return_value=MagicMock(iscanceled=lambda: False)):
        mock_client.return_value.list_apis.return_value = [
            {"name": "mock", "display_name": "Mock", "price": 0,
             "languages_supported": [{"language_code": "auto"}]}]
        mock_client.return_value.create_job.return_value = {
            "status": "CREATED", "correlation_id": "c1"}
        done = tmp_path / "done.srt"
        done.write_text("1\n00:00:01,000 --> 00:00:02,000\nHi\n")
        mock_client.return_value.poll.return_value = {
            "status": "COMPLETED", "url": "file://" + str(done)}
        result = transcriber.run_transcription(
            None, "", {"file_original_path": str(src)}, "en", mock=True)
    assert calls, "pydemux fallback must run when MF fails"
    assert result == str(done)
