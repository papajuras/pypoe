"""Flip journal store: definitions, CRUD, sold lifecycle, legacy import."""

import tempfile
from pathlib import Path

from pypoe.flipper import journal

tmp = Path(tempfile.mkdtemp())
journal._DB = tmp / "journal.db"
journal._LEGACY = tmp / "flips"
journal._conn = None


def reset():
    journal._conn = None
    if journal._DB.exists():
        journal._DB.unlink()


# --- Test 1: definitions ---
defs = journal.definitions()
assert len(defs) == 36 * 4 == 144, f"expected 144 definitions, got {len(defs)}"
assert len({d["label"] for d in defs}) == 144, "definition labels not unique"
assert defs[0]["label"] == "royal plate 27", defs[0]["label"]
print(f"Test 1 PASS — {len(defs)} definitions")

# --- Test 2: add open flip, league stamped ---
reset()
rid = journal.add("Allflame", "Royal Plate", 28, cost=5.0)
rec = journal.list_all()[0]
assert rec["id"] == rid and rec["income"] is None and rec["sold_at"] is None
assert rec["net"] is None and rec["league"] == "Allflame"
print(f"Test 2 PASS — open flip id={rid} league={rec['league']}")

# --- Test 3: fill income → sold, net computed ---
assert journal.update(rid, income=11.0)
rec = journal.list_all()[0]
assert rec["income"] == 11.0 and rec["sold_at"] is not None and rec["net"] == 6.0
print(f"Test 3 PASS — sold net={rec['net']}")

# --- Test 4: reopen (income cleared) ---
assert journal.update(rid, income=None)
rec = journal.list_all()[0]
assert rec["income"] is None and rec["sold_at"] is None
print("Test 4 PASS — reopened")

# --- Test 5: delete ---
assert journal.delete(rid)
assert journal.list_all() == []
print("Test 5 PASS — delete")

# --- Test 6: legacy import from ignore/flips format, one row = one flip ---
reset()
journal._LEGACY.write_text(
    "royal plate 28 -1 -1 +5\nconquest lamellar 28 -1 +11\n"
    "torturer's mask 28 -1\nsyndicate's garb 29 -9\nsacred chainmail 28 -5\n"
)
rows = journal.list_all()
assert len(rows) == 5, f"expected 5 legacy rows, got {len(rows)}"
by_base = {r["base"]: r for r in rows}
rp = by_base["Royal Plate"]  # canonical casing from definitions
assert rp["cost"] == 2 and rp["income"] == 5 and rp["net"] == 3 and rp["sold_at"] is not None
assert by_base["Conquest Lamellar"]["cost"] == 1 and by_base["Conquest Lamellar"]["income"] == 11
assert by_base["Torturer's Mask"]["cost"] == 1 and by_base["Torturer's Mask"]["income"] is None
assert by_base["Torturer's Mask"]["sold_at"] is None
assert by_base["Syndicate's Garb"]["cost"] == 9 and by_base["Syndicate's Garb"]["income"] is None
assert by_base["Sacred Chainmail"]["cost"] == 5 and by_base["Sacred Chainmail"]["income"] is None
assert journal.list_all()[0]["base"] == "Sacred Chainmail"  # second call: no re-import
print("Test 6 PASS — legacy import (5 rows, one flip each, idempotent)")

# --- Test 7: persistence round-trip across connection reopen ---
reset()
journal.add("Standard", "Necrotic Armour", 30, cost=2.0, income=4.0)
journal._conn = None  # simulate process restart
rec = journal.list_all()[0]
assert rec["base"] == "Necrotic Armour" and rec["net"] == 2.0
print("Test 7 PASS — round-trip")

print("\nAll journal tests PASS")
