"""Energy strategies (N1-N5).

Post-midterm thesis: oil carries a war-risk premium (US-Iran conflict, Hormuz flows ~70%
of pre-war). Election-day crude fell ~8% as the GOP blamed the war for its losses,
raising the odds of de-escalation; but the White House alone controls war policy and
tariffs. A Democratic Congress pushes clean energy, grid and data-centre oversight, and
probes oil/gas deals, yet cannot override vetoes. Gasoline at ~$4.15 keeps affordability
politics (SPR, export curbs, windfall-tax rhetoric) in play through the 2028 election.
"""
from __future__ import annotations

import numpy as np

from midterm_quant import indicators as ind
from midterm_quant.engine.base import TargetWeightStrategy


class N1OilTrendCurve(TargetWeightStrategy):
    CODE = "N1"
    NAME = "Crude trend + curve-shape filter"
    ASSET_CLASS = "Energy"
    ASSETS = ("USO",)
    SIGNALS = ("USL",)
    BENCHMARK = "USO"
    START = "2009-03-01"
    REBALANCE = "W"
    WARMUP = 260
    THESIS = "Supply shocks (war, OPEC+, sanctions) trend; only hold the trend when the futures curve agrees (front-month fund USO outperforming the 12-month strip USL = backwardation/tightening)."
    params = (("target_vol", 0.20), ("curve_lookback", 63))

    def target_weights(self):
        uso = self.series("USO", 260)
        usl = self.series("USL", self.p.curve_lookback + 2)
        score = ind.tsmom_score(uso, (63, 126, 252))
        curve = ind.pct_change(uso, self.p.curve_lookback) - ind.pct_change(usl, self.p.curve_lookback)
        size = ind.vol_target_weight(uso, self.p.target_vol, 60, cap=0.98)
        if score > 0 and curve > 0:
            return {"USO": size}
        if score < 0 and curve < 0:
            return {"USO": -size}
        return {"USO": 0.0}


class N2OilRiskPremiumFade(TargetWeightStrategy):
    CODE = "N2"
    NAME = "Geopolitical risk-premium fade"
    ASSET_CLASS = "Energy"
    ASSETS = ("USO",)
    SIGNALS = ("fred:GASREGW",)
    BENCHMARK = "USO"
    START = "2009-01-01"
    REBALANCE = "D"
    WARMUP = 520
    THESIS = "War-driven spikes that push pump prices into the politically painful zone invite offsets (SPR, diplomacy, OPEC+ barrels, demand loss) - fade +2-sigma spikes when gasoline is expensive; buy -2-sigma crashes."
    params = (("entry_z", 2.0), ("exit_z", 0.5), ("max_hold", 30), ("gas_pct", 0.7), ("target_vol", 0.20))

    def target_weights(self):
        uso = self.series("USO", 300)
        z = ind.return_zscore(uso, 20, 250)
        st = self.state
        side = st.get("side", 0)
        if side:
            st["days"] += 1
            done = (side > 0 and z > -self.p.exit_z) or (side < 0 and z < self.p.exit_z)
            if done or st["days"] >= self.p.max_hold:
                st["side"] = 0
                return {"USO": 0.0}
            return None
        size = ind.vol_target_weight(uso, self.p.target_vol, 20, cap=0.98)
        if z > self.p.entry_z:
            gas_rank = ind.percentile_rank(self.series("fred:GASREGW", 500), 500)
            if gas_rank > self.p.gas_pct:
                st.update(side=-1, days=0)
                return {"USO": -size}
        elif z < -self.p.entry_z:
            st.update(side=1, days=0)
            return {"USO": size}
        return None


class N3EnergyEquityVsCrude(TargetWeightStrategy):
    CODE = "N3"
    NAME = "E&P equities vs crude relative value"
    ASSET_CLASS = "Energy"
    ASSETS = ("XOP", "USO")
    BENCHMARK = "XLE"
    START = "2007-06-01"
    REBALANCE = "D"
    WARMUP = 130
    THESIS = "Producer equities discount the long-dated curve and policy risk (windfall-tax rhetoric, permitting, investigations); the spot crude risk premium moves faster. Trade stretched XOP/USO dislocations back to the mean."
    params = (("window", 60), ("entry", 2.0), ("exit", 0.5), ("stop", 4.0), ("max_hold", 40), ("leg", 0.4))

    def target_weights(self):
        ratio = np.log(self.series("XOP", 130) / self.series("USO", 130))
        z = ind.zscore(ratio, self.p.window)
        st = self.state
        if st.get("side"):
            st["days"] += 1
            if abs(z) < self.p.exit or abs(z) > self.p.stop or st["days"] >= self.p.max_hold:
                st["side"] = 0
                return {"XOP": 0.0, "USO": 0.0}
            return None
        if z > self.p.entry:
            st.update(side=-1, days=0)
            return {"XOP": -self.p.leg, "USO": self.p.leg}
        if z < -self.p.entry:
            st.update(side=1, days=0)
            return {"XOP": self.p.leg, "USO": -self.p.leg}
        return None


class N4CleanVsFossilRotation(TargetWeightStrategy):
    CODE = "N4"
    NAME = "Clean vs fossil policy rotation"
    ASSET_CLASS = "Energy"
    ASSETS = ("ICLN", "XLE")
    SIGNALS = ("^TNX",)
    BENCHMARK = "XLE"
    START = "2009-09-01"
    REBALANCE = "M"
    WARMUP = 260
    THESIS = "Congressional control shifts policy odds between clean and fossil energy (TAN +9% on election day), but clean energy is long-duration and rate-sensitive. Follow relative momentum, de-rate clean energy when yields jump."
    params = (("lookback", 63), ("rate_shock", 0.25))

    def target_weights(self):
        c, e = self.series("ICLN", 260), self.series("XLE", 260)
        tnx = self.series("^TNX", self.p.lookback + 2)
        rel = ind.pct_change(c, self.p.lookback) - ind.pct_change(e, self.p.lookback)
        dy = ind.diff(tnx, self.p.lookback)
        if rel > 0 and dy < self.p.rate_shock:
            w = {"ICLN": 1.0}
        elif rel > 0:
            w = {"ICLN": 0.5, "XLE": 0.5}
        else:
            w = {"XLE": 1.0}
        px = {"ICLN": c, "XLE": e}
        return {k: (v if px[k][-1] > ind.sma(px[k], 200) else v * 0.5) for k, v in w.items()}


class N5CrackSpreadSeasonal(TargetWeightStrategy):
    CODE = "N5"
    NAME = "Gasoline crack seasonal mean-reversion"
    ASSET_CLASS = "Energy"
    ASSETS = ("UGA", "USO")
    BENCHMARK = "USO"
    START = "2009-06-01"
    REBALANCE = "D"
    WARMUP = 260
    THESIS = "Gasoline is the political price (affordability was a top midterm issue). Cracks seasonally widen into the driving season and narrow after; enter only when the spread is stretched against the season."
    params = (("window", 250), ("entry", 1.0), ("leg", 0.4), ("max_hold", 60))

    def target_weights(self):
        spread = np.log(self.series("UGA", 260) / self.series("USO", 260))
        z = ind.zscore(spread, self.p.window)
        m = self.today.month
        st = self.state
        side = st.get("side", 0)
        if side:
            st["days"] += 1
            if (side > 0 and z >= 0) or (side < 0 and z <= 0) or st["days"] >= self.p.max_hold:
                st["side"] = 0
                return {"UGA": 0.0, "USO": 0.0}
            return None
        if m in (1, 2, 3) and z < -self.p.entry:
            st.update(side=1, days=0)
            return {"UGA": self.p.leg, "USO": -self.p.leg}
        if m in (8, 9, 10) and z > self.p.entry:
            st.update(side=-1, days=0)
            return {"UGA": -self.p.leg, "USO": self.p.leg}
        return None


STRATEGIES = [N1OilTrendCurve, N2OilRiskPremiumFade, N3EnergyEquityVsCrude, N4CleanVsFossilRotation, N5CrackSpreadSeasonal]
