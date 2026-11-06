"""The post-midterm observation dashboard: 36 indicators, each with explicit timing.

Every reading carries

* ``observation_date`` - the date the number describes (per input; the oldest input wins);
* ``available_at``     - when the input was published (catalogue rule, ``data/catalog.py``);
* ``retrieved_at``     - when this run downloaded it (cache sidecar);
* ``age_days`` and ``status`` - OK, STALE (older than the series' allowed age) or MISSING.
  A STALE or MISSING reading is never shown with a supportive or alert tone.

``read_all(asof)`` evaluates every indicator *as of* the close of ``asof`` using only data
whose ``available_at`` is on or before that date (revision-prone FRED series come from the
ALFRED vintage of that date when ``asof`` is in the past). That makes the weekly history used
by the scenario rule (``research/scenarios.py``) point-in-time.

Thresholds were declared on 4 Nov 2026 (docs/02); the three direct measures added on 6 Nov
(M11, M12, N-f) have thresholds declared in ``SPECS`` before their first reading.
"""
from __future__ import annotations

import datetime as dt
import math
from dataclasses import asdict, dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

from midterm_quant import config
from midterm_quant import indicators as ind
from midterm_quant.data import catalog
from midterm_quant.data.sources import (_cache_path, fetch_fred, fetch_fred_vintage, fetch_stablecoin_supply,
                                        fetch_yahoo, read_meta)
from midterm_quant.strategies.crypto import halving_phase

MONTH_CODES = "FGHJKMNQUVXZ"


class MissingInput(Exception):
    pass


# ---------------------------------------------------------------------------- loader --
class Loader:
    """Point-in-time access to every input as of the close of ``asof``."""

    def __init__(self, asof: pd.Timestamp, live: bool):
        self.asof = pd.Timestamp(asof).normalize()
        self.live = live          # True: today's files are the vintage; False: use ALFRED vintages
        self.used: dict[str, dict] = {}

    def _note(self, name: str, s: pd.Series, kind: str, cache_name: str) -> None:
        last = s.index.max() if len(s) else None
        avail = catalog.available_dates(name, pd.DatetimeIndex([last]))[0] if last is not None else None
        try:
            meta = read_meta(_cache_path(kind, cache_name))
        except FileNotFoundError:
            meta = {}
        self.used[name] = {
            "series": name, "observation_date": last.date().isoformat() if last is not None else None,
            "available_at": avail.date().isoformat() if avail is not None else None,
            "retrieved_at": meta.get("retrieved_at_utc"), "vintage": meta.get("vintage_id"),
            "units": catalog.meta(name).units, "source_url": catalog.meta(name).source_url,
        }

    def fred(self, sid: str) -> pd.Series:
        name = f"fred:{sid}"
        if not self.live and catalog.meta(name).revisions == "material":
            vd = (self.asof + pd.Timedelta(days=1)).date().isoformat()
            s = fetch_fred_vintage(sid, vd)
            kind, cache = "alfred", f"{sid}_{vd}"
        else:
            s = fetch_fred(sid)
            kind, cache = "fred", sid
        s = s.dropna()
        s = s[catalog.available_dates(name, s.index) <= self.asof]
        if not len(s):
            raise MissingInput(name)
        self._note(name, s, kind, cache)
        return s

    def yahoo(self, sym: str) -> pd.Series:
        s = fetch_yahoo(sym)["close"].dropna()
        s = s[s.index <= self.asof]
        if not len(s):
            raise MissingInput(sym)
        self._note(sym, s, "yahoo", sym)
        return s

    def stablecoins(self) -> pd.Series:
        s = fetch_stablecoin_supply().dropna()
        s = s[catalog.available_dates("llama:stablecoins", s.index) <= self.asof + pd.Timedelta(days=1)]
        if not len(s):
            raise MissingInput("llama:stablecoins")
        self._note("llama:stablecoins", s, "defillama", "stablecoins_usd")
        return s


# ------------------------------------------------------------------------------ spec --
@dataclass
class Spec:
    code: str
    group: str
    name: str
    measures: str            # what the number is
    not_measures: str        # what it must not be read as
    formula: str
    inputs: tuple
    units: str
    frequency: str
    rule: str                # threshold -> regime, declared in advance
    tones: dict              # regime -> alert | watch | supportive | neutral | info
    declared: str = "2026-11-04"
    better: str = ""         # the direct measure, where this is a proxy
    missing: str = "Reading shown as MISSING; never coloured; excluded from signpost counts (counts as 'not holding')."


@dataclass
class Reading:
    code: str
    group: str
    name: str
    value: str
    value_num: float
    context: str
    regime: str
    tone: str
    status: str
    observation_date: str | None
    age_days: int | None
    inputs: list = field(default_factory=list)
    rule: str = ""
    measures: str = ""
    not_measures: str = ""
    better: str = ""
    extra: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


SPECS: dict[str, Spec] = {}
FUNCS: dict[str, Callable] = {}


def indicator(spec: Spec):
    def deco(fn):
        SPECS[spec.code] = spec
        FUNCS[spec.code] = fn
        return fn
    return deco


def _z(s: pd.Series, n: int) -> float:
    return ind.zscore(s.to_numpy(), min(n, len(s)))


def _chg(s: pd.Series, n: int) -> float:
    return ind.diff(s.to_numpy(), n)


def _pct(s: pd.Series, n: int) -> float:
    return ind.pct_change(s.to_numpy(), n)


def _rel(L: Loader, a: str, b: str, n: int = 63) -> float:
    x, y = L.yahoo(a), L.yahoo(b)
    j = x.index.intersection(y.index)
    return _pct(x[j], n) - _pct(y[j], n)


ALERT, WATCH, GOOD, NEUTRAL, INFO = "alert", "watch", "supportive", "neutral", "info"

# --------------------------------------------------------------------- macro & policy --
@indicator(Spec("M1", "Macro and policy", "Economic policy uncertainty (30-day average)",
                "Newspaper-based policy-uncertainty index, 30-day mean, z-score vs 3 years",
                "Not a forecast of policy outcomes; daily counts are revised", "mean30(USEPUINDXD); z vs trailing 756 obs",
                ("fred:USEPUINDXD",), "index", "daily", "z > +1.5 STRESS; z < -0.5 CALM",
                {"STRESS": ALERT, "NEUTRAL": NEUTRAL, "CALM": GOOD}))
def m1(L):
    s = L.fred("USEPUINDXD").rolling(30).mean().dropna()
    z = _z(s, 756)
    return s.iloc[-1], f"{s.iloc[-1]:.0f}", f"z {z:+.2f} vs 3 years", "STRESS" if z > 1.5 else "NEUTRAL" if z > -0.5 else "CALM", {"z": z}


@indicator(Spec("M2", "Macro and policy", "10-year Treasury yield (FRED DGS10)",
                "Constant-maturity 10-year yield from the H.15 release", "Not CBOE ^TNX, which closes at 15:00 CT and can differ",
                "DGS10 level; 63-business-day change", ("fred:DGS10",), "percent", "daily",
                "> 5.0% or +50bp in 63 days STRESS", {"STRESS": ALERT, "NEUTRAL": NEUTRAL}))
def m2(L):
    s = L.fred("DGS10")
    ch = _chg(s, 63) * 100
    return s.iloc[-1], f"{s.iloc[-1]:.2f}%", f"{ch:+.0f}bp in 3 months", "STRESS" if s.iloc[-1] > 5.0 or ch > 50 else "NEUTRAL"


@indicator(Spec("M3", "Macro and policy", "10-year term premium (Kim-Wright)",
                "Model estimate of the compensation for holding long Treasuries", "A model output, revised when re-estimated; not observable",
                "z of the 63-day change vs 756 days", ("fred:THREEFYTP10",), "percent", "daily (lagged ~5 days)",
                "z > +1.5 STRESS", {"STRESS": ALERT, "NEUTRAL": NEUTRAL}))
def m3(L):
    s = L.fred("THREEFYTP10")
    z = ind.rolling_change_zscore(s.to_numpy(), 63, 756)
    return s.iloc[-1], f"{s.iloc[-1]:.2f}%", f"3-month change z {z:+.2f}", "STRESS" if z > 1.5 else "NEUTRAL"


@indicator(Spec("M4", "Macro and policy", "2-year yield minus effective fed funds",
                "Average policy rate the market expects over roughly two years, plus a term premium",
                "Not a meeting-by-meeting path: use M12 (fed funds futures) for that",
                "DGS2 - DFF on the same date", ("fred:DGS2", "fred:DFF"), "basis points", "daily",
                "> +25bp HIGHER RATES PRICED; < -50bp CUTS PRICED", {"HIGHER RATES PRICED": ALERT, "CUTS PRICED": WATCH, "ON HOLD": NEUTRAL},
                better="M12 fed funds futures path; OIS curve (licensed)"))
def m4(L):
    a, b = L.fred("DGS2"), L.fred("DFF")
    j = a.index.intersection(b.index)
    v = (a[j] - b[j]).iloc[-1] * 100
    return v, f"{v:+.0f}bp", f"effective fed funds {b.iloc[-1]:.2f}%", "HIGHER RATES PRICED" if v > 25 else "CUTS PRICED" if v < -50 else "ON HOLD"


@indicator(Spec("M5", "Macro and policy", "10-year breakeven inflation",
                "DGS10 minus the 10-year TIPS yield", "Includes inflation risk and TIPS liquidity premia, not pure expected inflation",
                "T10YIE level; 63-day change", ("fred:T10YIE",), "percent", "daily", "> 2.6% STRESS",
                {"STRESS": ALERT, "NEUTRAL": NEUTRAL}))
def m5(L):
    s = L.fred("T10YIE")
    return s.iloc[-1], f"{s.iloc[-1]:.2f}%", f"{_chg(s, 63) * 100:+.0f}bp in 3 months", "STRESS" if s.iloc[-1] > 2.6 else "NEUTRAL"


@indicator(Spec("M6", "Macro and policy", "10-year real yield (TIPS)",
                "10-year TIPS constant-maturity yield", "Opportunity cost of gold, one of several drivers since 2022",
                "DFII10 level; 63-day change", ("fred:DFII10",), "percent", "daily", "> 2.5% and rising: gold HEADWIND",
                {"HEADWIND": ALERT, "NEUTRAL": NEUTRAL}))
def m6(L):
    s = L.fred("DFII10")
    ch = _chg(s, 63) * 100
    return s.iloc[-1], f"{s.iloc[-1]:.2f}%", f"{ch:+.0f}bp in 3 months", "HEADWIND" if s.iloc[-1] > 2.5 and ch > 0 else "NEUTRAL"


@indicator(Spec("M7", "Macro and policy", "Broad trade-weighted dollar",
                "Fed nominal broad dollar index vs its 200-day mean", "Published weekly; history revised with trade weights",
                "DTWEXBGS / SMA200 - 1", ("fred:DTWEXBGS",), "index", "daily, released weekly", "above SMA200 STRONG USD",
                {"STRONG USD": WATCH, "WEAK USD": GOOD}))
def m7(L):
    s = L.fred("DTWEXBGS")
    sma = s.rolling(200).mean().iloc[-1]
    return s.iloc[-1] / sma - 1, f"{s.iloc[-1]:.1f}", f"{s.iloc[-1] / sma - 1:+.1%} vs 200-day", "STRONG USD" if s.iloc[-1] > sma else "WEAK USD"


@indicator(Spec("M8", "Macro and policy", "4-week minus 3-month bill yield",
                "Kink at the front of the bill curve", "A debt-limit X-date gauge only when an X-date is near",
                "DTB4WK - DTB3", ("fred:DTB4WK", "fred:DTB3"), "basis points", "daily", "> +15bp X-DATE STRESS",
                {"X-DATE STRESS": ALERT, "NEUTRAL": NEUTRAL}))
def m8(L):
    a, b = L.fred("DTB4WK"), L.fred("DTB3")
    j = a.index.intersection(b.index)
    v = (a[j] - b[j]).iloc[-1] * 100
    return v, f"{v:+.0f}bp", "1-month vs 3-month bills", "X-DATE STRESS" if v > 15 else "NEUTRAL"


@indicator(Spec("M9", "Macro and policy", "Fed net liquidity (same-Wednesday basis)",
                "Fed total assets minus the Treasury's cash account minus overnight reverse repo, all on the same Wednesday, USD billions",
                "An accounting identity for reserves-plus; its link to asset prices is empirical, not causal",
                "WALCL/1000 - WDTGAL/1000 - RRPONTSYD(Wednesday); 13-week change", ("fred:WALCL", "fred:WDTGAL", "fred:RRPONTSYD"),
                "USD billions", "weekly (Wednesday)", "13-week change > 0 EXPANDING, < 0 DRAINING",
                {"DRAINING": ALERT, "EXPANDING": GOOD}))
def m9(L):
    w, t, r = L.fred("WALCL"), L.fred("WDTGAL"), L.fred("RRPONTSYD")
    weds = w.index.intersection(t.index)
    rrp = r.reindex(r.index.union(weds)).ffill(limit=3).reindex(weds).fillna(0.0)
    nl = pd.Series(ind.net_liquidity_bn(w[weds], t[weds], rrp), index=weds)
    prior = nl[: nl.index[-1] - pd.Timedelta(days=91)]
    ch = nl.iloc[-1] - prior.iloc[-1]
    return ch, f"${nl.iloc[-1]:,.0f}bn", f"{ch:+,.0f}bn over 13 weeks; TGA ${t[weds].iloc[-1] / 1000:,.0f}bn", "EXPANDING" if ch > 0 else "DRAINING"


@indicator(Spec("M10", "Macro and policy", "Credit risk-appetite proxy: HYG vs IEF",
                "20-day change in log(HYG/IEF), z vs 500 days: high-yield bond ETF against intermediate Treasuries",
                "Not a credit spread and not a 'credit impulse' (the change in credit growth); ETF prices mix spread, duration and flows",
                "z of the 20-day change of log(HYG/IEF) vs 500 obs", ("HYG", "IEF"), "z-score", "daily",
                "z < -1.5 STRESS", {"STRESS": ALERT, "NEUTRAL": NEUTRAL}, better="M11 high-yield option-adjusted spread"))
def m10(L):
    x, y = L.yahoo("HYG"), L.yahoo("IEF")
    j = x.index.intersection(y.index)
    z = ind.rolling_change_zscore(np.log((x[j] / y[j]).to_numpy()), 20, 500)
    return z, f"{z:+.2f}z", "high-yield ETF vs Treasuries", "STRESS" if z < -1.5 else "NEUTRAL"


@indicator(Spec("M11", "Macro and policy", "High-yield option-adjusted spread (ICE BofA)",
                "Spread of US high-yield bonds over Treasuries, option-adjusted", "FRED shows only the latest 3 years under ICE's licence",
                "BAMLH0A0HYM2 level; 63-day change", ("fred:BAMLH0A0HYM2",), "percentage points", "daily",
                ">= 5.0pp or +1.0pp in 63 days STRESS; >= 4.0pp WATCH", {"STRESS": ALERT, "WATCH": WATCH, "CALM": NEUTRAL},
                declared="2026-11-06"))
def m11(L):
    s = L.fred("BAMLH0A0HYM2")
    ch = _chg(s, 63)
    reg = "STRESS" if s.iloc[-1] >= 5.0 or ch >= 1.0 else "WATCH" if s.iloc[-1] >= 4.0 else "CALM"
    return s.iloc[-1], f"{s.iloc[-1] * 100:.0f}bp", f"{ch * 100:+.0f}bp in 3 months", reg


def _contract_path(L: Loader, root: str, exch: str, months_ahead: int) -> list[tuple[str, pd.Timestamp, float]]:
    """(symbol, delivery month, last close) for contracts trading on the asof date."""
    out = []
    start = L.asof.to_period("M")
    for k in range(0, months_ahead + 2):
        p = start + k
        sym = f"{root}{MONTH_CODES[p.month - 1]}{str(p.year)[2:]}.{exch}"
        try:
            s = L.yahoo(sym)
        except Exception:
            continue
        if s.index[-1] < L.asof - pd.Timedelta(days=4):   # expired or not trading
            continue
        out.append((sym, p.to_timestamp(), float(s.iloc[-1])))
    return out


@indicator(Spec("M12", "Macro and policy", "Fed funds futures: implied policy path",
                "100 minus each CME 30-day fed funds future = the market's expected average effective rate in that month",
                "Futures include a small risk premium; monthly averages blur meetings inside a month",
                "100 - ZQ price for each month; path change = Jun-2027 implied minus current effective rate",
                ("ZQ contracts", "fred:DFF"), "percent / basis points", "daily (contract closes)",
                "Jun-27 implied minus effective > +25bp HIKES PRICED; < -25bp CUTS PRICED", {"HIKES PRICED": ALERT, "CUTS PRICED": WATCH, "ON HOLD": NEUTRAL},
                declared="2026-11-06", missing="Contract histories exist only for listed contracts, so past readings cannot be rebuilt: MISSING for history."))
def m12(L):
    path = _contract_path(L, "ZQ", "CBT", 14)
    if len(path) < 4:
        raise MissingInput("ZQ contracts")
    eff = L.fred("DFF").iloc[-1]
    implied = {p.strftime("%b-%y"): 100 - px for _, p, px in path}
    target = pd.Timestamp(L.asof.year + (1 if L.asof.month >= 6 else 0), 6, 1)
    jun = next((100 - px for _, p, px in path if p == target), None)
    if jun is None:
        raise MissingInput("ZQ June contract")
    v = (jun - eff) * 100
    reg = "HIKES PRICED" if v > 25 else "CUTS PRICED" if v < -25 else "ON HOLD"
    pts = ", ".join(f"{k} {v_:.2f}%" for k, v_ in list(implied.items())[1:8:2])
    return v, f"{v:+.0f}bp by {target:%b %Y}", f"effective {eff:.2f}%; {pts}", reg, {"path": implied}


# --------------------------------------------------------------------------- equities --
@indicator(Spec("E-a", "U.S. equities", "S&P 500 trend",
                "Index level vs its 200-day average; drawdown from the 252-day high", "Price index only, no dividends",
                "^GSPC / SMA200 - 1", ("^GSPC",), "index points", "daily", "below SMA200 RISK-OFF",
                {"RISK-OFF": ALERT, "RISK-ON": GOOD}))
def ea(L):
    s = L.yahoo("^GSPC")
    sma = s.rolling(200).mean().iloc[-1]
    return s.iloc[-1] / sma - 1, f"{s.iloc[-1]:,.0f}", f"{s.iloc[-1] / sma - 1:+.1%} vs 200-day; {ind.drawdown(s.to_numpy(), 252):.1%} from 1-year high", "RISK-ON" if s.iloc[-1] > sma else "RISK-OFF"


@indicator(Spec("E-b", "U.S. equities", "VIX term structure",
                "Ratio of 30-day to 3-month implied volatility", "Implied, not realised, volatility",
                "^VIX / ^VIX3M", ("^VIX", "^VIX3M"), "ratio", "daily (16:15 ET)", "> 1.0 STRESS; < 0.9 CALM",
                {"STRESS": ALERT, "NEUTRAL": NEUTRAL, "CALM": GOOD}))
def eb(L):
    v, v3 = L.yahoo("^VIX"), L.yahoo("^VIX3M")
    j = v.index.intersection(v3.index)
    ratio = v[j].iloc[-1] / v3[j].iloc[-1]
    return ratio, f"{v[j].iloc[-1]:.1f}", f"VIX/VIX3M {ratio:.2f}", "STRESS" if ratio > 1.0 else "NEUTRAL" if ratio > 0.9 else "CALM"


@indicator(Spec("E-c", "U.S. equities", "Breadth: equal-weight vs cap-weight",
                "63-day return of RSP minus SPY", "Relative performance, not the share of stocks rising",
                "ret63(RSP) - ret63(SPY)", ("RSP", "SPY"), "percent", "daily", "> 0 BROADENING",
                {"BROADENING": GOOD, "NARROW": WATCH}))
def ec(L):
    v = _rel(L, "RSP", "SPY")
    return v, f"{v:+.1%}", "equal- minus cap-weight, 63 days", "BROADENING" if v > 0 else "NARROW"


@indicator(Spec("E-d", "U.S. equities", "Small caps vs large caps",
                "63-day return of IWM minus SPY", "Relative performance only", "ret63(IWM) - ret63(SPY)", ("IWM", "SPY"),
                "percent", "daily", "> 0 BROADENING", {"BROADENING": GOOD, "NARROW": WATCH}))
def ed(L):
    v = _rel(L, "IWM", "SPY")
    return v, f"{v:+.1%}", "small minus large, 63 days", "BROADENING" if v > 0 else "NARROW"


@indicator(Spec("E-e", "U.S. equities", "Semiconductor relative strength: SMH vs SPY",
                "63-day return of the semiconductor ETF minus the S&P 500",
                "Not a measure of AI regulation risk: semis move on earnings, capex, export controls, rates and positioning",
                "ret63(SMH) - ret63(SPY)", ("SMH", "SPY"), "percent", "daily", "< -5% SEMIS LAGGING",
                {"SEMIS LAGGING": ALERT, "NEUTRAL": NEUTRAL},
                better="Event-dated basket of data-centre names around dated regulatory actions (not built: needs a curated event list)"))
def ee(L):
    v = _rel(L, "SMH", "SPY")
    return v, f"{v:+.1%}", "semiconductors minus market, 63 days", "SEMIS LAGGING" if v < -0.05 else "NEUTRAL"


@indicator(Spec("E-f", "U.S. equities", "Policy-sensitive sector baskets vs SPY",
                "63-day relative returns of defence, health care, solar, regional banks, energy ETFs",
                "Sector moves have many causes; this flags where prices moved, not why", "ret63(X) - ret63(SPY)",
                ("ITA", "XLV", "TAN", "KRE", "XLE", "SPY"), "percent", "daily", "informational", {"INFO": INFO}))
def ef(L):
    names = {"ITA": "defence", "XLV": "health care", "TAN": "solar", "KRE": "regional banks", "XLE": "energy"}
    vals = {k: _rel(L, k, "SPY") for k in names}
    best = max(vals, key=vals.get)
    return vals[best], f"leader: {names[best]}", ", ".join(f"{names[k]} {v:+.0%}" for k, v in vals.items()), "INFO"


@indicator(Spec("E-g", "U.S. equities", "Midterm seasonal window and election clock",
                "Two separate clocks: days since the seasonal window opened (1 Oct of the midterm year) and trading days since election day",
                "The seasonal window is a calendar rule, not an election effect; its start predates the election",
                "calendar arithmetic", (), "days", "daily", "1 Oct midterm year - 31 Dec pre-election year IN WINDOW",
                {"IN WINDOW": INFO, "OUT OF WINDOW": INFO}))
def eg(L):
    from midterm_quant.strategies.equities import in_midterm_sweet_spot

    d = L.asof.date()
    election = max(x for x in config.MIDTERM_DATES if x <= d)
    window_start = dt.date(election.year, 10, 1)
    spx = L.yahoo("^GSPC")
    tdays = int(((spx.index > pd.Timestamp(election)) & (spx.index <= L.asof)).sum())
    return float((d - window_start).days), f"window day {(d - window_start).days}", f"trading day {tdays} after election day {election:%d %b %Y}; window opened {window_start:%d %b %Y}", "IN WINDOW" if in_midterm_sweet_spot(d) else "OUT OF WINDOW"


# ----------------------------------------------------------------------------- crypto --
@indicator(Spec("C-a", "Crypto", "Bitcoin Mayer multiple",
                "BTC price / 200-day average, completed UTC daily bars only", "Not a valuation model",
                "BTC-USD / SMA200", ("BTC-USD",), "ratio", "daily (UTC)", "< 0.8 DEEP VALUE; > 2.4 EUPHORIC; else above/below 1",
                {"DEEP VALUE": WATCH, "EUPHORIC": ALERT, "UPTREND": GOOD, "DOWNTREND": ALERT}))
def ca(L):
    s = L.yahoo("BTC-USD")
    mm = s.iloc[-1] / s.rolling(200).mean().iloc[-1]
    reg = "DEEP VALUE" if mm < 0.8 else "EUPHORIC" if mm > 2.4 else "UPTREND" if mm > 1 else "DOWNTREND"
    return mm, f"{mm:.2f}", f"BTC ${s.iloc[-1]:,.0f} (UTC bar {s.index[-1]:%d %b}), {ind.drawdown(s.to_numpy(), 365):.0%} from 1-year high", reg


@indicator(Spec("C-b", "Crypto", "Bitcoin 30-day realised volatility",
                "Annualised (365) stdev of daily log returns, UTC bars", "Realised, not implied", "rv30 * sqrt(365)",
                ("BTC-USD",), "percent", "daily (UTC)", "> 70% STRESS", {"STRESS": ALERT, "NEUTRAL": NEUTRAL}))
def cb(L):
    v = ind.realized_vol(L.yahoo("BTC-USD").to_numpy(), 30, 365)
    return v, f"{v:.0%}", "annualised", "STRESS" if v > 0.7 else "NEUTRAL"


@indicator(Spec("C-c", "Crypto", "ETH/BTC ratio",
                "Ether priced in bitcoin, 90-day change", "Relative performance only", "ETH/BTC; ret90",
                ("ETH-USD", "BTC-USD"), "ratio", "daily (UTC)", "> +10% ALT-SEASON", {"ALT-SEASON": INFO, "BTC DOMINANCE": INFO}))
def cc(L):
    e, b = L.yahoo("ETH-USD"), L.yahoo("BTC-USD")
    j = e.index.intersection(b.index)
    r = e[j] / b[j]
    ch = _pct(r, 90)
    return ch, f"{r.iloc[-1]:.4f}", f"{ch:+.0%} in 90 days", "ALT-SEASON" if ch > 0.10 else "BTC DOMINANCE"


@indicator(Spec("C-d", "Crypto", "Crypto equity vs bitcoin: COIN vs BTC",
                "63-day return of Coinbase shares minus bitcoin",
                "Not a clean U.S. regulatory sentiment index: mixes company earnings, equity beta and regulation; COIN trades 09:30-16:00 ET, BTC 24/7",
                "ret63(COIN) - ret63(BTC) on common dates", ("COIN", "BTC-USD"), "percent", "daily",
                "< -10% CRYPTO EQUITY LAGS", {"CRYPTO EQUITY LAGS": WATCH, "NEUTRAL": NEUTRAL},
                better="Event study of COIN/BTC around dated SEC/CFTC/congressional actions (needs a curated event list)"))
def cd(L):
    v = _rel(L, "COIN", "BTC-USD")
    return v, f"{v:+.1%}", "Coinbase minus bitcoin, 63 days", "CRYPTO EQUITY LAGS" if v < -0.10 else "NEUTRAL"


@indicator(Spec("C-e", "Crypto", "Stablecoin supply: level and 30-day growth",
                "Total USD-pegged stablecoins (DefiLlama), level and 30-day change", "History is restated by the source; past growth rates are not point-in-time",
                "level; level/level[-30] - 1", ("llama:stablecoins",), "USD", "daily (00:00 UTC snapshot)",
                "30-day growth > 0 INFLOW", {"INFLOW": GOOD, "OUTFLOW": ALERT}))
def ce(L):
    s = L.stablecoins()
    g = _pct(s, 30)
    d = s.iloc[-1] - s.iloc[-31]
    return g, f"${s.iloc[-1] / 1e9:,.0f}bn", f"30 days {g:+.1%} ({d / 1e9:+,.0f}bn)", "INFLOW" if g > 0 else "OUTFLOW"


@indicator(Spec("C-f", "Crypto", "Halving-cycle clock",
                "Days since the last halving and to the estimated next one", "The next halving date is an estimate from block times; the phase labels are in-sample (see C3)",
                "calendar arithmetic", (), "days", "daily", "phase by days since halving (in-sample boundaries)", {"INFO": INFO}))
def cf(L):
    today = L.asof.date()
    nxt = min(h for h in config.BTC_HALVINGS if h > today)
    return float((nxt - today).days), halving_phase(today).upper(), f"{(nxt - today).days} days to the estimated halving", "INFO"


# ----------------------------------------------------------------------------- energy --
@indicator(Spec("N-a", "Energy", "Brent minus WTI (front-month futures)",
                "Brent minus WTI continuous front-month futures, USD per barrel",
                "Not a pure war-risk premium: includes crude quality, location, freight, pipeline and contract-roll timing",
                "BZ=F - CL=F on common dates", ("BZ=F", "CL=F"), "USD per barrel", "daily", "> $6 WIDE",
                {"WIDE": WATCH, "NORMAL": NEUTRAL}, better="Freight-adjusted spread and tanker-insurance rates (licensed)"))
def na(L):
    b, w = L.yahoo("BZ=F"), L.yahoo("CL=F")
    j = b.index.intersection(w.index)
    sp = b[j].iloc[-1] - w[j].iloc[-1]
    return sp, f"${sp:.1f}", f"Brent ${b[j].iloc[-1]:.1f}, WTI ${w[j].iloc[-1]:.1f}; Brent {_pct(b, 63):+.0%} in 3 months", "WIDE" if sp > 6 else "NORMAL"


@indicator(Spec("N-b", "Energy", "Oil-fund roll proxy: USO vs USL",
                "63-day return of a front-month oil fund minus a 12-month-strip fund",
                "Not the futures curve: fund returns include roll timing, costs and USO's 2020 restructuring",
                "ret63(USO) - ret63(USL)", ("USO", "USL"), "percent", "daily", "> 0 FRONT OUTPERFORMING",
                {"FRONT OUTPERFORMING": INFO, "STRIP OUTPERFORMING": INFO}, better="N-f actual WTI contract curve"))
def nb(L):
    v = _rel(L, "USO", "USL")
    return v, f"{v:+.1%}", "front-month fund minus 12-month strip, 63 days", "FRONT OUTPERFORMING" if v > 0 else "STRIP OUTPERFORMING"


@indicator(Spec("N-f", "Energy", "WTI futures curve: 1st vs 12th contract",
                "Front WTI contract minus the contract 11 months later (NYMEX CL), USD per barrel", "Only the current curve can be rebuilt from free data; expired contracts are not available",
                "CL[1] - CL[12] on the asof date", ("CL contracts",), "USD per barrel", "daily",
                "> 0 BACKWARDATION; < 0 CONTANGO", {"BACKWARDATION": INFO, "CONTANGO": INFO}, declared="2026-11-06",
                missing="Expired contract histories are not available from the free source: MISSING for history."))
def nf(L):
    path = _contract_path(L, "CL", "NYM", 14)
    if len(path) < 12:
        raise MissingInput("CL contracts")
    (s1, p1, f1), (s12, p12, f12) = path[0], path[11]
    v = f1 - f12
    sign = "+" if v >= 0 else "-"
    return v, f"{sign}${abs(v):.2f}", f"{s1.split('.')[0]} ${f1:.2f} vs {s12.split('.')[0]} ${f12:.2f} ({v / f1:+.1%})", "BACKWARDATION" if v > 0 else "CONTANGO", {"curve": {s: px for s, _, px in path}}


@indicator(Spec("N-c", "Energy", "U.S. retail gasoline price",
                "EIA weekly regular-grade price and its 2-year percentile", "National average; regional prices differ",
                "GASREGW; percentile rank vs 104 weeks", ("fred:GASREGW",), "USD per gallon", "weekly (Monday)",
                "> $4.00 or > 70th percentile AFFORDABILITY PRESSURE", {"AFFORDABILITY PRESSURE": ALERT, "NEUTRAL": NEUTRAL}))
def nc(L):
    s = L.fred("GASREGW")
    pr = ind.percentile_rank(s.to_numpy(), 104)
    return s.iloc[-1], f"${s.iloc[-1]:.2f}", f"higher than {pr:.0%} of the past 2 years", "AFFORDABILITY PRESSURE" if s.iloc[-1] > 4.0 or pr > 0.7 else "NEUTRAL", {"pctile": pr}


@indicator(Spec("N-d", "Energy", "Oil shock detector (USO 20-day return z)",
                "z of the 20-day log return of USO vs a year of 20-day returns", "Fund returns include roll yield",
                "return_zscore(USO, 20, 250)", ("USO",), "z-score", "daily", "> +2 SPIKE; < -2 CRASH",
                {"SPIKE": ALERT, "CRASH": WATCH, "NORMAL": NEUTRAL}))
def nd(L):
    z = ind.return_zscore(L.yahoo("USO").to_numpy(), 20, 250)
    return z, f"{z:+.2f}", "vs a year of 20-day returns", "SPIKE" if z > 2 else "CRASH" if z < -2 else "NORMAL"


@indicator(Spec("N-e", "Energy", "Clean vs fossil energy equities",
                "63-day return of ICLN minus XLE", "Relative performance; clean energy is also rate-sensitive",
                "ret63(ICLN) - ret63(XLE)", ("ICLN", "XLE"), "percent", "daily", "> 0 CLEAN LEADS",
                {"CLEAN LEADS": INFO, "FOSSIL LEADS": INFO}))
def ne(L):
    v = _rel(L, "ICLN", "XLE")
    return v, f"{v:+.1%}", "clean minus fossil, 63 days", "CLEAN LEADS" if v > 0 else "FOSSIL LEADS"


# ----------------------------------------------------------------------------- metals --
@indicator(Spec("P-a", "Precious metals", "Gold trend",
                "Front-month gold futures vs 200-day average; drawdown from the all-time high", "Continuous front-month series, not roll-adjusted",
                "GC=F / SMA200 - 1", ("GC=F",), "USD per ounce", "daily", "below SMA200 DOWNTREND",
                {"DOWNTREND": ALERT, "UPTREND": GOOD}))
def pa(L):
    s = L.yahoo("GC=F")
    sma = s.rolling(200).mean().iloc[-1]
    return s.iloc[-1] / sma - 1, f"${s.iloc[-1]:,.0f}", f"{s.iloc[-1] / s.max() - 1:.0%} from high; {s.iloc[-1] / sma - 1:+.1%} vs 200-day", "UPTREND" if s.iloc[-1] > sma else "DOWNTREND"


@indicator(Spec("P-b", "Precious metals", "Gold/silver ratio",
                "Gold price / silver price, z vs 2 years", "Relative value, not a timing signal by itself",
                "GC=F / SI=F; z vs 504", ("GC=F", "SI=F"), "ratio", "daily", "z > +1 SILVER CHEAP; z < -1 SILVER RICH",
                {"SILVER CHEAP": INFO, "SILVER RICH": INFO, "NEUTRAL": NEUTRAL}))
def pb(L):
    g, s = L.yahoo("GC=F"), L.yahoo("SI=F")
    j = g.index.intersection(s.index)
    r = g[j] / s[j]
    z = _z(r, 504)
    return z, f"{r.iloc[-1]:.1f}", f"z {z:+.2f} vs 2 years", "SILVER CHEAP" if z > 1 else "SILVER RICH" if z < -1 else "NEUTRAL"


@indicator(Spec("P-c", "Precious metals", "Gold/oil price ratio (input-cost proxy)",
                "Ounces-of-gold-to-barrels ratio vs its 200-day average",
                "Not a miner margin: energy is one input among labour, royalties, sustaining capex; margins need company all-in sustaining costs",
                "GC=F / CL=F (CL > $5); vs SMA200", ("GC=F", "CL=F"), "ratio", "daily", "above SMA200 COST TAILWIND",
                {"COST TAILWIND": GOOD, "COST HEADWIND": WATCH},
                better="Company AISC and free cash flow from quarterly filings (not collected: no free structured source)"))
def pc(L):
    g, o = L.yahoo("GC=F"), L.yahoo("CL=F")
    j = g.index.intersection(o.index)
    r = (g[j] / o[j])[o[j] > 5]
    sma = r.rolling(200).mean().iloc[-1]
    return r.iloc[-1] / sma - 1, f"{r.iloc[-1]:.1f}", f"{r.iloc[-1] / sma - 1:+.0%} vs 200-day", "COST TAILWIND" if r.iloc[-1] > sma else "COST HEADWIND"


@indicator(Spec("P-d", "Precious metals", "Miners vs bullion: GDX vs GLD",
                "63-day return of gold miners minus gold", "Relative performance", "ret63(GDX) - ret63(GLD)",
                ("GDX", "GLD"), "percent", "daily", "> 0 CONFIRMING", {"CONFIRMING": GOOD, "DIVERGING": WATCH}))
def pd_(L):
    v = _rel(L, "GDX", "GLD")
    return v, f"{v:+.1%}", "miners minus bullion, 63 days", "CONFIRMING" if v > 0 else "DIVERGING"


@indicator(Spec("P-e", "Precious metals", "Platinum/gold ratio",
                "Platinum / gold futures, z vs 1 year", "Industrial demand proxy only", "PL=F / GC=F; z vs 252",
                ("PL=F", "GC=F"), "ratio", "daily", "z < -1 PGM WEAK", {"PGM WEAK": WATCH, "NEUTRAL": NEUTRAL}))
def pe(L):
    p, g = L.yahoo("PL=F"), L.yahoo("GC=F")
    j = p.index.intersection(g.index)
    r = p[j] / g[j]
    z = _z(r, 252)
    return z, f"{r.iloc[-1]:.3f}", f"z {z:+.2f} vs 1 year", "PGM WEAK" if z < -1 else "NEUTRAL"


ORDER = ["M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M9", "M10", "M11", "M12",
         "E-a", "E-b", "E-c", "E-d", "E-e", "E-f", "E-g",
         "C-a", "C-b", "C-c", "C-d", "C-e", "C-f",
         "N-a", "N-b", "N-f", "N-c", "N-d", "N-e",
         "P-a", "P-b", "P-c", "P-d", "P-e"]
ORIGINAL_33 = [c for c in ORDER if c not in ("M11", "M12", "N-f")]
assert len(ORDER) == 36 and set(ORDER) == set(SPECS)


def expected_bar_missing(name: str, last_obs: pd.Timestamp, asof: pd.Timestamp) -> bool:
    """A daily price series should have a bar dated ``asof``: crypto every UTC day, U.S.-listed
    instruments on every day SPY traded. A missing completed bar is a source gap."""
    kind = catalog._yahoo_kind(name) if not name.startswith(("fred:", "llama:", "derived:")) else None
    if kind == "crypto":
        return last_obs < asof
    if kind in ("us_listed",) or name in ("^GSPC", "^VIX", "^VIX3M"):
        spy = fetch_yahoo("SPY")["close"]
        return asof in spy.index and last_obs < asof
    return False


def _age_status(L: Loader, spec: Spec) -> tuple[str | None, int | None, str, list]:
    obs, worst, notes = None, "OK", []
    for name, u in L.used.items():
        if u["observation_date"] is None:
            continue
        o = pd.Timestamp(u["observation_date"])
        if obs is None or o < obs:
            obs = o
        if name.split(".")[-1] in ("CBT", "NYM", "CMX", "CME"):
            continue
        if (L.asof - o).days > catalog.max_age_days(name):
            worst = "STALE"
            notes.append(f"{name} last observation {o.date()} is older than its {catalog.max_age_days(name)}-day limit")
        elif expected_bar_missing(name, o, L.asof):
            worst = "STALE"
            notes.append(f"{name}: source has no completed bar for {L.asof.date()}; last bar {o.date()}")
    if obs is None:
        return None, None, worst, notes
    return obs.date().isoformat(), int((L.asof - obs).days), worst, notes


def read_one(code: str, asof=None, live: bool = True) -> Reading:
    spec = SPECS[code]
    asof = pd.Timestamp(asof or config.BACKTEST_END)
    L = Loader(asof, live)
    try:
        out = FUNCS[code](L)
        value_num, value, context, regime = out[:4]
        extra = out[4] if len(out) > 4 else {}
        if isinstance(value_num, float) and not math.isfinite(value_num):
            raise MissingInput("non-finite")
        obs, age, status, notes = _age_status(L, spec)
        if notes:
            extra = {**extra, "data_notes": notes}
    except Exception as exc:  # keep the dashboard alive if one source fails
        value_num, value, context, regime, extra = float("nan"), "n/a", f"missing input: {exc}", "MISSING", {}
        obs, age, status = None, None, "MISSING"
    tone = spec.tones.get(regime, NEUTRAL) if status == "OK" else ("stale" if status == "STALE" else "missing")
    return Reading(code, spec.group, spec.name, value, float(value_num), context, regime, tone, status, obs, age,
                   list(L.used.values()), spec.rule, spec.measures, spec.not_measures, spec.better, extra)


def read_all(asof=None, live: bool = True) -> list[Reading]:
    return [read_one(c, asof, live) for c in ORDER]
