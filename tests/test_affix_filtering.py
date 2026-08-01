"""Regular item affixes must be filtered by _matches_item, not the cluster-jewel matcher.
Regression: load_affixes applied _matches_affliction_jewel to all item types, dropping every
mod whose spawn weight relied on explicit tags (sword, two_hand_weapon, ...) — only the 10
universal "default" life prefixes survived. See git diff for the fix.
"""

from pypoe.db.affixes import load_affixes


# --- Regular items return tag-gated damage mods, not just life ---
p, s = load_affixes("2H Sword")
assert len(p) > 100, f"2H Sword prefixes collapsed: {len(p)}"
assert len(s) > 100, f"2H Sword suffixes collapsed: {len(s)}"
tag_gated = [e for e in p if e["mod_id"] == "LocalAddedColdDamageTwoHand1"]
assert len(tag_gated) == 1, "tag-gated 2H mod (LocalAddedColdDamageTwoHand1) missing"
print("Test 1 PASS (2H Sword:", len(p), "prefixes /", len(s), "suffixes)")

# --- Another regular base for good measure ---
pr, sr = load_affixes("Ring")
assert len(pr) > 100, f"Ring prefixes collapsed: {len(pr)}"
assert len(sr) > 100, f"Ring suffixes collapsed: {len(sr)}"
print("Test 2 PASS (Ring:", len(pr), "/", len(sr), ")")

# --- Cluster jewels keep their own matcher (not regressed) ---
cp, cs = load_affixes("Cluster Jewel (Large)", "Two-Handed Melee Damage")
assert len(cp) >= 20 and len(cs) >= 20, f"cluster jewel collapsed: {len(cp)}/{len(cs)}"
assert sum(1 for e in cs if e["name"] == "of Significance") == 3
print("Test 3 PASS (cluster:", len(cp), "/", len(cs), ")")

print("\nAll affix filtering tests PASS")
