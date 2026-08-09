#!/bin/bash
# pypoe — network health harness for the Pi gatherer.
# Checks each layer in dependency order. Exit code = number of failures.
# If check 1 or 2 fails, the host networking is bricked -> reboot the Pi.
#
# Usage: ./bin/test-net.sh [--quiet]
set -uo pipefail

REMOTE="pi"
PORT=23467
HOME_IP_HINT="83.22"   # host egress should be a home IP (not a VPN one)

pass=0; fail=0
report() { # name result detail
    if [ "$2" = "PASS" ]; then
        echo "[PASS] $1"
        pass=$((pass+1))
    else
        echo "[FAIL] $1 — $3"
        fail=$((fail+1))
    fi
}

# 1. SSH reachable (host not bricked).
if timeout 8 ssh "$REMOTE" "true" 2>/dev/null; then
    report "ssh $REMOTE" PASS
else
    report "ssh $REMOTE" FAIL "host unreachable via SSH — likely bricked"
    echo "NETWORK_STATUS=BRICKED"
    exit 2
fi

# 2. Host egress (wlan0, no VPN).
HOST_IP="$(ssh "$REMOTE" "curl -s --max-time 6 https://api.ipify.org" 2>/dev/null)"
if [[ "$HOST_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    report "host egress ($HOST_IP)" PASS
else
    report "host egress" FAIL "no internet from host — bricked"
    echo "NETWORK_STATUS=BRICKED"
    exit 2
fi

# 3. Netns VPN egress.
VPN_IP="$(ssh "$REMOTE" "sudo ip netns exec pypoe-vpn curl -s --max-time 8 https://api.ipify.org" 2>/dev/null)"
if [[ "$VPN_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    report "netns VPN egress ($VPN_IP)" PASS
else
    report "netns VPN egress" FAIL "no internet through pypoe-vpn netns"
fi

# 4. Gatherer serving inside the netns.
if timeout 8 ssh "$REMOTE" "sudo ip netns exec pypoe-vpn curl -sf --max-time 5 http://10.200.200.2:$PORT/api/status >/dev/null" 2>/dev/null; then
    report "gatherer in netns" PASS
else
    report "gatherer in netns" FAIL "no health at 10.200.200.2:$PORT"
fi

# 5. THE GOAL: gatherer reachable from the LAN via pi.local.
if timeout 8 curl -sf --compressed "http://pi.local:$PORT/api/status" >/dev/null 2>&1; then
    report "LAN -> pi.local:$PORT" PASS
else
    report "LAN -> pi.local:$PORT" FAIL "BFF cannot reach gatherer over the LAN"
fi

echo "RESULT: $pass pass, $fail fail"
exit "$fail"
