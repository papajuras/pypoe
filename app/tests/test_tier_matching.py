"""Tier-colliding mods (shared name, distinct roll ranges) must match only their own range."""

from pypoe.db.affixes import load_affixes, save_text_for
from pypoe.crafting.matching import any_of_list_in_string


# --- Test 1: influenced — Warlord Strength tiers on Amulet ---
p, s = load_affixes("Amulet")
wl = [e for e in s if e["influence"] == "WARLORD" and "Strength" in e["game_text"]]
assert len(wl) >= 2, f"expected multiple warlord strength tiers, got {len(wl)}"
t1 = [e for e in wl if "5-8" in e["game_text"]][0]
t2 = [e for e in wl if "9-12" in e["game_text"]][0]
p1, p2 = save_text_for(t1), save_text_for(t2)
assert p1 != p2, f"tiers must yield distinct patterns: {p1!r} {p2!r}"
assert any_of_list_in_string("7(5-8)% increased strength", [p1]), p1
assert not any_of_list_in_string("7(5-8)% increased strength", [p2]), p2
assert any_of_list_in_string("12(9-12)% increased strength", [p2]), p2
assert not any_of_list_in_string("12(9-12)% increased strength", [p1]), p1
print("Test 1 PASS (warlord strength tiers)")

# --- Test 2: non-influenced — "of Abjuration" spell-suppression tiers on Body Armour ---
p, s = load_affixes("Body Armour")
abj = [e for e in s if e["name"] == "of Abjuration"]
assert len(abj) >= 2, f"expected multiple of Abjuration tiers, got {len(abj)}"
pats = [save_text_for(e) for e in abj]
assert len(set(pats)) == len(pats), f"tiers must be distinct: {pats}"
lo = [e for e in abj if "11-12" in e["game_text"]][0]
hi = [e for e in abj if "17-19" in e["game_text"]][0]
pl, ph = save_text_for(lo), save_text_for(hi)
assert any_of_list_in_string("11(11-12)% chance to suppress spell damage", [pl]), pl
assert not any_of_list_in_string("11(11-12)% chance to suppress spell damage", [ph]), ph
assert any_of_list_in_string("18(17-19)% chance to suppress spell damage", [ph]), ph
assert not any_of_list_in_string("18(17-19)% chance to suppress spell damage", [pl]), pl
print("Test 2 PASS (of Abjuration spell-suppression tiers)")

print("\nAll tests PASS")
