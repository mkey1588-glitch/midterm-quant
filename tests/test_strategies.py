"""Smoke + causality tests for all 20 strategies (and the rejected specs) on synthetic data."""
import pytest

from midterm_quant.engine.runner import required_series, run_backtest
from midterm_quant.strategies import ALL, REJECTED, SUPERSEDED

from conftest import synthetic_panel


def _panel(cls, n=None, seed=7):
    n = n or cls.WARMUP + 320
    return synthetic_panel(required_series(cls), cls.CALENDAR, n=n, seed=seed)


def test_registry_shape():
    classes = {}
    for cls in ALL:
        classes.setdefault(cls.ASSET_CLASS, []).append(cls.CODE)
    assert {k: len(v) for k, v in classes.items()} == {
        "US Equities": 5, "Crypto": 5, "Energy": 5, "Precious Metals": 5,
    }
    for cls in ALL:
        assert cls.THESIS, f"{cls.CODE} needs a THESIS linking it to the midterm analysis"


@pytest.mark.parametrize("cls", ALL + REJECTED + SUPERSEDED, ids=lambda c: c.CODE)
def test_runs_and_respects_limits(cls):
    p = _panel(cls)
    r = run_backtest(cls, start=p.calendar[0], panel=p)
    assert len(r.equity) > 100
    assert r.equity.notna().all() and (r.equity > 0).all()
    for _, target in r.rebalances:
        assert sum(v for v in target.values() if v > 0) <= cls.MAX_LONG + 1e-3  # targets stored rounded to 4dp
        assert sum(abs(v) for v in target.values()) <= cls.MAX_GROSS + 1e-3
        assert set(target) <= set(cls.ASSETS)
    assert r.exposure["gross"].max() < 1.5


@pytest.mark.parametrize("cls", ALL, ids=lambda c: c.CODE)
def test_no_lookahead(cls):
    """Decisions up to bar T must not change when data after T is deleted."""
    full = _panel(cls, seed=11)
    cut = len(full.calendar) - 120
    trunc = synthetic_panel(required_series(cls), cls.CALENDAR, n=len(full.calendar), seed=11)
    for name, df in trunc.frames.items():
        trunc.frames[name] = df.iloc[:cut]
    trunc.calendar = trunc.calendar[:cut]
    last_day = trunc.calendar[-1].date()

    a = run_backtest(cls, start=full.calendar[0], panel=full).rebalances
    b = run_backtest(cls, start=trunc.calendar[0], panel=trunc).rebalances
    a = [(d, t) for d, t in a if d <= last_day]
    assert a == b
    assert len(b) > 0
