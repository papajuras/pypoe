#!/bin/bash
# pypoe — deploy the gatherer module to the Pi (home LAN, netns WireGuard VPN).
# Re-runnable: stops the running service gracefully, ships current code,
# installs deps, restarts. Preserves the Pi's gatherer/gatherer/data/
# (flips.db, POESESSID) — data is seeded only on first deploy.
#
# Prereq: `ssh pi` works (see ~/.ssh/config), Pi reachable, VPN conf in ignore/.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE="pi"
REMOTE_DIR="/home/paweljuras/gatherer"
PORT=23467

# ssh/scp helpers (rely on ~/.ssh/config Host pi).
ssh_pi() { ssh "$REMOTE" "$1"; }
scp_pi() { scp "$1" "$REMOTE:$2"; }

# 1. Gracefully stop the running service (no-op if not installed/running).
echo "==> Stopping pypoe-gatherer (graceful)"
ssh_pi "sudo systemctl stop pypoe-gatherer 2>/dev/null || true; echo stopped"

# 2. Package the gatherer module (excludes data/, .venv, logs).
TARBALL="$(mktemp /tmp/gatherer-deploy.XXXXXX.tgz)"
echo "==> Packaging gatherer module"
tar czf "$TARBALL" \
    --exclude='gatherer/gatherer/data' \
    --exclude='gatherer/.venv' \
    --exclude='gatherer/log' \
    --exclude='*/__pycache__' \
    --exclude='*.pyc' \
    -C "$REPO" gatherer

# 3. Ship + extract to $REMOTE_DIR (strip the top-level gatherer/ dir).
echo "==> Uploading to $REMOTE"
scp_pi "$TARBALL" /tmp/gatherer-deploy.tgz
rm -f "$TARBALL"

# Preserve the Pi's data dir (flips.db, POESESSID) across the wipe-and-extract.
ssh_pi "if [ -d $REMOTE_DIR/gatherer/data ]; then cp -r $REMOTE_DIR/gatherer/data /tmp/gatherer-data-backup && echo backed_up; else echo no_data; fi"
ssh_pi "rm -rf $REMOTE_DIR && mkdir -p $REMOTE_DIR && tar xzf /tmp/gatherer-deploy.tgz -C $REMOTE_DIR --strip-components=1 && echo extracted"

# 4. Install uv (if missing) + sync deps.
echo "==> Installing deps"
ssh_pi "export PATH=\$HOME/.local/bin:\$PATH; command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh; cd $REMOTE_DIR && uv sync --quiet"

# 5. Restore preserved data, or seed on first deploy.
BACKUP_STATE="$(ssh_pi "[ -d /tmp/gatherer-data-backup ] && echo has_backup || echo no_backup")"
if [ "$BACKUP_STATE" = "has_backup" ]; then
    echo "==> Restoring Pi data (flips.db + POESESSID preserved)"
    ssh_pi "mkdir -p $REMOTE_DIR/gatherer/data && cp -r /tmp/gatherer-data-backup/. $REMOTE_DIR/gatherer/data/ && rm -rf /tmp/gatherer-data-backup"
else
    echo "==> First deploy — seeding flips.db + POESESSID"
    ssh_pi "mkdir -p $REMOTE_DIR/gatherer/data"
    scp_pi "$REPO/gatherer/gatherer/data/flips.db" "$REMOTE_DIR/gatherer/data/flips.db"
    scp_pi "$REPO/gatherer/gatherer/data/POESESSID" "$REMOTE_DIR/gatherer/data/POESESSID"
fi

# 6. WireGuard VPN for the gatherer (netns; host SSH stays on the LAN).
echo "==> Installing WireGuard + VPN netns"
VPN_CONF="$(ls "$REPO"/ignore/*.conf 2>/dev/null | head -1 || true)"
if [ -n "$VPN_CONF" ]; then
    ssh_pi "sudo apt-get install -y -qq wireguard-tools iptables >/dev/null 2>&1; echo wg-installed"
    scp_pi "$VPN_CONF" /tmp/wg0.conf
    # Strip DNS: the netns resolv.conf (/etc/netns/pypoe-vpn) is managed by
    # pypoe-vpn.sh + pypoe-gatherer.sh; a DNS= line makes wg-quick call
    # resolvconf (not installed on the Pi) and abort.
    ssh_pi "sed -i '/^DNS *=/d' /tmp/wg0.conf && sudo cp /tmp/wg0.conf /etc/wireguard/wg0.conf && sudo chmod 600 /etc/wireguard/wg0.conf && echo conf-shipped"
    scp_pi "$REPO/bin/pypoe-vpn.sh" /tmp/pypoe-vpn.sh
    ssh_pi "sudo cp /tmp/pypoe-vpn.sh /usr/local/sbin/pypoe-vpn.sh && sudo chmod +x /usr/local/sbin/pypoe-vpn.sh && echo vpn-script-shipped"
    scp_pi "$REPO/bin/pypoe-gatherer.sh" /tmp/pypoe-gatherer.sh
    ssh_pi "sudo cp /tmp/pypoe-gatherer.sh /usr/local/sbin/pypoe-gatherer.sh && sudo chmod +x /usr/local/sbin/pypoe-gatherer.sh && echo gatherer-script-shipped"
else
    echo "!! No ignore/*.conf found — skipping VPN setup"
fi

# 7. Install systemd units (VPN + gatherer-in-netns) + start.
echo "==> Installing systemd units"
ssh_pi "cat > /tmp/pypoe-vpn.service <<'EOF'
[Unit]
Description=pypoe WireGuard VPN netns (gatherer only)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/pypoe-vpn.sh up
ExecStop=/usr/local/sbin/pypoe-vpn.sh down
Restart=on-failure
RestartSec=15
StartLimitIntervalSec=0

[Install]
WantedBy=multi-user.target
EOF
sudo cp /tmp/pypoe-vpn.service /etc/systemd/system/pypoe-vpn.service
cat > /tmp/pypoe-gatherer.service <<'EOF'
[Unit]
Description=pypoe data gatherer (VPN netns)
After=network-online.target pypoe-vpn.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$REMOTE_DIR
Environment=PYTHONPATH=$REMOTE_DIR
ExecStart=/usr/local/sbin/pypoe-gatherer.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
sudo cp /tmp/pypoe-gatherer.service /etc/systemd/system/pypoe-gatherer.service
sudo systemctl daemon-reload
sudo systemctl enable pypoe-vpn pypoe-gatherer
sudo systemctl restart pypoe-vpn
sudo systemctl restart pypoe-gatherer
echo started"

# 8. Wait for health + confirm flip count.
echo "==> Waiting for health (http://pi.local:$PORT)..."
for i in $(seq 1 15); do
    if curl -sf --compressed "http://pi.local:$PORT/api/status" >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

echo "==> Health via pi.local:"
curl -s --compressed "http://pi.local:$PORT/api/status" 2>/dev/null || echo "(not reachable via pi.local yet)"
echo
echo "==> Deploy complete. Flips on Pi:"
ssh_pi "curl -s --compressed http://10.200.200.2:$PORT/api/flips | python3 -c 'import sys,json; print(len(json.load(sys.stdin)[\"flips\"]), \"flips\")'"
