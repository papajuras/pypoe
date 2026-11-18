"""Serle's Masterwork availability fix tests (PoB 'Source:' signal).

Run: cd santa-maria && uv run python -m tools.tests.test_availability
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import phase7_build_validity as bv
from tools.phase6_api import get_start_seed

ROOT = Path(__file__).resolve().parents[2]
SERLE = "Serle's Masterwork"
AVAILABLE = 'Soul Tether'


def _db_digests():
    out = []
    for db in ('cache/nodes.db', 'cache/edges.db'):
        p = ROOT / db
        out.append(hashlib.sha256(p.read_bytes()).hexdigest())
    return out


def test_serles_detected_unavailable():
    assert bv._pob_availability()[SERLE] == 'unavailable'
    r = bv.validate_build(bv.BuildState([SERLE]))
    assert r['status'] == bv.INVALID, r
    assert 'No longer obtainable' in r['reason']
    assert 'item_availability' in r['checked']


def test_addition_rejected_and_attributed():
    state = bv.BuildState([AVAILABLE])
    r = bv.validate_addition(state, SERLE)
    assert r['status'] == bv.INVALID, r
    assert 'candidate' in r['reason'] and 'no longer obtainable' in r['reason']
    assert state.items == [AVAILABLE]          # no mutation


def test_available_unique_stays_valid():
    r = bv.validate_build(bv.BuildState([AVAILABLE]))
    assert r['status'] == bv.VALID, r
    ac = r['availability_checks']
    assert ac['status'] == bv.VALID
    assert ac['items'][0]['availability'] == 'available'
    # mixed list: unavailable poisons the whole state
    r2 = bv.validate_build(bv.BuildState([AVAILABLE, SERLE]))
    assert r2['status'] == bv.INVALID and 'No longer obtainable' in r2['reason']


def test_no_graph_mutation():
    before = _db_digests()
    bv.validate_build(bv.BuildState([SERLE, AVAILABLE]))
    bv.validate_addition(bv.BuildState(), SERLE)
    assert _db_digests() == before, 'nodes.db/edges.db changed'


def test_api_seed_exposes_availability():
    for name, want in ((SERLE, 'unavailable'), (AVAILABLE, 'available'),
                       ("Demigod's Eye", None)):    # no PoB block -> not checked
        e = get_start_seed({'name_contains': name, 'count': 1})['seeds'][0]
        assert e['type'] == 'UniqueItem'
        assert e.get('availability') == want, (name, e)


def test_cli_rejects_serles():
    cli = ROOT / 'tools' / 'phase7_build_validity.py'
    p = subprocess.run([sys.executable, str(cli), 'build', SERLE],
                       capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out['status'] == 'invalid' and 'No longer obtainable' in out['reason']


if __name__ == '__main__':
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for fn in fns:
        fn()
        print(f'{fn.__name__}: OK')
    print(f'{len(fns)} tests passed')
