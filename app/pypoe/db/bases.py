"""Flip base-type definitions — single source of truth for generator + journal."""

QUALITIES = [27, 28, 29, 30]

GROUPS = [
    {
        "name": "body armour",
        "bases": [
            ("Royal Plate", 84, 86),
            ("Syndicate's Garb", 84, 86),
            ("Twilight Regalia", 84, 86),
            ("Conquest Lamellar", 84, 86),
            ("Sacred Chainmail", 84, 86),
            ("Necrotic Armour", 84, 86),
            ("Astral Plate", 84, 86),
            ("Assassin's Garb", 84, 86),
        ],
        "category": None,
        "notes": "",
    },
    {
        "name": "helmet",
        "bases": [
            ("Giantslayer Helmet", 84, 85),
            ("Majestic Pelt", 84, 85),
            ("Lich's Circlet", 84, 85),
            ("Haunted Bascinet", 84, 85),
            ("Penitent Mask", 84, 85),
            ("Divine Crown", 84, 85),
            ("Bone Helmet", 84, 85),
            ("Torturer's Mask", 84, 85),
            ("Blizzard Crown", 84, 85),
        ],
        "category": "armour.helmet",
        "donor_ilvl": 88,
        "notes": "check Nook's Crown card price",
    },
    {
        "name": "gloves",
        "bases": [
            ("Velour Gloves", 84, 85),
            ("Gripped Gloves", 84, 85),
            ("Trapsetter Gloves", 84, 85),
            ("Warlock Gloves", 84, 85),
            ("Nexus Gloves", 84, 85),
            ("Fingerless Silk Gloves", 84, 85),
            ("Wyvernscale Gauntlets", 84, 85),
            ("Paladin Gloves", 84, 85),
            ("Apothecary's Gloves", 84, 85),
            ("Phantom Mitts", 84, 85),
        ],
        "category": "armour.gloves",
        "donor_ilvl": 87,
        "notes": "",
    },
    {
        "name": "boots",
        "bases": [
            ("Velour Boots", 84, 85),
            ("Stormrider Boots", 84, 85),
            ("Warlock Boots", 84, 85),
            ("Dreamquest Slippers", 84, 85),
            ("Wyvernscale Boots", 84, 85),
            ("Two-Toned Boots", 84, 85),
            ("Paladin Boots", 84, 85),
            ("Phantom Boots", 84, 85),
            ("Fugitive Boots", 84, 85),
        ],
        "category": "armour.boots",
        "donor_ilvl": 88,
        "notes": "",
    },
]
