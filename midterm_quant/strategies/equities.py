"""US equity strategies (E1-E5).

Post-midterm thesis (Nov 2026): a Democratic Congress facing a Republican White House
means gridlock - no new fiscal stimulus, a tariff regime that stays executive-driven,
recurring funding/debt-limit standoffs, and intensified oversight of AI/data centres.
Historically, the 12 months after a midterm have been the best stretch of the
presidential cycle; the risks are policy shocks rather than recessionary fiscal shifts.
"""
from __future__ import annotations

import datetime as dt

import numpy as np

from midterm_quant import indicators as ind
from midterm_quant.engine.base import TargetWeightStrategy


def in_midterm_sweet_spot(d: dt.date) -> bool:
    """1 Oct of a midterm year through 31 Dec of the pre-election year."""
    return (d.year % 4 == 2 and d.month >= 10) or (d.year % 4 == 3)


class E1PresidentialCycleTrend(TargetWeightStrategy):
    CODE = "E1"
    NAME = "Midterm-cycle seasonal + trend"
    ASSET_CLASS = "US Equities"
    ASSETS = ("SPY",)
    BENCHMARK = "SPY"
    START = "1994-01-01"
    REBALANCE = "W"
    WARMUP = 210
    THESIS = "Q4 of the midterm year through the pre-election year is historically the strongest cycle window; a 200d trend filter limits damage when a policy or macro shock overrides seasonality."
    params = (("sweet_up", 1.0), ("sweet_down", 0.6), ("base_up", 0.7), ("base_down", 0.3), ("sma", 200))

    def target_weights(self):
        px = self.series("SPY", self.p.sma)
        up = px[-1] > ind.sma(px, self.p.sma)
        if in_midterm_sweet_spot(self.today):
            w = self.p.sweet_up if up else self.p.sweet_down
        else:
            w = self.p.base_up if up else self.p.base_down
        return {"SPY": w}


class E2PolicySectorMomentum(TargetWeightStrategy):
    CODE = "E2"
    NAME = "Policy-regime sector momentum"
    ASSET_CLASS = "US Equities"
    SECTORS = ("XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY")
    THEMES = ("ITA", "KRE", "XBI", "TAN", "SMH")   # defence, regional banks, biotech, solar, semis
    ASSETS = SECTORS + THEMES + ("IEF",)
    BENCHMARK = "SPY"
    START = "2001-01-01"
    REBALANCE = "M"
    WARMUP = 260
    THESIS = "Policy shocks (tariffs, healthcare subsidies, defence budgets, AI/data-centre scrutiny, clean-energy credits) create persistent sector trends; ride the strongest risk-adjusted trends, park unused slots in Treasuries."
    params = (("top_n", 3), ("lookback", 126), ("skip", 21))

    def target_weights(self):
        scores = {}
        for name in self.SECTORS + self.THEMES:
            if not self.available(name, 253):
                continue
            px = self.series(name, 253)
            if px[-1] < ind.sma(px, 200):
                continue
            s = ind.risk_adjusted_momentum(px, self.p.lookback, skip=self.p.skip)
            if np.isfinite(s) and s > 0:
                scores[name] = s
        picks = sorted(scores, key=scores.get, reverse=True)[: self.p.top_n]
        slot = 1.0 / self.p.top_n
        w = {p: slot for p in picks}
        empty = self.p.top_n - len(picks)
        if empty and self.available("IEF", 210):
            ief = self.series("IEF", 210)
            if ief[-1] > ind.sma(ief, 200):
                w["IEF"] = empty * slot
        return w


class E3VolTargetTermStructure(TargetWeightStrategy):
    CODE = "E3"
    NAME = "Vol-target + VIX term-structure"
    ASSET_CLASS = "US Equities"
    ASSETS = ("SPY",)
    SIGNALS = ("^VIX", "^VIX3M")
    BENCHMARK = "SPY"
    START = "2008-01-01"
    REBALANCE = "D"
    WARMUP = 210
    THESIS = "Gridlock removes fiscal tail risk but adds headline volatility (shutdowns, debt limit, tariffs, Iran). Scale exposure to realised vol and cut it when the VIX curve inverts."
    params = (("target_vol", 0.12), ("cap", 0.98), ("inversion", 1.0), ("cut", 0.5), ("min_trade", 0.05))

    def target_weights(self):
        px = self.series("SPY", 210)
        rv = max(ind.realized_vol(px, 20), ind.realized_vol(px, 60))
        w = min(self.p.cap, self.p.target_vol / rv) if rv > 0 else 0.0
        if self.available("^VIX3M", 1):
            ratio = self.last("^VIX") / self.last("^VIX3M")
            if ratio > self.p.inversion:
                w *= self.p.cut
        return {"SPY": w}


class E4BroadeningRotation(TargetWeightStrategy):
    CODE = "E4"
    NAME = "Broadening vs mega-cap rotation"
    ASSET_CLASS = "US Equities"
    ASSETS = ("RSP", "QQQ", "IWM")
    SIGNALS = ("^TNX",)
    BENCHMARK = "SPY"
    START = "2004-06-01"
    REBALANCE = "W"
    WARMUP = 260
    THESIS = "AI/data-centre regulation risk under a Democratic Congress and lower term premium (Fed-independence repricing) favour equal-weight and small caps over mega-cap growth; switch only when relative trend and yields confirm."
    ALLOC = {
        3: {"RSP": 0.5, "IWM": 0.5},
        2: {"RSP": 0.7, "QQQ": 0.3},
        1: {"RSP": 0.3, "QQQ": 0.7},
        0: {"QQQ": 1.0},
    }

    def target_weights(self):
        rsp, qqq, iwm = (self.series(n, 260) for n in ("RSP", "QQQ", "IWM"))
        tnx = self.series("^TNX", 30)
        ratio = rsp / qqq
        score = int(ratio[-1] > ind.sma(ratio, 100))
        score += int(ind.diff(tnx, 20) < 0)
        score += int(ind.pct_change(iwm, 63) > ind.pct_change(qqq, 63))
        w = dict(self.ALLOC[score])
        if rsp[-1] < ind.sma(rsp, 200) and qqq[-1] < ind.sma(qqq, 200):
            w = {k: v * 0.5 for k, v in w.items()}
        return w


class E5PoliticalShockReversal(TargetWeightStrategy):
    CODE = "E5"
    NAME = "Political-shock reversal (credit-filtered)"
    ASSET_CLASS = "US Equities"
    ASSETS = ("SPY",)
    SIGNALS = ("HYG", "IEF")
    BENCHMARK = "SPY"
    START = "2008-06-01"
    REBALANCE = "D"
    WARMUP = 270
    THESIS = "Shutdown, debt-limit and tariff headlines cause sharp equity dips that revert when credit does not confirm. Buy RSI(2) washouts in uptrends, or in downtrends only if HY credit is calm."
    params = (("rsi_entry", 10.0), ("max_hold", 10), ("stop", -0.08), ("credit_z", -1.0), ("size", 0.98))

    def target_weights(self):
        px = self.series("SPY", 260)
        st = self.state
        if st.get("in"):
            st["days"] += 1
            ret = px[-1] / st["entry"] - 1.0
            if px[-1] > ind.sma(px, 5) or st["days"] >= self.p.max_hold or ret < self.p.stop:
                st["in"] = False
                return {"SPY": 0.0}
            return None
        if ind.rsi(px, 2) >= self.p.rsi_entry:
            return None
        uptrend = px[-1] > ind.sma(px, 200)
        credit_calm = False
        if self.available("HYG", 262) and self.available("IEF", 262):
            credit = np.log(self.series("HYG", 262) / self.series("IEF", 262))
            credit_calm = ind.rolling_change_zscore(credit, 10, 250) > self.p.credit_z
        if uptrend or credit_calm:
            st.update(**{"in": True, "days": 0, "entry": px[-1]})
            return {"SPY": self.p.size}
        return None


STRATEGIES = [E1PresidentialCycleTrend, E2PolicySectorMomentum, E3VolTargetTermStructure, E4BroadeningRotation, E5PoliticalShockReversal]
