"""Offline synthetic data so the test-suite never touches the network."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from midterm_quant.data.align import Panel  # noqa: E402

# Plausible starting levels for signal series (geometric random walks keep them > 0).
LEVELS = {
    "fred:DTB3": 2.0, "fred:DFII10": 1.0, "fred:WALCL": 7.0e6, "fred:WTREGEN": 7.0e5,
    "fred:RRPONTSYD": 100.0, "fred:DTWEXBGS": 110.0, "fred:USEPUINDXD": 120.0,
    "fred:THREEFYTP10": 0.5, "fred:GASREGW": 3.0, "^VIX": 18.0, "^VIX3M": 20.0, "^TNX": 3.0,
    "llama:stablecoins": 1.5e11, "derived:netliq_bn": 6000.0, "fred:WDTGAL": 8.0e5,
}


def synthetic_panel(names, calendar="nyse", n=900, seed=0, start="2015-01-01") -> Panel:
    rng = np.random.default_rng(seed)
    if calendar == "crypto":
        cal = pd.date_range(start, periods=n, freq="D")
    else:
        cal = pd.bdate_range(start, periods=n)
    panel = Panel(calendar=cal)
    for name in dict.fromkeys(names):
        level = LEVELS.get(name, 100.0)
        vol = 0.01 if name.startswith(("fred:", "llama:")) else 0.02
        close = level * np.exp(np.cumsum(rng.normal(0.0002, vol, n)))
        open_ = close * np.exp(rng.normal(0, vol / 4, n))
        df = pd.DataFrame(
            {"open": open_, "high": np.maximum(open_, close) * 1.002, "low": np.minimum(open_, close) * 0.998,
             "close": close, "volume": 1e6},
            index=cal,
        )
        panel.frames[name] = df
        panel.inception[name] = cal[0]
    return panel


@pytest.fixture
def make_panel():
    return synthetic_panel
