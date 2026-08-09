#!/bin/bash
# pypoe VPN netns — WireGuard tunnel for the gatherer only.
# Host (SSH, Tailscale) stays on the main network; the gatherer runs inside
# this namespace where wg0 is the default route.
#
# Usage: pypoe-vpn.sh {up|down}
set -euo pipefail

NS="pypoe-vpn"
CONF="/etc/wireguard/wg0.conf"
VETH_CIDR="10.200.200.0/24"
VETH_HOST="10.200.200.1"
VETH_NS="10.200.200.2"
GATHERER_PORT=23467
WAN_IF="wlan0"   # Pi's home-LAN uplink (DHCP-proof: DNAT matches the interface)

down() {
    # stop the tunnel inside the ns
    ip netns exec "$NS" wg-quick down wg0 2>/dev/null || true
    # tear down veth pair + ns
    ip netns exec "$NS" ip link del veth1 2>/dev/null || true
    ip link del veth0 2>/dev/null || true
    ip netns delete "$NS" 2>/dev/null || true
    # flush rules (loop: tolerate duplicates left by pre-fix versions)
    while iptables -t nat -D PREROUTING -i "$WAN_IF" -p tcp --dport "$GATHERER_PORT" -j DNAT --to-destination "$VETH_NS:$GATHERER_PORT" 2>/dev/null; do :; done
    while iptables -t nat -D POSTROUTING -s "$VETH_CIDR" -o "$WAN_IF" -j MASQUERADE 2>/dev/null; do :; done
    while iptables -D FORWARD -i "$WAN_IF" -o veth0 -j ACCEPT 2>/dev/null; do :; done
    while iptables -D FORWARD -i veth0 -o "$WAN_IF" -j ACCEPT 2>/dev/null; do :; done
    sysctl -w net.ipv4.ip_forward=0 >/dev/null 2>&1 || true
}

up() {
    down
    sysctl -w net.ipv4.ip_forward=1 >/dev/null

    ip netns add "$NS"
    ip link add veth0 type veth peer name veth1 netns "$NS"
    ip addr add "${VETH_HOST}/24" dev veth0
    ip link set veth0 up
    ip netns exec "$NS" ip addr add "${VETH_NS}/24" dev veth1
    ip netns exec "$NS" ip link set veth1 up
    ip netns exec "$NS" ip link set lo up
    # default route via host so the wg endpoint is reachable pre-tunnel
    ip netns exec "$NS" ip route add default via "$VETH_HOST" dev veth1

    # DNS for the netns
    mkdir -p "/etc/netns/$NS"
    echo "nameserver 1.1.1.1" > "/etc/netns/$NS/resolv.conf"

    # outbound NAT for tunnel + DNS via host
    iptables -t nat -A POSTROUTING -s "$VETH_CIDR" -o "$WAN_IF" -j MASQUERADE
    iptables -A FORWARD -i veth0 -o "$WAN_IF" -j ACCEPT
    iptables -A FORWARD -i "$WAN_IF" -o veth0 -j ACCEPT

    # bring up wg inside the ns (adds wg0 + default via wg0 + endpoint route via veth1)
    ip netns exec "$NS" wg-quick up wg0

    # wg-quick's policy routing sends ALL unmarked traffic to wg0; that would
    # route replies to LAN clients into the tunnel and break the BFF. Add the
    # LAN subnet to the netns main table so it beats the wg0 default.
    HOST_CIDR="$(ip -o -4 addr show "$WAN_IF" | awk '{print $4}')"
    if [ -n "$HOST_CIDR" ]; then
        LAN_CIDR="$(python3 -c "import ipaddress,sys; print(ipaddress.ip_network(sys.argv[1], strict=False).with_prefixlen)" "$HOST_CIDR")"
        ip netns exec "$NS" ip route add "$LAN_CIDR" via "$VETH_HOST" dev veth1
    fi

    # wait for handshake
    for i in $(seq 1 15); do
        if ip netns exec "$NS" wg show wg0 2>/dev/null | grep -q "latest handshake"; then
            echo "handshake OK"
            break
        fi
        [ "$i" = 15 ] && { echo "ERROR: handshake failed" >&2; exit 1; }
        sleep 1
    done

    # BFF reachability: LAN:port -> netns veth1
    iptables -t nat -A PREROUTING -i "$WAN_IF" -p tcp --dport "$GATHERER_PORT" -j DNAT --to-destination "$VETH_NS:$GATHERER_PORT"
    echo "VPN netns up"
}

case "${1:-}" in
    up) up ;;
    down) down ;;
    *) echo "usage: $0 {up|down}"; exit 1 ;;
esac
