"""Point-in-time alignment of heterogeneous series onto one trading calendar.

Rules that keep backtests free of look-ahead:

* FRED and DefiLlama series are re-dated to their ``available_at`` date (rules in
  ``data/catalog.py``: H.4.1 Thursday 16:30, H.10 weekly on Monday, ...), so a strategy only
  sees a value on the first bar at whose close it had actually been published.
* With ``vintages=True`` (the default for backtests) revision-prone FRED series are replaced
  by their first-print values reconstructed from ALFRED vintages (``data/vintages.py``), so
  later revisions never leak into a historical decision.
* Market prices are joined as-of the bar date (the close is known at the close; the
  engine executes on the next bar's open).
* Rows before a series' first observation are back-filled with that first value only so
  Backtrader has a well-formed feed; strategies must check ``inception`` (exposed via
  ``TargetWeightStrategy.available``) before using such a series.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from midterm_quant.data import catalog
from midterm_quant.data.sources import fetch_fred, fetch_stablecoin_supply, fetch_yahoo


def is_fred(name: str) -> bool:
    return name.startswith("fred:")


def _as_available(name: str, s: pd.Series) -> pd.DataFrame:
    s = s.dropna().copy()
    s.index = catalog.available_dates(name, s.index)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return pd.DataFrame({"open": s, "high": s, "low": s, "close": s, "volume": 0.0})


def fred_values(name: str, vintages: bool = True, end=None) -> pd.Series:
    """Observation-dated FRED values: first prints where revisions matter, else the latest file."""
    sid = name.split(":", 1)[1]
    if vintages and catalog.meta(name).revisions == "material":
        from midterm_quant.data.vintages import first_print

        fp = first_print(sid, end=end)
        if fp is not None:
            return fp["value"]
    return fetch_fred(sid)


def _fred_frame(name: str, vintages: bool = True, end=None) -> pd.DataFrame:
    return _as_available(name, fred_values(name, vintages, end))


def _llama_frame(name: str) -> pd.DataFrame:
    if name != "llama:stablecoins":
        raise ValueError(name)
    return _as_available(name, fetch_stablecoin_supply())


def net_liquidity_bn() -> pd.Series:
    """WALCL - WDTGAL - RRP on each Wednesday, USD billions, observation-dated (Wednesday)."""
    from midterm_quant.indicators import net_liquidity_bn as nl

    w, t, r = fetch_fred("WALCL"), fetch_fred("WDTGAL"), fetch_fred("RRPONTSYD")
    weds = w.index.intersection(t.index)
    rrp = r.reindex(r.index.union(weds)).ffill(limit=3).reindex(weds).fillna(0.0)  # RRP is 0 on non-operating days
    return pd.Series(nl(w[weds].to_numpy(), t[weds].to_numpy(), rrp.to_numpy()), index=weds, name="netliq_bn")


def load_raw(name: str, vintages: bool = True, end=None) -> pd.DataFrame:
    if name == "derived:netliq_bn":
        return _as_available(name, net_liquidity_bn())
    if is_fred(name):
        return _fred_frame(name, vintages, end)
    if name.startswith("llama:"):
        return _llama_frame(name)
    return fetch_yahoo(name)


@dataclass
class Panel:
    calendar: pd.DatetimeIndex
    frames: dict = field(default_factory=dict)      # name -> aligned OHLCV DataFrame
    inception: dict = field(default_factory=dict)   # name -> first real observation on calendar
    last_real: dict = field(default_factory=dict)   # name -> last calendar date with a real (not filled) value

    def close(self, name: str) -> pd.Series:
        return self.frames[name]["close"]


def make_calendar(kind: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    if kind == "crypto":
        return pd.date_range(start.normalize(), end.normalize(), freq="D")
    if kind == "nyse":
        spy = fetch_yahoo("SPY").index
        return spy[(spy >= start) & (spy <= end)]
    raise ValueError(f"unknown calendar {kind!r}")


def last_real_date(raw: pd.DataFrame, calendar: pd.DatetimeIndex) -> pd.Timestamp | None:
    """Last date (on or before the calendar end) at which the series had a genuine value."""
    idx = raw["close"].dropna().index
    idx = idx[idx <= calendar[-1]]
    return idx.max() if len(idx) else None


def align(raw: pd.DataFrame, calendar: pd.DatetimeIndex, ffill_limit: int | None) -> tuple[pd.DataFrame, pd.Timestamp | None]:
    raw = raw[~raw.index.duplicated(keep="last")].sort_index()
    union = raw.index.union(calendar)
    df = raw.reindex(union)
    observed = df["close"].notna()
    df["close"] = df["close"].ffill(limit=ffill_limit)
    filled = ~observed & df["close"].notna()
    for k in ("open", "high", "low"):
        df.loc[filled, k] = df.loc[filled, "close"]
    df["volume"] = df["volume"].where(~filled, 0.0)
    df = df.reindex(calendar)
    real = df["close"].notna()
    inception = df.index[real.argmax()] if real.any() else None
    if inception is not None:
        # Pre-inception placeholder rows (guarded by `inception`); never back-fill gaps
        # *inside* the history, which would leak future values.
        lead = df.index < inception
        df.loc[lead, ["open", "high", "low", "close"]] = df.loc[inception, ["open", "high", "low", "close"]].to_numpy()
        df.loc[lead, "volume"] = 0.0
    df = df.ffill()
    df["volume"] = df["volume"].fillna(0.0)
    return df[["open", "high", "low", "close", "volume"]].astype(float), inception


def build_panel(names, calendar: str = "nyse", start=None, end=None, vintages: bool = True) -> Panel:
    start = pd.Timestamp(start or "1990-01-01")
    end = pd.Timestamp(end or pd.Timestamp.today().normalize())
    cal = make_calendar(calendar, start, end)
    panel = Panel(calendar=cal)
    for name in dict.fromkeys(names):  # de-duplicate, keep order
        raw = load_raw(name, vintages, end)
        limit = None if (is_fred(name) or name.startswith(("llama:", "derived:"))) else (5 if calendar == "nyse" else 4)
        df, inc = align(raw, cal, limit)
        if inc is None:
            raise ValueError(f"{name}: no observations between {start.date()} and {end.date()}")
        panel.frames[name] = df
        panel.inception[name] = inc
        panel.last_real[name] = last_real_date(raw, cal)
    return panel
