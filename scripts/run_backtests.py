"""Run every registered trial, evaluate the 20-strategy book on the standard basis, write evidence.

Usage:  .venv/bin/python scripts/run_backtests.py [--no-charts]

Outputs
  reports/evidence/trial_registry.csv        all 46 configurations: recorded vs rerun results
  reports/evidence/performance_risk.csv      standardised metrics + 4 benchmarks for the book
  reports/evidence/class_blends.csv          equal-weight class blends (excess-return Sharpe)
  reports/evidence/blend_attribution.csv     risk contribution and leave-one-out per sleeve
  reports/evidence/vintage_sensitivity.csv   first-print vs latest-vintage inputs
  reports/evidence/ledgers/<CODE>/           nav, positions, targets, orders (CSV, gzip)
  reports/results/backtests.json             machine-readable bundle for the site
  reports/backtest_summary.md, reports/current_signals.md, reports/yearly_returns.csv,
  reports/equity_<class>.png
"""
import argparse
import json
import math

import _bootstrap  # noqa: F401
import numpy as np
import pandas as pd

from midterm_quant import config
from midterm_quant.data.sources import fetch_yahoo
from midterm_quant.engine import evaluation as ev
from midterm_quant.engine.runner import run_backtest
from midterm_quant.strategies import ALL, BY_CODE
from midterm_quant.strategies.trials import N_TRIALS, TRIALS

EVIDENCE_LABEL = {
    "D1": "Pre-specified rule; development-sample backtest",
    "D2": "Revised after seeing results; development-sample backtest",
    "D3": "In-sample research (parameters fitted to known outcomes)",
}
# Market-neutral spread books are compared with cash first; directional books with the
# risk-matched reference asset.
PRIMARY = {"N3": "cash", "N5": "cash"}
VINTAGE_SENSITIVE = ["C2", "P1", "P4"]


def next_decision(rebalance: str, calendar: str, last: pd.Timestamp) -> str:
    step = pd.Timedelta(days=1) if calendar == "crypto" else pd.offsets.BDay(1)
    d = last + step
    if rebalance == "W":
        while d.isocalendar()[1] == last.isocalendar()[1]:
            d += step
    elif rebalance == "M":
        while d.month == last.month:
            d += step
    return d.date().isoformat()


def write_ledger(code: str, r) -> None:
    d = config.EVIDENCE_DIR / "ledgers" / code
    d.mkdir(parents=True, exist_ok=True)
    L = r.ledger
    nav = L["nav"].copy()
    nav.insert(0, "nav_index", nav["value"] / nav["value"].iloc[0])
    nav.to_csv(d / "nav.csv.gz", float_format="%.6f", compression="gzip")
    L["positions"].to_csv(d / "positions.csv.gz", float_format="%.5f", compression="gzip")
    L["targets"].to_csv(d / "targets.csv", index=False, float_format="%.4f")
    L["orders"].to_csv(d / "orders.csv.gz", index=False, float_format="%.6f", compression="gzip")


def reconcile_cash(r) -> dict:
    """Cash identity: final cash = initial + interest + sells - buys - commission - borrow."""
    L = r.ledger
    o = L["orders"]
    filled = o[o["status"] == "Completed"] if len(o) else o
    buys = filled.loc[filled["side"] == "BUY", "notional"].sum() if len(filled) else 0.0
    sells = -filled.loc[filled["side"] == "SELL", "notional"].sum() if len(filled) else 0.0
    nav = L["nav"]
    last = nav.iloc[-1]
    # interest booked on the final bar is credited by the broker one bar later
    pending_interest = last["interest_cum"] - nav["interest_cum"].iloc[-2] if len(nav) > 1 else 0.0
    implied = L["cash0"] + last["interest_cum"] - pending_interest + sells - buys - last["commission_cum"] - last["borrow_cum"]
    return {"cash_reported": float(last["cash"]), "cash_implied": float(implied),
            "cash_gap_pct_nav": float((last["cash"] - implied) / last["value"])}


def blends(book: dict, rf_m: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, attrib = [], []
    by_class = {}
    for code, r in book.items():
        by_class.setdefault(r.asset_class, []).append((code, r))
    for cls_name, items in by_class.items():
        for variant, members in (("all five", items), ("excluding C3", [(c, r) for c, r in items if c != "C3"])):
            if variant == "excluding C3" and len(members) == len(items):
                continue
            rets = pd.concat({c: ev.monthly_returns(r.equity) for c, r in members}, axis=1).dropna()
            blend = rets.mean(axis=1)
            rf = rf_m.reindex(blend.index).fillna(0.0)
            ex = blend - rf
            nav = (1 + blend).cumprod()
            ref = members[0][1].benchmark
            ref_m = ev.monthly_returns(fetch_yahoo(ref)["close"]).reindex(blend.index)
            scale = blend.std(ddof=1) / ref_m.std(ddof=1)
            rm = scale * ref_m + (1 - scale) * rf
            rmex = rm - rf
            years = len(blend) / 12
            rows.append({
                "Class": cls_name, "Sleeves": "+".join(c for c, _ in members), "Variant": variant,
                "Start": str(blend.index[0]), "End": str(blend.index[-1]),
                "CAGR": float(nav.iloc[-1] ** (1 / years) - 1), "Vol": float(blend.std(ddof=1) * math.sqrt(12)),
                "Sharpe": float(ex.mean() / ex.std(ddof=1) * math.sqrt(12)),
                "MaxDD": float((nav / nav.cummax() - 1).min()),
                "Ref": ref, "Ref Sharpe": float((ref_m - rf).mean() / (ref_m - rf).std(ddof=1) * math.sqrt(12)),
                "RiskMatched Sharpe": float(rmex.mean() / rmex.std(ddof=1) * math.sqrt(12)),
                "Avg pairwise corr": float(rets.corr().where(~np.eye(len(members), dtype=bool)).stack().mean()),
            })
            if variant == "all five":
                rc = ev.risk_contributions(rets)
                loo = ev.leave_one_out(rets, rf_m).set_index("Sleeve")
                for c in rets.columns:
                    attrib.append({"Class": cls_name, "Sleeve": c, "Risk contribution": float(rc[c]),
                                   "Blend Sharpe without it": float(loo.loc[c, "Blend Sharpe"]),
                                   "Delta if removed": float(loo.loc[c, "Delta if removed"]),
                                   "Blend Sharpe (all)": float(loo.loc["(all)", "Blend Sharpe"])})
    return pd.DataFrame(rows), pd.DataFrame(attrib)


def charts(book):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    surface, ink, ink2, grid = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    strat_c, bench_c = "#2a78d6", "#eb6834"
    by_class = {}
    for r in book.values():
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
            ax.legend(loc="lower right", fontsize=7, frameon=False, labelcolor=ink2)
        fig.suptitle(f"{cls}: growth of $1 (log scale), net of costs, development sample", fontsize=11, color=ink, x=0.01, ha="left")
        fig.tight_layout()
        fig.savefig(config.REPORTS_DIR / f"equity_{cls.lower().replace(' ', '_')}.png", dpi=130, facecolor=surface)
        plt.close(fig)


def pct(v, d=1):
    return "" if v is None or (isinstance(v, float) and not math.isfinite(v)) else f"{v:+.{d}%}"


def num(v, d=2):
    return "" if v is None or (isinstance(v, float) and not math.isfinite(v)) else f"{v:.{d}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-charts", action="store_true")
    args = ap.parse_args()
    config.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. every trial, point-in-time inputs ------------------------------------------------
    runs = {}
    for t in TRIALS:
        r = run_backtest(t.cls, **t.params)
        runs[t.trial_id] = r
        print(f"{t.trial_id:7s} {r.name[:44]:44s} CAGR {r.metrics['CAGR']:+6.1%}  daily-Sharpe {r.metrics['Sharpe']:5.2f}", flush=True)
    rf_pct = next(iter(runs.values())).rf
    rf_m = ev.rf_monthly(rf_pct)
    sr_m = {}
    for tid, r in runs.items():
        m = ev.monthly_returns(r.equity)
        ex = m - rf_m.reindex(m.index).fillna(0.0)
        sr_m[tid] = float(ex.mean() / ex.std(ddof=1)) if ex.std(ddof=1) > 0 else 0.0
    var_sr = float(np.var(list(sr_m.values()), ddof=1))
    spy = fetch_yahoo("SPY")["close"]

    # 2. standard evaluation for book + rejected/superseded --------------------------------
    perf = []
    for t in TRIALS:
        r = runs[t.trial_id]
        cls = t.cls
        e = ev.evaluate(r.equity, rf_pct, fetch_yahoo(cls.BENCHMARK)["close"], cls.BENCHMARK, spy,
                        r.exposure["gross"], r.exposure["net"], r.turnover_per_year, N_TRIALS, var_sr,
                        config.cost_bps(cls.BENCHMARK))
        e.update({"Trial": t.trial_id, "Family": t.family, "Status": t.status, "Name": r.name,
                  "Class": r.asset_class, "Evidence": getattr(cls, "EVIDENCE", "D1"), "Version": getattr(cls, "VERSION", "v1"),
                  "Primary": PRIMARY.get(t.trial_id, "risk_matched"), "Params": json.dumps(t.params, sort_keys=True),
                  "Recorded CAGR": t.recorded.get("CAGR"), "Recorded Sharpe (daily basis)": t.recorded.get("Sharpe"),
                  "Recorded MaxDD": t.recorded.get("MaxDD"), "Recorded on": t.when, "Note": t.note})
        e.update(reconcile_cash(r))
        perf.append(e)
    perf = pd.DataFrame(perf).set_index("Trial")
    perf.to_csv(config.EVIDENCE_DIR / "trial_registry.csv", float_format="%.6g")
    book_codes = [c.CODE for c in ALL]
    book = {c: runs[c] for c in book_codes}
    bp = perf.loc[book_codes].copy()
    bp.to_csv(config.EVIDENCE_DIR / "performance_risk.csv", float_format="%.6g")
    for tid in book_codes + ["C5a", "P3a", "C2v1"]:
        write_ledger(tid, runs[tid])

    # 3. blends -------------------------------------------------------------------------
    bl, attrib = blends(book, rf_m)
    bl.to_csv(config.EVIDENCE_DIR / "class_blends.csv", index=False, float_format="%.6g")
    attrib.to_csv(config.EVIDENCE_DIR / "blend_attribution.csv", index=False, float_format="%.6g")

    # 4. vintage sensitivity -------------------------------------------------------------
    vs = []
    for code in VINTAGE_SENSITIVE:
        latest = run_backtest(BY_CODE[code], vintages=False)
        a, b = ev.monthly_returns(book[code].equity), ev.monthly_returns(latest.equity)
        def shp(x):
            e_ = x - rf_m.reindex(x.index).fillna(0.0)
            return float(e_.mean() / e_.std(ddof=1) * math.sqrt(12))
        same = sum(1 for (d1, t1), (d2, t2) in zip(book[code].rebalances, latest.rebalances) if d1 == d2 and t1 == t2)
        vs.append({"Code": code, "Sharpe first-print": shp(a), "Sharpe latest-vintage": shp(b),
                   "CAGR first-print": float((1 + a).prod() ** (12 / len(a)) - 1),
                   "CAGR latest-vintage": float((1 + b).prod() ** (12 / len(b)) - 1),
                   "Rebalances": len(book[code].rebalances), "Identical targets": same,
                   "Signal now first-print": json.dumps((book[code].signal_now or {}).get("target")),
                   "Signal now latest-vintage": json.dumps((latest.signal_now or {}).get("target"))})
    vs = pd.DataFrame(vs)
    vs.to_csv(config.EVIDENCE_DIR / "vintage_sensitivity.csv", index=False, float_format="%.6g")

    # 5. yearly returns ------------------------------------------------------------------
    yearly = {}
    for c, r in book.items():
        y = r.equity.resample("YE").last()
        yr = y.pct_change()
        yr.iloc[0] = y.iloc[0] - 1.0
        yearly[c] = yr
    yearly = pd.DataFrame(yearly)
    yearly.index = yearly.index.year
    yearly.to_csv(config.REPORTS_DIR / "yearly_returns.csv", float_format="%.4f")

    # 6. positions and signals -------------------------------------------------------------
    sig_rows = []
    for c, r in book.items():
        cls = BY_CODE[c]
        last_day = r.equity.index[-1]
        held = r.ledger["positions"].iloc[-1]
        held = {k: round(float(v), 4) for k, v in held.items() if abs(v) > 1e-4}
        sn = r.signal_now or {}
        stale = []
        from midterm_quant.data import catalog
        from midterm_quant.research.monitor import expected_bar_missing
        for name, last in r.input_last.items():
            if last is None:
                continue
            age = (pd.Timestamp(config.BACKTEST_END) - pd.Timestamp(last)).days
            if age > catalog.max_age_days(name):
                stale.append(f"{name} stale (last {last})")
            elif expected_bar_missing(name, pd.Timestamp(last), last_day):
                stale.append(f"{name} missing {last_day.date()} bar (last {last}, carried forward)")
        nxt = next_decision(cls.REBALANCE, cls.CALENDAR, last_day)
        step = pd.Timedelta(days=1) if cls.CALENDAR == "crypto" else pd.offsets.BDay(1)
        if sn.get("target") is None:
            status = "hold current position (stateful rule, no new entry)"
        elif sn.get("computed_on_rebalance"):
            status = f"order for the next open ({(last_day + step).date().isoformat()})"
        else:
            status = f"indicative only: re-decided at the {nxt} close"
        sig_rows.append({"Code": c, "Name": r.name, "Class": r.asset_class, "Evidence": cls.EVIDENCE, "Signal status": status,
                         "Data through": last_day.date().isoformat(),
                         "Backtest position at close": held,
                         "Model signal at close": sn.get("target"),
                         "Signal is hold-current": sn.get("target") is None,
                         "Rebalance": cls.REBALANCE, "Next decision": next_decision(cls.REBALANCE, cls.CALENDAR, last_day),
                         "Stale inputs": stale, "Input last dates": r.input_last})
    with open(config.RESULTS_DIR / "backtests.json", "w") as f:
        json.dump({
            "backtest_end": config.BACKTEST_END, "n_trials": N_TRIALS, "var_sr_monthly": var_sr,
            "evidence_labels": EVIDENCE_LABEL,
            "book": json.loads(bp.reset_index().to_json(orient="records")),
            "trials": json.loads(perf.reset_index().to_json(orient="records")),
            "blends": json.loads(bl.to_json(orient="records")),
            "attribution": json.loads(attrib.to_json(orient="records")),
            "vintage_sensitivity": json.loads(vs.to_json(orient="records")),
            "signals": sig_rows,
            "monthly_nav": {c: {str(k): round(float(v), 5) for k, v in ev.month_end(r.equity).items()} for c, r in book.items()},
            "monthly_bench": {c: {str(k): round(float(v), 5) for k, v in ev.month_end(r.bench).items()} for c, r in book.items()},
        }, f, default=str)

    # 7. human-readable summary ----------------------------------------------------------
    cols = ["Name", "Evidence", "Start", "CAGR", "Vol", "Sharpe", "DSR", "MaxDD", "MaxDD_days_to_recover", "Beta_SPY",
            "AvgGross", "Turnover/yr", "Ref", "buy_hold_Sharpe", "trend_Sharpe", "risk_matched_Sharpe", "IR_vs_risk_matched"]
    md = [f"# Backtest summary: development sample through {config.BACKTEST_END}", "",
          "**Evidence status.** Every figure below comes from data that was available while the rules were written "
          f"(4 Nov 2026). None of it is out-of-sample. {N_TRIALS} configurations were tried in total "
          "(`reports/evidence/trial_registry.csv`); the deflated Sharpe ratio (DSR) is the probability that the true "
          f"Sharpe exceeds the best of {N_TRIALS} unskilled trials. C3 is in-sample research and is not counted as a result.", "",
          "**Conventions.** Month-end returns, sqrt(12) annualisation for every class, excess over the 3-month T-bill "
          "(FRED DTB3); strategy NAVs net of 2-15bp one-way costs, 1% short borrow, T-bill interest on idle cash; "
          "orders fill at the next bar's open; revision-prone FRED inputs use first-print (ALFRED) values. "
          "Benchmarks: buy-and-hold of the reference asset, a 10-month trend rule on it (with costs), and the reference "
          "scaled to the strategy's volatility (ex post).", "",
          "| Code | " + " | ".join(cols) + " |", "|" + "---|" * (len(cols) + 1)]
    for c, row in bp.iterrows():
        vals = []
        for k in cols:
            v = row[k]
            if k in ("CAGR", "Vol", "MaxDD"):
                vals.append(pct(v))
            elif k in ("Sharpe", "DSR", "Beta_SPY", "AvgGross", "Turnover/yr", "buy_hold_Sharpe", "trend_Sharpe", "risk_matched_Sharpe", "IR_vs_risk_matched"):
                vals.append(num(v))
            elif k == "MaxDD_days_to_recover":
                vals.append("not yet" if v is None or (isinstance(v, float) and not math.isfinite(v)) else str(int(v)))
            else:
                vals.append(str(v))
        md.append(f"| {c} | " + " | ".join(vals) + " |")
    md += ["", "## Class blends (equal weight, monthly rebalanced, excess-return Sharpe)", "",
           "| Class | Variant | Start | CAGR | Vol | Sharpe | MaxDD | Ref | Ref Sharpe | Risk-matched Sharpe | Avg corr |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, b in bl.iterrows():
        md.append(f"| {b['Class']} | {b['Variant']} | {b['Start']} | {pct(b['CAGR'])} | {pct(b['Vol'])} | {num(b['Sharpe'])} | {pct(b['MaxDD'])} | {b['Ref']} | {num(b['Ref Sharpe'])} | {num(b['RiskMatched Sharpe'])} | {num(b['Avg pairwise corr'])} |")
    md += ["", "## Does each sleeve earn its place? (risk contribution and leave-one-out)", "",
           "| Class | Sleeve | Risk contribution | Blend Sharpe without it | Change if removed |", "|---|---|---|---|---|"]
    for _, a in attrib.iterrows():
        md.append(f"| {a['Class']} | {a['Sleeve']} | {a['Risk contribution']:.0%} | {a['Blend Sharpe without it']:.2f} | {a['Delta if removed']:+.2f} |")
    md += ["", "## First-print vs latest-vintage inputs", "",
           "| Code | Sharpe first-print | Sharpe latest-vintage | Identical rebalance targets |", "|---|---|---|---|"]
    for _, v in vs.iterrows():
        md.append(f"| {v['Code']} | {v['Sharpe first-print']:.2f} | {v['Sharpe latest-vintage']:.2f} | {v['Identical targets']} of {v['Rebalances']} |")
    md += ["", "## Trial registry (all configurations tried)", "",
           "| Trial | Family | Status | Recorded on | Params | Recorded CAGR / Sharpe (daily basis) | Rerun CAGR / Sharpe (monthly) | DSR |", "|---|---|---|---|---|---|---|---|"]
    for tid, row in perf.iterrows():
        rec = f"{pct(row['Recorded CAGR'])} / {num(row['Recorded Sharpe (daily basis)'])}" if pd.notna(row["Recorded CAGR"]) else "n/a (new)"
        md.append(f"| {tid} | {row['Family']} | {row['Status']} | {row['Recorded on']} | `{row['Params']}` | {rec} | {pct(row['CAGR'])} / {num(row['Sharpe'])} | {num(row['DSR'])} |")
    (config.REPORTS_DIR / "backtest_summary.md").write_text("\n".join(md) + "\n")

    sig = [f"# Model signals at the {config.BACKTEST_END} close", "",
           "**No executed holdings.** Nothing here has been traded, on paper or live. 'Backtest position' is the "
           "hypothetical book at the close; 'Model signal' is what the rule asks for on that bar; it is traded only at "
           "the next scheduled decision.", "",
           "| Code | Evidence | Backtest position | Model signal | Signal status | Next decision | Data gaps / stale inputs |", "|---|---|---|---|---|---|---|"]
    for s in sig_rows:
        pos = ", ".join(f"{k} {v:+.0%}" for k, v in s["Backtest position at close"].items()) or "cash"
        tgt = "hold current" if s["Signal is hold-current"] else (", ".join(f"{k} {v:+.0%}" for k, v in s["Model signal at close"].items() if abs(v) > 1e-4) or "cash")
        sig.append(f"| {s['Code']} | {s['Evidence']} | {pos} | {tgt} | {s['Signal status']} | {s['Next decision']} | {', '.join(s['Stale inputs']) or 'none'} |")
    (config.REPORTS_DIR / "current_signals.md").write_text("\n".join(sig) + "\n")
    print("wrote reports/backtest_summary.md, reports/current_signals.md, reports/evidence/*")
    if not args.no_charts:
        charts(book)


if __name__ == "__main__":
    main()
