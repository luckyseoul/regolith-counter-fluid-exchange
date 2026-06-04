#!/usr/bin/env bash
# Clone/sync full rcfx tree (including DEM checkpoints) to nicknite.
set -euo pipefail
SRC="/home/nick/rcfx/"
DEST="nicknite@192.168.1.44:~/rcfx/"
RSYNC_OPTS=(-avz --progress -e "ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15")
echo "Syncing ${SRC} -> ${DEST}"
rsync "${RSYNC_OPTS[@]}" "$SRC" "$DEST"
echo "Done. Verify:"
echo "  ssh nicknite@192.168.1.44 'ls -la ~/rcfx && git -C ~/rcfx log -1 --oneline'"