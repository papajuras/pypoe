"""Smoke test: start the app, wait for API requests, report pass/fail."""

import os
import re
import subprocess
import sys
import time
from pathlib import Path

LOG_DIR = Path("log")
TIMEOUT_STARTUP = 15
TIMEOUT_REQUESTS = 120


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def main() -> int:
    proc = subprocess.Popen(
        [sys.executable, "main.py", "--tray-only"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    for p in LOG_DIR.glob("requests-*.log"):
        p.unlink(missing_ok=True)

    print("smoke: starting app...", flush=True)

    # Wait for startup: process stays alive and any log file appears
    t0 = time.time()
    while time.time() - t0 < TIMEOUT_STARTUP:
        if not alive(proc.pid):
            _, err = proc.communicate(timeout=5)
            print(f"smoke: FAIL — app exited early (code={proc.returncode})")
            if err:
                print(err.decode()[:2000])
            return 1
        if list(LOG_DIR.glob("requests-*.log")):
            break
        time.sleep(0.5)
    else:
        _, err = proc.communicate(timeout=5)
        print(f"smoke: FAIL — no audit log within {TIMEOUT_STARTUP}s (code={proc.returncode})")
        if err:
            print(err.decode()[:2000])
        return 1

    print("smoke: app running, watching for requests...", flush=True)

    deadline = time.time() + TIMEOUT_REQUESTS
    successes = 0
    while time.time() < deadline:
        if not alive(proc.pid):
            print("smoke: FAIL — process died")
            return 1

        logs = sorted(LOG_DIR.glob("requests-*.log"))
        if logs:
            content = max(logs, key=lambda p: p.stat().st_mtime).read_text()
            successes = max(successes, len(re.findall(r"RESP.*→ 200", content)))

        if successes >= 2:
            print(f"smoke: PASS — {successes} successful requests", flush=True)
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            return 0

        time.sleep(1)

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
    err = proc.stderr.read(2000).decode() if proc.stderr else ""
    print(f"smoke: FAIL — only {successes} successes in {TIMEOUT_REQUESTS}s")
    if err:
        print(f"  stderr: {err[:500]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
