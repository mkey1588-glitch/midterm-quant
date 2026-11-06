"""Point-in-time (first-print) reconstruction of revision-prone FRED series from ALFRED.

A backtest that reads today's FRED file uses *revised* history: a value dated 2021-03-03
may have been changed in 2023 when trade weights or a model were re-estimated. Here each
observation instead takes the value from the first ALFRED vintage that contained it.

Vintages are sampled on the first business day of every month (plus the run's end date), so
"first print" means "as published at most one month after release". Observations older than
the earliest archived vintage can only be taken from that earliest vintage; they are flagged
``pre_archive`` and reported in the data manifest, because they may include revisions.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from midterm_quant import config
from midterm_quant.data.sources import fetch_fred, fetch_fred_vintage

_PROBE_FILE = "first_vintage.json"


def _probe_cache() -> dict:
    p = config.CACHE_DIR / "alfred" / _PROBE_FILE
    return json.loads(p.read_text()) if p.exists() else {}


def _save_probe(d: dict) -> None:
    p = config.CACHE_DIR / "alfred" / _PROBE_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=1, sort_keys=True))


def _bday_month_starts(start: pd.Timestamp, end: pd.Timestamp) -> list[str]:
    ms = pd.date_range(start.to_period("M").to_timestamp(), end, freq="BMS")
    return [d.date().isoformat() for d in ms]


def first_vintage(sid: str, earliest_year: int = 1995) -> str | None:
    """Earliest monthly vintage date (first business day of a month) that ALFRED serves."""
    cache = _probe_cache()
    if sid in cache:
        return cache[sid]
    today = pd.Timestamp.today().normalize()
    found = None
    for year in range(earliest_year, today.year + 1):
        vd = pd.date_range(f"{year}-01-01", periods=1, freq="BMS")[0].date().isoformat()
        if len(fetch_fred_vintage(sid, vd)):
            found = year
            break
    if found is None:
        cache[sid] = None
    else:
        months = _bday_month_starts(pd.Timestamp(f"{found - 1}-01-01"), pd.Timestamp(f"{found}-01-31"))
        first = next(m for m in months if len(fetch_fred_vintage(sid, m)))
        cache[sid] = first
    _save_probe(cache)
    return cache[sid]


def first_print(sid: str, end=None) -> pd.DataFrame | None:
    """DataFrame indexed by observation date: value, vintage (date first seen), pre_archive."""
    end = pd.Timestamp(end or config.BACKTEST_END)
    fv = first_vintage(sid)
    if fv is None:
        return None
    dates = _bday_month_starts(pd.Timestamp(fv), end)
    end_iso = (end + pd.Timedelta(days=1)).date().isoformat()  # vintage as of the day after the close
    if end_iso not in dates:
        dates.append(end_iso)
    parts, seen = [], None
    for i, vd in enumerate(dates):
        s = fetch_fred_vintage(sid, vd)
        if not len(s):
            continue
        new = s if seen is None else s[s.index > seen]
        if len(new):
            parts.append(pd.DataFrame({"value": new, "vintage": vd, "pre_archive": i == 0}))
            seen = new.index.max()
    if not parts:
        return None
    return pd.concat(parts).sort_index()


def revision_audit(sid: str, vintage_dates) -> pd.DataFrame:
    """How much each past vintage differs from today's file on the observations they share."""
    latest = fetch_fred(sid)
    rows = []
    for vd in vintage_dates:
        old = fetch_fred_vintage(sid, vd)
        j = old.index.intersection(latest.index)
        if not len(j):
            rows.append({"series": sid, "vintage": vd, "overlap": 0})
            continue
        d = (latest[j] - old[j]).abs()
        rel = d / latest[j].abs().replace(0, np.nan)
        rows.append({
            "series": sid, "vintage": vd, "overlap": int(len(j)),
            "share_changed": float((d > 1e-9).mean()),
            "max_abs_diff": float(d.max()),
            "mean_abs_diff": float(d.mean()),
            "max_rel_diff": float(rel.max()) if rel.notna().any() else float("nan"),
            "missing_in_latest": int(len(old.index.difference(latest.index))),
        })
    return pd.DataFrame(rows)
