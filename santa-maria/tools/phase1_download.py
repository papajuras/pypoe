#!/usr/bin/env python3
"""Download RePoE English + pob-data/poe1 files as-is into santa-maria/data/.

Self-contained: fetches the git tree listings from the GitHub API itself
(no external /tmp dumps), then downloads every file from raw.githubusercontent.com.
Skips already-downloaded files (non-empty).

Scope: the intended Phase-1 scope is ENFORCED in code by `scope_filter`
(.json only, no .min.json; RePoE data/ also excludes the 9 language dirs and
Metadata/Terrain/). The RePoE git `data/` tree at the recorded commit SHA is
taken as the authoritative equivalent of the published RePoE export (the
published site is built from this repo); this is documented in `_meta.scope`.

Snapshot integrity:
- The manifest is built from the CURRENT download scope (the planned file
  list), NOT from whatever happens to exist on disk.
- Stale/out-of-scope files on disk are detected, reported, and EXCLUDED from
  the manifest (never silently part of the valid snapshot). They are not
  deleted.
- Upstream provenance (commit SHA + date per source repo) is recorded under a
  reserved `_meta` key; `_meta` also records planned / downloaded-ok / missing
  / stale counts so the scope is auditable.
"""
import json, os, urllib.request, hashlib
from datetime import datetime, timezone
from urllib.parse import quote
from pathlib import Path

SANTA = Path(__file__).resolve().parents[1]
DATA = SANTA / 'data'
MANIFEST = {}
META_KEY = '_meta'

LANGS = {'French','German','Japanese','Korean','Portuguese','Russian','Spanish','Thai','Traditional Chinese'}

REPOE_TREE = 'https://api.github.com/repos/repoe-fork/repoe-fork.github.io/git/trees/master?recursive=1'
REPOE_RAW = 'https://raw.githubusercontent.com/repoe-fork/repoe-fork.github.io/master/data/'
REPOE_REPO = 'repoe-fork/repoe-fork.github.io'
POB_TREE = 'https://api.github.com/repos/repoe-fork/pob-data/git/trees/master?recursive=1'
POB_RAW = 'https://raw.githubusercontent.com/repoe-fork/pob-data/master/pob-data/poe1/'
POB_REPO = 'repoe-fork/pob-data'


def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'recon'})
    return json.load(urllib.request.urlopen(req, timeout=120))


def repo_provenance(owner_repo):
    """Upstream commit SHA + committer date for a repo's master branch."""
    info = get_json(f'https://api.github.com/repos/{owner_repo}/commits/master')
    return {'commit': info.get('sha'),
            'date': (info.get('commit') or {}).get('committer', {}).get('date')}


def fetch(url, dest, retries=3):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return False
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'recon'})
            data = urllib.request.urlopen(req, timeout=120).read()
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'wb') as f:
                f.write(data)
            return True
        except Exception as e:
            if i == retries - 1:
                print(f"FAIL {url}: {e}")
    return False


def scope_filter(prefix, rel):
    """Enforce the intended download scope in code.

    Returns True if `rel` (relative to the source prefix) is in scope.
    Applied identically to the RePoE `data/` tree and the recursive
    `pob-data/poe1/` tree. `prefix` is 'repoe' or 'pob'.
    """
    if not rel.endswith('.json'):
        return False
    if rel.endswith('.min.json'):
        return False                      # .min.json build artifacts
    if prefix == 'repoe':
        if rel.split('/')[0] in LANGS:
            return False                  # non-English languages
        if rel.startswith('Metadata/Terrain/'):
            return False                  # procedural tile graphs
    return True


SCOPE_DESCRIPTION = (
    'in-scope = .json files, excluding .min.json build artifacts; RePoE data/ '
    'additionally excluding the 9 non-English language dirs and Metadata/Terrain/ '
    '(procedural tile graphs). The RePoE git `data/` tree at the recorded commit '
    'is taken as the authoritative equivalent of the published RePoE export '
    '(the site is built from this repo); provenance (commit/tree SHA) is recorded '
    'in _meta so the snapshot is auditable.'
)


def plan():
    """Return (files, provenance). files = [(relpath, url, dest)] covering the
    current intended download scope; provenance = per-repo commit/tree info."""
    files = []

    tree = get_json(REPOE_TREE)
    tree_sha = tree.get('sha')
    for e in tree.get('tree', []):
        if e['type'] != 'blob':
            continue
        p = e['path']
        if not p.startswith('data/'):
            continue
        rel = p[len('data/'):]
        if not scope_filter('repoe', rel):
            continue
        files.append((f'repoe/{rel}', REPOE_RAW + quote(rel, safe='/'), DATA / 'repoe' / rel))

    ptree = get_json(POB_TREE)
    ptree_sha = ptree.get('sha')
    for e in ptree.get('tree', []):
        if e['type'] != 'blob':
            continue
        p = e['path']
        if not p.startswith('pob-data/poe1/'):
            continue
        rel = p[len('pob-data/poe1/'):]
        if not scope_filter('pob', rel):
            continue
        files.append((f'pob/{rel}', POB_RAW + quote(rel, safe='/'), DATA / 'pob' / rel))

    provenance = {
        'repoe': {**repo_provenance(REPOE_REPO), 'tree': tree_sha},
        'pob': {**repo_provenance(POB_REPO), 'tree': ptree_sha},
    }
    return files, provenance


def build_manifest(files):
    """Manifest from the planned scope only: relpath -> [size, sha1] for files
    present on disk; missing planned files are returned separately."""
    manifest = {}
    missing = []
    for rel, _url, dest in files:
        if dest.exists() and dest.stat().st_size > 0:
            manifest[rel] = [dest.stat().st_size, hashlib.sha1(dest.read_bytes()).hexdigest()]
        else:
            missing.append(rel)
    return manifest, missing


def stale_files(files, root=DATA):
    """JSON files on disk that are NOT in the current download scope."""
    planned = {rel for rel, _u, _d in files}
    on_disk = set()
    for r, _, fs in os.walk(root):
        for fn in fs:
            if fn == 'manifest.json' or not fn.endswith('.json'):
                continue
            on_disk.add(os.path.relpath(os.path.join(r, fn), root))
    return sorted(on_disk - planned)


def main():
    files, provenance = plan()
    print(f"planning {len(files)} files")
    new = 0
    for _rel, url, dest in files:
        if fetch(url, dest):
            new += 1
    print(f"downloaded {new} new files")
    manifest, missing = build_manifest(files)
    stale = stale_files(files)
    if stale:
        print(f"WARNING: {len(stale)} stale/out-of-scope file(s) on disk excluded from manifest: {stale[:5]}")
    if missing:
        print(f"WARNING: {len(missing)} planned file(s) missing on disk (download failed?): {missing[:5]}")
    manifest[META_KEY] = {
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'sources': provenance,
        'scope': SCOPE_DESCRIPTION,
        'planned_count': len(files),
        'downloaded_ok_count': len(manifest),
        'missing_count': len(missing),
        'missing_files': missing,
        'downloaded_new': new,
        'stale_count': len(stale),
        'stale_files': stale,
    }
    with open(DATA / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=0, sort_keys=True)
    print(f"manifest entries: {len(manifest) - 1}")


if __name__ == '__main__':
    main()
