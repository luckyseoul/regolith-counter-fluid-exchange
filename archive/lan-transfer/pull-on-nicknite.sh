#!/usr/bin/env bash
# Run this script ON nicknite (192.168.1.44), not on soulkiller.
# Pulls full rcfx clone including DEM checkpoints from soulkiller LAN services.
set -euo pipefail
SRC_HOST="${SRC_HOST:-192.168.1.113}"
DEST="${DEST:-$HOME/rcfx}"

MODE="${1:-rsync}"
case "$MODE" in
  git)
    echo "Git clone (no large checkpoints) from git://${SRC_HOST}:9418/rcfx"
    git clone "git://${SRC_HOST}:9418/rcfx" "$DEST"
    ;;
  tar)
    echo "Downloading tarball from http://${SRC_HOST}:8877/rcfx-clone.tar.gz"
    curl -fL -o /tmp/rcfx-clone.tar.gz "http://${SRC_HOST}:8877/rcfx-clone.tar.gz"
    mkdir -p "$(dirname "$DEST")"
    tar -xzf /tmp/rcfx-clone.tar.gz -C "$(dirname "$DEST")"
    ;;
  rsync|*)
    echo "Rsync full tree (includes DEM checkpoints) from rsync://${SRC_HOST}:8873/rcfx/"
    mkdir -p "$DEST"
    rsync -avz --progress "rsync://${SRC_HOST}:8873/rcfx/" "${DEST}/"
    ;;
esac
if [ -d "${DEST}/.git" ]; then
  git -C "$DEST" log -1 --oneline
fi
echo "Done."