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
    assert _mkv_kind("A_OPUS") == "opus"        # Ogg re-encapsulation
    assert _mkv_kind("A_PCM/INT/LIT") == "pcm"  # WAV wrap
    assert _mkv_kind("A_PCM/INT/BIG") is None   # big-endian: honest no
    assert _mkv_kind("A_VORBIS") is None        # honest: not supported


@pytest.mark.parametrize("name,ext,min_bytes", [
    ("tiny_aac.mp4", ".aac", 2000),
    ("tiny_aac.mkv", ".aac", 2000),
    ("tiny_ac3.mkv", ".ac3", 8000),
    ("tiny_eac3.mkv", ".eac3", 8000),
    ("tiny_mp3.mkv", ".mp3", 2000),
    ("tiny_flac.mkv", ".flac", 20000),
    ("tiny_opus.mkv", ".ogg", 2000),
    ("tiny_pcm.mkv", ".wav", 40000),
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
        extract_audio_track(fixture("tiny_vorbis.mkv"), str(tmp_path / "x"))


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


def test_opus_output_is_valid_ogg(tmp_path):
    """RFC 7845 shape: BOS page carries OpusHead, every page CRC verifies."""
    from resources.lib.audio_demux import _ogg_crc
    out = tmp_path / "x.ogg"
    extract_audio_track(fixture("tiny_opus.mkv"), str(out))
    data = out.read_bytes()
    assert data[:4] == b"OggS"
    assert b"OpusHead" in data[:100] and b"OpusTags" in data
    pos, pages = 0, 0
    while pos < len(data):
        assert data[pos:pos+4] == b"OggS", f"page boundary lost at {pos}"
        nseg = data[pos+26]
        body = sum(data[pos+27:pos+27+nseg])
        page = bytearray(data[pos:pos+27+nseg+body])
        stored = bytes(page[22:26])
        page[22:26] = b"\x00\x00\x00\x00"
        assert _ogg_crc(bytes(page)) == int.from_bytes(stored, "little"), \
            f"CRC mismatch on page {pages}"
        pos += 27 + nseg + body
        pages += 1
    assert pages >= 3                       # head + tags + >=1 data page
    # last page must carry EOS
    last_flags = None
    pos2 = 0
    while pos2 < len(data):
        nseg = data[pos2+26]
        body = sum(data[pos2+27:pos2+27+nseg])
        last_flags = data[pos2+5]
        pos2 += 27 + nseg + body
    assert last_flags & 0x04, "final page missing EOS flag"


def test_pcm_output_is_valid_wav(tmp_path):
    out = tmp_path / "x.wav"
    extract_audio_track(fixture("tiny_pcm.mkv"), str(out))
    data = out.read_bytes()
    assert data[:4] == b"RIFF" and data[8:12] == b"WAVE"
    import struct
    riff_len, = struct.unpack("<I", data[4:8])
    assert riff_len == len(data) - 8, "RIFF size not patched"
    fmt_tag, channels, rate = struct.unpack("<HHI", data[20:28])
    assert fmt_tag == 1 and channels == 1 and rate == 44100
    data_len, = struct.unpack("<I", data[40:44])
    assert data_len == len(data) - 44, "data chunk size not patched"
    assert abs(data_len / (rate * 2) - 1.0) < 0.05, "should be ~1 second"


def test_opus_samples_toc_table():
    from resources.lib.audio_demux import _opus_samples
    assert _opus_samples(bytes([0x78])) == 960          # config 15 = hybrid 20 ms
    assert _opus_samples(bytes([(16 << 3) | 0])) == 120  # CELT 2.5ms, 1 frame
    assert _opus_samples(bytes([(1 << 3) | 1])) == 1920  # SILK 20ms, 2 frames
    assert _opus_samples(bytes([(0 << 3) | 3, 0x03])) == 1440  # 3 x 10ms
    assert _opus_samples(b"") == 0
