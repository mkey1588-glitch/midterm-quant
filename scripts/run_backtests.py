"""Backtest all 20 strategies (plus rejected first specs) and write reports/.

Usage:  .venv/bin/python scripts/run_backtests.py [--codes E1 C3 ...] [--no-charts]
Outputs: reports/backtest_summary.{csv,md}, reports/yearly_returns.csv,
         reports/current_signals.md, reports/equity_<class>.png
"""
import argparse

import _bootstrap  # noqa: F401
import numpy as np
import pandas as pd

from midterm_quant import config
from midterm_quant.engine.runner import run_backtest
from midterm_quant.strategies import ALL, REJECTED

PCT = ["CAGR", "Vol", "MaxDD", "WorstYear", "Bench CAGR", "Bench MaxDD"]
RATIO = ["Sharpe", "Calmar", "Bench Sharpe", "AvgGross", "Turnover/yr"]


def fmt_table(df: pd.DataFrame) -> str:
    out = df.copy()
    for c in PCT:
        if c in out:
            out[c] = out[c].map(lambda v: f"{v:+.1%}" if pd.notna(v) else "")
    for c in RATIO:
        if c in out:
            out[c] = out[c].map(lambda v: f"{v:.2f}" if pd.notna(v) else "")
    cols = list(out.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in out.itertuples(index=False)]
    return "\n".join(lines)


def charts(results):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    surface, ink, ink2, grid = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    strat_c, bench_c = "#2a78d6", "#eb6834"
    by_class = {}
    for r in results:
        by_class.setdefault(r.asset_class, []).append(r)
    for cls, rs in by_class.items():
        fig, axes = plt.subplots(1, len(rs), figsize=(4.0 * len(rs), 3.4), facecolor=surface)
        for ax, r in zip(axes, rs):
            ax.set_facecolor(surface)
            ax.plot(r.bench.index, r.bench.values, color=bench_c, lw=1.6, label=f"Buy & hold {r.benchmark}")
            ax.plot(r.equity.index, r.equity.values, color=strat_c, lw=2.0, label="Strategy")
            ax.set_yscale("log")
            ax.set_title(f"{r.code}  {r.name}", fontsize=9, color=ink, loc="left")
            ax.grid(True, color=grid, lw=0.6)
            ax.tick_params(colors=ink2, labelsize=7)
            for s in ax.spines.values():
                s.set_visible(False)
            m = r.metrics
            ax.text(0.02, 0.96, f"CAGR {m['CAGR']:+.1%}  Sharpe {m['Sharpe']:.2f}\nMaxDD {m['MaxDD']:.0%}",
                    transform=ax.transAxes, fontsize=7, color=ink2, va="top")
            ax.legend(loc="lower right", fontsize=7, frameon=False, labelcolor=ink2)
        fig.suptitle(f"{cls}: growth of $1 (log scale), net of costs", fontsize=11, color=ink, x=0.01, ha="left")
        fig.tight_layout()
        path = config.REPORTS_DIR / f"equity_{cls.lower().replace(' ', '_')}.png"
        fig.savefig(path, dpi=130, facecolor=surface)
        plt.close(fig)
        print("wrote", path)


def blends(results) -> pd.DataFrame:
    """Equal-weight blend of each asset class's five sleeves (daily-rebalanced approximation)."""
    from midterm_quant.engine.metrics import perf_stats

    rows = []
    by_class = {}
    for r in results:
        by_class.setdefault(r.asset_class, []).append(r)
    for cls, rs in by_class.items():
        rets = pd.concat({r.code: r.equity.pct_change() for r in rs}, axis=1).dropna()
        eq = (1 + rets.mean(axis=1)).cumprod()
        periods = 365 if cls == "Crypto" else 252
        m = perf_stats(eq, periods)
        bench = rs[0].bench.reindex(eq.index)
        b = perf_stats(bench / bench.iloc[0], periods)
        rows.append({"Class": cls, "Sleeves": "+".join(r.code for r in rs), "Start": m["Start"], "CAGR": m["CAGR"],
                     "Vol": m["Vol"], "Sharpe": m["Sharpe"], "MaxDD": m["MaxDD"], "Bench": rs[0].benchmark,
                     "Bench CAGR": b["CAGR"], "Bench Sharpe": b["Sharpe"], "Bench MaxDD": b["MaxDD"],
                     "Avg pairwise corr": float(rets.corr().where(~np.eye(len(rs), dtype=bool)).stack().mean())})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codes", nargs="*")
    ap.add_argument("--no-charts", action="store_true")
    args = ap.parse_args()
    config.REPORTS_DIR.mkdir(exist_ok=True)

    results, rejected = [], []
    for cls in ALL + REJECTED:
        if args.codes and cls.CODE not in args.codes:
            continue
        r = run_backtest(cls)
        (rejected if cls in REJECTED else results).append(r)
        m = r.metrics
        print(f"{r.code:4s} {r.name[:44]:44s} CAGR {m['CAGR']:+6.1%} Sharpe {m['Sharpe']:5.2f} MaxDD {m['MaxDD']:6.1%}", flush=True)

    summary = pd.DataFrame([r.summary_row() for r in results])
    summary.to_csv(config.REPORTS_DIR / "backtest_summary.csv", index=False)
    yearly = {}
    for r in results:
        y = r.equity.resample("YE").last()
        yr = y.pct_change()
        yr.iloc[0] = y.iloc[0] - 1.0
        yearly[r.code] = yr
    yearly = pd.DataFrame(yearly)
    yearly.index = yearly.index.year
    yearly.to_csv(config.REPORTS_DIR / "yearly_returns.csv", float_format="%.4f")

    asof = max(r.equity.index[-1] for r in results).date().isoformat() if results else ""
    md = [f"# Backtest summary (data through {asof})", "",
          "Net of per-asset costs (2-15 bp one-way), 1% short borrow, idle cash earns 3M T-bill. "
          "Sharpe/Sortino are excess over T-bills. Orders fill at the next bar's open.", "",
          fmt_table(summary.drop(columns=["Strategy"]).rename(columns={"Code": "Code"})), ""]
    bl = blends(results) if not args.codes else pd.DataFrame()
    if len(bl):
        bl.to_csv(config.REPORTS_DIR / "class_blends.csv", index=False)
        md += ["## Equal-weight blend of the five sleeves per asset class", "",
               "In this table both blend and benchmark Sharpe are computed vs zero (not excess of T-bills), so they are comparable with each other but not with the per-strategy table above.", "",
               fmt_table(bl.assign(**{"Avg pairwise corr": bl["Avg pairwise corr"].round(2)})), ""]
    if rejected:
        md += ["## Rejected first specifications (research log)", "",
               fmt_table(pd.DataFrame([r.summary_row() for r in rejected]).drop(columns=["Strategy"])), ""]
    (config.REPORTS_DIR / "backtest_summary.md").write_text("\n".join(md))

    sig = [f"# Current strategy positioning (as of {asof})", "",
           "| Code | Strategy | Target weights (rest in T-bills) | Last rebalance |", "|---|---|---|---|"]
    for r in results:
        w = ", ".join(f"{k} {v:+.0%}" for k, v in r.last_target.items()) or "100% T-bills"
        sig.append(f"| {r.code} | {r.name} | {w} | {r.last_rebalance} |")
    (config.REPORTS_DIR / "current_signals.md").write_text("\n".join(sig) + "\n")
    print("wrote reports/backtest_summary.md, reports/current_signals.md")
    if not args.no_charts and results:
        charts(results)


if __name__ == "__main__":
    main()
