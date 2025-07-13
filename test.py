def any_of_list_in_string(s, patterns):
    s = s.lower()
    return any(p.lower() in s for p in patterns)
cpd = """
Item Class: Two Hand Swords
Rarity: Magic
Wicked Ezomyte Blade
--------
Two Handed Sword
Physical Damage: 102-190 (augmented)
Critical Strike Chance: 6.50%
Attacks per Second: 1.40
Weapon Range: 1.3 metres
--------
Requirements:
Level: 61
Str: 113
Dex: 113
--------
Sockets: G 
--------
Item Level: 82
--------
{ Implicit Modifier — Damage, Critical }
+25% to Global Critical Strike Multiplier (implicit)
--------
{ Prefix Modifier "Wicked" (Tier: 6) — Damage, Physical, Attack }
65(65-84)% increased Physical Damage
--------
Shaper Item
"""


prefixes = ["20% more Attack Damage", "phys"]

def count_patterns_in_string(s, patterns):
    s = s.lower()
    return sum(1 for p in patterns if p.lower() in s)

if __name__=="__main__":
    s = "The quick brown fox jumps over the lazy dog"
    patterns = ["quick", "fox", "cat"]
    count = count_patterns_in_string(s, patterns)
    print(count)  # Output: 2
