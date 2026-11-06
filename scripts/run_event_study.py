"""Midterm event study -> reports/event_study.md (+ CSV of every observation)."""
import _bootstrap  # noqa: F401
import pandas as pd

from midterm_quant import config
from midterm_quant.research import event_study as es


def md_table(df: pd.DataFrame, pct_cols=(), bp_cols=(), index=True) -> str:
    d = df.reset_index() if index else df.copy()
    for c in d.columns:
        if c in pct_cols:
            d[c] = d[c].map(lambda v: f"{v:+.1%}" if pd.notna(v) else "")
        elif c in bp_cols:
            d[c] = d[c].map(lambda v: f"{v:+.0f}bp" if pd.notna(v) else "")
    cols = [str(c) for c in d.columns]
    rows = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    rows += ["| " + " | ".join(str(v) for v in r) + " |" for r in d.itertuples(index=False)]
    return "\n".join(rows)


def main():
    config.REPORTS_DIR.mkdir(exist_ok=True)
    fr = es.midterm_forward_returns()
    fr.to_csv(config.REPORTS_DIR / "event_study_observations.csv", index=False)
    summ = es.summarize(fr)
    pct = [c for c in summ.columns if "mean" in c or "median" in c or "%pos" in c]
    tnx = summ.loc[["US 10Y yield (bp)"]] if "US 10Y yield (bp)" in summ.index else None
    px = summ.drop(index=["US 10Y yield (bp)"], errors="ignore")
    out = ["# Midterm election event study", "",
           "Forward returns from the close on US midterm election day (21/63/126/252 trading days).", "",
           "## Summary by asset", "", md_table(px, pct_cols=pct), ""]
    if tnx is not None:
        bp = [c for c in tnx.columns if "mean" in c or "median" in c]
        out += ["10-year yield change (bp):", "", md_table(tnx, pct_cols=[c for c in tnx.columns if "%pos" in c], bp_cols=bp), ""]
    sp = fr[fr.asset == "S&P 500"][["year", "outcome", *es.HORIZONS]]
    out += ["## S&P 500 after every midterm", "", md_table(sp, pct_cols=list(es.HORIZONS), index=False), ""]
    for asset in ["Gold", "WTI crude", "Bitcoin"]:
        sub = fr[fr.asset == asset][["year", "outcome", *es.HORIZONS]]
        if len(sub):
            out += [f"## {asset} after midterms", "", md_table(sub, pct_cols=list(es.HORIZONS), index=False), ""]
    pc = es.presidential_cycle()
    out += ["## Presidential cycle (S&P 500 calendar-year price return, 1950-2025)", "",
            md_table(pc, pct_cols=["mean", "median", "%pos"]), ""]
    ss = es.sweet_spot_returns()
    out += ["## Seasonal sweet spot: 30 Sep (midterm year) -> 30 Jun (pre-election year)", "",
            md_table(ss, pct_cols=["Q4 midterm -> Q2 pre-election"], index=False),
            "", f"Mean {ss.iloc[:, 2].mean():+.1%}, median {ss.iloc[:, 2].median():+.1%}, positive {(ss.iloc[:, 2] > 0).mean():.0%} of {len(ss)}.", ""]
    (config.REPORTS_DIR / "event_study.md").write_text("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
