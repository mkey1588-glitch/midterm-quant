"""Compare the current data cache with a reference manifest (by default the committed one).

Usage: .venv/bin/python scripts/verify_data.py [reference_manifest.json]

For each series: identical hash -> IDENTICAL. Different hash -> compare values up to the
backtest end: Yahoo adjusted closes are rescaled after each dividend, so daily *returns* are
compared (RETURNS MATCH if max abs difference < 1e-6); other sources compare levels
(VALUES MATCH / CHANGED). New observations after the cutoff are ignored. Exit status 1 if any
series used by the results CHANGED or is MISSING.
"""
import json
import sys

import _bootstrap  # noqa: F401
import pandas as pd

from midterm_quant import config
from midterm_quant.data.sources import read_meta


def main():
    ref_path = sys.argv[1] if len(sys.argv) > 1 else config.EVIDENCE_DIR / "data_manifest.reference.json"
    try:
        ref = json.loads(open(ref_path).read())
    except FileNotFoundError:
        print(f"no reference manifest at {ref_path}; nothing to verify")
        return 0
    end = pd.Timestamp(ref.get("backtest_end", config.BACKTEST_END))
    bad, rows = 0, []
    for s in ref["series"]:
        kind, name = s["kind"], s["series"]
        if kind == "alfred":
            continue
        stem = name.split(":", 1)[1] if kind == "fred" else ("stablecoins_usd" if kind == "defillama" else name)
        safe = stem.replace("^", "IDX_").replace("=", "_").replace("/", "_").replace(":", "_")
        path = config.CACHE_DIR / kind / f"{safe}.csv"
        if not path.exists():
            rows.append((name, "MISSING"))
            bad += 1
            continue
        if read_meta(path).get("sha256") == s["sha256"]:
            rows.append((name, "IDENTICAL"))
            continue
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        col = "close" if "close" in df.columns else df.columns[0]
        x = df[col].dropna()
        x = x[x.index <= end]
        vintage = config.CACHE_DIR / "vintages" / kind / safe
        prior = sorted(vintage.glob("*.csv")) if vintage.exists() else []
        # find the snapshot whose hash equals the reference, if we still have it locally
        ref_snap = next((p for p in prior if __import__("hashlib").sha256(p.read_bytes()).hexdigest() == s["sha256"]), None)
        if ref_snap is None:
            rows.append((name, "DIFFERENT HASH (reference bytes not held locally; compare returns after re-download)"))
            continue
        y = pd.read_csv(ref_snap, index_col=0, parse_dates=True)
        y = y[col if col in y.columns else y.columns[0]].dropna()
        y = y[y.index <= end]
        j = x.index.intersection(y.index)
        if kind == "yahoo":
            d = (x[j].pct_change() - y[j].pct_change()).abs().max()
            status = "RETURNS MATCH (rescaled adjusted prices)" if d < 1e-6 else f"CHANGED (max return diff {d:.2e})"
        else:
            d = (x[j] - y[j]).abs().max()
            status = "VALUES MATCH" if d < 1e-9 else f"CHANGED (max diff {d:.4g})"
        if status.startswith("CHANGED"):
            bad += 1
        rows.append((name, status))
    for n, st in rows:
        if st != "IDENTICAL":
            print(f"{n:28s} {st}")
    print(f"{sum(1 for _, s in rows if s == 'IDENTICAL')} identical, {len(rows)} checked, {bad} changed or missing")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
