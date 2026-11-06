"""The observation dashboard as of the backtest cutoff close: reports/monitor.md + reports/results/monitor.json.

Usage: .venv/bin/python scripts/run_monitor.py [--asof YYYY-MM-DD]
Each row shows the value, the date the value describes, its age, and OK/STALE/MISSING.
"""
import argparse
import datetime as dt
import json

import _bootstrap  # noqa: F401

from midterm_quant import config
from midterm_quant.research.monitor import ORIGINAL_33, read_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=config.BACKTEST_END)
    args = ap.parse_args()
    rows = read_all(args.asof, live=True)
    generated = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    lines = [f"# Observation dashboard as of the {args.asof} close", "",
             f"Generated {generated}. Each value is dated by the observation it describes; 'age' is days from that observation to {args.asof}.", "",
             "| Group | Code | Indicator | Value | Observation date | Age (d) | Status | Read | Context | Rule |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r.group} | {r.code} | {r.name} | {r.value} | {r.observation_date or '-'} | {r.age_days if r.age_days is not None else '-'} | {r.status} | **{r.regime}** | {r.context} | {r.rule} |")
        print(f"{r.code:5s} {r.name[:46]:46s} {r.value:>14s} {str(r.observation_date):>10s} {r.status:7s} {r.regime}")
    config.REPORTS_DIR.mkdir(exist_ok=True)
    (config.REPORTS_DIR / "monitor.md").write_text("\n".join(lines) + "\n")
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.RESULTS_DIR / "monitor.json").write_text(json.dumps({
        "asof": args.asof, "generated_utc": generated, "original_33": ORIGINAL_33,
        "readings": [r.as_dict() for r in rows]}, indent=1, default=str))
    print("wrote reports/monitor.md, reports/results/monitor.json")


if __name__ == "__main__":
    main()
