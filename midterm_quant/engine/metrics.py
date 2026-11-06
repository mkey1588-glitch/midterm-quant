"""Performance statistics from an equity curve."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd


def perf_stats(equity: pd.Series, periods: int = 252, rf_pct: pd.Series | None = None) -> dict:
    """CAGR, vol, excess-return Sharpe/Sortino (vs T-bills if given), drawdown, Calmar."""
    equity = equity.dropna()
    if len(equity) < 3:
        return {}
    r = equity.pct_change().dropna()
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-9)
    total = equity.iloc[-1] / equity.iloc[0] - 1.0
    cagr = (1.0 + total) ** (1.0 / years) - 1.0
    vol = r.std(ddof=1) * math.sqrt(periods)
    if rf_pct is not None:
        rf = rf_pct.reindex(r.index).ffill().fillna(0.0) / 100.0 / periods
    else:
        rf = 0.0
    ex = r - rf
    sharpe = ex.mean() / ex.std(ddof=1) * math.sqrt(periods) if ex.std(ddof=1) > 0 else float("nan")
    downside = math.sqrt(np.mean(np.minimum(ex.to_numpy(), 0.0) ** 2)) * math.sqrt(periods)
    sortino = ex.mean() * periods / downside if downside > 0 else float("nan")
    dd = equity / equity.cummax() - 1.0
    maxdd = dd.min()
    calmar = cagr / abs(maxdd) if maxdd < 0 else float("nan")
    yearly = equity.resample("YE").last().pct_change().dropna()
    out = {
        "Start": equity.index[0].date().isoformat(),
        "End": equity.index[-1].date().isoformat(),
        "Years": round(years, 1),
        "CAGR": cagr,
        "Vol": vol,
        "Sharpe": sharpe,
        "Sortino": sortino,
        "MaxDD": maxdd,
        "Calmar": calmar,
        "TotalReturn": total,
        "WorstYear": yearly.min() if len(yearly) else float("nan"),
    }
    return {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in out.items()}
