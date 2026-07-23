"""Verify builder display and save text match in-game clipboard text."""

from db.affixes import load_affixes


# --- Test 1: Recover Life on Block (Shaper influenced) ---
p, s = load_affixes("Shield")
mod = [a for a in s if a["mod_id"] == "RecoverLifePercentOnBlockUber1_"][0]
assert mod["influence"] == "SHAPER"

display = f'[{mod["influence"]}] {mod["name"]} — {mod["game_text"]}'
print(f"Dropdown: {display}")

item_text = "Recover 5(3-5)% of Life when you Block".lower()
assert mod["game_text"].lower() in item_text, (
    f"Test 1 FAILED\n"
    f"  search_text: {mod['game_text']!r}\n"
    f"  item_text:   {item_text!r}"
)
print("Test 1 PASS")

# --- Test 2: Cold Damage per 10 Dex (Shaper influenced) ---
p, s = load_affixes("1H Sword")
mod = [a for a in p if a["mod_id"] == "AddedColdDamagePerDexterityUber1"][0]
assert mod["influence"] == "SHAPER"

display = f'[{mod["influence"]}] {mod["name"]} — {mod["game_text"]}'
print(f"Dropdown: {display}")

item_text = "Adds (1-2) to (3-4) Cold Damage to Attacks with this Weapon per 10 Dexterity".lower()
assert mod["game_text"].lower() in item_text, (
    f"Test 2 FAILED\n"
    f"  search_text: {mod['game_text']!r}\n"
    f"  item_text:   {item_text!r}"
)
print("Test 2 PASS")

# --- Test 3: Non-influenced retains formatted stats ---
p, s = load_affixes("Ring")
mod = [a for a in p if a["name"] == "Aqua"][0]
assert not mod["influence"]
print(f"Dropdown: {mod['name']} — {mod['game_text']}")
assert "base maximum mana" in mod["game_text"], (
    f"Test 3 FAILED: non-influenced mod lost stat info: {mod['game_text']!r}"
)
print("Test 3 PASS")

print("\nAll tests PASS")
