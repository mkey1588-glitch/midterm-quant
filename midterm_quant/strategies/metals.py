"""Precious-metal strategies (P1-P5).

Post-midterm thesis: gold blew off to ~$5,300-5,600 in Jan 2026 and corrected ~27% to
<$3,900 by 30 Oct before bouncing on the result. Structural bid (central banks bought
675t YTD), fiscal stress ($40tn debt, ~6% of GDP deficits, a 2027 debt-limit fight) and
Fed-independence questions are offset by 2.6% real yields and a firm dollar. A Democratic
Senate now vets Fed nominees, lowering the 'politicised Fed' tail that drove the 2025-26
melt-up; silver/PGMs are the high-beta, industrially exposed sleeve.
"""
from __future__ import annotations

import math

import numpy as np

from midterm_quant import indicators as ind
from midterm_quant.engine.base import TargetWeightStrategy


class P1GoldMacroTrend(TargetWeightStrategy):
    CODE = "P1"
    NAME = "Gold trend with real-yield/USD tilt"
    ASSET_CLASS = "Precious Metals"
    ASSETS = ("GLD",)
    SIGNALS = ("fred:DFII10", "fred:DTWEXBGS")
    BENCHMARK = "GLD"
    START = "2007-03-01"
    REBALANCE = "W"
    WARMUP = 210
    THESIS = "Trend carries most of the weight (the real-yield link broke after 2022 as central banks bought), with tilts toward gold when real yields and the dollar are falling."
    params = (("w_trend", 0.6), ("w_real", 0.2), ("w_usd", 0.2), ("ry_scale", 0.5), ("usd_scale", 0.03))

    def target_weights(self):
        g = self.series("GLD", 210)
        trend = np.mean([g[-1] > ind.sma(g, 50), g[-1] > ind.sma(g, 200), ind.pct_change(g, 126) > 0])
        dry = ind.diff(self.series("fred:DFII10", 70), 63)
        tilt_r = (1.0 - ind.clip(dry / self.p.ry_scale, -1, 1)) / 2 if math.isfinite(dry) else 0.5
        tilt_d = 0.5
        if self.available("fred:DTWEXBGS", 70):
            dusd = ind.pct_change(self.series("fred:DTWEXBGS", 70), 63)
            tilt_d = (1.0 - ind.clip(dusd / self.p.usd_scale, -1, 1)) / 2
        return {"GLD": self.p.w_trend * trend + self.p.w_real * tilt_r + self.p.w_usd * tilt_d}


class P2GoldSilverRatio(TargetWeightStrategy):
    CODE = "P2"
    NAME = "Gold/silver ratio reversion"
    ASSET_CLASS = "Precious Metals"
    ASSETS = ("GLD", "SLV")
    BENCHMARK = "GLD"
    START = "2008-09-01"
    REBALANCE = "W"
    WARMUP = 520
    THESIS = "Silver's 55% crash from the Jan-2026 peak pushed the gold/silver ratio up; the ratio mean-reverts over 1-2 year horizons. Tilt the metal sleeve toward the cheap metal, halve exposure when both are below trend."
    params = (("window", 504), ("slope", 0.25))

    def target_weights(self):
        if not (self.available("SLV", self.p.window) and self.available("GLD", self.p.window)):
            return {"GLD": 0.5}
        g, s = self.series("GLD", self.p.window), self.series("SLV", self.p.window)
        z = ind.zscore(np.log(g / s), self.p.window)
        w_s = ind.clip(0.5 + self.p.slope * z, 0.0, 1.0)
        scale = 0.5 if (g[-1] < ind.sma(g, 200) and s[-1] < ind.sma(s, 200)) else 1.0
        return {"GLD": (1.0 - w_s) * scale, "SLV": w_s * scale}


class P3MinerMarginRotation(TargetWeightStrategy):
    CODE = "P3"
    EVIDENCE = "D2"
    PROVENANCE = "Revision of P3a after P3a's -72% drawdown; 2 configurations tried (GDX trend gate on/off); gate on adopted. The gold/oil ratio is an input-cost proxy, not a miner-margin measure."
    NAME = "Miner margin rotation (gold/oil ratio)"
    ASSET_CLASS = "Precious Metals"
    ASSETS = ("GDX", "GLD")
    SIGNALS = ("USO",)
    BENCHMARK = "GLD"
    START = "2007-06-01"
    REBALANCE = "W"
    WARMUP = 210
    THESIS = "Miner margins = gold price minus costs, ~20-25% of which is energy, so the gold/oil ratio is the margin proxy. The war oil spike crushed it; election-day oil -8% sent GDX +6.7%. Own miners only when gold, the gold/oil ratio and GDX all trend up; bullion when only gold does; cash otherwise."
    params = (("sma", 200),)

    def target_weights(self):
        n = self.p.sma
        gdx, gld, uso = self.series("GDX", n), self.series("GLD", n), self.series("USO", n)
        gold_up = gld[-1] > ind.sma(gld, n)
        ratio = gld / uso
        margin_up = ratio[-1] > ind.sma(ratio, n)
        if gold_up and margin_up and gdx[-1] > ind.sma(gdx, n):
            return {"GDX": 1.0, "GLD": 0.0}
        if gold_up:
            return {"GLD": 1.0, "GDX": 0.0}
        return {"GLD": 0.0, "GDX": 0.0}


class P3aMinerMomentum(TargetWeightStrategy):
    """REJECTED first specification of P3 (kept for the research log).

    Gold 3m momentum minus 0.25x oil momentum. Whipsawed through the 2011-15 miner
    bear market: 2007-2026 CAGR +2.4%, max drawdown -72%.
    """

    CODE = "P3a"
    NAME = "Miner momentum rotation (rejected)"
    ASSET_CLASS = "Precious Metals"
    ASSETS = ("GDX", "GLD")
    SIGNALS = ("USO",)
    BENCHMARK = "GLD"
    START = "2007-06-01"
    REBALANCE = "W"
    WARMUP = 210
    params = (("lookback", 63), ("energy_share", 0.25))

    def target_weights(self):
        gdx, gld = self.series("GDX", 210), self.series("GLD", 210)
        uso = self.series("USO", self.p.lookback + 2)
        gm = ind.pct_change(gld, self.p.lookback)
        margin = gm - self.p.energy_share * ind.pct_change(uso, self.p.lookback)
        if gm > 0 and margin > 0 and gdx[-1] > ind.sma(gdx, 100):
            return {"GDX": 1.0, "GLD": 0.0}
        if gm > 0:
            return {"GLD": 1.0, "GDX": 0.0}
        if gld[-1] > ind.sma(gld, 200):
            return {"GLD": 0.5, "GDX": 0.0}
        return {"GLD": 0.0, "GDX": 0.0}


class P4PolicyStressGold(TargetWeightStrategy):
    CODE = "P4"
    NAME = "Policy-stress gold overlay"
    ASSET_CLASS = "Precious Metals"
    ASSETS = ("GLD",)
    SIGNALS = ("fred:USEPUINDXD", "^VIX", "fred:THREEFYTP10")
    BENCHMARK = "GLD"
    START = "2008-01-01"
    REBALANCE = "W"
    WARMUP = 830
    THESIS = "Gridlock-era stress events (shutdowns, debt-limit X-date, tariff escalations, war-powers fights, Fed-independence clashes) show up in policy-uncertainty, VIX and term premium. Scale gold with a composite stress score."
    params = (("w_min", 0.1), ("w_span", 0.88), ("k", 1.5), ("trend_cut", 0.6))

    def target_weights(self):
        epu = self.series("fred:USEPUINDXD", 790)
        epu_s = np.convolve(epu, np.ones(30) / 30, mode="valid")
        z_epu = ind.zscore(epu_s, min(756, len(epu_s)))
        z_vix = ind.zscore(self.series("^VIX", 252), 252)
        z_tp = ind.rolling_change_zscore(self.series("fred:THREEFYTP10", 820), 63, 756)
        zs = [z for z in (z_epu, z_vix, z_tp) if math.isfinite(z)]
        stress = float(np.mean(zs)) if zs else 0.0
        w = self.p.w_min + self.p.w_span * ind.sigmoid(self.p.k * stress)
        g = self.series("GLD", 210)
        if g[-1] < ind.sma(g, 200):
            w *= self.p.trend_cut
        return {"GLD": w}


class P5PreciousRotation(TargetWeightStrategy):
    CODE = "P5"
    NAME = "Gold/silver/platinum/palladium dual momentum"
    ASSET_CLASS = "Precious Metals"
    ASSETS = ("GLD", "SLV", "PPLT", "PALL")
    BENCHMARK = "GLD"
    START = "2011-03-01"
    REBALANCE = "M"
    WARMUP = 260
    THESIS = "Tariffs (Section 232 on critical minerals), Russian PGM supply risk and auto/AI demand move the metals apart; hold the two strongest risk-adjusted trends, inverse-vol weighted, cash when none trend."
    params = (("top_n", 2), ("lookback", 126))

    def target_weights(self):
        cand = {}
        for a in self.ASSETS:
            if not self.available(a, 253):
                continue
            px = self.series(a, 253)
            if ind.pct_change(px, self.p.lookback) <= 0 or px[-1] < ind.sma(px, 200):
                continue
            cand[a] = (ind.risk_adjusted_momentum(px, self.p.lookback), ind.realized_vol(px, 63))
        picks = sorted(cand, key=lambda a: cand[a][0], reverse=True)[: self.p.top_n]
        if not picks:
            return {}
        inv = {a: 1.0 / cand[a][1] for a in picks}
        tot = sum(inv.values())
        return {a: v / tot for a, v in inv.items()}


STRATEGIES = [P1GoldMacroTrend, P2GoldSilverRatio, P3MinerMarginRotation, P4PolicyStressGold, P5PreciousRotation]
REJECTED = [P3aMinerMomentum]
