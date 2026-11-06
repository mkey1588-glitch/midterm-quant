"""Standardised performance and risk evaluation.

One convention for every strategy, so equities (252-day calendar) and crypto (365-day
calendar) are comparable:

* **Returns** are month-end to month-end NAV changes; every ratio is annualised with sqrt(12).
  Native daily statistics are reported separately and labelled as such.
* **Risk-free rate**: FRED DTB3 (3-month bill, secondary market, discount basis), the monthly
  average divided by 12. The same series pays interest on idle cash inside the backtests.
* **Window**: each strategy's first full month after warm-up to the last complete month
  before ``config.BACKTEST_END``.
* **Costs**: strategy NAVs are net of the per-asset costs in ``config.COST_BPS``, short-borrow
  fees and cash interest. Benchmarks are frictionless except the trend rule, which pays the
  same per-trade costs.

Benchmarks per strategy (all from the same price files):

1. ``cash``: T-bills (Sharpe 0 by construction).
2. ``buy_hold``: the strategy's reference asset, held throughout.
3. ``trend``: the reference asset when its month-end close is above its 10-month average,
   otherwise T-bills; switches pay costs.
4. ``risk_matched``: the reference asset scaled to the strategy's realised volatility, the rest
   in T-bills. The scale uses the full-sample volatility, so this benchmark is *ex post*.

Deflated Sharpe ratio follows Bailey and Lopez de Prado (2014) with the trial count from the
trial registry.
"""
from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
import pandas as pd

from midterm_quant import config

_N = NormalDist()

CRISES = {
    "GFC 2008-09": ("2008-09-01", "2009-03-09"),
    "Euro crisis 2011": ("2011-07-22", "2011-10-03"),
    "COVID 2020": ("2020-02-19", "2020-04-30"),
    "Rates 2022": ("2022-01-03", "2022-10-12"),
}


def month_end(x: pd.Series) -> pd.Series:
    x = x.dropna()
    return x.groupby(x.index.to_period("M")).last()


def rf_monthly(dtb3_pct: pd.Series) -> pd.Series:
    """Monthly risk-free return from DTB3 (percent per year): monthly mean / 12."""
    s = dtb3_pct.dropna()
    return (s.groupby(s.index.to_period("M")).mean() / 100.0 / 12.0).rename("rf")


def _window(m: pd.Series, end: str) -> pd.Series:
    last_complete = pd.Period(pd.Timestamp(end), "M")
    if pd.Timestamp(end) != pd.Timestamp(end) + pd.offsets.MonthEnd(0):
        last_complete = last_complete - 1
    return m[m.index <= last_complete]


def monthly_returns(nav: pd.Series, end: str = config.BACKTEST_END) -> pd.Series:
    m = _window(month_end(nav), end)
    return m.pct_change().iloc[1:]  # first month-end is the base


def drawdown_stats(nav: pd.Series) -> dict:
    nav = nav.dropna()
    peak = nav.cummax()
    dd = nav / peak - 1.0
    trough = dd.idxmin()
    peak_date = nav[:trough].idxmax()
    after = nav[trough:]
    rec = after[after >= nav[peak_date]]
    recovery = rec.index[0] if len(rec) else None
    under = (dd < 0).astype(int)
    # longest spell under water, in calendar days
    spells, start = [], None
    for t, u in under.items():
        if u and start is None:
            start = t
        elif not u and start is not None:
            spells.append((t - start).days)
            start = None
    if start is not None:
        spells.append((nav.index[-1] - start).days)
    return {
        "MaxDD": float(dd.min()),
        "MaxDD_peak": peak_date.date().isoformat(),
        "MaxDD_trough": trough.date().isoformat(),
        "MaxDD_recovered": recovery.date().isoformat() if recovery is not None else "not recovered",
        "MaxDD_days_to_recover": int((recovery - trough).days) if recovery is not None else None,
        "Longest_underwater_days": int(max(spells)) if spells else 0,
    }


def _beta(y: pd.Series, x: pd.Series) -> float:
    j = y.index.intersection(x.index)
    if len(j) < 12:
        return float("nan")
    a, b = y[j].to_numpy(), x[j].to_numpy()
    v = np.var(b, ddof=1)
    return float(np.cov(a, b, ddof=1)[0, 1] / v) if v > 0 else float("nan")


def psr(sr: float, n: int, skew: float, kurt: float, sr_star: float = 0.0) -> float:
    """Probabilistic Sharpe ratio (per-period SR, n observations, non-excess kurtosis)."""
    if not (math.isfinite(sr) and n > 2):
        return float("nan")
    den = 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr * sr
    if den <= 0:
        return float("nan")
    return float(_N.cdf((sr - sr_star) * math.sqrt(n - 1) / math.sqrt(den)))


def expected_max_sr(n_trials: int, var_sr: float) -> float:
    """Expected maximum per-period Sharpe among ``n_trials`` unskilled trials (Bailey-LdP)."""
    if n_trials < 2 or not (var_sr > 0):
        return 0.0
    g = 0.5772156649
    return math.sqrt(var_sr) * ((1 - g) * _N.inv_cdf(1 - 1.0 / n_trials) + g * _N.inv_cdf(1 - 1.0 / (n_trials * math.e)))


def benchmarks(ref_px: pd.Series, rf_m: pd.Series, target_vol_m: float, cost_bps: float,
               end: str = config.BACKTEST_END) -> dict[str, pd.Series]:
    """Monthly return series for cash, buy-and-hold, 10-month trend and risk-matched benchmarks."""
    px = _window(month_end(ref_px), end)
    r = px.pct_change().iloc[1:]
    rf = rf_m.reindex(r.index).fillna(0.0)
    sma10 = px.rolling(10).mean()
    signal = (px > sma10).astype(float).shift(1).reindex(r.index).fillna(0.0)  # decided at prior month-end
    switches = signal.diff().abs().fillna(signal.iloc[0] if len(signal) else 0.0)
    trend = signal * r + (1 - signal) * rf - switches * cost_bps / 1e4
    vol_b = r.std(ddof=1)
    scale = float(target_vol_m / vol_b) if vol_b > 0 else 0.0
    risk_matched = scale * r + (1 - scale) * rf
    return {"cash": rf.copy(), "buy_hold": r, "trend": trend, "risk_matched": risk_matched,
            "_scale": pd.Series([scale])}


def evaluate(nav: pd.Series, rf_pct: pd.Series, ref_px: pd.Series, ref_name: str, spy_px: pd.Series,
             gross: pd.Series, net: pd.Series, turnover_per_year: float, n_trials: int, var_sr_m: float,
             cost_bps: float, end: str = config.BACKTEST_END) -> dict:
    """The standard metric set for one strategy NAV (daily, any calendar)."""
    r = monthly_returns(nav, end)
    rf_m = rf_monthly(rf_pct)
    rf = rf_m.reindex(r.index).fillna(0.0)
    ex = r - rf
    n = len(ex)
    years = n / 12.0
    sd = ex.std(ddof=1)
    sr_m = ex.mean() / sd if sd > 0 else float("nan")
    skew = float(((ex - ex.mean()) ** 3).mean() / sd ** 3) if sd > 0 else float("nan")
    kurt = float(((ex - ex.mean()) ** 4).mean() / sd ** 4) if sd > 0 else float("nan")
    downside = math.sqrt(np.mean(np.minimum(ex.to_numpy(), 0.0) ** 2))
    q = ex.quantile(0.05)
    total = float((1 + r).prod() - 1)
    out = {
        "Start": str(r.index[0]), "End": str(r.index[-1]), "Months": n,
        "CAGR": (1 + total) ** (1 / years) - 1 if years > 0 else float("nan"),
        "Vol": float(r.std(ddof=1) * math.sqrt(12)),
        "Sharpe": float(sr_m * math.sqrt(12)),
        "Sortino": float(ex.mean() / downside * math.sqrt(12)) if downside > 0 else float("nan"),
        "Skew": skew, "Kurtosis": kurt,
        "WorstMonth": float(r.min()), "CVaR95_month": float(r[ex <= q].mean() + 0.0),
        "AvgGross": float(gross.mean()), "AvgNet": float(net.mean()), "Turnover/yr": float(turnover_per_year),
    }
    out.update(drawdown_stats(nav[nav.index <= pd.Timestamp(end)]))
    spy_m = monthly_returns(spy_px, end)
    ref_m = monthly_returns(ref_px, end)
    out["Beta_SPY"] = _beta(r, spy_m)
    out["Beta_ref"] = _beta(r, ref_m)
    out["Corr_SPY"] = float(r.corr(spy_m.reindex(r.index)))
    # crisis correlations on daily returns, only where both series trade
    dr = nav.pct_change()
    sd_ = spy_px.pct_change()
    for label, (a, b) in CRISES.items():
        j = dr[a:b].index.intersection(sd_[a:b].index)
        out[f"CrisisCorr {label}"] = float(dr[j].corr(sd_[j])) if len(j) > 20 else float("nan")
    # probabilistic / deflated Sharpe on monthly excess returns
    out["PSR_0"] = psr(sr_m, n, skew, kurt, 0.0)
    sr_star = expected_max_sr(n_trials, var_sr_m)
    out["SR_star_ann"] = sr_star * math.sqrt(12)
    out["DSR"] = psr(sr_m, n, skew, kurt, sr_star)
    out["N_trials"] = n_trials
    # benchmarks over exactly the same months
    bm = benchmarks(ref_px, rf_m, r.std(ddof=1), cost_bps, end)
    out["Ref"] = ref_name
    out["RiskMatchScale"] = float(bm.pop("_scale").iloc[0])
    for k, b in bm.items():
        b = b.reindex(r.index)
        bex = b - rf
        bsd = bex.std(ddof=1)
        tot = float((1 + b.fillna(0)).prod() - 1)
        out[f"{k}_CAGR"] = (1 + tot) ** (1 / years) - 1 if years > 0 else float("nan")
        out[f"{k}_Sharpe"] = float(bex.mean() / bsd * math.sqrt(12)) if bsd > 0 else (0.0 if k == "cash" else float("nan"))
        eq = (1 + b.fillna(0)).cumprod()
        out[f"{k}_MaxDD"] = float((eq / eq.cummax() - 1).min())
    # active return vs the risk-matched benchmark
    act = r - bm["risk_matched"].reindex(r.index)
    asd = act.std(ddof=1)
    out["IR_vs_risk_matched"] = float(act.mean() / asd * math.sqrt(12)) if asd > 0 else float("nan")
    out["t_vs_risk_matched"] = float(act.mean() / (asd / math.sqrt(n))) if asd > 0 else float("nan")
    return out


def risk_contributions(returns: pd.DataFrame) -> pd.Series:
    """Share of an equal-weight blend's variance contributed by each sleeve (sums to 1)."""
    w = np.full(returns.shape[1], 1.0 / returns.shape[1])
    cov = returns.cov().to_numpy()
    port_var = float(w @ cov @ w)
    return pd.Series(w * (cov @ w) / port_var, index=returns.columns)


def leave_one_out(returns: pd.DataFrame, rf: pd.Series) -> pd.DataFrame:
    """Blend Sharpe with every sleeve, and without each one: a sleeve earns its place only if
    removing it lowers the blend Sharpe."""
    def sharpe(df):
        b = df.mean(axis=1) - rf.reindex(df.index).fillna(0.0)
        return float(b.mean() / b.std(ddof=1) * math.sqrt(12))

    full = sharpe(returns)
    rows = [{"Sleeve": "(all)", "Blend Sharpe": full, "Delta if removed": 0.0}]
    for c in returns.columns:
        s = sharpe(returns.drop(columns=c))
        rows.append({"Sleeve": c, "Blend Sharpe": s, "Delta if removed": s - full})
    return pd.DataFrame(rows)
