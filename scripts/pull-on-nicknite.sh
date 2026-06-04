#!/usr/bin/env bash
# Run this script ON nicknite (192.168.1.44), not on soulkiller.
# Pulls full rcfx clone including DEM checkpoints from soulkiller LAN services.
set -euo pipefail
SRC_HOST="${SRC_HOST:-192.168.1.113}"
DEST="${DEST:-$HOME/rcfx}"

echo "Pulling rcfx from ${SRC_HOST} -> ${DEST}"
mkdir -p "$DEST"
rsync -avz --progress "rsync://${SRC_HOST}:8873/rcfx/" "${DEST}/"
if [ -d "${DEST}/.git" ]; then
  git -C "$DEST" log -1 --oneline
fi
echo "Done. Latest commit on soulkiller should be: 8e88bc2 (or newer)"