#!/usr/bin/env bash
# Runs the transcription capability probe (tests/probe/) inside a headless Kodi
# of the requested version and prints the machine-readable result line.
#
#   scripts/kodi_probe_test.sh Omega-21.3     # or Matrix / Nexus / Piers-22.0b1
#
# Same container mechanics as kodi_smoke_test.sh. For ANDROID the probe cannot
# run in Docker - build the sideload zip instead:
#   cd tests/probe && zip -r ../../dist/service.opensubtitles.transcriptionprobe.zip \
#       service.opensubtitles.transcriptionprobe
# then install it on the device via "Install from zip file" and read the result:
#   adb logcat -d | grep TRANSCRIPTION-PROBE-RESULT
set -euo pipefail

TAG="${1:?usage: kodi_probe_test.sh <image-tag e.g. Omega-21.3>}"
IMAGE="matthuisman/kodi-headless:${TAG}"
NAME="kodi-probe-$(echo "$TAG" | tr '[:upper:].' '[:lower:]-')"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROBE_ID="service.opensubtitles.transcriptionprobe"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT
cleanup

echo "== [$TAG] first boot =="
docker run -d --name "$NAME" "$IMAGE" >/dev/null
sleep 25

if docker exec "$NAME" sh -c 'test -f /defaults/advancedsettings.xml -o -f /config/.kodi/userdata/advancedsettings.xml'; then
  docker exec "$NAME" sh -c 'for f in /defaults/advancedsettings.xml /config/.kodi/userdata/advancedsettings.xml; do
      [ -f "$f" ] && printf "<advancedsettings/>\n" > "$f"; done; true'
  docker restart "$NAME" >/dev/null
  sleep 25
fi

DB_PATH=$(docker exec "$NAME" sh -c 'find /config /root /home /data -maxdepth 5 -name "Addons*.db" 2>/dev/null | head -1')
[ -n "$DB_PATH" ] || { echo "FATAL: no Addons DB found"; exit 1; }
KODI_HOME=$(echo "$DB_PATH" | sed 's|/userdata/Database/.*||')

docker stop "$NAME" >/dev/null
docker cp "$REPO_ROOT/tests/probe/$PROBE_ID" "$NAME:$KODI_HOME/addons/$PROBE_ID"
docker cp "$NAME:$DB_PATH" /tmp/kodi-probe-addons.db
python3 - "$PROBE_ID" <<'EOF'
import sqlite3, sys
con = sqlite3.connect("/tmp/kodi-probe-addons.db")
con.execute("INSERT OR REPLACE INTO installed (addonID, enabled, installDate) "
            "VALUES (?, 1, '2026-01-01 00:00:00')", (sys.argv[1],))
con.commit(); con.close()
EOF
docker cp /tmp/kodi-probe-addons.db "$NAME:$DB_PATH"

echo "== [$TAG] probe boot =="
docker start "$NAME" >/dev/null
RESULT=""
for i in $(seq 1 24); do
  sleep 5
  RESULT=$(docker exec "$NAME" sh -c "grep -h 'TRANSCRIPTION-PROBE-RESULT' $KODI_HOME/temp/kodi.log 2>/dev/null" || true)
  [ -n "$RESULT" ] && break
done

echo "$RESULT"
case "$RESULT" in
  *'"verdict"'*) echo "== [$TAG] PROBE OK =="; exit 0 ;;
  *)             echo "== [$TAG] NO PROBE RESULT =="; exit 1 ;;
esac
