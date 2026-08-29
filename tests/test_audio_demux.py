"""Generalized pure-Python demux: MKV raw tracks + extension probing
(docs/audio_extraction_matrix.md - measured against a full codec grid)."""
import struct

from resources.lib.audio_demux import _mkv_kind, probe_extension


def test_mkv_codec_table_covers_the_film_world():
    for codec, kind in (("A_AAC", "aac"), ("A_AAC/MPEG4/LC", "aac"),
                        ("A_AC3", "raw"), ("A_EAC3", "raw"),
                        ("A_MPEG/L3", "raw"), ("A_DTS", "raw"),
                        ("A_FLAC", "flac")):
        assert _mkv_kind(codec) == kind, codec
    assert _mkv_kind("A_OPUS") is None          # honest: not supported
    assert _mkv_kind("A_PCM/INT/LIT") is None


def test_probe_extension_defaults_to_aac_for_mp4(tmp_path):
    f = tmp_path / "x.mp4"
    f.write_bytes(struct.pack(">I", 20) + b"ftypisom" + b"\0" * 12)
    assert probe_extension(str(f)) == ".aac"
