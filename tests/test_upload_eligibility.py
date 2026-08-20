"""Covers the auto-upload dry-run eligibility checks (resources/lib/upload_eligibility.py)."""
import pytest

from resources.lib.upload_eligibility import check_upload_eligibility, format_resume


def _srt(cues=30):
    blocks = []
    for i in range(cues):
        blocks.append(f"{i+1}\n00:{i:02d}:01,000 --> 00:{i:02d}:03,500\nLine {i+1}\n")
    return ("\n".join(blocks)).encode("utf-8")


def _session(tmp_path, **overrides):
    sub = tmp_path / "Movie.2024.en.srt"
    sub.write_bytes(_srt())
    session = {
        "origin": "local",
        "sub_path": str(sub),
        "sub_language": "en",
        "total_time": 6000.0,
        "last_position": 5500.0,     # ~92% watched
        "subtitle_delay": "0.000 s",
        "stream_switched": False,
        "media": {"imdb_id": 123},
        "moviehash": "8e245d9679d31e12",
    }
    session.update(overrides)
    return session


def _failed(checks):
    return [name for name, passed, _detail in checks if not passed]


def test_perfect_session_is_eligible(tmp_path):
    eligible, checks = check_upload_eligibility(_session(tmp_path), consent_enabled=True)
    assert eligible, format_resume(eligible, checks)
    assert _failed(checks) == []


def test_consent_off_blocks_everything(tmp_path):
    eligible, checks = check_upload_eligibility(_session(tmp_path), consent_enabled=False)
    assert not eligible and "consent" in _failed(checks)


def test_opensubtitles_sourced_file_is_never_reuploaded(tmp_path):
    eligible, checks = check_upload_eligibility(
        _session(tmp_path, origin="opensubtitles"), consent_enabled=True)
    assert not eligible and "origin" in _failed(checks)


def test_under_80_percent_watched_fails(tmp_path):
    eligible, checks = check_upload_eligibility(
        _session(tmp_path, last_position=4000.0), consent_enabled=True)  # 66%
    assert not eligible and "watched-80pct" in _failed(checks)


def test_adjusted_subtitle_offset_fails(tmp_path):
    eligible, checks = check_upload_eligibility(
        _session(tmp_path, subtitle_delay="1.500 s"), consent_enabled=True)
    assert not eligible and "no-subtitle-offset" in _failed(checks)


def test_stream_switch_mid_playback_fails(tmp_path):
    eligible, checks = check_upload_eligibility(
        _session(tmp_path, stream_switched=True), consent_enabled=True)
    assert not eligible and "no-stream-switch" in _failed(checks)


def test_empty_subtitle_file_fails(tmp_path):
    session = _session(tmp_path)
    with open(session["sub_path"], "wb") as f:
        f.write(b"")
    eligible, checks = check_upload_eligibility(session, consent_enabled=True)
    failed = _failed(checks)
    assert not eligible and "file-size" in failed and "content-not-empty" in failed


def test_non_subtitle_content_fails(tmp_path):
    session = _session(tmp_path)
    with open(session["sub_path"], "wb") as f:
        f.write(b"just some prose without any timestamps " * 50)
    eligible, checks = check_upload_eligibility(session, consent_enabled=True)
    assert not eligible and "looks-like-subtitle" in _failed(checks)


def test_missing_file_short_circuits(tmp_path):
    eligible, checks = check_upload_eligibility(
        _session(tmp_path, sub_path=str(tmp_path / "gone.srt")), consent_enabled=True)
    assert not eligible and "file-exists" in _failed(checks)


def test_oversized_file_fails(tmp_path):
    session = _session(tmp_path)
    with open(session["sub_path"], "wb") as f:
        f.write(_srt() + b"x" * (3 * 1024 * 1024))
    eligible, checks = check_upload_eligibility(session, consent_enabled=True)
    assert not eligible and "file-size" in _failed(checks)


def test_resume_format_names_every_check(tmp_path):
    eligible, checks = check_upload_eligibility(_session(tmp_path), consent_enabled=True)
    resume = format_resume(eligible, checks)
    assert resume.startswith("AUTO-UPLOAD DRY RUN => ELIGIBLE")
    for name in ("consent", "watched-80pct", "no-subtitle-offset", "content-not-empty",
                 "looks-like-subtitle", "subhash", "feature-id"):
        assert name in resume
