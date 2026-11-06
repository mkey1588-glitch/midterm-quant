import math

import numpy as np
import pytest

from midterm_quant import indicators as ind


def test_sma_and_pct_change():
    x = np.arange(1.0, 11.0)  # 1..10
    assert ind.sma(x, 4) == pytest.approx(8.5)
    assert ind.pct_change(x, 5) == pytest.approx(10 / 5 - 1)
    assert ind.pct_change(x, 3, skip=2) == pytest.approx(8 / 5 - 1)
    assert math.isnan(ind.sma(x, 11))
    assert math.isnan(ind.pct_change(x, 10))


def test_zscore_and_change_zscore():
    x = np.array([1.0, 2.0, 3.0, 4.0, 10.0])
    w = x[-5:]
    assert ind.zscore(x, 5) == pytest.approx((10 - w.mean()) / w.std(ddof=1))
    lin = np.arange(100.0)
    assert ind.rolling_change_zscore(lin, 5, 50) == 0.0  # constant changes -> zero dispersion


def test_realized_vol_matches_constant_returns():
    r = 0.01
    x = 100 * np.exp(np.cumsum(np.r_[0, np.tile([r, -r], 50)]))
    v = ind.realized_vol(x, 20, 252)
    assert v == pytest.approx(np.std(np.tile([r, -r], 10), ddof=1) * math.sqrt(252))


def test_rsi_bounds():
    up = np.arange(1.0, 20.0)
    assert ind.rsi(up, 2) == 100.0
    down = up[::-1]
    assert ind.rsi(down, 2) == pytest.approx(0.0)


def test_tsmom_score_and_vol_target():
    up = np.exp(np.linspace(0, 1, 300))
    assert ind.tsmom_score(up, (21, 63, 126)) == 1.0
    assert ind.tsmom_score(up[::-1], (21, 63, 126)) == -1.0
    assert math.isnan(ind.tsmom_score(up[:50], (21, 63, 126)))
    assert ind.vol_target_weight(up, 0.1, 20, cap=0.98) == 0.98  # ~zero vol -> capped


def test_percentile_rank_and_drawdown():
    x = np.array([1.0, 2.0, 3.0, 4.0, 2.5])
    assert ind.percentile_rank(x, 5) == pytest.approx(0.5)
    assert ind.drawdown(x) == pytest.approx(2.5 / 4 - 1)


def test_net_liquidity_units():
    # WALCL and TGA in $mm, RRP in $bn
    assert ind.net_liquidity(7_000_000, 800_000, 100) == 7_000_000 - 800_000 - 100_000
