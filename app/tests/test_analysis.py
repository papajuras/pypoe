"""Market analysis engine: event classification, priors, posterior, CIF, end-to-end.

Runs each module's built-in self-check against a temp DB, then an end-to-end
synthetic scenario verifying the closed-form results behave correctly.
"""

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_ANALYSIS = _ROOT / "pypoe" / "analysis"


def run_module(name: str):
    res = subprocess.run(
        [sys.executable, str(_ANALYSIS / f"{name}.py")],
        capture_output=True, text=True,
    )
    assert res.returncode == 0, f"{name} self-check failed:\n{res.stdout}\n{res.stderr}"
    return res.stdout.strip()


# --- Test 1-3: module self-checks ---
for mod in ("engine", "prior", "survival"):
    print(run_module(mod))

# --- Test 4: end-to-end on synthetic snapshots ---
out = run_module("__init__")
print(out)
assert "analysis._demo OK" in out

print("test_analysis: all self-checks PASS")
