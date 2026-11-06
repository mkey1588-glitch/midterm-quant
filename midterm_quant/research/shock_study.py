"""S&P 500 after large one-day drops: a descriptive event study with its design choices exposed.

Design (fixed before any group comparison is read):

* Event: a close-to-close fall of at least ``threshold`` (default 3.5%) in the S&P 500 price
  index, 1950 onward. Clusters are collapsed to their first day: a drop counts only if no other
  qualifying drop occurred in the previous ``gap`` sessions (default 20).
* Group assignment is made on the drop day's own close and never changed afterwards:
  ``above200`` = the close is above its 200-day average *after* the drop.
* Outcomes: forward price returns at 21/63/126/252 sessions, and the further decline =
  the lowest close in the next 63 sessions relative to the drop-day close.

Two caveats are computed, not just stated: with a 20-session de-clustering gap the 12-month
windows of neighbouring events overlap, so the events are not independent; ``episodes`` groups
events whose 12-month windows overlap. And the "within 6% of the 52-week high" filter (distance
from the high at the close *before* the drop) was added on 5 Nov after looking at that day's
setup (1.7% below the high before the drop, 5.9% after it), so it is reported only as a post-hoc
cut with neighbouring thresholds.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from midterm_quant.data.sources import fetch_yahoo

H = {"1m": 21, "3m": 63, "6m": 126, "12m": 252}
SEED = 20261106


def events(px: pd.Series, threshold: float = 0.035, gap: int = 20, end=None) -> pd.DataFrame:
    px = px.dropna()
    px = px[px.index >= "1950-01-01"]
    if end is not None:
        px = px[px.index <= pd.Timestamp(end)]
    r = px.pct_change()
    sma = px.rolling(200).mean()
    hi = px.rolling(252, min_periods=60).max()
    idx = np.where(r.to_numpy() <= -threshold)[0]
    first = [i for k, i in enumerate(idx) if k == 0 or i - idx[k - 1] > gap]
    rows = []
    for i in first:
        row = {"date": px.index[i].date().isoformat(), "ret": float(r.iloc[i]),
               "dd_before": float(px.iloc[i - 1] / hi.iloc[i - 1] - 1),
               "above200": bool(px.iloc[i] > sma.iloc[i]) if i >= 199 else False, "i": i}
        for k, n in H.items():
            row[k] = float(px.iloc[i + n] / px.iloc[i] - 1) if i + n < len(px) else np.nan
        j = min(i + 63, len(px) - 1)
        row["further_dd_3m"] = float(px.iloc[i:j + 1].min() / px.iloc[i] - 1) if j > i else np.nan
        row["complete_12m"] = i + 252 < len(px)
        rows.append(row)
    df = pd.DataFrame(rows)
    # episodes: chain events whose 12-month windows overlap
    ep, cur, last_i = [], 0, None
    for i in df["i"]:
        if last_i is not None and i - last_i > 252:
            cur += 1
        ep.append(cur)
        last_i = i
    df["episode"] = ep
    return df


def summarize(df: pd.DataFrame, label: str) -> dict:
    out = {"group": label, "n": int(len(df)), "episodes": int(df["episode"].nunique()) if len(df) else 0}
    for k in H:
        v = df[k].dropna()
        out[f"{k} median"] = float(v.median()) if len(v) else np.nan
        out[f"{k} %pos"] = float((v > 0).mean()) if len(v) else np.nan
        out[f"{k} negatives"] = int((v <= 0).sum())
        out[f"{k} n"] = int(len(v))
    out["worst further fall 3m"] = float(df["further_dd_3m"].min()) if len(df) else np.nan
    out["median further fall 3m"] = float(df["further_dd_3m"].median()) if len(df) else np.nan
    return out


def overlap_pairs(df: pd.DataFrame, horizon: int = 252) -> int:
    i = df["i"].to_numpy()
    return int(sum(1 for a in range(len(i)) for b in range(a + 1, len(i)) if i[b] - i[a] < horizon))


def episode_bootstrap(df: pd.DataFrame, col: str = "12m", n: int = 10000, level: float = 0.90) -> tuple[float, float]:
    """CI for the median by resampling whole episodes (clusters of overlapping windows)."""
    d = df.dropna(subset=[col])
    groups = [g[col].to_numpy() for _, g in d.groupby("episode")]
    if len(groups) < 3:
        return np.nan, np.nan
    rng = np.random.default_rng(SEED)
    meds = []
    for _ in range(n):
        pick = rng.integers(0, len(groups), len(groups))
        meds.append(np.median(np.concatenate([groups[p] for p in pick])))
    a = (1 - level) / 2
    return float(np.quantile(meds, a)), float(np.quantile(meds, 1 - a))


def current_case(px: pd.Series, day) -> dict | None:
    """The drop on ``day`` itself: its size and group, with no forward returns yet."""
    px = px.dropna()
    day = pd.Timestamp(day)
    if day not in px.index:
        return None
    i = px.index.get_loc(day)
    hi = px.iloc[max(0, i - 252):i].max()
    sma = px.iloc[i - 199:i + 1].mean()
    return {"date": day.date().isoformat(), "ret": float(px.iloc[i] / px.iloc[i - 1] - 1),
            "dd_before": float(px.iloc[i - 1] / hi - 1), "above200": bool(px.iloc[i] > sma),
            "close": float(px.iloc[i]), "sma200": float(sma)}


def study(end=None, current=None) -> dict:
    """History of drops up to ``end`` (exclusive of the current case) plus the current case."""
    px = fetch_yahoo("^GSPC")["close"]
    base = events(px, end=end)
    groups = [summarize(base, "all events"), summarize(base[base.above200], "above 200-day after the drop"),
              summarize(base[~base.above200], "below 200-day after the drop")]
    posthoc = []
    for x in (0.04, 0.05, 0.06, 0.07, 0.08, 0.10):
        sub = base[base.above200 & (base.dd_before > -x)]
        posthoc.append({**summarize(sub, f"above 200-day and within {x:.0%} of 52w high"), "threshold": x,
                        "pre_specified": False})
    grid = []
    for thr in (0.03, 0.035, 0.04):
        for gap in (20, 63):
            ev = events(px, thr, gap, end)
            s_all, s_up = summarize(ev, "all"), summarize(ev[ev.above200], "above200")
            grid.append({"threshold": thr, "gap": gap, "n all": s_all["n"], "episodes": s_all["episodes"],
                         "n above200": s_up["n"], "above200 6m %pos": s_up["6m %pos"], "above200 12m %pos": s_up["12m %pos"],
                         "above200 12m negatives": s_up["12m negatives"], "all worst further fall 3m": s_all["worst further fall 3m"],
                         "above200 worst further fall 3m": s_up["worst further fall 3m"], "12m overlapping pairs": overlap_pairs(ev)})
    up = base[base.above200]
    return {
        "history_end": str(end), "current_case": current_case(px, current) if current else None,
        "design": {"threshold": 0.035, "gap": 20, "since": "1950-01-01", "group_rule": "close vs 200-day average on the drop day",
                   "posthoc_note": "The near-the-high filter (distance from the 52-week high at the close before the drop) was added on 5 Nov 2026 after seeing that day's setup (1.7% below the high before the drop, 5.9% after it); the 6% threshold is not pre-specified."},
        "events": base.drop(columns=["i"]).to_dict(orient="records"),
        "groups": groups, "posthoc_filters": posthoc, "sensitivity": grid,
        "overlap_pairs_12m": overlap_pairs(base), "episodes": int(base["episode"].nunique()),
        "above200_12m_median_ci90_episode_bootstrap": episode_bootstrap(up),
        "all_12m_median_ci90_episode_bootstrap": episode_bootstrap(base),
    }
