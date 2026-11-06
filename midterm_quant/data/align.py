"""Point-in-time alignment of heterogeneous series onto one trading calendar.

Rules that keep backtests free of look-ahead:

* FRED series are shifted forward by their *publication lag* before being joined, so a
  strategy only sees a value on the first bar after it was actually published.
* Market prices are joined as-of the bar date (the close is known at the close; the
  engine executes on the next bar's open).
* Rows before a series' first observation are back-filled with that first value only so
  Backtrader has a well-formed feed; strategies must check ``inception`` (exposed via
  ``TargetWeightStrategy.available``) before using such a series.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
from pandas.tseries.offsets import BDay

from midterm_quant.data.sources import fetch_fred, fetch_stablecoin_supply, fetch_yahoo

# Publication lag in business days for FRED series (default 1 for daily market series).
FRED_LAG_BDAYS = {
    "WALCL": 2,        # H.4.1, Wednesday level released Thursday 16:30 ET
    "WTREGEN": 2,      # H.4.1
    "RRPONTSYD": 1,
    "THREEFYTP10": 5,  # Kim-Wright term premium, updated with a short delay
    "GASREGW": 1,
    "USEPUINDXD": 1,
    "CPIAUCSL": 32,    # monthly, dated 1st of month, released mid-following month
    "UNRATE": 26,
}
MONTHLY_DEFAULT_LAG = 32


def is_fred(name: str) -> bool:
    return name.startswith("fred:")


def _fred_frame(name: str) -> pd.DataFrame:
    sid = name.split(":", 1)[1]
    s = fetch_fred(sid)
    if len(s) > 3:
        median_gap = s.index.to_series().diff().dt.days.median()
    else:
        median_gap = 1
    lag = FRED_LAG_BDAYS.get(sid, MONTHLY_DEFAULT_LAG if median_gap > 20 else 1)
    s = s.copy()
    s.index = s.index + BDay(lag)
    s = s[~s.index.duplicated(keep="last")]
    return pd.DataFrame({"open": s, "high": s, "low": s, "close": s, "volume": 0.0})


def _llama_frame(name: str) -> pd.DataFrame:
    if name != "llama:stablecoins":
        raise ValueError(name)
    s = fetch_stablecoin_supply().copy()
    s.index = s.index + pd.Timedelta(days=1)  # daily snapshot, usable the next day
    return pd.DataFrame({"open": s, "high": s, "low": s, "close": s, "volume": 0.0})


def load_raw(name: str) -> pd.DataFrame:
    if is_fred(name):
        return _fred_frame(name)
    if name.startswith("llama:"):
        return _llama_frame(name)
    return fetch_yahoo(name)


@dataclass
class Panel:
    calendar: pd.DatetimeIndex
    frames: dict = field(default_factory=dict)      # name -> aligned OHLCV DataFrame
    inception: dict = field(default_factory=dict)   # name -> first real observation on calendar

    def close(self, name: str) -> pd.Series:
        return self.frames[name]["close"]


def make_calendar(kind: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    if kind == "crypto":
        return pd.date_range(start.normalize(), end.normalize(), freq="D")
    if kind == "nyse":
        spy = fetch_yahoo("SPY").index
        return spy[(spy >= start) & (spy <= end)]
    raise ValueError(f"unknown calendar {kind!r}")


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


def build_panel(names, calendar: str = "nyse", start=None, end=None) -> Panel:
    start = pd.Timestamp(start or "1990-01-01")
    end = pd.Timestamp(end or pd.Timestamp.today().normalize())
    cal = make_calendar(calendar, start, end)
    panel = Panel(calendar=cal)
    for name in dict.fromkeys(names):  # de-duplicate, keep order
        raw = load_raw(name)
        limit = None if (is_fred(name) or name.startswith("llama:")) else (5 if calendar == "nyse" else 4)
        df, inc = align(raw, cal, limit)
        if inc is None:
            raise ValueError(f"{name}: no observations between {start.date()} and {end.date()}")
        panel.frames[name] = df
        panel.inception[name] = inc
    return panel
