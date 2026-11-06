"""Offline tests for the 6 Nov 2026 review iteration: timing rules, units, evaluation maths,
ledgers, the scenario rule, the shock-study design and specification completeness."""
import math

import numpy as np
import pandas as pd
import pytest

from midterm_quant import indicators as ind
from midterm_quant.data import catalog
from midterm_quant.engine import evaluation as ev
from midterm_quant.engine.runner import required_series, run_backtest
from midterm_quant.research import monitor, scenarios, shock_study
from midterm_quant.specs import all_specs
from midterm_quant.strategies import ALL, BY_CODE
from midterm_quant.strategies.trials import N_TRIALS, TRIALS

from conftest import synthetic_panel


# ---- availability rules ------------------------------------------------------------------
def test_h10_weekly_release_is_next_tuesday():
    # H.10: a Monday 2 Nov 2026 observation is published Monday 9 Nov after the close -> usable Tuesday 10 Nov
    obs = pd.DatetimeIndex(["2026-11-02", "2026-11-06"])
    assert list(catalog.available_dates("fred:DTWEXBGS", obs)) == [pd.Timestamp("2026-11-10"), pd.Timestamp("2026-11-10")]


def test_h41_wednesday_level_usable_friday():
    assert catalog.available_dates("fred:WALCL", pd.DatetimeIndex(["2026-11-04"]))[0] == pd.Timestamp("2026-11-06")
    assert catalog.meta("fred:WDTGAL").units.startswith("USD millions, Wednesday")
    assert "week average" in catalog.meta("fred:WTREGEN").units


def test_crypto_and_stablecoin_bars_complete_next_utc_day():
    assert catalog.available_dates("llama:stablecoins", pd.DatetimeIndex(["2026-11-05"]))[0] == pd.Timestamp("2026-11-06")
    assert catalog.meta("BTC-USD").timestamp.startswith("UTC calendar-day bar")


def test_monthly_release_after_month_end():
    a = catalog.available_dates("fred:UNRATE", pd.DatetimeIndex(["2026-09-01"]))[0]
    assert a >= pd.Timestamp("2026-11-01")  # September data is not usable in September or October


def test_every_series_used_by_strategies_is_catalogued():
    for cls in ALL:
        for name in required_series(cls):
            m = catalog.meta(name)
            assert m.units and m.release and m.available_rule and m.license
            assert "not catalogued" not in m.notes, name


# ---- units ---------------------------------------------------------------------------------
def test_net_liquidity_units_are_billions():
    # WALCL 6,748,145 mm; WDTGAL 936,248 mm; RRP 0.225 bn (FRED, 4 Nov 2026)
    v = float(ind.net_liquidity_bn(6_748_145, 936_248, 0.225))
    assert abs(v - (6748.145 - 936.248 - 0.225)) < 1e-9


# ---- evaluation maths ---------------------------------------------------------------------
def test_psr_and_dsr_behave():
    assert ev.psr(0.0, 120, 0.0, 3.0) == pytest.approx(0.5)
    assert ev.psr(0.3, 120, 0.0, 3.0) > 0.99
    assert ev.expected_max_sr(1, 0.01) == 0.0
    assert ev.expected_max_sr(46, 0.01) > ev.expected_max_sr(5, 0.01) > 0


def test_risk_matched_benchmark_has_target_vol():
    idx = pd.bdate_range("2010-01-01", periods=1500)
    rng = np.random.default_rng(1)
    px = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, len(idx)))), index=idx)
    rf = pd.Series(0.0, index=pd.period_range("2010-01", periods=80, freq="M"))
    b = ev.benchmarks(px, rf, target_vol_m=0.02, cost_bps=2.0, end="2016-12-31")
    assert b["risk_matched"].std(ddof=1) == pytest.approx(0.02, rel=1e-6)
    assert (b["cash"] == 0).all()


def test_drawdown_recovery():
    nav = pd.Series([1.0, 1.2, 0.9, 1.0, 1.25, 1.1], index=pd.date_range("2020-01-01", periods=6))
    d = ev.drawdown_stats(nav)
    assert d["MaxDD"] == pytest.approx(0.9 / 1.2 - 1)
    assert d["MaxDD_recovered"] == "2020-01-05" and d["MaxDD_days_to_recover"] == 2


# ---- ledgers -------------------------------------------------------------------------------
@pytest.mark.parametrize("code", ["E1", "N3", "C1"])
def test_ledger_identities(code):
    cls = BY_CODE[code]
    p = synthetic_panel(required_series(cls), cls.CALENDAR, n=cls.WARMUP + 400, seed=3)
    r = run_backtest(cls, start=p.calendar[0], panel=p)
    nav, pos, orders = r.ledger["nav"], r.ledger["positions"], r.ledger["orders"]
    # NAV = cash + sum(units x close): the gross exposure recomputed from weights must match
    assert np.allclose(pos.abs().sum(axis=1).reindex(nav.index).fillna(0), nav["gross"], atol=1e-9)
    filled = orders[orders["status"] == "Completed"]
    assert len(filled) > 0 and (filled["commission"] >= 0).all()
    assert nav["commission_cum"].iloc[-1] == pytest.approx(filled["commission"].sum(), rel=1e-9)
    assert r.signal_now is not None


# ---- scenario rule --------------------------------------------------------------------------
def _counts(seq):
    return pd.DataFrame([{"week_end": f"2026-{(i // 4) + 1:02d}-{(i % 4) * 7 + 1:02d}", "scenario": "C", "holding": h, "of": 6,
                          "which": [], "gaps": []} for i, h in enumerate(seq)])


def test_three_signals_four_weeks_confirm_and_revoke():
    st = scenarios.states(_counts([3, 3, 3, 2, 3, 3, 3, 3, 2, 1, 1, 0]))["state"].tolist()
    assert st[:7] == ["WATCHING"] * 7          # the run of 3s is broken by a 2
    assert st[7] == "CONFIRMED"                 # four consecutive weeks >= 3
    assert st[8] == "CONFIRMED"                 # a 2 neither confirms nor revokes
    assert st[9] == "CONFIRMED"                 # one week <= 1 is not enough
    assert st[10] == "REVOKED"                  # two consecutive weeks <= 1
    assert st[11] == "WATCHING"


def test_scenario_signposts_reference_real_indicators():
    for _, _, sps in scenarios.SCENARIOS.values():
        for s in sps:
            assert set(s.codes) <= set(monitor.SPECS)
    assert {k: len(v[2]) for k, v in scenarios.SCENARIOS.items()} == {"A": 7, "B": 6, "C": 6}


# ---- shock study design ---------------------------------------------------------------------
def test_shock_events_decluster_and_fix_groups():
    idx = pd.bdate_range("1990-01-01", periods=900)
    px = pd.Series(100.0, index=idx) * np.exp(np.cumsum(np.full(len(idx), 0.0004)))
    for i in (300, 305, 600):          # 305 is inside the 20-session gap of 300
        px.iloc[i:] *= 0.95
    ev_ = shock_study.events(px, 0.035, 20)
    assert len(ev_) == 2
    assert ev_["above200"].dtype == bool
    assert shock_study.overlap_pairs(ev_) == 0  # 300 sessions apart > 252


# ---- specifications and trial registry ---------------------------------------------------
def test_every_strategy_fully_specified():
    specs = all_specs()
    assert len(specs) == 20
    for s in specs:
        for k in ("signal", "entry", "exit", "invalidation", "provenance", "missing_data", "decision_time",
                  "execution", "benchmark_reference", "benchmark_primary"):
            assert s[k], (s["code"], k)
        assert s["inputs"] and all(i["units"] and i["release"] for i in s["inputs"])


def test_every_indicator_fully_specified():
    assert len(monitor.ORDER) == 36 and len(monitor.ORIGINAL_33) == 33
    for code, sp in monitor.SPECS.items():
        for k in ("measures", "not_measures", "formula", "units", "frequency", "rule", "missing"):
            assert getattr(sp, k), (code, k)
        assert sp.tones


def test_proxy_indicators_are_not_named_as_what_they_are_not():
    names = {c: s.name.lower() for c, s in monitor.SPECS.items()}
    assert "impulse" not in names["M10"] and "ai" not in names["E-e"].split()
    assert "regulatory" not in names["C-d"] and "war" not in names["N-a"] and "margin" not in names["P-c"]


def test_trial_registry_complete_and_c3_is_research():
    assert N_TRIALS == 46
    assert BY_CODE["C3"].EVIDENCE == "D3"
    adopted = {t.trial_id for t in TRIALS if t.status in ("adopted", "in-sample research")}
    assert {c.CODE for c in ALL} == adopted
    assert {t.trial_id for t in TRIALS if t.family == "C5"} >= {"C5a", "C5", "C5x-1", "C5x-2", "C5x-3"}
    assert any(t.trial_id == "C2v1" and t.status == "superseded" for t in TRIALS)
