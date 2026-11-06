"""Event studies with controls, the shock study, the election-value ablation, global transmission,
engine reconciliation and the scenario-signpost history. Writes JSON for the site and Markdown.

Usage: .venv/bin/python scripts/run_research.py
Outputs: reports/results/{event_study,shock_study,ablation,global,reconciliation,scenarios}.json,
         reports/event_study.md, reports/research_controls.md, reports/evidence/reconciliation.json
"""
import json
import math

import _bootstrap  # noqa: F401
import numpy as np
import pandas as pd

from midterm_quant import config
from midterm_quant.research import ablation, event_study as es, global_transmission, reconcile, scenarios, shock_study


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(float(o)) else float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp, pd.Period)):
        return str(o)
    return o


def dump(name, obj):
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (config.RESULTS_DIR / f"{name}.json").write_text(json.dumps(_clean(obj), indent=1, default=str))


def md_table(df: pd.DataFrame, pct=(), num=(), index=False) -> str:
    d = df.reset_index() if index else df.copy()
    for c in d.columns:
        if c in pct:
            d[c] = d[c].map(lambda v: f"{v:+.1%}" if pd.notna(v) else "")
        elif c in num:
            d[c] = d[c].map(lambda v: f"{v:.2f}" if pd.notna(v) else "")
    cols = [str(c) for c in d.columns]
    rows = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    rows += ["| " + " | ".join(str(v) for v in r) + " |" for r in d.itertuples(index=False)]
    return "\n".join(rows)


def main():
    out = []
    # 1. midterm event study: original tables plus controls --------------------------------
    fr = es.midterm_forward_returns()
    fr.to_csv(config.REPORTS_DIR / "event_study_observations.csv", index=False)
    summ = es.summarize(fr)
    ally = es.election_day_returns()
    ally.to_csv(config.EVIDENCE_DIR / "election_day_all_years.csv", index=False)
    vs = es.midterm_vs_other_years(ally)
    cyc = es.by_cycle_year(ally)
    loo = es.leave_one_out(ally)
    reg, n_reg = es.controlled_regression(ally)
    season = es.seasonal_window_all_years()
    sp = fr[fr.asset == "S&P 500"]
    above = ally[(ally.midterm == 1)]
    dump("event_study", {
        "evidence": "descriptive", "summary": summ.reset_index().to_dict(orient="records"),
        "sp500_by_midterm": sp.to_dict(orient="records"),
        "midterm_vs_other_years": vs.to_dict(orient="records"), "by_cycle_year_12m": cyc.reset_index().to_dict(orient="records"),
        "leave_one_out_12m": {"min_mean": float(loo["mean without"].min()), "max_mean": float(loo["mean without"].max()),
                              "min_pct_pos": float(loo["%pos without"].min()), "rows": loo.to_dict(orient="records")},
        "regression_12m": {"n": n_reg, "table": reg.reset_index().rename(columns={"index": "term"}).to_dict(orient="records")},
        "seasonal_window_by_cycle": season.reset_index().to_dict(orient="records"),
        "notes": ["The 19 midterm 12-month windows do not overlap, but 19 observations cannot separate an election effect from the presidential-cycle seasonal or from the macro state.",
                  "Valuation controls (e.g. CAPE) are not included: no free machine-readable source was wired in. Recession dating (NBER) is excluded because it is decided after the fact."],
    })
    out += ["# Midterm event study with controls", "",
            f"Forward S&P 500 price returns from the close of election day (the Tuesday after the first Monday in November) for every year 1950-2025 (n = {len(ally)}). Descriptive only.", "",
            "## Midterm years vs all other years", "",
            md_table(vs.assign(**{"midterm 90% CI": vs["midterm 90% CI"].map(lambda t: f"{t[0]:+.1%} to {t[1]:+.1%}"),
                                  "other 90% CI": vs["other 90% CI"].map(lambda t: f"{t[0]:+.1%} to {t[1]:+.1%}")}),
                     pct=["midterm mean", "midterm %pos", "other mean", "other %pos", "difference"], num=["permutation p (two-sided)"]), "",
            "## By year of the presidential cycle (12 months after the November election date)", "",
            md_table(cyc, pct=["mean", "median", "%pos"], index=True), "",
            f"Leave-one-election-out: the midterm 12-month mean ranges from {loo['mean without'].min():+.1%} to {loo['mean without'].max():+.1%}; the share positive never falls below {loo['%pos without'].min():.0%}.", "",
            f"## Regression of the 12-month return on a midterm dummy and state controls (n = {n_reg}, HC1 standard errors)", "",
            md_table(reg.round(4), index=True), "",
            "## Seasonal window (30 Sep to 30 Jun) for every year, by cycle year", "", md_table(season, pct=["mean", "median", "%pos"], index=True), ""]

    # 2. shock study -------------------------------------------------------------------
    hist_end = (pd.Timestamp(config.BACKTEST_END) - pd.offsets.BDay(1)).date().isoformat()
    sh = shock_study.study(end=hist_end, current=config.BACKTEST_END)
    dump("shock_study", sh)
    g = pd.DataFrame(sh["groups"])
    ph = pd.DataFrame(sh["posthoc_filters"])
    sens = pd.DataFrame(sh["sensitivity"])
    out += ["# S&P 500 after one-day drops of 3.5% or more (1950 onward)", "",
            f"History to {hist_end}: {len(sh['events'])} events (first day of each cluster, 20-session gap) in {sh['episodes']} independent episodes; {sh['overlap_pairs_12m']} pairs of events have overlapping 12-month windows. Groups are fixed on the drop day's close. The current case ({config.BACKTEST_END}: {sh['current_case']['ret']:+.1%}, {'above' if sh['current_case']['above200'] else 'below'} its 200-day average, {sh['current_case']['dd_before']:.1%} from the 52-week high before the drop) is not in the history.", "",
            md_table(g[["group", "n", "episodes", "6m %pos", "6m negatives", "12m %pos", "12m negatives", "12m median", "worst further fall 3m"]],
                     pct=["6m %pos", "12m %pos", "12m median", "worst further fall 3m"]), "",
            "**Post-hoc filter (not pre-specified).** The filter measures the distance from the 52-week high at the close before the drop. It was added on 5 Nov after seeing the current case (1.7% below its high before the drop, 5.9% after it); the 6% threshold was not specified in advance. Neighbouring thresholds:", "",
            md_table(ph[["threshold", "n", "6m %pos", "12m negatives", "worst further fall 3m"]], pct=["threshold", "6m %pos", "worst further fall 3m"]), "",
            "**Sensitivity to the event definition**", "",
            md_table(sens, pct=["threshold", "above200 6m %pos", "above200 12m %pos", "all worst further fall 3m", "above200 worst further fall 3m"]), ""]

    # 3. ablation ------------------------------------------------------------------------
    ab = ablation.run()
    dump("ablation", ab)
    st = pd.DataFrame(ab["steps"]).drop(columns=["features"])
    out += ["# Does election information add predictive value? (nested walk-forward)", "",
            f"Target: next-month S&P 500 excess price return. Out-of-sample {st['oos_start'].iloc[0]} to {st['oos_end'].iloc[0]}; {ab['n_trials']} model configurations counted.", "",
            md_table(st.drop(columns=["oos_start", "oos_end"]), pct=["R2_OS vs hist mean", "timing CAGR", "timing MaxDD", "timing Time invested"],
                     num=["Clark-West t vs hist mean", "CW p", "timing Sharpe", "timing Switches/yr"]), "",
            md_table(pd.DataFrame(ab["increments"]), pct=["delta R2_OS"], num=["Clark-West t", "p"]), "",
            f"Buy-and-hold over the same months: Sharpe {ab['buy_hold']['Sharpe']:.2f}, CAGR {ab['buy_hold']['CAGR']:+.1%}.", "", ab["election_feature_note"], ""]

    # 4. global ---------------------------------------------------------------------------
    gl = global_transmission.run()
    dump("global", gl)
    re_ = pd.DataFrame(gl["reaction"])
    se = pd.DataFrame(gl["sensitivities"])
    out += ["# Global transmission", "", f"Election window: last close on or before {gl['window']['pre']} to last close on or before {gl['window']['post']}.", "",
            md_table(re_.drop(columns=["local last date"]), pct=["local", "fx vs USD", "USD (local x FX)", "US-listed ETF", "hedged ETF"]), "",
            gl["timing_note"], "",
            "Five-year monthly sensitivities (betas; t-statistics HC1):", "",
            md_table(se[["market", "basis", "beta dUS10y (pp)", "beta USD broad", "beta Brent", "beta S&P 500", "t USD broad", "t Brent", "R2"]],
                     num=["beta dUS10y (pp)", "beta USD broad", "beta Brent", "beta S&P 500", "t USD broad", "t Brent", "R2"]), "",
            md_table(pd.DataFrame(gl["hedged_vs_unhedged"]), pct=["unhedged ann.", "hedged ann.", "currency effect ann."]), "",
            "Not measured: " + "; ".join(gl["not_measured"]), ""]

    # 5. reconciliation -------------------------------------------------------------------
    rc = reconcile.run()
    dump("reconciliation", rc)
    (config.EVIDENCE_DIR / "reconciliation.json").write_text(json.dumps(_clean(rc), indent=1))
    out += ["# Engine reconciliation (Backtrader vs independent pandas re-implementation)", "",
            md_table(pd.DataFrame(rc)[["strategy", "decisions compared", "target mismatches", "fills backtrader", "fills reference", "max fill price diff", "commission backtrader", "commission reference", "max daily NAV rel diff"]]), ""]

    # 6. scenario signposts: 16 weekly readings, point-in-time ----------------------------
    weeks = scenarios.week_ends(pd.Timestamp(config.BACKTEST_END), 16)
    counts = scenarios.weekly_counts(weeks)
    stt = scenarios.states(counts)
    dump("scenarios", {"rule": {"confirm": f">= {scenarios.CONFIRM_MIN} signposts in each of {scenarios.CONFIRM_WEEKS} consecutive weekly readings",
                                "revoke": f"<= {scenarios.REVOKE_MAX} signposts in {scenarios.REVOKE_WEEKS} consecutive weekly readings",
                                "missing": "missing or stale input = signpost not holding (listed as a gap)",
                                "independence": "scenarios evaluated separately; several or none may be confirmed",
                                "probabilities": "40/35/25 are subjective priors, not calibrated and not updated by the rule"},
                       "scenarios": {k: {"name": v[0], "prior": v[1], "signposts": [{"codes": list(s.codes), "label": s.label} for s in v[2]]} for k, v in scenarios.SCENARIOS.items()},
                       "history": stt.to_dict(orient="records")})
    last = stt.sort_values("week_end").groupby("scenario").tail(1)
    out += ["# Scenario signposts (weekly, point-in-time)", "",
            md_table(last[["scenario", "week_end", "holding", "of", "which", "gaps", "state"]]), ""]
    (config.REPORTS_DIR / "research_controls.md").write_text("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
