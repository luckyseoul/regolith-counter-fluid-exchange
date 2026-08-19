#!/usr/bin/env bash
# Push full rcfx tree (including DEM checkpoints) to nicknite via SSH.
# Requires: nicknite authorized_keys includes soulkiller key, or NICKNITE_PASSWORD for expect.
set -euo pipefail
SRC="/home/nick/rcfx/"
DEST="nicknite@192.168.1.44:~/rcfx/"
KEY="${KEY:-$HOME/.ssh/id_ed25519_nicknite}"
RSYNC_OPTS=(-avz --progress -e "ssh -i ${KEY} -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15")
echo "Syncing ${SRC} -> ${DEST}"
rsync "${RSYNC_OPTS[@]}" "$SRC" "$DEST"
echo "Done. Verify:"
echo "  ssh nicknite@192.168.1.44 'ls -la ~/rcfx && git -C ~/rcfx log -1 --oneline'"