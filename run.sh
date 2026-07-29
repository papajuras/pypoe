#!/bin/bash
cd "$(dirname "$0")"

CONFIG="pc-NO-FREE-4.conf"
NS="pypoe-vpn"
VETH_HOST="10.200.200.1"
VETH_NS="10.200.200.2"
IFACE_FILE="/tmp/pypoe-vpn-iface"
WG_IFACE="$(basename "$CONFIG" .conf)"

[ -f "$CONFIG" ] || { echo "ERROR: $CONFIG not found — VPN required" >&2; exit 1; }

if [ "$EUID" -ne 0 ]; then
    exec sudo "$0" "$@"
fi

# ── stale cleanup (previous crash/SIGKILL) ──
_stale_iface() { ip route get 1 2>/dev/null | awk '{print $5; exit}'; }
IFACE=$([ -f "$IFACE_FILE" ] && cat "$IFACE_FILE" 2>/dev/null || _stale_iface)

# kill any stale wg inside old namespace
ip netns exec "$NS" wg-quick down "$CONFIG" 2>/dev/null
# tear down veth peer first (this kills veth0 too)
ip netns exec "$NS" ip link del veth1 2>/dev/null
ip netns delete "$NS" 2>/dev/null
ip link del veth0 2>/dev/null

# flush iptables
while iptables -t nat -D POSTROUTING -s "${VETH_HOST}/24" -o "$IFACE" -j MASQUERADE 2>/dev/null; do :; done
while iptables -D FORWARD -i veth0 -o "$IFACE" -j ACCEPT 2>/dev/null; do :; done
while iptables -D FORWARD -i "$IFACE" -o veth0 -j ACCEPT 2>/dev/null; do :; done

# restore ip_forward from saved file
if [ -f "${IFACE_FILE}.orig_fwd" ]; then
    sysctl -q net.ipv4.ip_forward="$(cat "${IFACE_FILE}.orig_fwd")" 2>/dev/null
fi
rm -f "$IFACE_FILE" "${IFACE_FILE}.orig_fwd"

# ── save current state ──
IFACE=$(ip route get 1 | awk '{print $5; exit}')
echo "$IFACE" > "$IFACE_FILE"
ORIG_FWD=$(sysctl -n net.ipv4.ip_forward)
echo "$ORIG_FWD" > "${IFACE_FILE}.orig_fwd"

# ── setup ──
set -e
echo "VPN: creating namespace..."
ip netns add "$NS"
ip link add veth0 type veth peer name veth1 netns "$NS"
ip addr add "${VETH_HOST}/24" dev veth0
ip link set veth0 up
ip netns exec "$NS" ip addr add "${VETH_NS}/24" dev veth1
ip netns exec "$NS" ip link set veth1 up
ip netns exec "$NS" ip link set lo up
ip netns exec "$NS" ip route add default via "$VETH_HOST" dev veth1

sysctl -q net.ipv4.ip_forward=1
iptables -t nat -A POSTROUTING -s "${VETH_HOST}/24" -o "$IFACE" -j MASQUERADE
iptables -A FORWARD -i veth0 -o "$IFACE" -j ACCEPT
iptables -A FORWARD -i "$IFACE" -o veth0 -j ACCEPT

mkdir -p "/etc/netns/$NS"
echo "nameserver 1.1.1.1" > "/etc/netns/$NS/resolv.conf"

echo "VPN: starting wireguard..."
ip netns exec "$NS" wg-quick up "$CONFIG"
ip netns exec "$NS" sh -c 'echo "nameserver 1.1.1.1" > /etc/resolv.conf'

echo "VPN: waiting for handshake..."
sleep 2
for i in $(seq 1 15); do
    if ip netns exec "$NS" wg show "$WG_IFACE" 2>/dev/null | grep -q "latest handshake"; then
        echo "VPN: handshake OK"
        break
    fi
    [ "$i" = 15 ] && { echo "ERROR: WireGuard handshake failed after 15s" >&2; exit 1; }
    sleep 1
done
set +e

# ── cleanup ──
CHILD_PID=""
_CLEANED=0
_cleanup() {
    [ "$_CLEANED" = 1 ] && return
    _CLEANED=1
    set +e
    [ -n "$CHILD_PID" ] && kill "$CHILD_PID" 2>/dev/null && wait "$CHILD_PID" 2>/dev/null
    ip netns exec "$NS" wg-quick down "$CONFIG" 2>/dev/null
    ip netns exec "$NS" ip link del veth1 2>/dev/null
    ip netns delete "$NS" 2>/dev/null
    ip link del veth0 2>/dev/null
    while iptables -t nat -D POSTROUTING -s "${VETH_HOST}/24" -o "$IFACE" -j MASQUERADE 2>/dev/null; do :; done
    while iptables -D FORWARD -i veth0 -o "$IFACE" -j ACCEPT 2>/dev/null; do :; done
    while iptables -D FORWARD -i "$IFACE" -o veth0 -j ACCEPT 2>/dev/null; do :; done
    sysctl -q net.ipv4.ip_forward="$ORIG_FWD" 2>/dev/null
    rm -f "$IFACE_FILE" "${IFACE_FILE}.orig_fwd"
    echo "VPN: cleaned up"
}
trap _cleanup EXIT INT TERM HUP

# ── launch ──
echo "VPN: running pypoe..."
ORIG_USER="${SUDO_USER:-$USER}"
ip netns exec "$NS" sudo -u "$ORIG_USER" HOME="/home/$ORIG_USER" .venv/bin/python3 main.py --tray-only "$@" &
CHILD_PID=$!
wait "$CHILD_PID"
