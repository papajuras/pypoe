#!/usr/bin/env python3
"""Generate tools/sources/applies_to_mechanics.json — mechanical sweep of the
"applies-to / transfiguration" bridge class from PoB ModParser (pinned commit).

Class boundary (mechanical, flag-identifier regexes over ModParser pattern
tables — NOT a mechanic list):

    (Improved)?[A-Za-z]+AppliesTo[A-Za-z]+      e.g. SpellDamageAppliesToAttacks
    [A-Za-z]*TransfigurationOf[A-Za-z]+         e.g. TransfigurationOfMind

(The Transfiguration family widened the boundary; they are the fixtures that
exposed the blind spot, not a curated target.)

Every binding is evidence-backed or reported unbound — never guessed:

- flag evidence:  the ModParser pattern-table line(s) that define the flag
  (file:line recorded per entry).
- handler evidence: where the flag is consumed in the Calc modules
  (`Flag(nil, "Name")`), the surrounding lines give the operand mod field
  (Sum("INC", ..., "Field")), the output field (NewMod(...)) and the value
  expression (data.misc.<Const> resolved against src/Modules/Data.lua).
- bridge-stat binding: KB Stat nodes bound by (a) RePoE English translation
  matching the ModParser phrase, or (b) the documented flag->id token
  transform (flag camel tokens -> stat-id fragments, verified to exist).
- operand binding (strict): PoB operand mod field (handler preferred, else
  the phrase's operand segment) -> candidate stat:<snake>_+% / stat:<snake>,
  accepted only if the node exists AND its RePoE translation names the same
  modifier family. Otherwise operand_stat = null (unbound, reported).

Flags already covered by the audited tools/sources/pob_stat_mechanics.json
are skipped (dedup by pob_flag) and reported as covered.

Idempotent: deterministic output for a given manifest commit.

Usage:
  python3 generate_applies_to.py             # write artifact + report
  python3 generate_applies_to.py --check     # verify artifact matches current sources, no write
"""
import json
import re
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parent
SANTA = Path(__file__).resolve().parents[2]
DATA = SANTA / 'data'
ARTIFACT = Path(__file__).resolve().parent / 'applies_to_mechanics.json'
AUDITED = Path(__file__).resolve().parent / 'pob_stat_mechanics.json'

MODPARSER = 'pob-src/src/Modules/ModParser.lua'
CALC_FILES = ('pob-src/src/Modules/CalcOffence.lua',
              'pob-src/src/Modules/CalcDefence.lua',
              'pob-src/src/Modules/CalcPerform.lua',
              'pob-src/src/Modules/CalcSetup.lua')
DATA_CONST = 'pob-src/src/Modules/Data.lua'

FLAG_RE = re.compile(r'\b(?:Improved)?[A-Za-z]+AppliesTo[A-Za-z]+\b'
                     r'|\b[A-Za-z]*TransfigurationOf[A-Za-z]+\b')
FLAG_CALL_RE = re.compile(r'flag\(\s*"([A-Za-z]+)"')
PATTERN_LINE_RE = re.compile(r'^\s*\[\s*"(.+?)"\s*\]\s*=')
HANDLER_RE = re.compile(r'Flag\((?:nil|cfg),\s*"([A-Za-z]+)"\)')
SUM_RE = re.compile(r'Sum\(\s*"INC",\s*(?:nil|cfg),\s*"([A-Za-z]+)"')
NEWMOD_RE = re.compile(r'NewMod\(\s*"([A-Za-z]+)",\s*"INC"')
MODFLAG_RE = re.compile(r'ModFlag\.([A-Za-z]+)')

CAMEL_RE = re.compile(r'(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])')


def camel_tokens(name):
    return [t.lower() for t in CAMEL_RE.sub('_', name).split('_') if t]


def snake(name):
    return '_'.join(camel_tokens(name))


def norm(text):
    """Normalize a phrase/translation for matching: lowercase, digits->{0},
    collapse punctuation/whitespace."""
    t = re.sub(r'\d+', '{0}', text.lower())
    return re.sub(r'[^a-z{0}]+'.format('0'), ' ', t.replace('{0}', ' {0} '))\
        .replace('%', ' % ').strip()


def tokens(text):
    return [t for t in norm(text).split() if t not in ('{0}', '%')]

# PoB pool fields whose INC modifier family is named "maximum <field>" in game
# wording (verified per candidate against RePoE translations at bind time).
POOL_FIELDS = {'mana', 'life', 'energy_shield'}

CONNECTOR_RE = re.compile(r'apply|affect|also|transformed')
CONNECTOR_TOKENS = {'to', 'at', 'of', 'value', 'while', 'if', 'when', 'during',
                    'you', 'your', 'their', 'the', 'and', 'a', 'an', 'is',
                    'are', 'in', 'increased', 'reduced', 'increases',
                    'reductions', 'increases', 'modifiers', 'per', 'instead'}
STOP_TOKENS = CONNECTOR_TOKENS | {'applies', 'apply', 'also', 'affect',
                                  'affects', 'transformed'}


def manifest_commit():
    meta = json.loads((DATA / 'manifest.json').read_text()).get('_meta') or {}
    commit = ((meta.get('sources') or {}).get('poblua') or {}).get('commit')
    assert commit, 'manifest _meta.sources.poblua.commit missing — run phase1_download.py'
    return commit


def load_translations():
    st = json.load(open(DATA / 'repoe' / 'stat_translations.json'))
    out = {}
    for grp in st:
        for sid in grp.get('ids', []):
            for e in grp.get('English', []):
                s = e.get('string')
                if s:
                    out.setdefault(sid, []).append(s)
    return out


def load_kb_stats():
    import sqlite3
    con = sqlite3.connect(SANTA / 'cache' / 'nodes.db')
    ids = {r[0][5:] for r in con.execute(
        "select node_id from nodes where type='Stat'")}
    con.close()
    return ids


def scan_flags(modparser):
    """flag -> {'phrases': [(line_no, lua_pattern, call_lines)], 'improved': bool}"""
    flags = {}
    lines = modparser.split('\n')
    for i, line in enumerate(lines, 1):
        pm = PATTERN_LINE_RE.match(line)
        if not pm:
            continue
        calls = FLAG_CALL_RE.findall(line)
        for fl in calls:
            if not FLAG_RE.fullmatch(fl):
                continue
            e = flags.setdefault(fl, {'phrases': [], 'improved': False})
            e['phrases'].append((i, pm.group(1)))
        if re.search(r'mod\(\s*"Improved[A-Za-z]+', line):
            m = re.search(r'Improved([A-Za-z]+)', line)
            if m:
                base = FLAG_RE.search(m.group(1))
    # improved flags companion: detect Improved<...> mod() on the same lines
    for i, line in enumerate(lines, 1):
        for m in re.finditer(r'mod\(\s*"Improved([A-Za-z]+AppliesTo[A-Za-z]+)', line):
            if m.group(1) in flags:
                flags[m.group(1)]['improved'] = True
    return flags


def handler_evidence(flag, calc_texts, data_consts):
    """Consume-site evidence: (file, line, operand_field, output_field,
    output_modflag, value)."""
    for f, text in calc_texts.items():
        for m in HANDLER_RE.finditer(text):
            if m.group(1) != flag:
                continue
            start = m.start()
            block = text[start:start + 700]
            ln = text[:start].count('\n') + 1
            sm = SUM_RE.search(block)
            nm = NEWMOD_RE.search(block)
            mf = MODFLAG_RE.search(block)
            value = None
            vm = re.search(r'data\.misc\.([A-Za-z]+)', block)
            if vm and vm.group(1) in data_consts:
                value = data_consts[vm.group(1)]
            return {'file': f.replace('pob-src/', ''),
                    'line': ln,
                    'operand_field': sm.group(1) if sm else None,
                    'output_field': nm.group(1) if nm else None,
                    'output_modflag': mf.group(1) if mf else None,
                    'value': value}
    return None


NEGATION_RE = re.compile(r'\b(?:dont|do_not|not|cannot|never|without)\b')


def _negated(text):
    return bool(NEGATION_RE.search(norm(text).replace(' ', '_')) or
                NEGATION_RE.search(text))


def pattern_to_phrase(p):
    """Lua pattern text -> normalized phrase: strip regex groups/captures."""
    p = re.sub(r'\((?:%[a-z%%d+]+)\)', ' {0} ', p)      # (%d+), (%a+), (%%)
    p = p.replace('%%', '%').replace('%s', ' {0} ').replace('%d', ' {0} ')
    return p


def bind_stats(flag, phrases, translations, kb_stats):
    """(canonical, members). Strict bindings only:
    (a) translation match = normalized EQUALITY between the ModParser phrase
        and the stat's English translation (value placeholders normalized);
    (b) flag token transform = all flag core tokens occur in the stat id AND
        the id is bridge-shaped (apply/affect/also/transformed) AND neither
        side is negated. virtual_* synthetic stats are skipped.
    Canonical = best-scoring member (translation evidence > no negation >
    shortest id). Mis-bindings are worse than unbound: anything else is
    reported, not guessed."""
    members, seen = [], set()
    phrases_n = [norm(pattern_to_phrase(p)) for _ln, p in phrases]
    phrases_neg = any(_negated(p) for _ln, p in phrases)
    # (a) normalized-equality translation match
    for sid, strs in sorted(translations.items()):
        if sid not in kb_stats or sid.startswith('virtual_'):
            continue
        for s in strs:
            if _negated(s) and not phrases_neg:
                continue
            if norm(s) in phrases_n:
                members.append({'stat': sid, 'role': None, 'value': None,
                                'condition': None,
                                'evidence': 'stat_translations equality'})
                seen.add(sid)
                break
    # (b) token transform
    toks = [t for t in camel_tokens(flag) if t not in STOP_TOKENS and t != 'improved']
    for sid in sorted(kb_stats):
        if sid in seen or sid.startswith('virtual_'):
            continue
        if toks and all(t in sid for t in toks) and CONNECTOR_RE.search(sid) \
                and not (NEGATION_RE.search(sid.replace('_', ' '))
                         and not phrases_neg):
            members.append({'stat': sid, 'role': None, 'value': None,
                            'condition': None,
                            'evidence': 'flag token transform'})
            seen.add(sid)
    if not members:
        return None, []
    # classify roles + value/condition from id segments
    canon = None
    for m in members:
        sid = m['stat']
        vm = re.search(r'_at_(\d+)%_value$', sid)
        pm = re.search(r'_at_%_value', sid)
        cond = re.search(r'_(while|if|when|during)_[a-z_]+$', sid)
        if vm:
            m['role'] = 'variant'
            m['value'] = int(vm.group(1))
        elif pm:
            m['role'] = 'variant'
            m['value'] = 'per-stat'
        elif re.search(r'_value$', sid):
            m['role'] = 'variant'
            m['value'] = 'per-stat'
        elif cond is None:
            m['role'] = 'canonical'
            canon = m
        if cond:
            m['condition'] = cond.group(0)[1:]
    if canon is None and members:
        # score-based fallback: translation evidence > no negation > shortest id
        def score(m):
            return (3 if m['evidence'].startswith('stat_translations') else 0) \
                - (5 if NEGATION_RE.search(m['stat'].replace('_', ' ')) else 0) \
                - len(m['stat']) / 1000
        canon = max(members, key=score)
        canon['role'] = 'canonical'
    return canon, members


def mod_field_phrases(modparser):
    """ModParser pattern-table index: PoB mod field (INC/BASE) -> set of
    normalized phrases that map to it. Used to corroborate operand families
    from PoB's own phrase table."""
    out = {}
    for line in modparser.split('\n'):
        pm = PATTERN_LINE_RE.match(line)
        if not pm:
            continue
        for m in re.finditer(r'mod\(\s*"([A-Za-z]+)",\s*"(?:INC|BASE)"', line):
            out.setdefault(m.group(1), set()).update(tokens(pm.group(1)))
    return out


def bind_operand(handler, phrases, modparser, field_phrases, translations, kb_stats):
    """Strict operand binding. Sources: handler operand mod field (strongest,
    code-region evidence) else the phrase's operand segment. A candidate
    stat:<family>_+% (or the pool-mapped maximum_<family>_+%) is accepted
    only if the node exists AND the family is corroborated by RePoE
    translation or by ModParser's own phrase table. Zero or multiple
    verified candidates -> unbound (never guessed)."""
    sources = []
    if handler and handler.get('operand_field'):
        sources.append((camel_tokens(handler['operand_field']),
                        f"handler {handler['file']}:{handler['line']} "
                        f"operand field {handler['operand_field']}"))
    for ln, p in phrases:
        seg = re.split(r' also appl| appl(?:y|ies) to| also affect| '
                       r'affect[s]? ', p, maxsplit=1)[0]
        seg = re.sub(r'^(increases and reductions to|modifiers to|increased)\s+', '', seg)
        seg = seg.strip()
        if seg:
            stoks = [t for t in tokens(seg) if t not in ('your', 'the')]
            sources.append((stoks, f'ModParser:{ln} phrase operand segment'))
    for ftoks, how in sources:
        fam = ' '.join(ftoks)
        if not fam:
            continue
        cands = ['_'.join(ftoks) + '_+%']
        if '_'.join(ftoks) in POOL_FIELDS:
            cands.insert(0, 'maximum_' + '_'.join(ftoks) + '_+%')
        hits = []
        for sid in cands:
            if sid not in kb_stats:
                continue
            corr = []
            for s in translations.get(sid, []):
                st = tokens(s)
                if st and all(t in st for t in ftoks):
                    corr.append('translation')
                    break
            # ModParser phrase-table corroboration: any phrase mapped to a
            # mod field whose tokens contain the family tokens
            for field, ph_toks in field_phrases.items():
                if set(ftoks) <= ph_toks:
                    corr.append('ModParser phrase table')
                    break
            if corr:
                hits.append((sid, how + '; ' + '/'.join(sorted(set(corr)))))
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            return None, f'ambiguous operand candidates: {[h[0] for h in hits]}'
    return None, 'no KB stat correspondence verified'


def camel_join(tokens_):
    return ''.join(t.title() for t in tokens_)


def operand_phrase(handler):
    return handler.get('operand_field') if handler else None


def main(check=False, report=True):
    commit = manifest_commit()
    modparser = (DATA / MODPARSER.replace('pob-src/', '')).read_text() \
        if False else (DATA / MODPARSER).read_text()
    calc_texts = {f: (DATA / f).read_text() for f in CALC_FILES if (DATA / f).exists()}
    dl = (DATA / DATA_CONST).read_text()
    data_consts = {m.group(1): float(m.group(2)) for m in
                   re.finditer(r'([A-Za-z]+) = ([\d.]+),', dl)}
    translations = load_translations()
    kb_stats = load_kb_stats()
    field_phrases = mod_field_phrases(modparser)
    audited = json.loads(AUDITED.read_text())
    covered = {m['pob_flag'] for m in audited['mechanics']}

    flags = scan_flags(modparser)
    entries, unbound, dyn = [], [], []
    for flag in sorted(flags):
        info = flags[flag]
        if flag in covered:
            dyn.append({'flag': flag, 'status': 'covered by audited artifact'})
            continue
        handler = handler_evidence(flag, calc_texts, data_consts)
        canon, members = bind_stats(flag, info['phrases'], translations, kb_stats)
        op_stat, op_ev = bind_operand(handler, info['phrases'], modparser,
                                      field_phrases, translations, kb_stats)
        value = (handler or {}).get('value')
        if value is None:
            for _ln, p in info['phrases']:
                vm = re.search(r'\((\d+)\)%% of their value', p)
                if vm:
                    value = int(vm.group(1))
                    break
        if canon is None:
            unbound.append({'flag': flag, 'reason': 'no KB bridge stat bound',
                            'phrases': [p for _l, p in info['phrases']]})
            continue
        entry = {
            'id': snake(flag),
            'pob_flag': flag,
            'improved_flag': f'Improved{flag}' if info['improved'] else None,
            'canonical_stat': 'stat:' + canon['stat'],
            'operand_stat': ('stat:' + op_stat) if op_stat else None,
            'product_stat': None,
            'members': [dict(m, stat='stat:' + m['stat']) for m in members],
            'operand_evidence': op_ev,
            'handler': {k: v for k, v in (handler or {}).items() if v is not None} or None,
            'value': value,
            'pattern_lines': [{'line': ln, 'phrase': p} for ln, p in info['phrases']],
        }
        entries.append(entry)

    artifact = {
        'provenance': {
            'provenance_class': 'generated_mechanical_extraction',
            'pob_repo': 'PathOfBuildingCommunity/PathOfBuilding',
            'pob_commit': commit,
            'pob_branch': 'master',
            'source_file': 'src/Modules/ModParser.lua',
            'extraction': 'mechanical sweep of applies-to / transfiguration flag class; '
                          'bindings evidence-backed (pattern lines, Calc handler regions, '
                          'RePoE stat translations); unresolvable bindings reported unbound',
        },
        'mechanics': entries,
        'unbound': unbound,
        'covered_by_audited': [d['flag'] for d in dyn],
    }
    if check:
        if ARTIFACT.exists():
            on_disk = json.loads(ARTIFACT.read_text())
            if on_disk != artifact:
                print('CHECK FAILED: committed applies_to_mechanics.json drifts '
                      'from the current sources (regenerate it)')
                raise SystemExit(1)
            print('check ok: applies_to_mechanics.json matches the pinned sources')
        else:
            print('applies_to_mechanics.json missing — run without --check to generate')
    else:
        ARTIFACT.write_text(json.dumps(artifact, indent=1, sort_keys=True))
    if report:
        print(f'applies-to sweep: {len(entries)} new mechanics, '
              f'{len(unbound)} unbound, {len(dyn)} covered by audited artifact')
        for e in entries:
            print(f"  {e['pob_flag']}: canonical={e['canonical_stat']} "
                  f"operand={e['operand_stat']} value={e['value']} "
                  f"members={len(e['members'])}")
        for u in unbound:
            print(f"  UNBOUND {u['flag']}: {u['reason']}")
    return len(entries), len(unbound)


if __name__ == '__main__':
    check = '--check' in sys.argv
    main(check=check)
