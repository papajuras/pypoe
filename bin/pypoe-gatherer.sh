#!/bin/bash
# Gatherer entrypoint: guarantees DNS inside the VPN netns regardless of
# iproute2's implicit /etc/netns resolv.conf bind-mount (which has been
# observed to occasionally not apply on service start -> silent total price
# failure).
exec ip netns exec pypoe-vpn bash -c '
  mount --bind /etc/netns/pypoe-vpn/resolv.conf /etc/resolv.conf 2>/dev/null || true
  mount --make-private /etc/resolv.conf 2>/dev/null || true
  exec /usr/bin/setpriv --reuid=1000 --regid=1000 --init-groups /home/paweljuras/gatherer/.venv/bin/python3 -m gatherer --port 23467
'
