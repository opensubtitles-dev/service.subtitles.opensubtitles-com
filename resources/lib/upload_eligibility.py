"""Auto-upload eligibility: decides whether a watched subtitle is worth sharing.

DRY-RUN STAGE (v2.0.0): the verdict is only logged, nothing is uploaded. The
checks mirror the server's upload pipeline (quota/bans/spam/dedup run there;
everything the CLIENT can verify runs here) so that when the upload call is
switched on, rejected payloads are already rare.

Pure module - no Kodi imports - so every check is unit-testable.
"""

import hashlib
import os
import re

# A plausible subtitle: has at least one SRT/VTT-style timestamp line
TIMESTAMP_RE = re.compile(r"\d{1,2}:\d{2}:\d{2}[,.]\d{3}\s*-->\s*\d{1,2}:\d{2}:\d{2}[,.]\d{3}")

MIN_SIZE_BYTES = 500          # below this it is a stub, not a subtitle
MAX_SIZE_BYTES = 2 * 1024 * 1024  # sane .srt ceiling; server caps at 50 MiB decompressed
MIN_WATCHED_RATIO = 0.8       # the user effectively finished the movie with it
MIN_TIMESTAMP_LINES = 20      # fewer cues than this is a fragment
ZERO_DELAYS = ("", "0.000 s", "0.000s", "0.0 s", "0 s", "0.00 s")


def _read_content(sub_path):
    with open(sub_path, "rb") as f:
        raw = f.read()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw, raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw, None


def check_upload_eligibility(session, consent_enabled):
    """Returns (eligible: bool, checks: list[(name, passed, detail)]).

    `session` is the playback session dict maintained by service_monitor. Order
    matters: cheap state checks first, file content last.
    """
    checks = []

    def check(name, passed, detail):
        checks.append((name, bool(passed), detail))
        return bool(passed)

    ok = check("consent", consent_enabled,
               "auto-upload enabled in settings" if consent_enabled else "auto-upload disabled")

    sub_path = (session or {}).get("sub_path") or ""
    ok &= check("subtitle-known", bool(sub_path), sub_path or "no subtitle tracked this session")

    origin = (session or {}).get("origin", "unknown")
    ok &= check("origin", origin != "opensubtitles",
                f"origin={origin}" + (" (already on OpenSubtitles - nothing to share)"
                                      if origin == "opensubtitles" else ""))

    total = float((session or {}).get("total_time") or 0)
    position = float((session or {}).get("last_position") or 0)
    ratio = (position / total) if total > 0 else 0.0
    ok &= check("watched-80pct", total > 0 and ratio >= MIN_WATCHED_RATIO,
                f"watched {position:.0f}s of {total:.0f}s ({ratio:.0%})")

    delay = str((session or {}).get("subtitle_delay", "")).strip()
    ok &= check("no-subtitle-offset", delay in ZERO_DELAYS,
                f"Player.SubtitleDelay={delay!r}" if delay else "offset never sampled (treated as 0)")

    ok &= check("no-stream-switch", not (session or {}).get("stream_switched"),
                "user kept this subtitle the whole playback"
                if not (session or {}).get("stream_switched")
                else "user switched subtitle streams mid-playback")

    # --- file checks (only meaningful when a path is known) -----------------
    if not sub_path or not os.path.isfile(sub_path):
        check("file-exists", False, f"not found: {sub_path!r}")
        return False, checks
    check("file-exists", True, sub_path)

    size = os.path.getsize(sub_path)
    ok &= check("file-size", MIN_SIZE_BYTES <= size <= MAX_SIZE_BYTES,
                f"{size} bytes (allowed {MIN_SIZE_BYTES}..{MAX_SIZE_BYTES})")

    raw, text = _read_content(sub_path)
    ok &= check("content-not-empty", bool(raw) and bool((text or "").strip()),
                f"{len(raw)} bytes, decodable={text is not None}")

    cues = len(TIMESTAMP_RE.findall(text or ""))
    ok &= check("looks-like-subtitle", cues >= MIN_TIMESTAMP_LINES,
                f"{cues} timestamp cues found (need >= {MIN_TIMESTAMP_LINES})")

    subhash = hashlib.md5(raw).hexdigest() if raw else ""
    check("subhash", bool(subhash), f"MD5 {subhash} (server dedup key)")

    # Metadata completeness - not blocking (server can resolve via /upload/guess),
    # but recorded so the dry-run shows what the payload would carry.
    media = (session or {}).get("media", {}) or {}
    has_id = bool(media.get("imdb_id") or media.get("tmdb_id"))
    check("feature-id", True,
          f"imdb/tmdb={'yes' if has_id else 'no - would rely on /upload/guess'}, "
          f"moviehash={'yes' if session.get('moviehash') else 'no'}, "
          f"language={session.get('sub_language') or 'unknown'}")

    return bool(ok), checks


def format_resume(eligible, checks):
    """One log-friendly block: PASS/FAIL per check plus the verdict."""
    lines = ["AUTO-UPLOAD DRY RUN " + ("=> ELIGIBLE (would upload)" if eligible
                                       else "=> NOT ELIGIBLE (would skip)")]
    for name, passed, detail in checks:
        lines.append(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")
    return "\n".join(lines)
