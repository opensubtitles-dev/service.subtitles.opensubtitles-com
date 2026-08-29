"""Pure-Python demux: full offline validation against tiny committed fixtures
(1-second real assets, built with ffmpeg - tests/fixtures/), plus the codec
table and extension probing (docs/audio_support_matrix.md)."""
import os
import struct

import pytest

from resources.lib.audio_demux import (extract_audio_track, probe_extension,
                                       _mkv_kind, UnsupportedSource)

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def fixture(name):
    return os.path.join(FIXTURES, name)


def test_mkv_codec_table_covers_the_film_world():
    for codec, kind in (("A_AAC", "aac"), ("A_AAC/MPEG4/LC", "aac"),
                        ("A_AC3", "raw"), ("A_EAC3", "raw"),
                        ("A_MPEG/L3", "raw"), ("A_DTS", "raw"),
                        ("A_FLAC", "flac")):
        assert _mkv_kind(codec) == kind, codec
    assert _mkv_kind("A_OPUS") is None          # honest: not supported
    assert _mkv_kind("A_PCM/INT/LIT") is None


@pytest.mark.parametrize("name,ext,min_bytes", [
    ("tiny_aac.mp4", ".aac", 2000),
    ("tiny_aac.mkv", ".aac", 2000),
    ("tiny_ac3.mkv", ".ac3", 8000),
    ("tiny_eac3.mkv", ".eac3", 8000),
    ("tiny_mp3.mkv", ".mp3", 2000),
    ("tiny_flac.mkv", ".flac", 20000),
])
def test_extraction_against_real_fixture(tmp_path, name, ext, min_bytes):
    assert probe_extension(fixture(name)) == ext
    out = tmp_path / (name + ext)
    frames = extract_audio_track(fixture(name), str(out))
    assert frames > 5
    assert out.stat().st_size >= min_bytes


def test_aac_output_is_valid_adts(tmp_path):
    out = tmp_path / "x.aac"
    extract_audio_track(fixture("tiny_aac.mkv"), str(out))
    data = out.read_bytes()
    assert data[0] == 0xFF and (data[1] & 0xF0) == 0xF0, "ADTS syncword"
    # frame length field of the first header must point at the next syncword
    flen = ((data[3] & 0x03) << 11) | (data[4] << 3) | (data[5] >> 5)
    assert data[flen] == 0xFF and (data[flen + 1] & 0xF0) == 0xF0


def test_mkv_and_mp4_routes_agree(tmp_path):
    a = tmp_path / "a.aac"
    b = tmp_path / "b.aac"
    extract_audio_track(fixture("tiny_aac.mkv"), str(a))
    extract_audio_track(fixture("tiny_aac.mp4"), str(b))
    # same source track remuxed - the extracted streams must be identical
    assert a.read_bytes() == b.read_bytes()


def test_unsupported_codec_rejected_honestly(tmp_path):
    with pytest.raises(UnsupportedSource):
        extract_audio_track(fixture("tiny_opus.mkv"), str(tmp_path / "x"))


def test_unrecognized_container_rejected(tmp_path):
    junk = tmp_path / "x.bin"
    junk.write_bytes(b"\x00" * 64)
    with pytest.raises(UnsupportedSource):
        extract_audio_track(str(junk), str(tmp_path / "y"))
    truncated = tmp_path / "t.mkv"
    truncated.write_bytes(b"\x1aE\xdf\xa3")     # EBML magic, nothing else
    with pytest.raises(UnsupportedSource):
        extract_audio_track(str(truncated), str(tmp_path / "z"))


def test_probe_extension_defaults_to_aac_for_mp4(tmp_path):
    f = tmp_path / "x.mp4"
    f.write_bytes(struct.pack(">I", 20) + b"ftypisom" + b"\0" * 12)
    assert probe_extension(str(f)) == ".aac"
