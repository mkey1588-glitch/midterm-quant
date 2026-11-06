"""Compare a LEAN backtest export with the Backtrader ledger for the same strategy.

Usage: .venv/bin/python scripts/reconcile_lean.py <lean-backtest-dir> E1|C1

Expects the LEAN result JSON (``*-order-events.json`` and the result file with the 'Strategy
Equity' chart) produced by ``lean backtest``. NOT YET EXERCISED: no LEAN run exists (see
lean/README.md). The comparison logic mirrors midterm_quant/research/reconcile.py.
"""
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401
import pandas as pd

from midterm_quant import config


def main():
    run_dir, code = Path(sys.argv[1]), sys.argv[2]
    led = config.EVIDENCE_DIR / "ledgers" / code
    bt_orders = pd.read_csv(led / "orders.csv.gz")
    bt_orders = bt_orders[bt_orders["status"] == "Completed"]
    events = []
    for f in run_dir.glob("*order-events*.json"):
        events += json.loads(f.read_text())
    lean = pd.DataFrame([e for e in events if e.get("status") == "filled"])
    if lean.empty:
        sys.exit("no filled LEAN order events found")
    lean["date"] = pd.to_datetime(lean["time"], unit="s").dt.date.astype(str)
    a = bt_orders.groupby("fill_date").agg(n=("asset", "size"), notional=("notional", "sum"), fee=("commission", "sum"))
    b = lean.groupby("date").agg(n=("symbolValue", "size"), notional=("fillPrice", lambda s: float((s * lean.loc[s.index, "fillQuantity"]).sum())),
                                 fee=("orderFeeAmount", "sum"))
    j = a.index.union(b.index)
    cmp = pd.concat({"backtrader": a.reindex(j), "lean": b.reindex(j)}, axis=1)
    diff = cmp[(cmp["backtrader"]["n"].fillna(0) != cmp["lean"]["n"].fillna(0))]
    print(f"fill dates: backtrader {len(a)}, lean {len(b)}, dates with different fill counts {len(diff)}")
    if len(diff):
        print("first divergence:\n", diff.head(5).to_string())


if __name__ == "__main__":
    main()
