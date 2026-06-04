#!/usr/bin/env bash
# Start LAN transfer services on soulkiller (192.168.1.113). Safe restarts — no broad pkill.
set -euo pipefail
BIND="${BIND:-192.168.1.113}"
RSYNC_CONF="${RSYNC_CONF:-/tmp/rsyncd-rcfx.conf}"

if [ ! -f "$RSYNC_CONF" ]; then
  cat > "$RSYNC_CONF" <<'EOF'
uid = nick
gid = nick
use chroot = no
read only = yes
hosts allow = 192.168.1.0/24

[rcfx]
path = /home/nick/rcfx
comment = RCFX clone (read-only)
EOF
fi

start_if_free() {
  local port="$1"
  local name="$2"
  if ss -tln | grep -q ":${port} "; then
    echo "${name} already listening on ${port}"
    return 0
  fi
  return 1
}

if ! start_if_free 8873 rsync; then
  rsync --daemon --config="$RSYNC_CONF" --port=8873
  echo "rsync daemon started on 8873"
fi

if ! start_if_free 8877 http; then
  python3 -m http.server 8877 --bind "$BIND" --directory /home/nick &
  echo "http server started on ${BIND}:8877 (pid $!)"
fi

if ! start_if_free 9418 git; then
  git daemon --reuseaddr --base-path=/home/nick --export-all \
    --listen="$BIND" --port=9418 --informative-errors &
  echo "git daemon started on ${BIND}:9418 (pid $!)"
fi

ss -tlnp | grep -E '8873|8877|9418' || true