"""Trial registry: every strategy configuration that has been backtested on the development data.

Multiple-testing corrections need the *number of attempts*, not just the survivors. This module
re-creates every configuration run during development (4 Nov 2026, recovered verbatim from the
session record) plus the changes made in the 6 Nov review iteration, so that

* the deflated Sharpe ratio can use the true trial count (``N_TRIALS``);
* earlier parameters and earlier results are preserved next to the adopted ones;
* nobody can relabel development data as a holdout: every trial below used data through
  4-5 Nov 2026.

``recorded`` holds the figures as printed at the time (daily-return Sharpe vs T-bills, the
4 Nov engine). ``scripts/run_trials.py`` re-runs every trial on the current engine and the
standardised evaluation, and writes both to ``reports/evidence/trial_registry.csv``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from midterm_quant import indicators as ind
from midterm_quant.engine.base import TargetWeightStrategy
from midterm_quant.strategies import crypto, energy, equities, metals


# ---- variant classes, verbatim logic from the 4 Nov development scripts ---------------------
class N1b(energy.N1OilTrendCurve):
    CODE, NAME = "N1b", "N1 variant (horizon agreement / long-only / no curve)"
    params = (("agree", 1.0), ("long_only", False), ("use_curve", True))

    def target_weights(self):
        uso = self.series("USO", 260)
        usl = self.series("USL", 65)
        score = ind.tsmom_score(uso, (63, 126, 252))
        curve = ind.pct_change(uso, 63) - ind.pct_change(usl, 63)
        if not self.p.use_curve:
            curve = score
        size = ind.vol_target_weight(uso, 0.20, 60, cap=0.98)
        if score >= self.p.agree and curve > 0:
            return {"USO": size}
        if score <= -self.p.agree and curve < 0 and not self.p.long_only:
            return {"USO": -size}
        return {"USO": 0.0}


class N2s(energy.N2OilRiskPremiumFade):
    CODE, NAME = "N2s", "N2 short-only variant"

    def target_weights(self):
        uso = self.series("USO", 300)
        z = ind.return_zscore(uso, 20, 250)
        st = self.state
        if st.get("side"):
            st["days"] += 1
            if z < self.p.exit_z or st["days"] >= self.p.max_hold:
                st["side"] = 0
                return {"USO": 0.0}
            return None
        if z > self.p.entry_z and ind.percentile_rank(self.series("fred:GASREGW", 500), 500) > self.p.gas_pct:
            st.update(side=-1, days=0)
            return {"USO": -ind.vol_target_weight(uso, self.p.target_vol, 20, cap=0.98)}
        return None


class P3b(metals.P3MinerMarginRotation):
    CODE, NAME = "P3b", "P3 revision candidate (gold/oil ratio, optional GDX gate)"
    params = (("gdx_trend", True),)

    def target_weights(self):
        gdx, gld, uso = self.series("GDX", 210), self.series("GLD", 210), self.series("USO", 210)
        gold_up = gld[-1] > ind.sma(gld, 200)
        go = gld / uso
        margin_up = go[-1] > ind.sma(go, 200)
        gdx_ok = gdx[-1] > ind.sma(gdx, 200) if self.p.gdx_trend else True
        if gold_up and margin_up and gdx_ok:
            return {"GDX": 1.0, "GLD": 0.0}
        if gold_up:
            return {"GLD": 1.0, "GDX": 0.0}
        return {"GLD": 0.0, "GDX": 0.0}


class C5x(TargetWeightStrategy):
    CODE, NAME = "C5x", "Stablecoin impulse candidates"
    ASSET_CLASS = "Crypto"
    ASSETS = ("BTC-USD", "ETH-USD")
    SIGNALS = ("llama:stablecoins",)
    CALENDAR, BENCHMARK, START, REBALANCE, WARMUP = "crypto", "BTC-USD", "2018-06-01", "W", 120
    params = (("lb", 30), ("trend", True))

    def target_weights(self):
        sc = self.series("llama:stablecoins", 120)
        if not self.available("llama:stablecoins", 100):
            return {}
        g, g90 = ind.pct_change(sc, self.p.lb), ind.pct_change(sc, 90)
        w = 0.0
        if g > 0:
            w += 0.5
        if g > g90 / 3:
            w += 0.25
        btc = self.series("BTC-USD", 101)
        if self.p.trend:
            w += 0.25 * (btc[-1] > ind.sma(btc, 100))
        return {"BTC-USD": w * 0.7, "ETH-USD": w * 0.3}


class N1x(TargetWeightStrategy):
    CODE, NAME = "N1x", "Energy-complex TSMOM (not adopted)"
    ASSET_CLASS = "Energy"
    ASSETS = ("USO", "UGA", "UNG", "XLE")
    BENCHMARK, START, REBALANCE, WARMUP, MAX_GROSS = "USO", "2009-03-01", "W", 260, 1.5
    params = (("tv", 0.10), ("agree", 0.3))

    def target_weights(self):
        w = {}
        for a in self.ASSETS:
            if not self.available(a, 253):
                continue
            px = self.series(a, 260)
            s = ind.tsmom_score(px, (63, 126, 252))
            if abs(s) < self.p.agree:
                w[a] = 0.0
                continue
            w[a] = np.sign(s) * ind.vol_target_weight(px, self.p.tv, 60, cap=0.6)
        return w


class N2x(TargetWeightStrategy):
    CODE, NAME = "N2x", "Brent-WTI spread reversion (not adopted)"
    ASSET_CLASS = "Energy"
    ASSETS = ("BNO", "USO")
    BENCHMARK, START, REBALANCE, WARMUP = "USO", "2011-06-01", "D", 130
    params = (("window", 120), ("entry", 2.0), ("exit", 0.5), ("max_hold", 40), ("leg", 0.45), ("stop", 4.0))

    def target_weights(self):
        z = ind.zscore(np.log(self.series("BNO", 130) / self.series("USO", 130)), self.p.window)
        st = self.state
        if st.get("side"):
            st["days"] += 1
            if abs(z) < self.p.exit or abs(z) > self.p.stop or st["days"] >= self.p.max_hold:
                st["side"] = 0
                return {"BNO": 0.0, "USO": 0.0}
            return None
        if z > self.p.entry:
            st.update(side=-1, days=0)
            return {"BNO": -self.p.leg, "USO": self.p.leg}
        if z < -self.p.entry:
            st.update(side=1, days=0)
            return {"BNO": self.p.leg, "USO": -self.p.leg}
        return None


# ---- the registry ----------------------------------------------------------------------------
@dataclass
class Trial:
    trial_id: str
    family: str              # the strategy slot the trial competed for
    cls: type
    params: dict = field(default_factory=dict)
    status: str = ""         # adopted | rejected | superseded | in-sample research | not adopted
    when: str = "2026-11-04"
    recorded: dict = field(default_factory=dict)   # CAGR, Sharpe, MaxDD as printed at the time
    note: str = ""


def _r(cagr, sh, dd):
    return {"CAGR": cagr, "Sharpe": sh, "MaxDD": dd}


E, C, N, P = equities, crypto, energy, metals
TRIALS: list[Trial] = [
    # first full run of the book, 4 Nov 2026 19:06 UTC (engine before the rejected-buy retry fix)
    Trial("E1", "E1", E.E1PresidentialCycleTrend, status="adopted", recorded=_r(0.095, 0.64, -0.250)),
    Trial("E2", "E2", E.E2PolicySectorMomentum, status="adopted", recorded=_r(0.074, 0.40, -0.321),
          note="18 rejected buys in the first run; the engine's retry fix lifted CAGR to 7.8% with no rule change."),
    Trial("E3", "E3", E.E3VolTargetTermStructure, status="adopted", recorded=_r(0.081, 0.70, -0.176)),
    Trial("E4", "E4", E.E4BroadeningRotation, status="adopted", recorded=_r(0.109, 0.61, -0.364)),
    Trial("E5", "E5", E.E5PoliticalShockReversal, status="adopted", recorded=_r(0.083, 0.69, -0.224)),
    Trial("C1", "C1", C.C1CryptoTrendVolTarget, status="adopted", recorded=_r(0.587, 1.29, -0.543)),
    Trial("C2v1", "C2", C.C2v1LiquidityRegimeBTC, status="superseded", recorded=_r(0.541, 1.22, -0.563),
          note="Superseded on 6 Nov for a data-definition error (week-average TGA), not for performance."),
    Trial("C3", "C3", C.C3HalvingCycle, status="in-sample research", recorded=_r(0.831, 1.49, -0.455),
          note="Phase boundaries chosen with knowledge of the 2017/2021/2025 tops."),
    Trial("C4", "C4", C.C4CryptoRotation, status="adopted", recorded=_r(0.400, 0.84, -0.661)),
    Trial("C5a", "C5", C.C5aShockReversal, status="rejected", recorded=_r(-0.012, -0.03, -0.456)),
    Trial("N1", "N1", N.N1OilTrendCurve, status="adopted", recorded=_r(-0.014, -0.06, -0.544), note="Kept as pre-specified despite no edge."),
    Trial("N2", "N2", N.N2OilRiskPremiumFade, status="adopted", recorded=_r(-0.007, -0.22, -0.405), note="Kept as pre-specified despite no edge."),
    Trial("N3", "N3", N.N3EnergyEquityVsCrude, status="adopted", recorded=_r(0.020, 0.10, -0.304)),
    Trial("N4", "N4", N.N4CleanVsFossilRotation, status="adopted", recorded=_r(0.093, 0.45, -0.449)),
    Trial("N5", "N5", N.N5CrackSpreadSeasonal, status="adopted", recorded=_r(0.030, 0.33, -0.082)),
    Trial("P1", "P1", P.P1GoldMacroTrend, status="adopted", recorded=_r(0.075, 0.54, -0.290)),
    Trial("P2", "P2", P.P2GoldSilverRatio, status="adopted", recorded=_r(0.088, 0.45, -0.551)),
    Trial("P3a", "P3", P.P3aMinerMomentum, status="rejected", recorded=_r(0.028, 0.18, -0.688)),
    Trial("P4", "P4", P.P4PolicyStressGold, status="adopted", recorded=_r(0.053, 0.40, -0.241)),
    Trial("P5", "P5", P.P5PreciousRotation, status="adopted", recorded=_r(0.089, 0.45, -0.475)),
    # variant sweeps, 4 Nov 2026 19:08-19:10 UTC
    Trial("C5a-v1", "C5", C.C5aShockReversal, {"trend_floor": 1.0}, "rejected", recorded=_r(0.036, 0.17, -0.354)),
    Trial("C5a-v2", "C5", C.C5aShockReversal, {"trend_floor": 1.0, "shock_z": -2.0}, "rejected", recorded=_r(0.091, 0.40, -0.394)),
    Trial("C5a-v3", "C5", C.C5aShockReversal, {"trend_floor": 1.0, "shock_z": -3.0}, "rejected", recorded=_r(0.031, 0.14, -0.279)),
    Trial("C5a-v4", "C5", C.C5aShockReversal, {"trend_floor": 1.0, "max_hold": 3}, "rejected", recorded=_r(0.084, 0.48, -0.169)),
    Trial("C5a-v5", "C5", C.C5aShockReversal, {"trend_floor": 1.0, "max_hold": 14}, "rejected", recorded=_r(0.017, 0.09, -0.360)),
    Trial("N1b-1", "N1", N1b, {"agree": 1.0}, "not adopted", recorded=_r(0.000, -0.02, -0.498)),
    Trial("N1b-2", "N1", N1b, {"agree": 1.0, "long_only": True}, "not adopted", recorded=_r(0.005, -0.05, -0.277)),
    Trial("N1b-3", "N1", N1b, {"agree": 1.0, "use_curve": False}, "not adopted", recorded=_r(0.014, 0.08, -0.502)),
    Trial("N1b-4", "N1", N1b, {"agree": 0.3, "long_only": True}, "not adopted", recorded=_r(0.009, 0.02, -0.271)),
    Trial("N2s-1", "N2", N2s, {}, "not adopted", recorded=_r(0.009, -0.13, -0.110)),
    Trial("N2s-2", "N2", N2s, {"gas_pct": 0.0}, "not adopted", recorded=_r(0.000, -0.14, -0.369)),
    Trial("N2s-3", "N2", N2s, {"entry_z": 1.5}, "not adopted", recorded=_r(0.012, -0.02, -0.172)),
    Trial("N2s-4", "N2", N2s, {"max_hold": 60}, "not adopted", recorded=_r(0.009, -0.13, -0.110)),
    Trial("P3", "P3", P.P3MinerMarginRotation, status="adopted", recorded=_r(0.054, 0.28, -0.453),
          note="Recorded as 'P3b gold/oil ratio {}' - identical rule to the adopted P3."),
    Trial("P3b-1", "P3", P3b, {"gdx_trend": False}, "not adopted", recorded=_r(0.058, 0.29, -0.559)),
    Trial("C5", "C5", C.C5StablecoinImpulse, status="adopted", recorded=_r(0.446, 1.02, -0.468),
          note="Recorded as 'C5x stablecoin {}' - identical rule to the adopted C5."),
    Trial("C5x-1", "C5", C5x, {"lb": 14}, "not adopted", recorded=_r(0.347, 0.88, -0.626)),
    Trial("C5x-2", "C5", C5x, {"lb": 60}, "not adopted", recorded=_r(0.424, 0.93, -0.471)),
    Trial("C5x-3", "C5", C5x, {"trend": False}, "not adopted", recorded=_r(0.322, 0.91, -0.392)),
    Trial("N1x-1", "N-alt", N1x, {}, "not adopted", recorded=_r(-0.018, -0.02, -0.751)),
    Trial("N1x-2", "N-alt", N1x, {"agree": 1.0}, "not adopted", recorded=_r(0.027, 0.16, -0.689)),
    Trial("N1x-3", "N-alt", N1x, {"tv": 0.08}, "not adopted", recorded=_r(-0.010, -0.02, -0.684)),
    Trial("N2x-1", "N-alt", N2x, {}, "not adopted", recorded=_r(0.005, -0.28, -0.187)),
    Trial("N2x-2", "N-alt", N2x, {"window": 60}, "not adopted", recorded=_r(-0.010, -0.60, -0.289)),
    Trial("N2x-3", "N-alt", N2x, {"entry": 1.5}, "not adopted", recorded=_r(0.003, -0.29, -0.189)),
    # review iteration, 6 Nov 2026: definitional fix decided before the run, adopted regardless of result
    Trial("C2", "C2", C.C2LiquidityRegimeBTC, status="adopted", when="2026-11-06",
          note="v2: Wednesday-consistent net liquidity in USD bn (WDTGAL + same-day RRP)."),
]

N_TRIALS = len(TRIALS)
assert N_TRIALS == 46 and len({t.trial_id for t in TRIALS}) == N_TRIALS
