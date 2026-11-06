"""Crypto strategies (C1-C5), traded on a 7-day calendar.

Post-midterm thesis: the CLARITY Act failed cloture (49-50, Sep 2026) and a Democratic
Congress makes a market-structure law unlikely before 2029, while oversight of the
President's family crypto ventures intensifies. US regulation becomes a headwind for
alt-coins more than for BTC. The dominant price drivers remain dollar liquidity (Fed
balance sheet, TGA swings around the 2027 debt-limit X-date) and the 4-year halving cycle
(next halving ~Apr 2028, inside the observation window).
"""
from __future__ import annotations

import math

import numpy as np

from midterm_quant import config
from midterm_quant import indicators as ind
from midterm_quant.engine.base import TargetWeightStrategy


class C1CryptoTrendVolTarget(TargetWeightStrategy):
    CODE = "C1"
    NAME = "BTC/ETH trend + vol target"
    ASSET_CLASS = "Crypto"
    ASSETS = ("BTC-USD", "ETH-USD")
    CALENDAR = "crypto"
    BENCHMARK = "BTC-USD"
    START = "2015-06-01"
    REBALANCE = "W"
    WARMUP = 130
    THESIS = "Crypto trends persist (reflexive flows, leverage cycles); multi-horizon time-series momentum with volatility targeting captures them while cutting exposure in regulatory/liquidity drawdowns."
    params = (("lookbacks", (20, 60, 120)), ("target_vol", 0.6), ("vol_window", 30))

    def target_weights(self):
        live = [a for a in self.ASSETS if self.available(a, 125)]
        if not live:
            return {}
        budget = 1.0 / len(live)
        w = {}
        for a in live:
            px = self.series(a, 125)
            score = np.mean([ind.pct_change(px, n) > 0 for n in self.p.lookbacks])
            w[a] = budget * score * ind.vol_target_weight(px, self.p.target_vol, self.p.vol_window, 365, cap=1.0)
        return w


class C2LiquidityRegimeBTC(TargetWeightStrategy):
    """v2 (6 Nov 2026): net liquidity on a consistent Wednesday basis in USD billions.

    v1 subtracted the week-average TGA (WTREGEN) from the Wednesday balance sheet. The fix was
    decided from the data definitions, before v2 was run, and v2 is adopted whatever its result;
    v1 stays runnable as ``C2v1`` and both appear in the trial registry.
    """

    CODE = "C2"
    VERSION = "v2"
    EVIDENCE = "D2"
    PROVENANCE = "v1 rule pre-specified on 4 Nov 2026; v2 changes only the net-liquidity input definition (WDTGAL, same-Wednesday RRP, USD bn) after an external review."
    NAME = "Dollar-liquidity regime BTC"
    ASSET_CLASS = "Crypto"
    ASSETS = ("BTC-USD",)
    SIGNALS = ("derived:netliq_bn", "fred:DTWEXBGS")
    CALENDAR = "crypto"
    BENCHMARK = "BTC-USD"
    START = "2015-06-01"
    REBALANCE = "W"
    WARMUP = 200
    THESIS = "Divided government makes a 2027 debt-limit standoff likely: Treasury runs down the TGA (liquidity injection) before the X-date and rebuilds it after (drain). Net liquidity and the dollar trend lead BTC."
    params = (("liq_lookback", 91), ("w_liq", 0.4), ("w_usd", 0.3), ("w_trend", 0.3))

    def liquidity_series(self, n):
        return self.series("derived:netliq_bn", n)

    def target_weights(self):
        n = self.p.liq_lookback + 1
        nl = self.liquidity_series(n)
        liq_up = nl[-1] > nl[0]
        usd_weak = True
        if self.available("fred:DTWEXBGS", 101):
            usd = self.series("fred:DTWEXBGS", 101)
            usd_weak = usd[-1] < ind.sma(usd, 100)
        btc = self.series("BTC-USD", 101)
        trend = btc[-1] > ind.sma(btc, 100)
        return {"BTC-USD": self.p.w_liq * liq_up + self.p.w_usd * usd_weak + self.p.w_trend * trend}


class C2v1LiquidityRegimeBTC(C2LiquidityRegimeBTC):
    """SUPERSEDED v1 of C2 (kept for the trial registry): week-average TGA, latest daily RRP."""

    CODE = "C2v1"
    VERSION = "v1"
    EVIDENCE = "D1"
    NAME = "Dollar-liquidity regime BTC (v1, superseded)"
    SIGNALS = ("fred:WALCL", "fred:WTREGEN", "fred:RRPONTSYD", "fred:DTWEXBGS")

    def liquidity_series(self, n):
        return ind.net_liquidity(
            self.series("fred:WALCL", n), self.series("fred:WTREGEN", n), self.series("fred:RRPONTSYD", n)
        )


def halving_phase(d, halvings=config.BTC_HALVINGS, expansion_end=540, bear_end=900) -> str:
    past = [h for h in halvings if h <= d]
    if not past:
        return "accumulation"
    days = (d - past[-1]).days
    if days < expansion_end:
        return "expansion"
    if days < bear_end:
        return "bear"
    return "accumulation"


class C3HalvingCycle(TargetWeightStrategy):
    """IN-SAMPLE RESEARCH, not a validated strategy: the phase boundaries (540 / 900 days) were
    chosen knowing where the 2017, 2021 and 2025 tops fell, and there are only three cycles.
    It is excluded from every count of strategies that beat a benchmark."""

    CODE = "C3"
    EVIDENCE = "D3"
    PROVENANCE = "Phase boundaries fitted by eye to the dates of the 2017, 2021 and 2025 cycle tops (in-sample)."
    NAME = "Halving-cycle phase + trend"
    ASSET_CLASS = "Crypto"
    ASSETS = ("BTC-USD",)
    CALENDAR = "crypto"
    BENCHMARK = "BTC-USD"
    START = "2015-06-01"
    REBALANCE = "W"
    WARMUP = 200
    THESIS = "Cycle tops have come ~1.5 years after each halving and bottoms ~1 year later; Nov 2026 sits at the bear->accumulation boundary ahead of the ~Apr 2028 halving. Only 3 full cycles: treat as a weak prior, gated by trend."
    params = (("w_expansion", 1.0), ("w_bear", 0.2), ("w_accum", 0.7), ("expansion_end", 540), ("bear_end", 900))

    def target_weights(self):
        phase = halving_phase(self.today, expansion_end=self.p.expansion_end, bear_end=self.p.bear_end)
        base = {"expansion": self.p.w_expansion, "bear": self.p.w_bear, "accumulation": self.p.w_accum}[phase]
        px = self.series("BTC-USD", 200)
        return {"BTC-USD": base * (1.0 if px[-1] > ind.sma(px, 200) else 0.5)}


class C4CryptoRotation(TargetWeightStrategy):
    CODE = "C4"
    NAME = "BTC/ETH/SOL dual-momentum rotation"
    ASSET_CLASS = "Crypto"
    ASSETS = ("BTC-USD", "ETH-USD", "SOL-USD")
    CALENDAR = "crypto"
    BENCHMARK = "BTC-USD"
    START = "2018-03-01"
    REBALANCE = "W"
    WARMUP = 110
    THESIS = "With US market-structure legislation stalled, regulatory risk falls hardest on alt-coins; rotate to whichever majors carry positive absolute and relative momentum, hold cash otherwise."
    params = (("top_n", 2),)

    def target_weights(self):
        cand = {}
        for a in self.ASSETS:
            if not self.available(a, 101):
                continue
            px = self.series(a, 101)
            if ind.pct_change(px, 90) <= 0 or px[-1] < ind.sma(px, 100):
                continue
            score = ind.risk_adjusted_momentum(px, 30, periods=365) + ind.risk_adjusted_momentum(px, 90, periods=365)
            vol = ind.realized_vol(px, 30, 365)
            if math.isfinite(score) and vol > 0:
                cand[a] = (score, vol)
        picks = sorted(cand, key=lambda a: cand[a][0], reverse=True)[: self.p.top_n]
        if not picks:
            return {}
        inv = {a: 1.0 / cand[a][1] for a in picks}
        tot = sum(inv.values())
        return {a: v / tot for a, v in inv.items()}


class C5StablecoinImpulse(TargetWeightStrategy):
    CODE = "C5"
    EVIDENCE = "D2"
    PROVENANCE = "Replacement for C5a after C5a lost money as first specified; 4 configurations tried (lookback 14/30/60, trend leg on/off); 30d with trend leg adopted. Stablecoin history is restated by DefiLlama, so growth rates are not point-in-time."
    NAME = "Stablecoin-supply liquidity impulse"
    ASSET_CLASS = "Crypto"
    ASSETS = ("BTC-USD", "ETH-USD")
    SIGNALS = ("llama:stablecoins",)
    CALENDAR = "crypto"
    BENCHMARK = "BTC-USD"
    START = "2018-06-01"
    REBALANCE = "W"
    WARMUP = 120
    THESIS = "Stablecoins are crypto's on-chain dollar base; the GENIUS Act (2025) is already law, so issuance keeps growing even with market-structure legislation dead. Net stablecoin creation is the marginal bid - scale BTC/ETH exposure with its growth and acceleration."
    params = (("lookback", 30), ("w_growth", 0.5), ("w_accel", 0.25), ("w_trend", 0.25), ("btc_share", 0.7))

    def target_weights(self):
        if not self.available("llama:stablecoins", 100):
            return {}
        sc = self.series("llama:stablecoins", 120)
        g = ind.pct_change(sc, self.p.lookback)
        g90 = ind.pct_change(sc, 90)
        btc = self.series("BTC-USD", 101)
        w = self.p.w_growth * (g > 0) + self.p.w_accel * (g > g90 / 3.0) + self.p.w_trend * (btc[-1] > ind.sma(btc, 100))
        return {"BTC-USD": w * self.p.btc_share, "ETH-USD": w * (1.0 - self.p.btc_share)}


class C5aShockReversal(TargetWeightStrategy):
    """REJECTED candidate (kept for the research log): buy >2.5-sigma BTC down days.

    Lost money in the pre-specified form (2015-2026 CAGR -1.2%, Sharpe -0.03); only
    worked after tightening the trend filter and shortening the hold, which is
    parameter-fragile. Not part of the 20-strategy book.
    """

    CODE = "C5a"
    NAME = "Liquidation-shock reversal (rejected)"
    ASSET_CLASS = "Crypto"
    ASSETS = ("BTC-USD",)
    CALENDAR = "crypto"
    BENCHMARK = "BTC-USD"
    START = "2015-06-01"
    REBALANCE = "D"
    WARMUP = 210
    params = (("shock_z", -2.5), ("vol_window", 60), ("max_hold", 7), ("stop", -0.12), ("trend_floor", 0.85), ("size", 0.98))

    def target_weights(self):
        px = self.series("BTC-USD", 210)
        st = self.state
        if st.get("in"):
            st["days"] += 1
            ret = px[-1] / st["entry"] - 1.0
            if px[-1] >= st["target"] or st["days"] >= self.p.max_hold or ret < self.p.stop:
                st["in"] = False
                return {"BTC-USD": 0.0}
            return None
        r = np.diff(np.log(px[-(self.p.vol_window + 2):]))
        sigma = np.std(r[:-1], ddof=1)
        if sigma > 0 and r[-1] < self.p.shock_z * sigma and px[-1] > self.p.trend_floor * ind.sma(px, 200):
            st.update(**{"in": True, "days": 0, "entry": px[-1], "target": px[-2]})
            return {"BTC-USD": self.p.size}
        return None


STRATEGIES = [C1CryptoTrendVolTarget, C2LiquidityRegimeBTC, C3HalvingCycle, C4CryptoRotation, C5StablecoinImpulse]
REJECTED = [C5aShockReversal]
SUPERSEDED = [C2v1LiquidityRegimeBTC]
