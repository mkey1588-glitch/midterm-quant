"""Complete specifications of the 20 strategies (the 36 indicators live in research/monitor.SPECS).

Machine fields (assets, signals, units, release timing, rebalance, warm-up, parameters,
evidence level) are read from the strategy classes and the data catalogue, so they cannot
drift from the code. The hand-written fields below say what the code does in words and add
what code cannot: invalidation criteria and parameter provenance.

Shared execution rules (engine/base.py), true for every strategy:

* Decision time: the close of the first bar of each rebalance period - ISO week (W), calendar
  month (M) or every bar (D) - after WARMUP bars. Equities/ETFs: 16:00 ET. Crypto: the close of
  the UTC day (00:00 UTC). Stateful rules (entries/exits) are evaluated daily.
* Execution: market order filled at the next bar's open; legs that reduce exposure first;
  weight changes under 2pp skipped (5pp for E3); long weights capped at 98%, gross at 100%
  unless stated.
* Costs: one-way 2bp (core ETFs), 5bp (commodity and thematic ETFs), 15bp (crypto); 1%/yr
  borrow on shorts; idle cash earns the 3-month T-bill (DTB3).
* Inputs: FRED/DefiLlama values become usable on their ``available_at`` date; revision-prone
  FRED series use ALFRED first prints.
* Missing data: a price gap is filled with the last close (no look-ahead); FRED values persist
  until the next release; a series before its first observation is not used (``available``
  checks); inputs older than the catalogue's max age, or missing the decision day's bar at the
  source, are flagged in current_signals.md and on the page (the last value is carried forward).
"""
from __future__ import annotations

from midterm_quant.data import catalog
from midterm_quant.strategies import ALL

COMMON_INVALIDATION = ("Prospective review (docs/07): after 24 months of frozen paper trading, retire or demote the rule if its "
                       "information ratio against its primary benchmark is below -0.25, or if its drawdown exceeds 1.5x the "
                       "development-sample maximum drawdown at any time.")

TEXT = {
    "E1": dict(
        signal="sweet = (year mod 4 = 2 and month >= 10) or year mod 4 = 3; up = SPY close > SMA200(SPY close).",
        entry="Weight = 100% (sweet and up), 60% (sweet, not up), 70% (not sweet, up), 30% (neither); capped at 98%.",
        exit="No separate exit: the weekly target replaces the position; the remainder sits in T-bills.",
        invalidation="The seasonal tilt is the hypothesis: if the 2026-27 window underperforms SPY while SPY is above its 200-day average, drop the seasonal weights to the base case.",
        provenance="Weights and the 200-day window chosen before the first run by a researcher who knew the presidential-cycle literature (Hirsch 1967) and its sample; no variants tried.",
        primary="risk_matched"),
    "E2": dict(
        signal="For each of 9 sector SPDRs and 5 thematic ETFs with 253 bars: eligible if close > SMA200 and score > 0, score = 126-day return skipping the last 21 days / realised vol.",
        entry="Hold the top 3 eligible at 1/3 each; empty slots go to IEF if IEF > its SMA200, else T-bills.",
        exit="Monthly re-ranking replaces holdings.",
        invalidation="Thematic universe chosen with 2026 hindsight (survivorship). Retire if it trails the equal-weight sector basket over the prospective window.",
        provenance="Top-3, 126/21 lookback and the thematic list set before the first run; no variants tried. The thematic list itself is a selection made with knowledge of 2020-2026 themes.",
        primary="risk_matched"),
    "E3": dict(
        signal="rv = max(rv20, rv60) of SPY (252-day annualisation); w = min(0.98, 12% / rv); halved if VIX / VIX3M > 1.",
        entry="Daily evaluation; trade only if the weight changes by at least 5pp.",
        exit="Continuous resizing; no discrete exit.",
        invalidation="If VIX3M stops being published or the ratio rule halves exposure more than 25% of days, review.",
        provenance="12% target and the inversion threshold of 1.0 set before the first run; no variants tried.",
        primary="risk_matched"),
    "E4": dict(
        signal="score = [RSP/QQQ > SMA100 of the ratio] + [10Y yield (^TNX) 20-day change < 0] + [IWM 63-day return > QQQ 63-day return].",
        entry="Allocation by score: 3 -> RSP 50/IWM 50; 2 -> RSP 70/QQQ 30; 1 -> RSP 30/QQQ 70; 0 -> QQQ 100. Halve all if RSP and QQQ are both below SMA200.",
        exit="Weekly re-scoring replaces the allocation.",
        invalidation="Turnover is ~16x a year: retire if net-of-cost information ratio is negative over the prospective window.",
        provenance="Score components and the allocation table set before the first run; no variants tried.",
        primary="risk_matched"),
    "E5": dict(
        signal="RSI(2) of SPY (Cutler, simple averages); credit = z of the 10-day change of log(HYG/IEF) vs 250 such changes.",
        entry="When flat: buy 98% SPY if RSI(2) < 10 and (SPY > SMA200 or credit z > -1).",
        exit="Close when SPY > SMA5, or after 10 days, or on a -8% loss from entry.",
        invalidation="Retire if the average trade's return net of costs turns negative over 30 prospective trades.",
        provenance="RSI(2) < 10 and the 5-day exit are the textbook Connors settings; the credit filter was added before the first run; no variants tried.",
        primary="risk_matched"),
    "C1": dict(
        signal="For BTC and ETH with 125 bars: score = share of {20, 60, 120}-day returns > 0; vol scale = min(1, 60% / rv30 (365-day annualisation)).",
        entry="Weight per coin = (1 / number of live coins) x score x vol scale.",
        exit="Weekly resizing; weight 0 when all horizons are negative.",
        invalidation=COMMON_INVALIDATION,
        provenance="Lookbacks and the 60% vol target set before the first run; no variants tried.",
        primary="risk_matched"),
    "C2": dict(
        signal="liq_up = net liquidity (WALCL - WDTGAL - RRP, same Wednesday, USD bn) above its value 91 days earlier; usd_weak = DTWEXBGS < SMA100; trend = BTC > SMA100.",
        entry="BTC weight = 0.4 x liq_up + 0.3 x usd_weak + 0.3 x trend.",
        exit="Weekly re-scoring.",
        invalidation="The liquidity link is empirical (2015-2026 only). Retire if the liquidity leg's contribution is negative over the prospective window.",
        provenance="v1 weights set before the first run; v2 (6 Nov 2026) changed only the net-liquidity definition after review and was adopted before its result was seen.",
        primary="risk_matched"),
    "C3": dict(
        signal="Phase by days since the last halving: expansion < 540, bear 540-900, accumulation > 900; trend = BTC > SMA200.",
        entry="Weight = 100% / 20% / 70% by phase, halved below the 200-day average.",
        exit="Weekly re-evaluation.",
        invalidation="IN-SAMPLE RESEARCH: not eligible for capital. Only the April 2028 halving and the cycle after it can test the phase boundaries.",
        provenance="Boundaries chosen by looking at where the 2017, 2021 and 2025 tops fell after their halvings; three cycles.",
        primary="risk_matched"),
    "C4": dict(
        signal="Eligible coins: 90-day return > 0 and price > SMA100; score = risk-adjusted 30-day + 90-day momentum (365-day annualisation).",
        entry="Hold the top 2 eligible, inverse-30-day-vol weighted; cash if none.",
        exit="Weekly re-ranking.",
        invalidation=COMMON_INVALIDATION,
        provenance="Set before the first run; no variants tried. SOL history starts 2020, so the universe grew during the sample.",
        primary="risk_matched"),
    "C5": dict(
        signal="g30, g90 = 30- and 90-day growth of total USD stablecoin supply; trend = BTC > SMA100.",
        entry="w = 0.5 x [g30 > 0] + 0.25 x [g30 > g90 / 3] + 0.25 x trend; split 70% BTC / 30% ETH.",
        exit="Weekly re-scoring.",
        invalidation="Stablecoin history is restated by DefiLlama, so the backtest is not point-in-time. Treat the prospective record (with saved daily snapshots) as the only valid test.",
        provenance="Replacement for the failed C5a; 4 configurations tried (lookback 14/30/60, trend leg on/off), 30-day with trend adopted.",
        primary="risk_matched"),
    "N1": dict(
        signal="TSMOM score over 63/126/252 days on USO; curve proxy = USO 63-day return - USL 63-day return.",
        entry="Long USO at 20%-vol size if score > 0 and proxy > 0; short if both < 0.",
        exit="Flat when the two disagree; weekly.",
        invalidation="No development-sample edge (Sharpe below zero). Kept only as a war-shock hedge; its incremental value to the energy blend is reported and is the test.",
        provenance="Pre-specified; 4 variants tried and not adopted (horizon agreement, long-only, no curve filter).",
        primary="risk_matched"),
    "N2": dict(
        signal="z = USO 20-day log return vs 250 such returns; gasoline percentile = GASREGW rank vs 500 weekly-filled days.",
        entry="Short USO at 20%-vol size if z > +2 and gasoline above its 70th percentile; long if z < -2.",
        exit="Close when z re-crosses +/-0.5 or after 30 days.",
        invalidation="No development-sample edge. Retire unless it lowers the energy blend's drawdown in the prospective window.",
        provenance="Pre-specified; 4 short-only variants tried and not adopted.",
        primary="risk_matched"),
    "N3": dict(
        signal="z = 60-day z-score of log(XOP / USO).",
        entry="z > +2: short XOP 40% / long USO 40%; z < -2: the reverse.",
        exit="Close at |z| < 0.5, |z| > 4 (stop) or after 40 days.",
        invalidation="Market-neutral: compare with cash. Retire if it loses money over the prospective window net of costs.",
        provenance="Pre-specified; no variants tried.",
        primary="cash"),
    "N4": dict(
        signal="rel = ICLN 63-day return - XLE 63-day return; dy = 63-day change in ^TNX.",
        entry="rel > 0 and dy < 25bp: ICLN 100%; rel > 0 and dy >= 25bp: 50/50; else XLE 100%. Halve any leg below its SMA200.",
        exit="Monthly re-evaluation.",
        invalidation=COMMON_INVALIDATION,
        provenance="Pre-specified; no variants tried.",
        primary="risk_matched"),
    "N5": dict(
        signal="z = 250-day z-score of log(UGA / USO).",
        entry="Jan-Mar and z < -1: long UGA 40% / short USO 40%; Aug-Oct and z > +1: the reverse.",
        exit="Close when z crosses 0 or after 60 days.",
        invalidation="Market-neutral: compare with cash. UGA liquidity limits size; retire if fills deviate from modelled costs by more than 10bp.",
        provenance="Pre-specified; no variants tried.",
        primary="cash"),
    "P1": dict(
        signal="trend = mean of [GLD > SMA50, GLD > SMA200, 126-day return > 0]; real-yield tilt from the 63-day change in DFII10; dollar tilt from the 63-day % change in DTWEXBGS.",
        entry="GLD weight = 0.6 x trend + 0.2 x real-yield tilt + 0.2 x dollar tilt.",
        exit="Weekly re-scoring.",
        invalidation=COMMON_INVALIDATION,
        provenance="Pre-specified; no variants tried. DTWEXBGS first prints exist only from March 2019.",
        primary="risk_matched"),
    "P2": dict(
        signal="z = 504-day z-score of log(GLD / SLV).",
        entry="Silver weight = clip(0.5 + 0.25 z, 0, 1); gold the rest; halve both if both are below SMA200.",
        exit="Weekly re-weighting.",
        invalidation=COMMON_INVALIDATION,
        provenance="Pre-specified; no variants tried.",
        primary="risk_matched"),
    "P3": dict(
        signal="gold_up = GLD > SMA200; ratio = GLD / USO above its SMA200; GDX > SMA200.",
        entry="All three: GDX 100%; gold_up only: GLD 100%; else cash.",
        exit="Weekly re-evaluation.",
        invalidation="Revised after P3a failed. The gold/oil ratio is not a miner-margin measure; retire if miner AISC data (when collected) contradicts the signal.",
        provenance="Revision of P3a; 2 configurations tried (GDX gate on/off), gate on adopted.",
        primary="risk_matched"),
    "P4": dict(
        signal="stress = mean of the available z-scores: 30-day EPU vs 756 days, VIX vs 252 days, 63-day term-premium change vs 756.",
        entry="GLD weight = 0.10 + 0.88 x sigmoid(1.5 x stress), x 0.6 if GLD is below SMA200.",
        exit="Weekly re-scoring.",
        invalidation=COMMON_INVALIDATION,
        provenance="Pre-specified; no variants tried. EPU and term-premium first prints exist only from 2014 and 2016.",
        primary="risk_matched"),
    "P5": dict(
        signal="For GLD, SLV, PPLT, PALL with 253 bars: eligible if 126-day return > 0 and price > SMA200; score = risk-adjusted 126-day momentum.",
        entry="Hold the top 2 eligible, inverse-63-day-vol weighted; cash if none.",
        exit="Monthly re-ranking.",
        invalidation=COMMON_INVALIDATION,
        provenance="Pre-specified; no variants tried.",
        primary="risk_matched"),
}

DECISION = {"D": "close of every bar", "W": "close of the first bar of each ISO week", "M": "close of the first bar of each month"}


def strategy_spec(cls) -> dict:
    t = TEXT[cls.CODE]
    inputs = []
    for name in list(cls.ASSETS) + list(cls.SIGNALS) + ["fred:DTB3"]:
        m = catalog.meta(name)
        inputs.append({"series": name, "role": "traded" if name in cls.ASSETS else ("cash rate" if name == "fred:DTB3" else "signal"),
                       "units": m.units, "frequency": m.frequency, "release": m.release, "available_rule": m.available_rule,
                       "revisions": m.revisions})
    params = {k: getattr(cls.params, k) for k in cls.params._getkeys()} if hasattr(cls.params, "_getkeys") else {}
    return {
        "code": cls.CODE, "name": cls.NAME, "class": cls.ASSET_CLASS, "version": cls.VERSION, "evidence": cls.EVIDENCE,
        "thesis": cls.THESIS, "inputs": inputs, "signal": t["signal"], "entry": t["entry"], "exit": t["exit"],
        "calendar": "UTC days, 7 per week" if cls.CALENDAR == "crypto" else "NYSE trading days",
        "decision_time": DECISION[cls.REBALANCE], "execution": "market order at the next bar's open",
        "warmup_bars": cls.WARMUP, "trading_starts": cls.START, "max_long": cls.MAX_LONG, "max_gross": cls.MAX_GROSS,
        "parameters": {k: (list(v) if isinstance(v, tuple) else v) for k, v in params.items()
                       if k not in ("inception", "trade_start", "cash_rate")},
        "min_trade": params.get("min_trade", 0.02),
        "invalidation": t["invalidation"], "provenance": t["provenance"] + " " + cls.PROVENANCE,
        "missing_data": "Engine rules (see module docstring); strategy-specific: " + (
            "uses `available()` guards for late-starting series." if "available(" in __import__("inspect").getsource(cls) else "no late-starting inputs."),
        "benchmark_reference": cls.BENCHMARK, "benchmark_primary": t["primary"],
    }


def all_specs() -> list[dict]:
    return [strategy_spec(c) for c in ALL]
