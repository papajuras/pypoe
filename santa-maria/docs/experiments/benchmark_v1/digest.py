#!/usr/bin/env python3
"""Digest raw benchmark envelopes into a compact per-entry summary."""

import json
from pathlib import Path

RAW = Path(__file__).resolve().parent / "raw"


def load(path):
    return json.loads(path.read_text())


def main():
    lines = []
    for rec_path in sorted(RAW.glob("*.record.json")):
        rec = load(rec_path)
        base = rec_path.name[: -len(".record.json")]
        lines.append(f"## [{rec['index']:3d}] {rec['node_id']}  ({rec['type']})")

        r = load(RAW / f"{base}.resolve.json")
        for res in r.get("results", [])[:3]:
            pi = res.get("passive_info")
            extra = ""
            if pi:
                extra = f" asc={pi.get('ascendancy')} keystone={pi.get('kind_flags', {}).get('is_keystone')} notable={pi.get('kind_flags', {}).get('is_notable')}"
            lines.append(f"  resolve: {res['id']} | {res.get('name')!r} | {res.get('availability')}{extra}")
        if r.get("meta", {}).get("ambiguous"):
            lines.append(f"  resolve: AMBIGUOUS total={r['meta'].get('total')}")
        if r.get("error"):
            lines.append(f"  resolve: ERROR {r['error']['code']} {str(r['error'].get('detail'))[:80]}")

        c = load(RAW / f"{base}.carriers.json")
        if not c.get("error"):
            counts = c["meta"]["counts"]
            nz = {k: v for k, v in counts.items() if v}
            lines.append(f"  carriers: {nz if nz else 'ALL ZERO'}")
            for res in c.get("results", [])[:12]:
                lines.append(f"    <- {res['carrier']} ({res['edge_type']}) {str(res.get('carrier_name'))[:48]!r}")
            if len(c.get("results", [])) > 12:
                lines.append(f"    ... +{len(c['results']) - 12} more")
        else:
            lines.append(f"  carriers: ERROR {c['error']['code']}")

        n = load(RAW / f"{base}.neighbour.json")
        if not n.get("error"):
            edges = [e for lvl in n.get("levels", []) for e in lvl.get("edges", [])]
            out_e = [e for e in edges if e.get("direction") == "out"]
            in_e = [e for e in edges if e.get("direction") != "out"]
            lines.append(f"  neighbour: out={len(out_e)} in={len(in_e)} truncated={n.get('truncated')}")
            by_type = {}
            for e in edges:
                by_type.setdefault(e["type"], []).append(e)
            for t, es in sorted(by_type.items()):
                lines.append(f"    {t} n={len(es)}:")
                for e in es[:10]:
                    other = e["to"] if e["direction"] == "out" else e["from"]
                    lines.append(f"      {'->' if e['direction'] == 'out' else '<-'} {other}")
                if len(es) > 10:
                    lines.append(f"      ... +{len(es) - 10} more")
        else:
            lines.append(f"  neighbour: ERROR {n['error'].get('code')}")
        lines.append("")

    out = Path(__file__).resolve().parent / "digest.txt"
    out.write_text("\n".join(lines))
    print(f"wrote {out} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
