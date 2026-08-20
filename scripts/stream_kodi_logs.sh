#!/usr/bin/env bash
# Real-time Kodi Log Streamer for service.subtitles.opensubtitles-com

# Detect OS and set default Kodi log path
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [ -f "$HOME/Library/Logs/kodi.log" ]; then
        LOG_PATH="$HOME/Library/Logs/kodi.log"
    else
        LOG_PATH="$HOME/Library/Application Support/Kodi/temp/kodi.log"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    LOG_PATH="$HOME/.kodi/temp/kodi.log"
elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* ]]; then
    LOG_PATH="$APPDATA/Kodi/kodi.log"
else
    LOG_PATH="$HOME/Library/Application Support/Kodi/temp/kodi.log"
fi

# Override with custom path if passed as argument
FILTER_MODE="filtered"
if [ "$1" == "--all" ] || [ "$1" == "-a" ]; then
    FILTER_MODE="all"
elif [ -n "$1" ] && [ -f "$1" ]; then
    LOG_PATH="$1"
fi

if [ ! -f "$LOG_PATH" ]; then
    echo "❌ Log file not found at: $LOG_PATH"
    echo "Make sure Kodi is running or has run at least once."
    exit 1
fi

FILE_SIZE=$(ls -lh "$LOG_PATH" | awk '{print $5}')
MOD_TIME=$(ls -lh "$LOG_PATH" | awk '{print $6, $7, $8}')

echo "========================================================"
echo " 📡 Kodi Log Streamer"
echo " 📁 File: $LOG_PATH ($FILE_SIZE, last updated $MOD_TIME)"
if [ "$FILTER_MODE" == "all" ]; then
echo " 🔍 Filter: ALL (Unfiltered)"
else
echo " 🔍 Filter: OpenSubtitles & Subtitles (Case-Insensitive)"
echo " 💡 Tip: Run with --all to see full Kodi log without filters"
fi
echo " ⚙️ Note: Enable Kodi Debug Logging (Settings -> System -> Logging)"
echo " (Press Ctrl+C to stop)"
echo "========================================================"

if [ "$FILTER_MODE" == "all" ]; then
    tail -n 50 -F "$LOG_PATH"
else
    tail -n 50 -F "$LOG_PATH" | grep --line-buffered -i -E "opensubtitles|subtitles|DialogSubtitleSearch|CPythonInvoker"
fi
