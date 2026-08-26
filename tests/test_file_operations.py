"""Regression tests for get_file_data path normalization.

The historic code stripped six characters from EVERY non-temp path (a leftover
of "rar://" prefix handling), which mangled the basename of plain local paths -
"/tv/E1.mkv" became ".mkv" - and with it the fallback search query and smart
ranking. Flagged by review on the Kodi repo submission (PR #4809).
"""
from unittest.mock import patch

from resources.lib.file_operations import get_file_data


def _no_hash(*_args, **_kwargs):
    return 0, "0000000000000000"


def test_local_path_keeps_full_basename():
    with patch("resources.lib.file_operations.hash_file", side_effect=_no_hash):
        item = get_file_data("/movies/The.Matrix.1999.1080p.mkv")
    assert item["basename"] == "The.Matrix.1999.1080p.mkv"
    assert item["file_original_path"] == "/movies/The.Matrix.1999.1080p.mkv"


def test_short_local_path_not_mangled():
    # "/tv/E1.mkv"[6:] == ".mkv" - the exact failure mode of the old slice
    with patch("resources.lib.file_operations.hash_file", side_effect=_no_hash):
        item = get_file_data("/tv/E1.mkv")
    assert item["basename"] == "E1.mkv"


def test_rar_path_keeps_archive_content_basename():
    with patch("resources.lib.file_operations.hash_file", side_effect=_no_hash):
        item = get_file_data("rar://%2fmovies%2ffoo.rar/The.Movie.2020.mkv")
    assert item["rar"] is True
    assert item["basename"] == "The.Movie.2020.mkv"


def test_stack_path_uses_first_part():
    with patch("resources.lib.file_operations.hash_file", side_effect=_no_hash):
        item = get_file_data("stack:///movies/part1.mkv , /movies/part2.mkv")
    assert item["file_original_path"] == "/movies/part1.mkv"
    assert item["basename"] == "part1.mkv"
