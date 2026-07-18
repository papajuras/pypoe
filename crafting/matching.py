def any_of_list_in_string(s: str, patterns: list[str]) -> bool:
    s = s.lower()
    return any(p.lower() in s for p in patterns)


def count_patterns_in_string(s: str, patterns: list[str]) -> int:
    s = s.lower()
    return sum(1 for p in patterns if p.lower() in s)


def has_prefix_slot(item_text: str) -> bool:
    return "prefix" not in item_text


def has_suffix_slot(item_text: str) -> bool:
    return "suffix" not in item_text


def matches_target(item_text: str, prefixes: list[str], suffixes: list[str], both_required: bool) -> bool:
    if both_required:
        return any_of_list_in_string(item_text, prefixes) and any_of_list_in_string(item_text, suffixes)
    return any_of_list_in_string(item_text, prefixes) or any_of_list_in_string(item_text, suffixes)
