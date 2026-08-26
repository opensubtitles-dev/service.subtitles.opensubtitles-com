#!/usr/bin/env bash
# Real-Kodi smoke test: boot a headless Kodi of the requested version in Docker,
# install the add-on + the smoke-test service wrapper, and assert that every
# shipped module imports inside that Kodi's actual embedded Python.
#
#   scripts/kodi_smoke_test.sh Omega-21.3     # or Matrix / Nexus / Piers-22.0b1
#
# Images: matthuisman/kodi-headless (Matrix, Nexus, Omega-21.3, Piers-22.0b1).
# Flow: first boot creates the userdata tree; we stop the container, copy both
# add-ons in, pre-enable them in the Addons DB (fresh installs are disabled by
# default since Kodi 18), boot again and grep kodi.log for the verdict line the
# smoke service logs.
set -euo pipefail

TAG="${1:?usage: kodi_smoke_test.sh <image-tag e.g. Omega-21.3>}"
IMAGE="matthuisman/kodi-headless:${TAG}"
NAME="kodi-smoke-$(echo "$TAG" | tr '[:upper:].' '[:lower:]-')"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ADDON_ID="service.subtitles.opensubtitles-com"
SMOKE_ID="service.opensubtitles.smoketest"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT
cleanup

echo "== [$TAG] first boot (creates userdata) =="
docker run -d --name "$NAME" "$IMAGE" >/dev/null
sleep 25

# Some image generations (Piers beta) ship an advancedsettings.xml template
# with empty MySQL credentials - Kodi then dies with "Failed to initialize
# databases". Neutralize BOTH copies (the container init re-copies /defaults
# into userdata on every start, so deleting only userdata's does not stick)
# and restart so Kodi falls back to SQLite.
if docker exec "$NAME" sh -c 'test -f /defaults/advancedsettings.xml -o -f /config/.kodi/userdata/advancedsettings.xml'; then
  echo "  (image ships MySQL advancedsettings template - neutralizing, restarting)"
  docker exec "$NAME" sh -c 'for f in /defaults/advancedsettings.xml /config/.kodi/userdata/advancedsettings.xml; do
      [ -f "$f" ] && printf "<advancedsettings/>\n" > "$f"; done; true'
  docker restart "$NAME" >/dev/null
  sleep 25
fi

# The writable data dir varies by image (/config/.kodi for linuxserver-based
# images); locate it via the Addons DB the first boot just created.
DB_PATH=$(docker exec "$NAME" sh -c 'find /config /root /home /data -maxdepth 5 -name "Addons*.db" 2>/dev/null | head -1')
[ -n "$DB_PATH" ] || { echo "FATAL: no Addons DB found after first boot"; exit 1; }
KODI_HOME=$(echo "$DB_PATH" | sed 's|/userdata/Database/.*||')
echo "kodi home: $KODI_HOME  (db: $DB_PATH)"

docker stop "$NAME" >/dev/null

echo "== install add-ons =="
docker cp "$REPO_ROOT" "$NAME:$KODI_HOME/addons/$ADDON_ID"
docker cp "$REPO_ROOT/tests/smoke/$SMOKE_ID" "$NAME:$KODI_HOME/addons/$SMOKE_ID"

# script.module.requests + its dependency chain, from the official Kodi mirror
# for the matching branch - users get these from the Kodi repo, the container
# has none. Missing ones (dependency sets differ per branch) are skipped.
case "$TAG" in
  Matrix*) BRANCH=matrix ;;
  Nexus*)  BRANCH=nexus ;;
  Omega*)  BRANCH=omega ;;
  Piers*)  BRANCH=piers ;;
  *)       BRANCH=omega ;;
esac
DEPS_DIR=$(mktemp -d)
DEP_IDS=""
for dep in script.module.requests script.module.urllib3 script.module.chardet \
           script.module.charset-normalizer script.module.idna script.module.certifi; do
  listing=$(curl -sL "https://mirrors.kodi.tv/addons/$BRANCH/$dep/" | { grep -o "$dep-[0-9.+a-z]*\.zip" || true; } | sort -uV)
  # The matrix container era runs Python 3.6; the mirror's newest module builds
  # need 3.7+, but the "+matrix"-suffixed builds are the 3.6-safe originals.
  if [ "$BRANCH" = "matrix" ] && echo "$listing" | grep -q "+matrix"; then
    zip_name=$(echo "$listing" | grep "+matrix" | tail -1)
  else
    zip_name=$(echo "$listing" | tail -1)
  fi
  if [ -n "$zip_name" ]; then
    curl -sL "https://mirrors.kodi.tv/addons/$BRANCH/$dep/$zip_name" -o "$DEPS_DIR/$dep.zip"
    unzip -qo "$DEPS_DIR/$dep.zip" -d "$DEPS_DIR"
    docker cp "$DEPS_DIR/$dep" "$NAME:$KODI_HOME/addons/$dep"
    DEP_IDS="$DEP_IDS $dep"
    echo "  dep installed: $zip_name"
  else
    echo "  dep skipped (not on $BRANCH): $dep"
  fi
done
rm -rf "$DEPS_DIR"

echo "== pre-enable in Addons DB =="
docker cp "$NAME:$DB_PATH" /tmp/kodi-smoke-addons.db
python3 - "$ADDON_ID" "$SMOKE_ID" $DEP_IDS <<'EOF'
import sqlite3, sys
con = sqlite3.connect("/tmp/kodi-smoke-addons.db")
for addon_id in sys.argv[1:]:
    con.execute("INSERT OR REPLACE INTO installed (addonID, enabled, installDate) "
                "VALUES (?, 1, '2026-01-01 00:00:00')", (addon_id,))
con.commit()
con.close()
EOF
docker cp /tmp/kodi-smoke-addons.db "$NAME:$DB_PATH"

echo "== second boot (runs smoke service) =="
docker start "$NAME" >/dev/null
VERDICT=""
for i in $(seq 1 24); do
  sleep 5
  VERDICT=$(docker exec "$NAME" sh -c "grep -h 'SMOKETEST RESULT' $KODI_HOME/temp/kodi.log 2>/dev/null" || true)
  [ -n "$VERDICT" ] && break
done

echo "verdict: ${VERDICT:-none}"
docker exec "$NAME" sh -c "grep -h 'SMOKETEST IMPORT FAIL' -A 15 $KODI_HOME/temp/kodi.log 2>/dev/null" || true

case "$VERDICT" in
  *PASS*) echo "== [$TAG] SMOKE PASS =="; exit 0 ;;
  *FAIL*) echo "== [$TAG] SMOKE FAIL =="; exit 1 ;;
  *)      echo "== [$TAG] NO VERDICT (service never ran) =="
          docker exec "$NAME" sh -c "tail -50 $KODI_HOME/temp/kodi.log 2>/dev/null" || true
          exit 1 ;;
esac
