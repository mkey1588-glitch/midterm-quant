"""Does election information add predictive value? A nested walk-forward ablation.

Question: once ordinary price-trend information is in a model of next-month S&P 500 excess
returns, do seasonality, policy/election features and macro state add out-of-sample value?

Design (fixed before the first run on 6 Nov 2026):

* Target: next-month S&P 500 price return minus the 3-month bill (TB3MS / 12). Price index
  only, so dividends are missing on both the timing rule and buy-and-hold; that biases the
  comparison slightly in favour of timing (it holds bills, which carry their full yield).
* Feature blocks, added in this order:
    1. trend   - 12-1 month momentum; index above its 10-month average
    2. season  - presidential-cycle window (1 Oct midterm year to 31 Dec pre-election year)
    3. policy  - EPU news index z-score (3 years); post-midterm 12-month dummy
    4. macro   - term spread (GS10 - TB3MS), credit spread (Baa - Aaa), 6-month change in GS10
  then 5. costs - the step-4 model's timing rule net of 2bp per switch.
  Monthly macro averages for month m are published early in month m+1, so features dated at
  month-end t use month t-1 values.
* Sample: 1986-01 (first full EPU year) to the last complete month. The first out-of-sample
  forecast is for 1996-01 (10 years of training).
* Nested walk-forward: every January the model is refitted on all data to date (expanding).
  The ridge penalty is chosen *inside* that training window by a time-series split (fit on
  the earlier part, validate on the last 60 months) from LAMBDAS. Every (block, lambda) pair
  counts as a trial in ``n_trials``.
* Evaluation on the out-of-sample months only: R^2_OS against the expanding historical mean
  (Campbell-Thompson), Clark-West test for nested models, and a long/cash timing rule
  (invest when the forecast is positive).

None of this is a holdout: the S&P 500 history was seen during development. The only clean
test is prospective (docs/07_validation_plan.md).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from midterm_quant import config
from midterm_quant.data.sources import fetch_fred, fetch_yahoo

LAMBDAS = (0.0, 0.1, 1.0, 10.0, 100.0, 1000.0)
BLOCKS = {
    "1 trend": ["mom12_1", "above10m"],
    "2 + season": ["mom12_1", "above10m", "sweet_spot"],
    "3 + policy": ["mom12_1", "above10m", "sweet_spot", "epu_z", "post_midterm"],
    "4 + macro": ["mom12_1", "above10m", "sweet_spot", "epu_z", "post_midterm", "term", "credit", "d_gs10_6m"],
}
COST_BPS = 2.0
OOS_START = "1996-01"
SAMPLE_START = "1986-01"


def _monthly(s: pd.Series, how: str = "last") -> pd.Series:
    s = s.dropna()
    g = s.groupby(s.index.to_period("M"))
    return g.last() if how == "last" else g.mean()


def features() -> pd.DataFrame:
    px = _monthly(fetch_yahoo("^GSPC")["close"])
    tb = fetch_fred("TB3MS")
    tb.index = tb.index.to_period("M")
    rf = tb / 100 / 12
    ret = px.pct_change()
    df = pd.DataFrame({"ret": ret, "rf": rf.reindex(px.index)})
    df["excess_next"] = (df["ret"] - df["rf"]).shift(-1)
    df["mom12_1"] = px.shift(1) / px.shift(12) - 1
    df["above10m"] = (px > px.rolling(10).mean()).astype(float)
    m = pd.Series(df.index.month, index=df.index)
    y = pd.Series(df.index.year, index=df.index)
    df["sweet_spot"] = (((y % 4 == 2) & (m >= 10)) | (y % 4 == 3)).astype(float)
    # post-midterm dummy: the 12 month-ends after a midterm election (Nov midterm year .. Oct next)
    df["post_midterm"] = (((y % 4 == 2) & (m >= 11)) | ((y % 4 == 3) & (m <= 10))).astype(float)

    def lagged(sid):
        s = fetch_fred(sid)
        s.index = s.index.to_period("M")
        return s.shift(1).reindex(df.index)  # month t-1 value is what is published by end of month t

    epu = lagged("USEPUINDXM")
    df["epu_z"] = (epu - epu.rolling(36).mean()) / epu.rolling(36).std()
    gs10, tb3 = lagged("GS10"), lagged("TB3MS")
    df["term"] = gs10 - tb3
    df["credit"] = lagged("BAA") - lagged("AAA")
    df["d_gs10_6m"] = gs10 - gs10.shift(6)
    end = pd.Period(pd.Timestamp(config.BACKTEST_END), "M") - 1
    return df[(df.index >= pd.Period(SAMPLE_START, "M")) & (df.index <= end)]


def _ridge(X: np.ndarray, y: np.ndarray, lam: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    Z1 = np.column_stack([np.ones(len(Z)), Z])
    pen = lam * np.eye(Z1.shape[1])
    pen[0, 0] = 0.0
    # numpy 2.0 + macOS Accelerate emits spurious FP warnings in small matmuls; results are
    # checked for finiteness instead.
    with np.errstate(all="ignore"):
        beta = np.linalg.solve(Z1.T @ Z1 + pen, Z1.T @ y)
    if not np.all(np.isfinite(beta)):
        raise FloatingPointError("non-finite ridge coefficients")
    return beta, mu, sd


def _predict(beta, mu, sd, X):
    with np.errstate(all="ignore"):
        return np.column_stack([np.ones(len(X)), (X - mu) / sd]) @ beta


def walk_forward(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    d = df.dropna(subset=cols + ["excess_next"])
    oos = d.index[d.index >= pd.Period(OOS_START, "M")]
    preds, lam_used, bench = {}, {}, {}
    for year in sorted({p.year for p in oos}):
        train = d[d.index < pd.Period(f"{year}-01", "M")]
        test = d[(d.index >= pd.Period(f"{year}-01", "M")) & (d.index <= pd.Period(f"{year}-12", "M"))]
        if len(train) < 120 or not len(test):
            continue
        # inner selection of lambda: fit on all but the last 60 training months
        fit, val = train.iloc[:-60], train.iloc[-60:]
        errs = {}
        for lam in LAMBDAS:
            b, mu, sd = _ridge(fit[cols].to_numpy(float), fit["excess_next"].to_numpy(float), lam)
            e = val["excess_next"].to_numpy() - _predict(b, mu, sd, val[cols].to_numpy(float))
            errs[lam] = float(np.mean(e ** 2))
        lam = min(errs, key=errs.get)
        b, mu, sd = _ridge(train[cols].to_numpy(float), train["excess_next"].to_numpy(float), lam)
        p = _predict(b, mu, sd, test[cols].to_numpy(float))
        for t, v in zip(test.index, p):
            preds[t], lam_used[t], bench[t] = v, lam, float(train["excess_next"].mean())
    out = pd.DataFrame({"pred": pd.Series(preds), "lambda": pd.Series(lam_used), "hist_mean": pd.Series(bench)})
    out["actual"] = d["excess_next"].reindex(out.index)
    out["ret_next"] = (d["ret"].shift(-1)).reindex(out.index)
    out["rf_next"] = (d["rf"].shift(-1)).reindex(out.index)
    return out.dropna()


def clark_west(actual, pred_small, pred_big) -> tuple[float, float]:
    """Clark-West (2007) adjusted MSPE test; positive t = bigger model adds value. NW(3) SE."""
    e1, e2 = actual - pred_small, actual - pred_big
    f = e1 ** 2 - (e2 ** 2 - (pred_small - pred_big) ** 2)
    f = np.asarray(f, float)
    n = len(f)
    u = f - f.mean()
    lr = u @ u / n
    for lag in range(1, 4):
        w = 1 - lag / 4
        lr += 2 * w * (u[lag:] @ u[:-lag]) / n
    t = f.mean() / math.sqrt(lr / n) if lr > 0 else float("nan")
    from statistics import NormalDist
    return float(t), float(1 - NormalDist().cdf(t))


def timing_stats(wf: pd.DataFrame, cost_bps: float = 0.0) -> dict:
    pos = (wf["pred"] > 0).astype(float)
    switches = pos.diff().abs().fillna(pos.iloc[0])
    r = pos * wf["ret_next"] + (1 - pos) * wf["rf_next"] - switches * cost_bps / 1e4
    ex = r - wf["rf_next"]
    eq = (1 + r).cumprod()
    years = len(r) / 12
    return {"CAGR": float(eq.iloc[-1] ** (1 / years) - 1), "Sharpe": float(ex.mean() / ex.std(ddof=1) * math.sqrt(12)),
            "MaxDD": float((eq / eq.cummax() - 1).min()), "Time invested": float(pos.mean()), "Switches/yr": float(switches.sum() / years)}


def run() -> dict:
    df = features()
    results, preds = [], {}
    for name, cols in BLOCKS.items():
        preds[name] = walk_forward(df, cols)
    # every step is scored on the same out-of-sample months (the latest common start)
    common = preds[list(BLOCKS)[0]].index
    for wf in preds.values():
        common = common.intersection(wf.index)
    preds = {k: v.loc[common] for k, v in preds.items()}
    for name, cols in BLOCKS.items():
        wf = preds[name]
        r2 = 1 - ((wf["actual"] - wf["pred"]) ** 2).sum() / ((wf["actual"] - wf["hist_mean"]) ** 2).sum()
        cw_t, cw_p = clark_west(wf["actual"].to_numpy(), wf["hist_mean"].to_numpy(), wf["pred"].to_numpy())
        results.append({"step": name, "features": cols, "oos_start": str(wf.index[0]), "oos_end": str(wf.index[-1]),
                        "months": int(len(wf)), "R2_OS vs hist mean": float(r2), "Clark-West t vs hist mean": cw_t,
                        "CW p": cw_p, "lambda (most used)": float(wf["lambda"].mode().iloc[0]),
                        **{f"timing {k}": v for k, v in timing_stats(wf).items()}})
    # step 5: costs on the full model
    full = preds["4 + macro"]
    results.append({"step": "5 + costs", "features": BLOCKS["4 + macro"], "oos_start": str(full.index[0]), "oos_end": str(full.index[-1]),
                    "months": int(len(full)), **{f"timing {k}": v for k, v in timing_stats(full, COST_BPS).items()}})
    # incremental tests: each block vs the one before it (on common months)
    inc = []
    names = list(BLOCKS)
    for a, b in zip(names[:-1], names[1:]):
        j = preds[a].index.intersection(preds[b].index)
        t, p = clark_west(preds[a].loc[j, "actual"].to_numpy(), preds[a].loc[j, "pred"].to_numpy(), preds[b].loc[j, "pred"].to_numpy())
        dr2 = (((preds[a].loc[j, "actual"] - preds[a].loc[j, "pred"]) ** 2).sum() - ((preds[b].loc[j, "actual"] - preds[b].loc[j, "pred"]) ** 2).sum()) / ((preds[a].loc[j, "actual"] - preds[a].loc[j, "hist_mean"]) ** 2).sum()
        inc.append({"added": b, "vs": a, "delta R2_OS": float(dr2), "Clark-West t": t, "p": p})
    bh = full.copy()
    bh["pred"] = 1.0
    return {
        "design": {"target": "next-month S&P 500 price return minus TB3MS/12", "sample_start": SAMPLE_START,
                   "oos_start": OOS_START, "refit": "annual, expanding window", "inner_selection": "last 60 training months",
                   "lambdas": list(LAMBDAS), "cost_bps_per_switch": COST_BPS},
        "steps": results, "increments": inc, "buy_hold": timing_stats(bh),
        "n_trials": len(BLOCKS) * len(LAMBDAS) + 1,
        "election_feature_note": "The policy block contains the only election feature available historically (a post-midterm dummy). Deviations from pre-election expectations need archived prediction-market or poll data, which this project does not have.",
    }
