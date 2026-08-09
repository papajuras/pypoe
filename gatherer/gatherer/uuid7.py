"""UUID v7 — timestamp-ordered UUIDs for flip identification.

Layout (RFC 9562): 48-bit Unix ms timestamp + version=7 + variant=10xx + random.
"""

from __future__ import annotations

import os
import time
import uuid


def uuid7(timestamp_ms: int | None = None) -> str:
    if timestamp_ms is None:
        timestamp_ms = int(time.time() * 1000)
    rand = os.urandom(10)
    b = bytearray(16)
    b[0:6] = timestamp_ms.to_bytes(6, "big")
    b[6] = 0x70 | (rand[0] & 0x0F)
    b[7] = rand[1]
    b[8] = 0x80 | (rand[2] & 0x3F)
    b[9:16] = rand[3:10]
    return str(uuid.UUID(bytes=bytes(b)))
