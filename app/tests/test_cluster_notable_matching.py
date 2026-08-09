"""Cluster jewel notables share generic affix names (Notable / of Significance)
but have unique game_text. Matching must use the notable's game_text
("1 Added Passive Skill is X"), which is what actually appears on the item,
instead of the ambiguous shared name.
"""

from pypoe.db.affixes import load_affixes, save_text_for


# --- Setup: suffix notables all share the name "of Significance" ---
p, s = load_affixes("Cluster Jewel (Large)", "Two-Handed Melee Damage")
suffix_entries = {e["mod_id"]: e for e in s}
prefix_entries = {e["mod_id"]: e for e in p}

significance = [e for e in s if e["name"] == "of Significance"]
assert len(significance) == 3, f"precondition: ambiguous name 'of Significance' -> {len(significance)}"
heavy = [e for e in significance if "heavyhitter" in e["mod_id"].lower()][0]

# --- Test 1: suffix notable saves as its unique game_text, not the shared name ---
saved = save_text_for(heavy)
assert saved == "1 Added Passive Skill is Heavy Hitter", repr(saved)
print("Test 1 PASS")

# --- Test 2: saved text round-trips to exactly one mod (disambiguation) ---
matches = [e for e in s if save_text_for(e) == saved]
assert matches == [heavy], [e["mod_id"] for e in matches]
print("Test 2 PASS")

# --- Test 3: saved text matches realistic item text; other same-name notables don't ---
item_text = """Suffix: of Significance
1 Added Passive Skill is Heavy Hitter""".lower()
assert saved.lower() in item_text
for other in significance:
    if other is heavy:
        continue
    assert save_text_for(other).lower() not in item_text, f"false positive: {other['mod_id']}"
print("Test 3 PASS")

# --- Test 4: prefix notables ("Notable" x13) also save as unique game_text ---
notables = [e for e in p if e["name"] == "Notable"]
assert len(notables) >= 2
assert all(save_text_for(e) not in {save_text_for(o) for o in notables if o is not e} for e in notables)
mastery = [e for e in notables if "martialmastery" in e["mod_id"].lower()][0]
assert save_text_for(mastery) == "1 Added Passive Skill is Martial Mastery"
print("Test 4 PASS")

# --- Regression: regular item mods still save their affix name ---
pr, sr = load_affixes("Ring")
ring_entries = {e["mod_id"]: e for e in pr + sr}
lizard = [e for e in sr if e["name"] == "of the Lizard"][0]
assert save_text_for(lizard) == "of the Lizard"
print("Test 5 PASS")

# --- Regression: cluster small-passive grants still save their real name ---
agile = [e for e in p if e["name"] == "Acrobat's"][0]
assert save_text_for(agile) == "Acrobat's"
print("Test 6 PASS")

print("\nAll cluster notable tests PASS")
