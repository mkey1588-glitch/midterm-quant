"""The 2-year post-midterm observation dashboard.

Each indicator is a small function returning (value, context, regime) from free data.
Regimes use fixed, pre-declared thresholds (documented in docs/02) so that the read-out
is mechanical rather than discretionary. Run ``scripts/run_monitor.py`` weekly.
"""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd

from midterm_quant import config
from midterm_quant import indicators as ind
from midterm_quant.data.sources import fetch_fred, fetch_stablecoin_supply, fetch_yahoo
from midterm_quant.strategies.crypto import halving_phase


def _y(sym: str) -> pd.Series:
    return fetch_yahoo(sym)["close"].dropna()


def _f(sid: str) -> pd.Series:
    return fetch_fred(sid).dropna()


def _z(s: pd.Series, n: int) -> float:
    return ind.zscore(s.to_numpy(), min(n, len(s)))


def _chg(s: pd.Series, n: int) -> float:
    return ind.diff(s.to_numpy(), n)


def _pct(s: pd.Series, n: int) -> float:
    return ind.pct_change(s.to_numpy(), n)


def _rel(a: str, b: str, n: int = 63) -> float:
    x, y = _y(a), _y(b)
    j = x.index.intersection(y.index)
    return _pct(x[j], n) - _pct(y[j], n)


@dataclass
class Reading:
    group: str
    code: str
    name: str
    value: str
    context: str
    regime: str  # "RISK-ON" / "NEUTRAL" / "STRESS" or a descriptive tag
    watch: str


def _r(group, code, name, watch):
    def deco(fn: Callable[[], tuple]):
        fn.meta = (group, code, name, watch)
        return fn
    return deco


# ---------------------------------------------------------------- macro & policy ----
@_r("Macro/Policy", "M1", "Economic Policy Uncertainty (30d avg)", "STRESS if 3y z > +1.5")
def m1():
    s = _f("USEPUINDXD").rolling(30).mean().dropna()
    z = _z(s, 756)
    return f"{s.iloc[-1]:.0f}", f"3y z {z:+.2f}", "STRESS" if z > 1.5 else "NEUTRAL" if z > -0.5 else "RISK-ON"


@_r("Macro/Policy", "M2", "10Y Treasury yield", "STRESS if > 5.0% or +50bp/3m")
def m2():
    s = _f("DGS10")
    ch = _chg(s, 63) * 100
    return f"{s.iloc[-1]:.2f}%", f"3m {ch:+.0f}bp", "STRESS" if s.iloc[-1] > 5.0 or ch > 50 else "NEUTRAL"


@_r("Macro/Policy", "M3", "10Y term premium (Kim-Wright)", "STRESS if 3m change z > +1.5 (fiscal/Fed-independence premium)")
def m3():
    s = _f("THREEFYTP10")
    z = ind.rolling_change_zscore(s.to_numpy(), 63, 756)
    return f"{s.iloc[-1]:.2f}%", f"3m chg z {z:+.2f}", "STRESS" if z > 1.5 else "NEUTRAL"


@_r("Macro/Policy", "M4", "2Y yield minus fed funds (implied path)", "> +25bp = hikes priced; < -50bp = cuts priced")
def m4():
    a, b = _f("DGS2"), _f("DFF")
    j = a.index.intersection(b.index)
    v = (a[j] - b[j]).iloc[-1] * 100
    reg = "HIKES PRICED" if v > 25 else "CUTS PRICED" if v < -50 else "ON HOLD"
    return f"{v:+.0f}bp", f"FF {b.iloc[-1]:.2f}%", reg


@_r("Macro/Policy", "M5", "10Y breakeven inflation", "STRESS if > 2.6% (oil pass-through de-anchoring)")
def m5():
    s = _f("T10YIE")
    return f"{s.iloc[-1]:.2f}%", f"3m {_chg(s, 63) * 100:+.0f}bp", "STRESS" if s.iloc[-1] > 2.6 else "NEUTRAL"


@_r("Macro/Policy", "M6", "10Y real yield (TIPS)", "Gold headwind if > 2.5% and rising")
def m6():
    s = _f("DFII10")
    ch = _chg(s, 63) * 100
    return f"{s.iloc[-1]:.2f}%", f"3m {ch:+.0f}bp", "HEADWIND" if s.iloc[-1] > 2.5 and ch > 0 else "NEUTRAL"


@_r("Macro/Policy", "M7", "Broad trade-weighted dollar", "Weak-USD regime if below 200d SMA")
def m7():
    s = _f("DTWEXBGS")
    sma = s.rolling(200).mean().iloc[-1]
    return f"{s.iloc[-1]:.1f}", f"vs 200d {s.iloc[-1] / sma - 1:+.1%}", "STRONG USD" if s.iloc[-1] > sma else "WEAK USD"


@_r("Macro/Policy", "M8", "Bill curve: 4-week minus 3-month T-bill", "Debt-limit X-date stress if > +15bp")
def m8():
    a, b = _f("DTB4WK"), _f("DTB3")
    j = a.index.intersection(b.index)
    v = (a[j] - b[j]).iloc[-1] * 100
    return f"{v:+.0f}bp", "1M vs 3M bills", "STRESS" if v > 15 else "NEUTRAL"


@_r("Macro/Policy", "M9", "Fed net liquidity (WALCL - TGA - RRP)", "Risk-on if 13w change > 0; TGA drawdown = pre-X-date injection")
def m9():
    w, t, r = _f("WALCL"), _f("WTREGEN"), _f("RRPONTSYD")
    df = pd.concat([w, t, r], axis=1).ffill().dropna()
    nl = (df.iloc[:, 0] - df.iloc[:, 1] - df.iloc[:, 2] * 1000) / 1e6
    ch = nl.iloc[-1] - nl[: nl.index[-1] - pd.Timedelta(days=91)].iloc[-1]
    return f"${nl.iloc[-1]:.2f}tn", f"13w {ch * 1000:+.0f}bn; TGA ${t.iloc[-1] / 1e6:.2f}tn", "RISK-ON" if ch > 0 else "DRAIN"


@_r("Macro/Policy", "M10", "Credit: HYG/IEF 20d change", "STRESS if z < -1.5")
def m10():
    x, y = _y("HYG"), _y("IEF")
    j = x.index.intersection(y.index)
    z = ind.rolling_change_zscore(np.log((x[j] / y[j]).to_numpy()), 20, 500)
    return f"{z:+.2f}z", "HY vs Treasuries", "STRESS" if z < -1.5 else "NEUTRAL"


# --------------------------------------------------------------------- equities -----
@_r("US Equities", "E-a", "S&P 500 trend / drawdown", "Risk-off if below 200d SMA")
def ea():
    s = _y("^GSPC")
    sma = s.rolling(200).mean().iloc[-1]
    return f"{s.iloc[-1]:,.0f}", f"vs 200d {s.iloc[-1] / sma - 1:+.1%}, DD {ind.drawdown(s.to_numpy(), 252):.1%}", "RISK-ON" if s.iloc[-1] > sma else "RISK-OFF"


@_r("US Equities", "E-b", "VIX and VIX/VIX3M", "STRESS if ratio > 1.0 (inverted)")
def eb():
    v, v3 = _y("^VIX"), _y("^VIX3M")
    ratio = v.iloc[-1] / v3.iloc[-1]
    return f"{v.iloc[-1]:.1f}", f"VIX/VIX3M {ratio:.2f}", "STRESS" if ratio > 1.0 else "NEUTRAL" if ratio > 0.9 else "CALM"


@_r("US Equities", "E-c", "Breadth: RSP vs SPY (63d)", "Broadening if > 0")
def ec():
    v = _rel("RSP", "SPY")
    return f"{v:+.1%}", "equal- vs cap-weight", "BROADENING" if v > 0 else "NARROW"


@_r("US Equities", "E-d", "Small caps: IWM vs SPY (63d)", "Broadening if > 0")
def ed():
    v = _rel("IWM", "SPY")
    return f"{v:+.1%}", "small vs large", "BROADENING" if v > 0 else "NARROW"


@_r("US Equities", "E-e", "AI-infrastructure risk: SMH vs SPY (63d)", "Regulation-risk repricing if < -5%")
def ee():
    v = _rel("SMH", "SPY")
    return f"{v:+.1%}", "semis vs market", "DERATING" if v < -0.05 else "NEUTRAL"


@_r("US Equities", "E-f", "Policy baskets vs SPY (63d)", "Largest movers flag where policy is being priced")
def ef():
    names = {"ITA": "defence", "XLV": "health", "TAN": "solar", "KRE": "reg. banks", "XLE": "energy"}
    vals = {k: _rel(k, "SPY") for k in names}
    ctx = ", ".join(f"{names[k]} {v:+.0%}" for k, v in vals.items())
    best = max(vals, key=vals.get)
    return f"lead: {names[best]}", ctx, "INFO"


@_r("US Equities", "E-g", "Midterm-cycle clock", "Seasonal sweet spot: Oct midterm yr -> Dec pre-election yr")
def eg():
    today = dt.date.today()
    last = max(d for d in config.MIDTERM_DATES if d <= today)
    from midterm_quant.strategies.equities import in_midterm_sweet_spot

    return f"day {(today - last).days}", f"since {last.isoformat()}", "SWEET SPOT" if in_midterm_sweet_spot(today) else "OFF-SEASON"


# ----------------------------------------------------------------------- crypto -----
@_r("Crypto", "C-a", "BTC Mayer multiple (price / 200d SMA)", "< 0.8 historically deep value; > 2.4 euphoric")
def ca():
    s = _y("BTC-USD")
    mm = s.iloc[-1] / s.rolling(200).mean().iloc[-1]
    reg = "DEEP VALUE" if mm < 0.8 else "EUPHORIC" if mm > 2.4 else "UPTREND" if mm > 1 else "DOWNTREND"
    return f"{mm:.2f}", f"BTC ${s.iloc[-1]:,.0f}, DD {ind.drawdown(s.to_numpy(), 365):.0%}", reg


@_r("Crypto", "C-b", "BTC 30d realized vol", "STRESS if > 70%")
def cb():
    v = ind.realized_vol(_y("BTC-USD").to_numpy(), 30, 365)
    return f"{v:.0%}", "annualised", "STRESS" if v > 0.7 else "NEUTRAL"


@_r("Crypto", "C-c", "ETH/BTC (90d change)", "Alt-season if > +10% and rising")
def cc():
    e, b = _y("ETH-USD"), _y("BTC-USD")
    j = e.index.intersection(b.index)
    r = e[j] / b[j]
    ch = _pct(r, 90)
    return f"{r.iloc[-1]:.4f}", f"90d {ch:+.0%}", "ALT-SEASON" if ch > 0.10 else "BTC DOMINANCE"


@_r("Crypto", "C-d", "US regulatory sentiment: COIN vs BTC (63d)", "Negative = US-specific regulatory discount widening")
def cd():
    v = _rel("COIN", "BTC-USD")
    return f"{v:+.1%}", "Coinbase vs bitcoin", "REG HEADWIND" if v < -0.10 else "NEUTRAL"


@_r("Crypto", "C-e", "Stablecoin supply (30d growth)", "Liquidity inflow if > 0")
def ce():
    s = fetch_stablecoin_supply()
    g = _pct(s, 30)
    return f"${s.iloc[-1] / 1e9:,.0f}bn", f"30d {g:+.1%}", "INFLOW" if g > 0 else "OUTFLOW"


@_r("Crypto", "C-f", "Halving-cycle phase", "Next halving ~Apr 2028 (estimate)")
def cf():
    today = dt.date.today()
    nxt = min(h for h in config.BTC_HALVINGS if h > today)
    return halving_phase(today).upper(), f"{(nxt - today).days} days to est. halving", "INFO"


# ----------------------------------------------------------------------- energy -----
@_r("Energy", "N-a", "Brent / WTI and spread", "War premium if Brent-WTI > $6")
def na():
    b, w = _y("BZ=F"), _y("CL=F")
    sp = b.iloc[-1] - w.iloc[-1]
    return f"${b.iloc[-1]:.1f} / ${w.iloc[-1]:.1f}", f"spread ${sp:.1f}, Brent 3m {_pct(b, 63):+.0%}", "WAR PREMIUM" if sp > 6 else "NORMAL"


@_r("Energy", "N-b", "Curve proxy: USO vs USL (63d)", "Backwardation tightening if > 0")
def nb():
    v = _rel("USO", "USL")
    return f"{v:+.1%}", "front vs 12m strip", "BACKWARDATION" if v > 0 else "CONTANGO"


@_r("Energy", "N-c", "US retail gasoline", "Political pain if > $4.00 or top-30% of 2y")
def nc():
    s = _f("GASREGW")
    pr = ind.percentile_rank(s.to_numpy(), 104)
    return f"${s.iloc[-1]:.2f}", f"2y pct {pr:.0%}", "POLITICAL PAIN" if s.iloc[-1] > 4.0 or pr > 0.7 else "NEUTRAL"


@_r("Energy", "N-d", "Oil 20d return z-score (USO)", "Spike if > +2, crash if < -2")
def nd():
    z = ind.return_zscore(_y("USO").to_numpy(), 20, 250)
    return f"{z:+.2f}", "vs 1y of 20d returns", "SPIKE" if z > 2 else "CRASH" if z < -2 else "NORMAL"


@_r("Energy", "N-e", "Clean vs fossil: ICLN vs XLE (63d)", "Policy/rates rotation signal")
def ne():
    v = _rel("ICLN", "XLE")
    return f"{v:+.1%}", "clean minus fossil", "CLEAN LEADS" if v > 0 else "FOSSIL LEADS"


# ----------------------------------------------------------------------- metals -----
@_r("Precious Metals", "P-a", "Gold price / drawdown", "Below 200d SMA = trend broken")
def pa():
    s = _y("GC=F")
    sma = s.rolling(200).mean().iloc[-1]
    return f"${s.iloc[-1]:,.0f}", f"DD from ATH {s.iloc[-1] / s.max() - 1:.0%}, vs 200d {s.iloc[-1] / sma - 1:+.1%}", "UPTREND" if s.iloc[-1] > sma else "DOWNTREND"


@_r("Precious Metals", "P-b", "Gold/silver ratio", "Silver cheap if 2y z > +1")
def pb():
    g, s = _y("GC=F"), _y("SI=F")
    j = g.index.intersection(s.index)
    r = g[j] / s[j]
    z = _z(r, 504)
    return f"{r.iloc[-1]:.1f}", f"2y z {z:+.2f}", "SILVER CHEAP" if z > 1 else "SILVER RICH" if z < -1 else "NEUTRAL"


@_r("Precious Metals", "P-c", "Gold/oil ratio (miner margin proxy)", "Miners favoured if above 200d SMA")
def pc():
    g, o = _y("GC=F"), _y("CL=F")
    j = g.index.intersection(o.index)
    r = (g[j] / o[j])[o[j] > 5]
    sma = r.rolling(200).mean().iloc[-1]
    return f"{r.iloc[-1]:.1f}", f"vs 200d {r.iloc[-1] / sma - 1:+.0%}", "MARGINS EXPANDING" if r.iloc[-1] > sma else "MARGINS SQUEEZED"


@_r("Precious Metals", "P-d", "Miners vs bullion: GDX vs GLD (63d)", "Confirms gold upleg if > 0")
def pd_():
    v = _rel("GDX", "GLD")
    return f"{v:+.1%}", "miners minus bullion", "CONFIRMING" if v > 0 else "DIVERGING"


@_r("Precious Metals", "P-e", "Platinum/gold ratio", "Industrial-metal stress if 1y z < -1")
def pe():
    p, g = _y("PL=F"), _y("GC=F")
    j = p.index.intersection(g.index)
    r = p[j] / g[j]
    z = _z(r, 252)
    return f"{r.iloc[-1]:.3f}", f"1y z {z:+.2f}", "PGM WEAK" if z < -1 else "NEUTRAL"


INDICATORS = [m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, ea, eb, ec, ed, ee, ef, eg, ca, cb, cc, cd, ce, cf, na, nb, nc, nd, ne, pa, pb, pc, pd_, pe]


def read_all() -> list[Reading]:
    out = []
    for fn in INDICATORS:
        group, code, name, watch = fn.meta
        try:
            value, context, regime = fn()
        except Exception as exc:  # keep the dashboard alive if one source fails
            value, context, regime = "n/a", f"error: {type(exc).__name__}", "UNKNOWN"
        if isinstance(value, float) and not math.isfinite(value):
            value = "n/a"
        out.append(Reading(group, code, name, value, context, regime, watch))
    return out
