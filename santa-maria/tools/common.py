"""Shared constants for the santa-maria data tools."""
import re

_STAT_HASH = re.compile(r'(?:explicit\.)?stat_\d+$')

# Conversion/scaling substring patterns. ORDER MATTERS: a stat id is bucketed
# under the FIRST pattern that matches, so vocab.py (bucketing) and report.py
# (appendix table) must iterate in exactly this order.
CONVERSION_PATTERNS = [
    '_+%', 'per_', 'local_', 'of_', 'and_', 'while_', 'if_', 'on_hit', 'when_',
    'permyriad', '_as_', '%_of', 'recently', 'to_add_as', 'scal', 'applies_to',
    'converted_to', '_-%', 'as_extra', 'gained_as',
]

# Exhaustive per-file conversion/scaling scan vocabulary: union of
# CONVERSION_PATTERNS and the keyword patterns previously hard-coded in
# analyze.py (applies_to, gained_as, converted_to, as_extra, to_add_as,
# permyriad, inverse, specialcase, scal, variant, royale). Deduplicated,
# order preserved. Used by analyze.py (scan) and report.py (rendering).
SCAN_PATTERNS = [
    'applies_to', 'gained_as', 'converted_to', 'as_extra', 'to_add_as',
    'permyriad', 'inverse', 'specialcase', 'scal', 'variant', 'royale',
    '_+%', 'per_', 'local_', 'of_', 'and_', 'while_', 'if_', 'on_hit', 'when_',
    '_as_', '%_of', 'recently', '_-%',
]

# Cross-reference classes (matched against string VALUES). Each entry:
# (description, predicate(v, vocab)). `vocab` is the global stat-id
# vocabulary set; `stat_id` membership is a set lookup, the rest are cheap
# string/regex checks.
REF_CLASSES = {
    'stat_id':            ('value in stat-vocabulary', lambda v, vocab: v in vocab),
    'stat_id_hash':       ('regex ^stat_\\d+$ or explicit.stat_\\d+',
                           lambda v, vocab: _STAT_HASH.match(v) is not None),
    'metadata_path':      ('startswith Metadata/', lambda v, vocab: v.startswith('Metadata/')),
    'art_path':           ('startswith Art/', lambda v, vocab: v.startswith('Art/')),
    'trade_hash':         ('regex ^\\d{8,10}$', lambda v, vocab: v.isdigit() and 8 <= len(v) <= 10),
    'numeric_id':         ('regex ^\\d{4,}$ (not trade-hash length)',
                           lambda v, vocab: v.isdigit() and len(v) >= 4 and not (8 <= len(v) <= 10)),
}
# Cross-reference classes matched against dict KEYS. The value recorded is the
# key name itself; the path shows where the key sits.
KEY_CLASSES = {
    'id_key':             ('key is `id` or ends in _id/_key/_hash',
                           lambda k: k == 'id' or k.endswith(('_id', '_key', '_hash'))),
    'embedded_unique_id': ('key contains "Unique" (unique-item mod naming convention)',
                           lambda k: 'Unique' in k),
}

# Keyed-map heuristic. A dict path is a keyed map (instance ids / data as
# keys, rendered as `{}`) when EITHER:
#   - one instance alone has more than KEYED_MAX_FIELDS distinct keys
#     (a huge dict like passives{} is inherently a map), OR
#   - it appears in >= 2 instances and its key set is unstable across
#     instances: distinct keys >= instances x KEYED_RATIO (a fixed-field
#     record repeats the same ~dozen keys in every instance and never trips
#     this), OR
#   - all its keys are numeric (level maps `1..40`, hash maps, id maps).
# Collapse is render-only; analyze.py still records every raw path.
KEYED_MIN_KEYS = 10
KEYED_MAX_FIELDS = 64
KEYED_RATIO = 0.3
