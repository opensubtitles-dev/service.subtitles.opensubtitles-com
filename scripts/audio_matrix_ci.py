#!/usr/bin/env python3
"""Audio extraction matrix runner for CI (real Windows/macOS/Linux runners).

Generates the container x codec asset grid with the runner's ffmpeg, then
exercises every no-install extraction route this OS offers and prints one
PASS/FAIL line per (route, asset). Exit 1 only when a route that MUST work
on this OS fails; informational routes report but never fail the job.

Run locally too: python3 scripts/audio_matrix_ci.py
"""
import os
import platform
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

failures = []


def say(route, asset, ok, detail="", required=False):
    mark = "PASS" if ok else ("FAIL" if required else "fail(info)")
    print(f"  [{mark}] {route:12s} {asset:16s} {detail}")
    if required and not ok:
        failures.append((route, asset, detail))


def build_grid(ffmpeg, out):
    base = os.path.join(out, "base.mp4")
    run = lambda *a: subprocess.run([ffmpeg, "-y", "-v", "error"] + list(a),
                                    capture_output=True)
    run("-f", "lavfi", "-i", "testsrc2=duration=30:size=320x180:rate=25",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=30",
        "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-b:a", "128k", base)
    assets = {}
    codecs = [("aac", ["-c:a", "aac", "-b:a", "128k"]),
              ("ac3", ["-c:a", "ac3", "-b:a", "384k"]),
              ("eac3", ["-c:a", "eac3", "-b:a", "256k"]),
              ("mp3", ["-c:a", "libmp3lame", "-b:a", "128k"]),
              ("dts", ["-strict", "-2", "-c:a", "dca", "-b:a", "768k"]),
              ("flac", ["-c:a", "flac"]),
              ("opus", ["-c:a", "libopus", "-b:a", "96k"]),
              ("pcm", ["-c:a", "pcm_s16le"])]
    for name, args in codecs:
        path = os.path.join(out, f"mkv_{name}.mkv")
        r = run("-i", base, "-c:v", "copy", *args, path)
        if r.returncode == 0:
            assets[f"mkv_{name}"] = path
    path = os.path.join(out, "mp4_aac.mp4")
    if run("-i", base, "-c", "copy", path).returncode == 0:
        assets["mp4_aac"] = path
    return assets


def decodes(ffmpeg, path):
    return subprocess.run([ffmpeg, "-v", "error", "-y", "-i", path, "-f", "null", "-"],
                          capture_output=True).returncode == 0


def main():
    system = platform.system()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("no ffmpeg on this runner - cannot build the asset grid")
        return 1
    out = tempfile.mkdtemp(prefix="audiomatrix_")
    assets = build_grid(ffmpeg, out)
    print(f"== {system} ({platform.machine()}) - {len(assets)} assets ==")

    # ---- route: pydemux (must work everywhere) --------------------------
    from resources.lib.audio_demux import extract_audio_track, probe_extension, \
        UnsupportedSource
    for name, path in sorted(assets.items()):
        dst = os.path.join(out, "pd_" + name + probe_extension(path))
        try:
            frames = extract_audio_track(path, dst)
            say("pydemux", name, decodes(ffmpeg, dst), f"{frames}f", required=True)
        except UnsupportedSource as e:
            # only DTS-class rejections are acceptable now (opus -> ogg
            # and pcm -> wav are re-encapsulated since 2.0.0-dev)
            say("pydemux", name, False, str(e),
                required=(name not in ("mkv_dts",)))

    # ---- route: afconvert (macOS must) ----------------------------------
    if system == "Darwin":
        for name, path in sorted(assets.items()):
            src = path
            if not path.endswith(".mp4"):
                src = os.path.join(out, "pd_" + name + probe_extension(path))
                if not os.path.exists(src):
                    say("afconvert", name, False, "no demuxed input",
                        required=(name != "mkv_dts"))
                    continue
            dst = os.path.join(out, "afc_" + name + ".m4a")
            r = subprocess.run(["afconvert", "-f", "m4af", "-d", "aac@16000",
                                "-b", "24000", "--mix", "-o", dst, src],
                               capture_output=True)
            ok = r.returncode == 0 and os.path.getsize(dst) if os.path.exists(dst) else False
            # afconvert has no DTS decoder and does not read Ogg Opus - both
            # fall through to other rungs (sync accepts the .ogg directly)
            say("afconvert", name, bool(ok), "",
                required=(name not in ("mkv_dts", "mkv_opus")))

    # ---- route: gstreamer (Linux informational: plugin set varies) ------
    if system == "Linux" and shutil.which("gst-launch-1.0"):
        for name, path in sorted(assets.items()):
            dst = os.path.join(out, "gst_" + name + ".aac")
            r = subprocess.run(
                ["gst-launch-1.0", "-q", "filesrc", "location=" + path, "!",
                 "decodebin", "!", "audioconvert", "!", "audioresample", "!",
                 "audio/x-raw,rate=16000,channels=1", "!", "avenc_aac",
                 "bitrate=24000", "!", "aacparse", "!",
                 "audio/mpeg,stream-format=adts", "!",
                 "filesink", "location=" + dst],
                capture_output=True, timeout=300)
            ok = os.path.exists(dst) and os.path.getsize(dst) and decodes(ffmpeg, dst)
            say("gstreamer", name, bool(ok), "", required=False)

    # ---- route: Media Foundation (Windows: THE validation target) ------
    if system == "Windows":
        from resources.lib import windows_audio
        for name, path in sorted(assets.items()):
            dst = os.path.join(out, "mf_" + name + ".m4a")
            try:
                size = windows_audio.transcode(path, dst)
                say("mf-ctypes", name, decodes(ffmpeg, dst), f"{size}b",
                    required=(name == "mp4_aac"))
            except windows_audio.WindowsAudioError as e:
                say("mf-ctypes", name, False, str(e), required=(name == "mp4_aac"))

    if failures:
        print(f"\n{len(failures)} REQUIRED failures")
        return 1
    print("\nall required routes passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
