"""Global transmission of the U.S. midterm result: local-currency, USD and hedged returns.

Channels measured (free data only):

* **Dollar** - each market's USD return is its local return compounded with the currency move;
  sensitivity to the Fed broad dollar index (DTWEXBGS).
* **U.S. rates** - sensitivity to the monthly change in the 10-year Treasury yield (DGS10).
* **Energy cost** - sensitivity to Brent (BZ=F); exporters and importers are tagged.
* **U.S. equity spillover** - sensitivity to the S&P 500.

Two outputs:

1. The election-window reaction: last close on or before 3 Nov 2026 (before any result was
   known in any time zone) to the last close on or before 5 Nov, in local currency, in USD
   (local index x FX), for the U.S.-listed ETF, and for a currency-hedged ETF where one exists.
2. Five-year (60-month) multivariate sensitivities, separately for local and USD returns,
   with heteroskedasticity-robust t-statistics.

The trade channel (tariff exposure by country and product) is not measured: the free sources
(UN Comtrade, USITC DataWeb) require registration keys this project does not hold.
Local-currency index returns approximate a hedged return before the interest-rate carry
(foreign minus U.S. short rate) and hedging costs; hedged ETFs show the realised version.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from midterm_quant import config
from midterm_quant.data.sources import fetch_fred, fetch_yahoo
from midterm_quant.research.event_study import ols_hc1

# fx: Yahoo symbol and whether it is quoted USD per local unit ("usd_per") or local per USD ("per_usd")
MARKETS = [
    {"market": "Euro area", "group": "Europe", "energy": "importer", "local": "^STOXX50E", "fx": ("EURUSD=X", "usd_per"), "etf": "EZU", "hedged": "HEDJ",
     "note": "HEDJ tracks a different (exporter-tilted) index from EZU, so the hedged-unhedged gap mixes currency and composition"},
    {"market": "Germany", "group": "Europe", "energy": "importer", "local": "^GDAXI", "fx": ("EURUSD=X", "usd_per"), "etf": "EWG", "hedged": None},
    {"market": "Japan", "group": "Japan", "energy": "importer", "local": "^N225", "fx": ("JPY=X", "per_usd"), "etf": "EWJ", "hedged": "DBJP"},
    {"market": "China (Shanghai Composite)", "group": "China and Asian supply chain", "energy": "importer", "local": "000001.SS", "fx": ("CNY=X", "per_usd"), "etf": "MCHI", "hedged": None},
    {"market": "Hong Kong", "group": "China and Asian supply chain", "energy": "importer", "local": "^HSI", "fx": ("HKD=X", "per_usd"), "etf": "EWH", "hedged": None},
    {"market": "Korea", "group": "China and Asian supply chain", "energy": "importer", "local": "^KS11", "fx": ("KRW=X", "per_usd"), "etf": "EWY", "hedged": None},
    {"market": "Taiwan", "group": "China and Asian supply chain", "energy": "importer", "local": "^TWII", "fx": ("TWD=X", "per_usd"), "etf": "EWT", "hedged": None},
    {"market": "India", "group": "Emerging markets", "energy": "importer", "local": "^BSESN", "fx": ("INR=X", "per_usd"), "etf": "INDA", "hedged": None},
    {"market": "Brazil", "group": "Emerging markets", "energy": "exporter", "local": "^BVSP", "fx": ("BRL=X", "per_usd"), "etf": "EWZ", "hedged": None},
    {"market": "Mexico", "group": "Emerging markets", "energy": "exporter", "local": "^MXX", "fx": ("MXN=X", "per_usd"), "etf": "EWW", "hedged": None},
    {"market": "Canada", "group": "Energy exporters", "energy": "exporter", "local": "^GSPTSE", "fx": ("CAD=X", "per_usd"), "etf": "EWC", "hedged": None},
    {"market": "Norway", "group": "Energy exporters", "energy": "exporter", "local": None, "fx": ("NOK=X", "per_usd"), "etf": "ENOR", "hedged": None},
    {"market": "Saudi Arabia", "group": "Energy exporters", "energy": "exporter", "local": None, "fx": None, "etf": "KSA", "hedged": None},
    {"market": "EM broad (MSCI EM)", "group": "Emerging markets", "energy": "mixed", "local": None, "fx": None, "etf": "EEM", "hedged": "HEEM"},
    {"market": "Developed ex-US (MSCI EAFE)", "group": "Europe", "energy": "importer", "local": None, "fx": None, "etf": "EFA", "hedged": "HEFA"},
]
PRE, POST = "2026-11-03", "2026-11-05"


def _px(sym: str | None) -> pd.Series | None:
    if not sym:
        return None
    try:
        return fetch_yahoo(sym)["close"].dropna()
    except Exception:
        return None


def _usd_per_local(fx) -> pd.Series | None:
    if not fx:
        return None
    s = _px(fx[0])
    if s is None:
        return None
    return s if fx[1] == "usd_per" else 1.0 / s


def _window_ret(s: pd.Series | None, a: str, b: str) -> float:
    if s is None:
        return float("nan")
    x, y = s[s.index <= pd.Timestamp(a)], s[s.index <= pd.Timestamp(b)]
    if not len(x) or not len(y) or y.index[-1] <= x.index[-1]:
        return float("nan")
    return float(y.iloc[-1] / x.iloc[-1] - 1)


def election_window() -> pd.DataFrame:
    rows = []
    for m in MARKETS:
        local, fx = _px(m["local"]), _usd_per_local(m["fx"])
        lr, fr = _window_ret(local, PRE, POST), _window_ret(fx, PRE, POST)
        usd = (1 + lr) * (1 + fr) - 1 if math.isfinite(lr) and math.isfinite(fr) else float("nan")
        rows.append({"market": m["market"], "group": m["group"], "energy": m["energy"],
                     "local": lr, "fx vs USD": fr, "USD (local x FX)": usd,
                     "US-listed ETF": _window_ret(_px(m["etf"]), PRE, POST),
                     "hedged ETF": _window_ret(_px(m["hedged"]), PRE, POST),
                     "local last date": (local[local.index <= pd.Timestamp(POST)].index[-1].date().isoformat() if local is not None and (local.index <= pd.Timestamp(POST)).any() else None)})
    for sym, name in (("SPY", "United States (SPY)"),):
        rows.append({"market": name, "group": "United States", "energy": "producer", "local": _window_ret(_px(sym), PRE, POST),
                     "fx vs USD": 0.0, "USD (local x FX)": _window_ret(_px(sym), PRE, POST),
                     "US-listed ETF": _window_ret(_px(sym), PRE, POST), "hedged ETF": float("nan"), "local last date": POST})
    return pd.DataFrame(rows)


def _monthly_ret(s: pd.Series) -> pd.Series:
    m = s.groupby(s.index.to_period("M")).last()
    return m.pct_change()


def sensitivities(months: int = 60) -> pd.DataFrame:
    end = pd.Period(pd.Timestamp(config.BACKTEST_END), "M") - 1
    f10 = fetch_fred("DGS10")
    d10 = f10.groupby(f10.index.to_period("M")).last().diff()
    usd = _monthly_ret(fetch_fred("DTWEXBGS"))
    brent = _monthly_ret(_px("BZ=F"))
    spx = _monthly_ret(_px("^GSPC"))
    X = pd.DataFrame({"dUS10y (pp)": d10, "USD broad": usd, "Brent": brent, "S&P 500": spx})
    X = X[(X.index <= end)].dropna().iloc[-months:]
    rows = []
    for m in MARKETS:
        series = {}
        local, fx = _px(m["local"]), _usd_per_local(m["fx"])
        if local is not None:
            series["local"] = _monthly_ret(local)
            if fx is not None:
                series["USD"] = (1 + series["local"]) * (1 + _monthly_ret(fx)) - 1
        elif m["etf"]:
            series["USD"] = _monthly_ret(_px(m["etf"]))
        if m["hedged"]:
            series["hedged ETF"] = _monthly_ret(_px(m["hedged"]))
        for basis, y in series.items():
            j = X.index.intersection(y.dropna().index)
            if len(j) < 36:
                continue
            res = ols_hc1(y[j].to_numpy(), X.loc[j].to_numpy(), list(X.columns))
            row = {"market": m["market"], "group": m["group"], "energy": m["energy"], "basis": basis, "months": len(j),
                   "start": str(j[0]), "end": str(j[-1])}
            for c in X.columns:
                row[f"beta {c}"] = float(res.loc[c, "coef"])
                row[f"t {c}"] = float(res.loc[c, "t"])
            yy = y[j].to_numpy()
            fitted = np.column_stack([np.ones(len(j)), X.loc[j].to_numpy()]) @ res["coef"].to_numpy()
            row["R2"] = float(1 - ((yy - fitted) ** 2).sum() / ((yy - yy.mean()) ** 2).sum())
            rows.append(row)
    return pd.DataFrame(rows)


def hedged_vs_unhedged() -> pd.DataFrame:
    rows = []
    end = pd.Timestamp(config.BACKTEST_END)
    for m in MARKETS:
        if not m["hedged"]:
            continue
        a, b = _px(m["etf"]), _px(m["hedged"])
        for yrs in (1, 3):
            start = end - pd.DateOffset(years=yrs)
            ra, rb = _window_ret(a, start.date().isoformat(), end.date().isoformat()), _window_ret(b, start.date().isoformat(), end.date().isoformat())
            rows.append({"market": m["market"], "years": yrs, "unhedged ETF": m["etf"], "hedged ETF": m["hedged"],
                         "unhedged ann.": (1 + ra) ** (1 / yrs) - 1, "hedged ann.": (1 + rb) ** (1 / yrs) - 1,
                         "currency effect ann.": ((1 + ra) ** (1 / yrs)) - ((1 + rb) ** (1 / yrs)),
                         "note": m.get("note", "same underlying index")})
    return pd.DataFrame(rows)


def run() -> dict:
    return {"window": {"pre": PRE, "post": POST}, "reaction": election_window().to_dict(orient="records"),
            "sensitivities": sensitivities().to_dict(orient="records"),
            "hedged_vs_unhedged": hedged_vs_unhedged().to_dict(orient="records"),
            "timing_note": "U.S.-listed ETFs trade 09:30-16:00 ET, after Asian and most European closes, so on 5 Nov an Asian-market ETF had already absorbed the U.S. selloff while that market's local index had not. Local and ETF windows are therefore not comparable day by day.",
            "not_measured": ["Trade/tariff exposure by country (UN Comtrade and USITC DataWeb need registration keys)",
                             "Hedged returns computed from local index plus interest carry (needs local short rates for every market)",
                             "Local-currency index for Norway and Saudi Arabia (no free daily series found; ETF in USD only)"]}
