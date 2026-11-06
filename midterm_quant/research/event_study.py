"""Historical midterm-election event study across asset classes.

Measures forward returns from the close of US midterm election day (T0) for the S&P 500
(1950-2022), gold and WTI futures (2002-2022), bitcoin (2014-2022), the dollar index and
the 10-year yield, plus the presidential-cycle seasonality of the S&P 500.
"""
from __future__ import annotations

import pandas as pd

from midterm_quant import config
from midterm_quant.data.sources import fetch_yahoo

HORIZONS = {"+1m": 21, "+3m": 63, "+6m": 126, "+12m": 252}
ASSETS = {
    "S&P 500": "^GSPC",
    "Gold": "GC=F",
    "WTI crude": "CL=F",
    "Bitcoin": "BTC-USD",
    "Dollar index": "DX-Y.NYB",
    "US 10Y yield (bp)": "^TNX",
}

# President's party outcome in each midterm (control after the election).
OUTCOMES = {
    1950: "Unified (D held both)", 1954: "Lost both chambers", 1958: "Opposition held both",
    1962: "Unified (D held both)", 1966: "Unified (D held both)", 1970: "Opposition held both",
    1974: "Opposition held both", 1978: "Unified (D held both)", 1982: "Split Congress",
    1986: "Lost Senate -> opposition both", 1990: "Opposition held both", 1994: "Lost both chambers",
    1998: "Opposition held both", 2002: "Unified (R gained Senate)", 2006: "Lost both chambers",
    2010: "Lost House", 2014: "Lost Senate -> opposition both", 2018: "Lost House",
    2022: "Lost House", 2026: "Lost both chambers",
}
CLOSEST_ANALOGS = (1954, 1994, 2006)  # president's party lost both chambers in one election


def _forward_returns(px: pd.Series, t0: pd.Timestamp, as_change: bool = False) -> dict:
    px = px.dropna()
    after = px.index[px.index >= t0]
    if len(after) == 0:
        return {}
    i0 = px.index.get_loc(after[0])
    base = px.iloc[i0]
    out = {}
    for label, n in HORIZONS.items():
        if i0 + n < len(px):
            v = px.iloc[i0 + n]
            out[label] = (v - base) * 100.0 if as_change else v / base - 1.0
    return out


def midterm_forward_returns() -> pd.DataFrame:
    rows = []
    for year, day in zip(config.MIDTERM_YEARS, config.MIDTERM_DATES):
        if year == 2026:
            continue
        for asset, sym in ASSETS.items():
            px = fetch_yahoo(sym)["close"]
            if px.index[0] > pd.Timestamp(day) - pd.Timedelta(days=5):
                continue
            fr = _forward_returns(px, pd.Timestamp(day), as_change=sym == "^TNX")
            if fr:
                rows.append({"year": year, "asset": asset, "outcome": OUTCOMES[year], **fr})
    return pd.DataFrame(rows)


def summarize(fr: pd.DataFrame) -> pd.DataFrame:
    g = fr.groupby("asset")
    out = []
    for asset, df in g:
        row = {"asset": asset, "n": len(df), "years": f"{df.year.min()}-{df.year.max()}"}
        for h in HORIZONS:
            s = df[h].dropna()
            row[f"{h} mean"] = s.mean()
            row[f"{h} median"] = s.median()
            row[f"{h} %pos"] = (s > 0).mean()
        out.append(row)
    return pd.DataFrame(out).set_index("asset").loc[[a for a in ASSETS if a in set(fr.asset)]]


def presidential_cycle(start_year: int = 1950, end_year: int = 2025) -> pd.DataFrame:
    """Average S&P 500 calendar-year price return by year of the presidential term."""
    px = fetch_yahoo("^GSPC")["close"]
    yearly = px.resample("YE").last().pct_change().dropna()
    yearly = yearly[(yearly.index.year >= start_year) & (yearly.index.year <= end_year)]
    names = {1: "Post-election (Y1)", 2: "Midterm (Y2)", 3: "Pre-election (Y3)", 0: "Election (Y4)"}
    df = pd.DataFrame({"ret": yearly.values, "year": yearly.index.year})
    df["phase"] = df.year.map(lambda y: names[y % 4])
    g = df.groupby("phase")["ret"]
    out = pd.DataFrame({"mean": g.mean(), "median": g.median(), "%pos": g.apply(lambda s: (s > 0).mean()), "n": g.size()})
    return out.loc[[names[1], names[2], names[3], names[0]]]


def sweet_spot_returns() -> pd.DataFrame:
    """S&P 500 return from 30 Sep of each midterm year to 30 Jun of the following year."""
    px = fetch_yahoo("^GSPC")["close"]
    rows = []
    for y in config.MIDTERM_YEARS:
        if y == 2026:
            continue
        a = px[:f"{y}-09-30"]
        b = px[:f"{y + 1}-06-30"]
        if len(a) and len(b):
            rows.append({"year": y, "outcome": OUTCOMES[y], "Q4 midterm -> Q2 pre-election": b.iloc[-1] / a.iloc[-1] - 1})
    return pd.DataFrame(rows)


def analog_table(fr: pd.DataFrame) -> pd.DataFrame:
    sp = fr[fr.asset == "S&P 500"].set_index("year")
    return sp.loc[[y for y in CLOSEST_ANALOGS if y in sp.index], ["outcome", *HORIZONS]]


# =====================================================================================
# Controls added in the 6 Nov 2026 review iteration. Everything here is DESCRIPTIVE:
# 19 midterms (non-overlapping 12-month windows) cannot identify a causal election effect.
# =====================================================================================
import math  # noqa: E402

import numpy as np  # noqa: E402

CYCLE = {2: "Midterm", 3: "Pre-election", 0: "Election", 1: "Post-election"}
SEED = 20261106


def election_day_returns(start: int = 1950, end: int = 2025) -> pd.DataFrame:
    """S&P 500 forward returns from the close of the first Tuesday after the first Monday in
    November, for *every* year, with the year's place in the presidential cycle and T0 state."""
    from midterm_quant.data.sources import fetch_fred

    px = fetch_yahoo("^GSPC")["close"].dropna()
    sma = px.rolling(200).mean()
    gs10, tb3 = fetch_fred("GS10"), fetch_fred("TB3MS")
    baa, aaa = fetch_fred("BAA"), fetch_fred("AAA")
    rows = []
    for y in range(start, end + 1):
        t0 = pd.Timestamp(config.midterm_election_day(y))
        after = px.index[px.index >= t0]
        if not len(after):
            continue
        i0 = px.index.get_loc(after[0])
        fr = _forward_returns(px, t0)
        prev_month = (t0 - pd.offsets.MonthBegin(1)) - pd.offsets.MonthBegin(1)  # month published by T0
        def at(s):
            s = s[s.index <= prev_month]
            return float(s.iloc[-1]) if len(s) else float("nan")
        rows.append({
            "year": y, "cycle": CYCLE[y % 4], "midterm": int(y % 4 == 2), **fr,
            "above200": int(px.iloc[i0] > sma.iloc[i0]) if i0 >= 200 else np.nan,
            "trail12": float(px.iloc[i0] / px.iloc[i0 - 252] - 1) if i0 >= 252 else np.nan,
            "term_spread": at(gs10) - at(tb3), "credit_spread": at(baa) - at(aaa),
        })
    return pd.DataFrame(rows)


def _boot_mean_ci(x: np.ndarray, rng, n: int = 10000, level: float = 0.90) -> tuple[float, float]:
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return float("nan"), float("nan")
    means = rng.choice(x, size=(n, len(x)), replace=True).mean(axis=1)
    a = (1 - level) / 2
    return float(np.quantile(means, a)), float(np.quantile(means, 1 - a))


def midterm_vs_other_years(df: pd.DataFrame) -> pd.DataFrame:
    """Mean forward return after election day: midterm years vs all other years, with a
    bootstrap CI for each mean and a permutation p-value for the difference."""
    rng = np.random.default_rng(SEED)
    out = []
    for h in HORIZONS:
        d = df[["midterm", h]].dropna()
        m, o = d.loc[d.midterm == 1, h].to_numpy(), d.loc[d.midterm == 0, h].to_numpy()
        diff = m.mean() - o.mean()
        lab = d.midterm.to_numpy()
        vals = d[h].to_numpy()
        perm = np.empty(5000)
        for k in range(5000):
            p = rng.permutation(lab)
            perm[k] = vals[p == 1].mean() - vals[p == 0].mean()
        out.append({"horizon": h, "midterm n": len(m), "midterm mean": m.mean(), "midterm 90% CI": _boot_mean_ci(m, rng),
                    "midterm %pos": float((m > 0).mean()), "other n": len(o), "other mean": o.mean(),
                    "other 90% CI": _boot_mean_ci(o, rng), "other %pos": float((o > 0).mean()),
                    "difference": diff, "permutation p (two-sided)": float((np.abs(perm) >= abs(diff)).mean())})
    return pd.DataFrame(out)


def by_cycle_year(df: pd.DataFrame, h: str = "+12m") -> pd.DataFrame:
    g = df.dropna(subset=[h]).groupby("cycle")[h]
    return pd.DataFrame({"n": g.size(), "mean": g.mean(), "median": g.median(), "%pos": g.apply(lambda s: (s > 0).mean())}).loc[
        ["Post-election", "Midterm", "Pre-election", "Election"]]


def leave_one_out(df: pd.DataFrame, h: str = "+12m") -> pd.DataFrame:
    m = df[(df.midterm == 1)].dropna(subset=[h]).set_index("year")[h]
    rows = [{"dropped": y, "mean without": float(m.drop(y).mean()), "%pos without": float((m.drop(y) > 0).mean())} for y in m.index]
    return pd.DataFrame(rows)


def ols_hc1(y: np.ndarray, X: np.ndarray, names: list[str]) -> pd.DataFrame:
    X = np.column_stack([np.ones(len(y)), X])
    names = ["const"] + names
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    xtx_inv = np.linalg.inv(X.T @ X)
    meat = X.T @ (X * (resid ** 2)[:, None])
    cov = xtx_inv @ meat @ xtx_inv * n / (n - k)
    se = np.sqrt(np.diag(cov))
    return pd.DataFrame({"coef": beta, "se (HC1)": se, "t": beta / se}, index=names)


def controlled_regression(df: pd.DataFrame, h: str = "+12m") -> tuple[pd.DataFrame, int]:
    cols = ["midterm", "above200", "trail12", "term_spread", "credit_spread"]
    d = df.dropna(subset=[h] + cols)
    return ols_hc1(d[h].to_numpy(), d[cols].to_numpy(dtype=float), cols), len(d)


def seasonal_window_all_years(start: int = 1950, end: int = 2025) -> pd.DataFrame:
    """30 Sep -> 30 Jun of the next year for every year, labelled by cycle year of the start."""
    px = fetch_yahoo("^GSPC")["close"]
    rows = []
    for y in range(start, end + 1):
        a, b = px[:f"{y}-09-30"], px[:f"{y + 1}-06-30"]
        if len(a) and len(b) and b.index[-1] > pd.Timestamp(f"{y + 1}-06-20"):
            rows.append({"year": y, "cycle": CYCLE[y % 4], "ret": float(b.iloc[-1] / a.iloc[-1] - 1)})
    df = pd.DataFrame(rows)
    g = df.groupby("cycle")["ret"]
    return pd.DataFrame({"n": g.size(), "mean": g.mean(), "median": g.median(), "%pos": g.apply(lambda s: (s > 0).mean())}).loc[
        ["Post-election", "Midterm", "Pre-election", "Election"]]
