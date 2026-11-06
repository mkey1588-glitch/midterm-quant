"""Independent re-implementation of two strategies to reconcile against Backtrader.

E1 (one ETF, weekly) and C1 (two coins, 7-day calendar, weekly) are rebuilt here with plain
pandas/numpy - different code for the signals and a hand-written broker - and run on exactly
the same aligned data. The reconciliation compares, rebalance by rebalance and day by day:

* signals: target weights at every decision;
* orders: count, sides and sizes;
* executions: fill prices (next bar's open) and commissions;
* cash and NAV: interest credited on idle cash and the end-to-end NAV path.

The reference broker follows the documented rules in ``engine/base.py``: decide at the close of
bar t, size each order as (target - current weight) x NAV_t / close_t, skip changes under 2pp,
sell first, fill at the open of t+1 with commission = cost x |notional|; interest on idle cash
= cash after bar t's fills x DTB3_t / periods, credited at the start of bar t+1.

This is a second engine for the same rules, not a LEAN port. The LEAN versions of E1 and C1
live in ``lean/`` and have not been run (no Docker on the research machine).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from midterm_quant import config
from midterm_quant.engine.runner import load_panel_for, run_backtest
from midterm_quant.strategies.crypto import C1CryptoTrendVolTarget
from midterm_quant.strategies.equities import E1PresidentialCycleTrend


def _period_key(d: pd.Timestamp, freq: str):
    return d.isocalendar()[:2] if freq == "W" else (d.year, d.month) if freq == "M" else d


def e1_targets(panel, cls) -> dict:
    spy = panel.close("SPY")
    sma = spy.rolling(200).mean()
    out = {}
    for d in spy.index:
        y, m = d.year, d.month
        sweet = (y % 4 == 2 and m >= 10) or (y % 4 == 3)
        up = spy[d] > sma[d]
        out[d] = {"SPY": (1.0 if up else 0.6) if sweet else (0.7 if up else 0.3)}
    return out


def c1_targets(panel, cls) -> dict:
    assets = list(cls.ASSETS)
    cal = panel.calendar
    out = {}
    lr = {a: np.log(panel.close(a)).diff() for a in assets}
    rv = {a: lr[a].rolling(30).std(ddof=1) * np.sqrt(365) for a in assets}
    inc = {a: cal.get_loc(panel.inception[a]) for a in assets}
    for i, d in enumerate(cal):
        live = [a for a in assets if i - inc[a] >= 125]
        w = {}
        for a in live:
            px = panel.close(a)
            score = np.mean([px.iloc[i] / px.iloc[i - n] - 1 > 0 for n in (20, 60, 120)])
            vt = min(1.0, 0.6 / rv[a].iloc[i]) if rv[a].iloc[i] > 0 else 0.0
            w[a] = score * vt / len(live)
        out[d] = w
    return out


def simulate(cls, target_fn, cash0: float = 1_000_000.0) -> dict:
    panel = load_panel_for(cls)
    cal = panel.calendar
    assets = list(cls.ASSETS)
    periods = 365 if cls.CALENDAR == "crypto" else 252
    start = pd.Timestamp(cls.START)
    rate = panel.close("fred:DTB3") / 100.0
    targets_all = target_fn(panel, cls)
    cost = {a: config.cost_bps(a) / 1e4 for a in assets}
    units = {a: 0.0 for a in assets}
    cash, pending, pending_interest = cash0, [], 0.0
    nav, decisions, fills = {}, [], []
    last_key, started = None, False
    for i, d in enumerate(cal):
        # 1. start of bar: credit yesterday's interest, then fill yesterday's orders at today's open
        cash += pending_interest
        pending_interest = 0.0
        for a, size in pending:
            px = panel.frames[a]["open"].iloc[i]
            comm = abs(size * px) * cost[a]
            if size > 0 and size * px + comm > cash + 1e-6:      # broker rejects buys it cannot pay for
                fills.append({"date": d, "asset": a, "size": 0.0, "price": px, "commission": 0.0, "status": "Rejected"})
                continue
            cash -= size * px + comm
            units[a] += size
            fills.append({"date": d, "asset": a, "size": size, "price": px, "commission": comm, "status": "Completed"})
        pending = []
        # 2. interest on idle cash, credited next bar
        r = rate.iloc[i]
        if np.isfinite(r) and r > 0 and cash > 0:
            pending_interest = cash * r / periods
        # 3. close-of-bar valuation and decision
        value = cash + sum(units[a] * panel.close(a).iloc[i] for a in assets)
        nav[d] = value
        key = _period_key(d, cls.REBALANCE)
        new = key != last_key
        last_key = key
        if i + 1 < cls.WARMUP or d < start:
            continue
        if not new and started:
            continue
        started = True
        tgt = {a: float(v) for a, v in targets_all[d].items()}
        longs = sum(v for v in tgt.values() if v > 0)
        if longs > cls.MAX_LONG:
            tgt = {a: v * cls.MAX_LONG / longs for a, v in tgt.items()}
        decisions.append((d, {a: round(v, 4) for a, v in tgt.items() if abs(v) > 1e-9}))
        legs = []
        for a in assets:
            px = panel.close(a).iloc[i]
            cur = units[a] * px / value
            t = tgt.get(a, 0.0)
            closing = t == 0.0 and units[a] != 0
            if abs(t - cur) < 0.02 and not closing:
                continue
            legs.append((t - cur, a, -units[a] if closing else (t - cur) * value / px))
        legs.sort(key=lambda x: x[0])
        pending = [(a, s) for _, a, s in legs if s != 0]
    return {"nav": pd.Series(nav), "decisions": decisions, "fills": pd.DataFrame(fills)}


def reconcile(cls, target_fn) -> dict:
    bt_res = run_backtest(cls)
    ref = simulate(cls, target_fn)
    a = dict(bt_res.rebalances)
    b = {d.date(): t for d, t in ref["decisions"]}
    common = sorted(set(a) & set(b))
    tgt_mismatch = [d.isoformat() for d in common if any(abs(a[d].get(k, 0) - b[d].get(k, 0)) > 1e-3 for k in set(a[d]) | set(b[d]))]
    o = bt_res.ledger["orders"]
    o = o[o["status"] == "Completed"]
    f = ref["fills"]
    f = f[f["status"] == "Completed"]
    bt_nav = bt_res.ledger["nav"]["value"]
    ref_nav = ref["nav"].reindex(bt_nav.index)
    rel = (bt_nav / ref_nav - 1).abs()
    # fill-price comparison on matching (date, asset)
    o2 = o.assign(date=pd.to_datetime(o["fill_date"])).groupby(["date", "asset"]).agg(price=("price", "mean"), size=("size_filled", "sum"), comm=("commission", "sum"))
    f2 = f.groupby(["date", "asset"]).agg(price=("price", "mean"), size=("size", "sum"), comm=("commission", "sum"))
    j = o2.index.intersection(f2.index)
    return {
        "strategy": cls.CODE, "decisions backtrader": len(a), "decisions reference": len(b), "decisions compared": len(common),
        "target mismatches": len(tgt_mismatch), "first mismatches": tgt_mismatch[:5],
        "fills backtrader": int(len(o)), "fills reference": int(len(f)), "fills matched by date+asset": int(len(j)),
        "max fill price diff": float((o2.loc[j, "price"] - f2.loc[j, "price"]).abs().max()) if len(j) else None,
        "max size diff (units)": float((o2.loc[j, "size"] - f2.loc[j, "size"]).abs().max()) if len(j) else None,
        "commission backtrader": float(o["commission"].sum()), "commission reference": float(f["commission"].sum()),
        "max daily NAV rel diff": float(rel.max()), "final NAV backtrader": float(bt_nav.iloc[-1]), "final NAV reference": float(ref_nav.iloc[-1]),
        "final NAV rel diff": float(bt_nav.iloc[-1] / ref_nav.iloc[-1] - 1),
    }


def run() -> list[dict]:
    return [reconcile(E1PresidentialCycleTrend, e1_targets), reconcile(C1CryptoTrendVolTarget, c1_targets)]
