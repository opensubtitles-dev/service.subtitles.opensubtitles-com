"""Transcription capability probe.

Answers, on the REAL device it runs on, every platform question the AI
transcription plan (docs/ai_transcription_plan.md) depends on:

  - which Python/OS/arch Kodi embeds here
  - ctypes usable?
  - Android: does dlopen of the public NDK media lib (libmediandk.so) work,
    and do the AMediaExtractor/AMediaCodec/AMediaMuxer symbols resolve?
    (This is the load-bearing question for ladder rung 2.)
  - is an ffmpeg executable present and actually runnable? (rung 1)
  - can we exec at all from app storage? (documents the Android W^X wall)
  - xbmcvfs read access (rungs 4/5)

Runs as an xbmc.service so headless/TV installs execute it automatically on
enable. Results go to the Kodi log as one machine-readable line prefixed
TRANSCRIPTION-PROBE-RESULT: and to transcription_probe.json in the add-on
profile dir. A visible notification summarizes pass/fail on devices with a UI.

Dev/CI only - never listed in scripts/addon_manifest.py, never shipped.
"""
import json
import os
import platform
import subprocess
import sys
import tempfile

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

__addon__ = xbmcaddon.Addon("service.opensubtitles.transcriptionprobe")


def probe():
    r = {
        "python": ".".join(str(v) for v in sys.version_info[:3]),
        "kodi": xbmc.getInfoLabel("System.BuildVersion"),
        "os_system": platform.system(),
        "machine": platform.machine(),
        "is_android": bool(xbmc.getCondVisibility("System.Platform.Android")),
        "is_linux": bool(xbmc.getCondVisibility("System.Platform.Linux")),
        "is_windows": bool(xbmc.getCondVisibility("System.Platform.Windows")),
        "is_osx": bool(xbmc.getCondVisibility("System.Platform.OSX")),
    }

    # --- ctypes: the foundation of the Android NDK route -------------------
    try:
        import ctypes
        r["ctypes"] = True
    except Exception as e:
        r["ctypes"] = False
        r["ctypes_error"] = repr(e)
        return r  # nothing below can work

    # --- rung 2: Android NDK media stack via dlopen ------------------------
    if r["is_android"]:
        for lib in ("libmediandk.so", "libandroid.so"):
            key = lib.replace(".so", "").replace("lib", "ndk_")
            try:
                handle = ctypes.CDLL(lib)
                r[key] = True
                if lib == "libmediandk.so":
                    for sym in ("AMediaExtractor_new", "AMediaCodec_createEncoderByType",
                                "AMediaMuxer_new", "AMediaExtractor_setDataSourceFd"):
                        r["sym_" + sym] = hasattr(handle, sym)
            except Exception as e:
                r[key] = False
                r[key + "_error"] = repr(e)

    # --- rung 1: ffmpeg executable -----------------------------------------
    ffmpeg = None
    try:
        from shutil import which
        ffmpeg = which("ffmpeg")
    except Exception:
        pass
    r["ffmpeg_on_path"] = ffmpeg or ""
    if ffmpeg:
        try:
            out = subprocess.run([ffmpeg, "-version"], capture_output=True, timeout=15)
            r["ffmpeg_runs"] = out.returncode == 0
            r["ffmpeg_version"] = out.stdout.decode(errors="replace").splitlines()[0][:80] if out.stdout else ""
        except Exception as e:
            r["ffmpeg_runs"] = False
            r["ffmpeg_error"] = repr(e)

    # --- the W^X wall: can we exec ANYTHING from app-writable storage? -----
    # Copies the system shell into our profile dir and tries to run it. On
    # Android API 29+ this must fail (documenting the wall); on desktop it
    # should succeed (documenting that a downloaded static ffmpeg would run).
    try:
        src = "/system/bin/sh" if r["is_android"] else "/bin/sh"
        if os.path.exists(src):
            profile = xbmcvfs.translatePath(__addon__.getAddonInfo("profile"))
            os.makedirs(profile, exist_ok=True)
            dst = os.path.join(profile, "probe_exec_test")
            with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                fdst.write(fsrc.read())
            os.chmod(dst, 0o755)
            out = subprocess.run([dst, "-c", "echo ok"], capture_output=True, timeout=10)
            r["exec_from_appdata"] = out.returncode == 0
            os.unlink(dst)
        else:
            r["exec_from_appdata"] = None  # no shell to copy (e.g. Windows)
    except Exception as e:
        r["exec_from_appdata"] = False
        r["exec_error"] = repr(e)

    # --- rungs 4/5: vfs byte access ----------------------------------------
    try:
        # the addon profile dir, not tempfile: Android has no /tmp and
        # tempfile.gettempdir() raises before the vfs is even exercised
        profile = xbmcvfs.translatePath(__addon__.getAddonInfo("profile"))
        os.makedirs(profile, exist_ok=True)
        tmp = os.path.join(profile, "probe_io.bin")
        with open(tmp, "wb") as tf:
            tf.write(b"opensubtitles-probe")
        f = xbmcvfs.File(tmp)
        r["xbmcvfs_read"] = f.readBytes(19) == b"opensubtitles-probe"
        f.close()
        os.unlink(tmp)
    except Exception as e:
        r["xbmcvfs_read"] = False
        r["xbmcvfs_error"] = repr(e)

    return r


def verdict(r):
    if r.get("is_android"):
        if r.get("ndk_mediandk") and r.get("sym_AMediaExtractor_new"):
            return "rung2-NDK-MEDIA-OK"
        if r.get("xbmcvfs_read"):
            return "rung4-REMUX-ONLY"
        return "URL-MODE-ONLY"
    if r.get("ffmpeg_runs") or r.get("exec_from_appdata"):
        return "rung1-FFMPEG-OK"
    if r.get("xbmcvfs_read"):
        return "rung4-REMUX-ONLY"
    return "URL-MODE-ONLY"


def run():
    r = probe()
    r["verdict"] = verdict(r)
    line = "TRANSCRIPTION-PROBE-RESULT: " + json.dumps(r, sort_keys=True)
    xbmc.log(line, xbmc.LOGINFO)
    try:
        profile = xbmcvfs.translatePath(__addon__.getAddonInfo("profile"))
        os.makedirs(profile, exist_ok=True)
        with open(os.path.join(profile, "transcription_probe.json"), "w") as f:
            json.dump(r, f, indent=2, sort_keys=True)
    except Exception as e:
        xbmc.log(f"TRANSCRIPTION-PROBE-RESULT: json write failed {e!r}", xbmc.LOGINFO)
    try:
        xbmcgui.Dialog().notification("Transcription probe", r["verdict"], "", 7000)
    except Exception:
        pass


if __name__ == "__main__":
    run()
