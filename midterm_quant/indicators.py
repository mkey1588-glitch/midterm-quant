"""Pure, framework-agnostic indicator functions on 1-D numpy arrays.

Convention: ``x[-1]`` is the most recent observation (the current bar). Every function
only reads the array it is given, so causality is guaranteed by the caller passing
history up to and including the current bar (which the Backtrader engine enforces).
Functions return ``nan`` when there is not enough history.
"""
from __future__ import annotations

import math

import numpy as np

NAN = float("nan")


def _ok(x: np.ndarray, n: int) -> bool:
    return x is not None and len(x) >= n and np.all(np.isfinite(x[-n:]))


def sma(x: np.ndarray, n: int) -> float:
    return float(np.mean(x[-n:])) if _ok(x, n) else NAN


def pct_change(x: np.ndarray, n: int, skip: int = 0) -> float:
    """Return from ``n+skip`` bars ago to ``skip`` bars ago (skip>0 => skip recent bars)."""
    need = n + skip + 1
    if not _ok(x, need):
        return NAN
    a, b = x[-need], x[-1 - skip]
    return float(b / a - 1.0) if a > 0 else NAN


def diff(x: np.ndarray, n: int) -> float:
    return float(x[-1] - x[-1 - n]) if _ok(x, n + 1) else NAN


def log_returns(x: np.ndarray) -> np.ndarray:
    return np.diff(np.log(x))


def realized_vol(x: np.ndarray, n: int, periods: int = 252) -> float:
    """Annualised close-to-close volatility over the last ``n`` returns."""
    if not _ok(x, n + 1):
        return NAN
    r = log_returns(x[-(n + 1):])
    return float(np.std(r, ddof=1) * math.sqrt(periods))


def zscore(x: np.ndarray, n: int) -> float:
    """z-score of the latest value versus the trailing ``n`` values (inclusive)."""
    if not _ok(x, n):
        return NAN
    w = x[-n:]
    sd = np.std(w, ddof=1)
    return float((w[-1] - w.mean()) / sd) if sd > 0 else 0.0


def rolling_change_zscore(x: np.ndarray, horizon: int, window: int) -> float:
    """z-score of the latest ``horizon``-bar change versus the last ``window`` such changes."""
    if not _ok(x, horizon + window):
        return NAN
    w = x[-(horizon + window):]
    ch = w[horizon:] - w[:-horizon]
    sd = np.std(ch, ddof=1)
    return float((ch[-1] - ch.mean()) / sd) if sd > 0 else 0.0


def return_zscore(x: np.ndarray, horizon: int, window: int) -> float:
    """z-score of the latest ``horizon``-bar log return versus overlapping history."""
    if not _ok(x, horizon + window) or np.any(x[-(horizon + window):] <= 0):
        return NAN
    return rolling_change_zscore(np.log(x), horizon, window)


def rsi(x: np.ndarray, n: int) -> float:
    """Cutler's RSI (simple averages) - used for the short-horizon RSI(2) signal."""
    if not _ok(x, n + 1):
        return NAN
    d = np.diff(x[-(n + 1):])
    up = d[d > 0].sum() / n
    dn = -d[d < 0].sum() / n
    if dn == 0:
        return 100.0
    return float(100.0 - 100.0 / (1.0 + up / dn))


def tsmom_score(x: np.ndarray, lookbacks=(21, 63, 126, 252)) -> float:
    """Average sign of trailing returns across lookbacks, in [-1, 1]."""
    signs = []
    for n in lookbacks:
        r = pct_change(x, n)
        if not math.isfinite(r):
            return NAN
        signs.append(np.sign(r))
    return float(np.mean(signs))


def risk_adjusted_momentum(x: np.ndarray, n: int, skip: int = 0, periods: int = 252) -> float:
    r = pct_change(x, n, skip)
    v = realized_vol(x, n, periods)
    if not (math.isfinite(r) and math.isfinite(v)) or v <= 0:
        return NAN
    return r / v


def vol_target_weight(x: np.ndarray, target: float, n: int, periods: int = 252, cap: float = 1.0) -> float:
    v = realized_vol(x, n, periods)
    if not math.isfinite(v) or v <= 0:
        return 0.0
    return float(min(cap, target / v))


def drawdown(x: np.ndarray, n: int | None = None) -> float:
    w = x if n is None else x[-n:]
    if len(w) == 0 or not np.all(np.isfinite(w)):
        return NAN
    return float(w[-1] / np.max(w) - 1.0)


def percentile_rank(x: np.ndarray, n: int) -> float:
    """Fraction of the trailing ``n`` values strictly below the latest value."""
    if not _ok(x, n):
        return NAN
    w = x[-n:]
    return float(np.mean(w[:-1] < w[-1]))


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-z))


def clip(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def ols_beta(y: np.ndarray, x: np.ndarray) -> float:
    if len(y) != len(x) or len(y) < 3:
        return NAN
    vx = np.var(x, ddof=1)
    return float(np.cov(y, x, ddof=1)[0, 1] / vx) if vx > 0 else NAN


def net_liquidity(walcl_mm: float, tga_mm: float, rrp_bn: float) -> float:
    """v1 formula, kept to reproduce C2 v1: USD millions = WALCL - TGA - RRP*1000."""
    return walcl_mm - tga_mm - rrp_bn * 1000.0


def net_liquidity_bn(walcl_mm, tga_mm, rrp_bn):
    """Fed net liquidity in USD billions.

    Units: WALCL and WDTGAL are published in USD millions, RRPONTSYD in USD billions.
    All three must refer to the same Wednesday (WALCL and WDTGAL are Wednesday levels).
    """
    return np.asarray(walcl_mm, dtype=float) / 1000.0 - np.asarray(tga_mm, dtype=float) / 1000.0 - np.asarray(rrp_bn, dtype=float)
