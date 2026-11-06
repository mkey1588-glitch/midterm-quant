import numpy as np
import pandas as pd
import pytest

from midterm_quant.engine.base import TargetWeightStrategy
from midterm_quant.engine.metrics import perf_stats
from midterm_quant.engine.runner import run_backtest


class HoldAAA(TargetWeightStrategy):
    CODE, NAME, ASSET_CLASS = "T1", "hold", "Test"
    ASSETS = ("AAA",)
    BENCHMARK = "AAA"
    START = "2015-01-01"
    WARMUP = 2
    REBALANCE = "M"
    params = (("w", 0.98),)

    def target_weights(self):
        return {"AAA": self.p.w}


class HoldOnce(HoldAAA):
    CODE = "T0"

    def target_weights(self):
        if self.state.get("done"):
            return None
        self.state["done"] = True
        return {"AAA": self.p.w}


class LongShort(TargetWeightStrategy):
    CODE, NAME, ASSET_CLASS = "T2", "pair", "Test"
    ASSETS = ("AAA", "BBB")
    BENCHMARK = "AAA"
    START = "2015-01-01"
    WARMUP = 2
    REBALANCE = "W"

    def target_weights(self):
        return {"AAA": 0.5, "BBB": -0.5}


class Overweight(HoldAAA):
    CODE = "T3"

    def target_weights(self):
        return {"AAA": 3.0}


def test_buy_and_hold_tracks_asset(make_panel):
    p = make_panel(["AAA", "fred:DTB3"], n=500)
    p.frames["fred:DTB3"].loc[:, ["open", "high", "low", "close"]] = 0.0  # no cash yield
    r = run_backtest(HoldOnce, panel=p, cash=1e6)
    # decided at bar 1's close (WARMUP=2), filled at bar 2's open, then held untouched
    asset_ret = p.close("AAA").iloc[-1] / p.frames["AAA"]["open"].iloc[2] - 1
    strat_ret = r.equity.iloc[-1] - 1
    assert strat_ret == pytest.approx(0.98 * asset_ret - 0.98 * 0.0002, abs=1e-3)
    assert r.rejected == 0
    assert r.exposure["gross"].iloc[-1] > 0.9


def test_cash_earns_tbill_yield(make_panel):
    p = make_panel(["AAA", "fred:DTB3"], n=253)
    p.frames["fred:DTB3"].loc[:, ["open", "high", "low", "close"]] = 5.0
    r = run_backtest(HoldAAA, panel=p, w=0.0)
    years_bars = (len(r.equity) - 1) / 252
    assert r.equity.iloc[-1] - 1 == pytest.approx((1 + 0.05 / 252) ** (len(r.equity) - 1) - 1, rel=0.02)
    assert years_bars > 0.9


def test_long_short_and_limits(make_panel):
    p = make_panel(["AAA", "BBB", "fred:DTB3"], n=300)
    r = run_backtest(LongShort, panel=p)
    assert r.exposure["gross"].iloc[-1] == pytest.approx(1.0, abs=0.15)
    assert abs(r.exposure["net"].iloc[-1]) < 0.15
    r2 = run_backtest(Overweight, panel=p)
    assert r2.exposure["gross"].max() <= 1.02  # MAX_LONG cap enforced (plus intra-month drift)


def test_perf_stats_known_series():
    idx = pd.bdate_range("2020-01-01", periods=253)
    eq = pd.Series(np.linspace(1.0, 1.1, 253), index=idx)
    m = perf_stats(eq, 252)
    assert m["TotalReturn"] == pytest.approx(0.1)
    assert m["MaxDD"] == 0.0
    assert m["Sharpe"] > 5
