"""Free daily data sources with an on-disk cache.

* Yahoo Finance chart API  -> total-return adjusted OHLCV for ETFs, indices, futures, crypto
* FRED (fredgraph.csv)     -> macro / rates / liquidity series (no API key required)

Every series is cached as CSV under ``config.CACHE_DIR``; a cached file younger than
``max_age_hours`` is reused so repeated backtests are offline and deterministic.

Provenance. Each download also writes ``<file>.meta.json`` (URL, UTC retrieval time, SHA-256,
row count, first and last observation) and, when the content changed, an immutable copy
under ``vintages/<kind>/<name>/<retrieved_at>.csv``. Snapshots are never overwritten, so a
later revision of a series cannot silently replace what was known earlier.

ALFRED. ``fetch_fred_vintage`` returns a FRED series exactly as it was published on a past
date (St. Louis Fed's archival service; no API key needed for the CSV endpoint).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import io
import json
import shutil
import time
import urllib.parse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
warnings.filterwarnings("ignore", message=".*OpenSSL.*")
import requests  # noqa: E402

from midterm_quant import config

_UA = {"User-Agent": "Mozilla/5.0 (research; midterm_quant)"}
_YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
_FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"


def _cache_path(kind: str, name: str) -> Path:
    safe = name.replace("^", "IDX_").replace("=", "_").replace("/", "_").replace(":", "_")
    p = config.CACHE_DIR / kind / f"{safe}.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def meta_path(path: Path) -> Path:
    return path.with_suffix(".meta.json")


def _record(path: Path, kind: str, name: str, url: str, index: pd.Index, vintage_id: str) -> None:
    """Write the provenance sidecar and keep an immutable snapshot of changed content."""
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    sha = _sha256(path)
    info = {
        "name": name, "kind": kind, "url": url, "retrieved_at_utc": now.isoformat(),
        "sha256": sha, "bytes": path.stat().st_size, "rows": int(len(index)),
        "first_obs": index.min().date().isoformat() if len(index) else None,
        "last_obs": index.max().date().isoformat() if len(index) else None,
        "vintage_id": vintage_id or f"latest@{now.isoformat()}",
    }
    meta_path(path).write_text(json.dumps(info, indent=1))
    vdir = config.CACHE_DIR / "vintages" / kind / path.stem
    vdir.mkdir(parents=True, exist_ok=True)
    prior = sorted(vdir.glob("*.csv"))
    if not prior or _sha256(prior[-1]) != sha:
        shutil.copy2(path, vdir / f"{now.strftime('%Y%m%dT%H%M%SZ')}.csv")


def read_meta(path: Path) -> dict:
    mp = meta_path(path)
    if mp.exists():
        return json.loads(mp.read_text())
    # cache written before provenance tracking: describe what is on disk, flag the gap
    return {"retrieved_at_utc": dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).replace(microsecond=0).isoformat(),
            "sha256": _sha256(path), "bytes": path.stat().st_size, "vintage_id": "unrecorded (pre-provenance cache; mtime used)"}


def _fresh(path: Path, max_age_hours: float) -> bool:
    """A cached file is reused while younger than ``max_age_hours``; MQ_MAX_AGE_HOURS overrides
    it (``OFFLINE=1 scripts/reproduce.sh`` sets a huge value to freeze the snapshot)."""
    import os

    max_age_hours = float(os.environ.get("MQ_MAX_AGE_HOURS", max_age_hours))
    return path.exists() and (time.time() - path.stat().st_mtime) < max_age_hours * 3600


def _get(url: str, params: dict | None = None, retries: int = 4) -> requests.Response:
    delay = 2.0
    for attempt in range(retries):
        r = requests.get(url, params=params, headers=_UA, timeout=30)
        if r.status_code == 200:
            return r
        if r.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
            time.sleep(delay)
            delay *= 2
            continue
        r.raise_for_status()
    raise RuntimeError(f"failed to download {url}")


def fetch_yahoo(symbol: str, max_age_hours: float = 20.0, refresh: bool = False) -> pd.DataFrame:
    """Daily OHLCV, adjusted for splits *and* dividends (total-return prices).

    Index: tz-naive dates in the exchange's local calendar (UTC days for crypto).
    """
    path = _cache_path("yahoo", symbol)
    if not refresh and _fresh(path, max_age_hours):
        return pd.read_csv(path, index_col=0, parse_dates=True)

    params = {
        "period1": -2208988800,  # 1900-01-01; 0 would truncate history at 1970
        "period2": int(time.time()) + 86400,
        "interval": "1d",
        "events": "div,split",
        "includeAdjustedClose": "true",
    }
    r = _get(_YAHOO.format(sym=urllib.parse.quote(symbol)), params=params)
    res = r.json()["chart"]["result"][0]
    offset = res["meta"].get("gmtoffset", 0) or 0
    q = res["indicators"]["quote"][0]
    idx = pd.to_datetime(np.asarray(res["timestamp"]) + offset, unit="s").normalize()
    df = pd.DataFrame(
        {k: pd.to_numeric(pd.Series(q.get(k)), errors="coerce").to_numpy() for k in ("open", "high", "low", "close", "volume")},
        index=idx,
    )
    adj = res["indicators"].get("adjclose")
    if adj:
        adjclose = pd.to_numeric(pd.Series(adj[0]["adjclose"]), errors="coerce").to_numpy()
        factor = adjclose / df["close"].to_numpy()
        factor = np.where(np.isfinite(factor) & (factor > 0), factor, 1.0)
        for k in ("open", "high", "low", "close"):
            df[k] = df[k] * factor
    df = df[~df.index.duplicated(keep="last")].dropna(subset=["close"])
    # Repair missing/zero opens/highs/lows (common for indices and old history).
    for k in ("open", "high", "low"):
        bad = df[k].isna() | (df[k] <= 0)
        df.loc[bad, k] = df.loc[bad, "close"]
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    df["volume"] = df["volume"].fillna(0.0)
    df.index.name = "date"
    df.to_csv(path)
    _record(path, "yahoo", symbol, _YAHOO.format(sym=urllib.parse.quote(symbol)), df.index, "")
    time.sleep(0.25)  # be polite to the endpoint
    return df


def fetch_fred(series_id: str, max_age_hours: float = 20.0, refresh: bool = False) -> pd.Series:
    """A FRED series as a float Series indexed by observation date (missing '.' -> NaN dropped)."""
    path = _cache_path("fred", series_id)
    if not refresh and _fresh(path, max_age_hours):
        s = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        s.name = series_id
        return s
    r = _get(_FRED.format(sid=series_id))
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"])
    s = pd.to_numeric(df.set_index("date")[series_id], errors="coerce").dropna()
    s.to_frame().to_csv(path)
    _record(path, "fred", series_id, _FRED.format(sid=series_id), s.index, "")
    return s


_ALFRED = "https://alfred.stlouisfed.org/graph/alfredgraph.csv?id={sid}&vintage_date={vd}"


def fetch_fred_vintage(series_id: str, vintage_date: str) -> pd.Series:
    """The series as published on ``vintage_date`` (ALFRED). Cached forever: vintages never change.

    Returns an empty Series when ALFRED holds no vintage that early.
    """
    path = _cache_path("alfred", f"{series_id}_{vintage_date}")
    if path.exists():
        s = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        s.name = series_id
        return s.dropna()
    url = _ALFRED.format(sid=series_id, vd=vintage_date)
    r = requests.get(url, headers=_UA, timeout=60)
    if r.status_code != 200 or not r.text.startswith("observation_date"):
        s = pd.Series(dtype=float, name=series_id)
    else:
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = ["date", series_id]
        df["date"] = pd.to_datetime(df["date"])
        s = pd.to_numeric(df.set_index("date")[series_id], errors="coerce").dropna()
    s.index.name = "date"
    s.to_frame().to_csv(path)
    _record(path, "alfred", f"{series_id}@{vintage_date}", url, s.index, f"ALFRED vintage {vintage_date}")
    time.sleep(0.2)
    return s


_LLAMA_STABLES = "https://stablecoins.llama.fi/stablecoincharts/all"


def fetch_stablecoin_supply(max_age_hours: float = 20.0, refresh: bool = False) -> pd.Series:
    """Total USD-pegged stablecoin supply (DefiLlama, free, no key), daily from late 2017."""
    path = _cache_path("defillama", "stablecoins_usd")
    if not refresh and _fresh(path, max_age_hours):
        s = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        s.name = "stablecoins"
        return s
    rows = _get(_LLAMA_STABLES).json()
    s = pd.Series(
        {pd.Timestamp(int(r["date"]), unit="s").normalize(): float(r["totalCirculatingUSD"].get("peggedUSD", np.nan)) for r in rows},
        name="stablecoins",
    ).dropna().sort_index()
    s.to_frame().to_csv(path)
    _record(path, "defillama", "stablecoins", _LLAMA_STABLES, s.index, "")
    return s
