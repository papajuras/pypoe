#!/bin/bash
# Clean up every artifact left by run.sh after a crash/SIGKILL.
# Run with:  sudo ./bin/cleanup-vpn.sh   (from project root)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

NS="pypoe-vpn"
VETH_CIDR="10.200.200.0/24"
IFACE_FILE="/tmp/pypoe-vpn-iface"
CONFIG="pc-NO-FREE-4.conf"

echo "=== pypoe VPN cleanup ==="

# 1. kill running processes
echo "[1/6] Killing pypoe processes..."
pkill -f "main.py.*--tray-only" 2>/dev/null || true
pkill -f "run\.sh"              2>/dev/null || true
sleep 0.5

# 2. tear down WireGuard inside the namespace
echo "[2/6] Tearing down WireGuard..."
if ip netns list 2>/dev/null | grep -qw "$NS"; then
    ip netns exec "$NS" wg-quick down "$CONFIG" 2>/dev/null || true
fi

# 3. delete veth pair + namespace
echo "[3/6] Removing veth pair and namespace..."
ip netns exec "$NS" ip link del veth1 2>/dev/null || true
ip link del veth0 2>/dev/null || true
ip netns delete "$NS" 2>/dev/null || true

# 4. flush iptables rules — try every known interface, then generic
echo "[4/6] Flushing iptables rules..."
IFACES="enp9s0 wlp10s0"
[ -f "$IFACE_FILE" ] && IFACES="$IFACES $(cat "$IFACE_FILE" 2>/dev/null)"
# deduplicate
IFACES=$(echo "$IFACES" | tr ' ' '\n' | sort -u)

for iface in $IFACES; do
    while iptables -t nat -D POSTROUTING -s "$VETH_CIDR" -o "$iface" -j MASQUERADE 2>/dev/null; do :; done
    while iptables -D FORWARD -i veth0 -o "$iface" -j ACCEPT 2>/dev/null; do :; done
    while iptables -D FORWARD -i "$iface" -o veth0 -j ACCEPT 2>/dev/null; do :; done
done

# fallback: interface-less (in case interface spec differs)
while iptables -t nat -D POSTROUTING -s "$VETH_CIDR" -j MASQUERADE 2>/dev/null; do :; done
while iptables -D FORWARD -i veth0 -j ACCEPT 2>/dev/null; do :; done
while iptables -D FORWARD -o veth0 -j ACCEPT 2>/dev/null; do :; done

# 5. restore ip_forward
echo "[5/6] Restoring ip_forward..."
ORIG_FWD="0"
[ -f "${IFACE_FILE}.orig_fwd" ] && ORIG_FWD=$(cat "${IFACE_FILE}.orig_fwd" 2>/dev/null)
sysctl -q net.ipv4.ip_forward="$ORIG_FWD" 2>/dev/null || true

# 6. clean temp files + DNS config
echo "[6/6] Cleaning temp files..."
rm -f "$IFACE_FILE" "${IFACE_FILE}.orig_fwd" "/etc/netns/$NS/resolv.conf" 2>/dev/null

echo "=== Done ==="
