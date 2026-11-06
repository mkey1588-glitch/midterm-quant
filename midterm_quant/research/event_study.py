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
