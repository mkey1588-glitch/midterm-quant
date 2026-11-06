"""Data dictionary: units, timing, revision behaviour and licensing for every input series.

Each series used anywhere in the library has one ``SeriesMeta`` record. The record says

* what the number *is* (units, frequency, source, how its date is stamped);
* when it becomes *available* to a decision (``release`` text plus the machine rule in
  ``available_rule``) - the backtests and the monitor use only values whose ``available_at``
  is on or before the decision time;
* whether later revisions can change history (``revisions``), which decides whether a
  point-in-time vintage reconstruction is needed;
* whether the raw data may be redistributed (``redistributable``). Where it may not, the
  repository ships hashes and acquisition instructions instead of the data.

Times are US/Eastern unless stated. A "bar" is one row in the source file.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd
from pandas.tseries.offsets import BDay


@dataclass(frozen=True)
class SeriesMeta:
    key: str                 # library name: Yahoo symbol, "fred:<id>" or "llama:<name>"
    description: str
    source: str
    source_url: str
    units: str
    frequency: str
    timestamp: str           # what the row date means
    release: str             # when the value is published
    available_rule: str      # machine rule: "same_close", "next_utc_day", "bdays:<n>", "h10_weekly", "monthly:<days>"
    revisions: str           # none | rare | material | restated
    license: str
    redistributable: bool
    notes: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


_YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
_YAHOO_LIC = "Yahoo Finance terms of service: personal use; no redistribution of raw data"
_FRED_LIC = "FRED: public-domain source data unless the series notes a copyright holder"


def _fred(sid, description, units, frequency, release, rule, revisions="none", lic=_FRED_LIC, redistributable=True, notes=""):
    return SeriesMeta(
        key=f"fred:{sid}", description=description, source=f"FRED {sid}",
        source_url=f"https://fred.stlouisfed.org/series/{sid}", units=units, frequency=frequency,
        timestamp="observation date as defined by the source (see FRED notes)", release=release,
        available_rule=rule, revisions=revisions, license=lic, redistributable=redistributable, notes=notes,
    )


FRED = {m.key: m for m in [
    _fred("DTB3", "3-month Treasury bill, secondary market rate", "percent per year, discount basis", "daily (business days)",
          "Federal Reserve H.15, posted next business day", "bdays:1",
          notes="Used as the risk-free rate and as interest on idle cash; converted to a daily rate with the strategy's own calendar."),
    _fred("DTB4WK", "4-week Treasury bill, secondary market rate", "percent per year, discount basis", "daily (business days)",
          "H.15, next business day", "bdays:1"),
    _fred("DGS10", "10-year Treasury constant-maturity yield", "percent per year", "daily (business days)",
          "H.15 (from Treasury's par curve), posted on FRED the next business day", "bdays:1",
          notes="Differs from CBOE ^TNX (Yahoo), which is an intraday index closing at 15:00 CT."),
    _fred("DGS2", "2-year Treasury constant-maturity yield", "percent per year", "daily (business days)",
          "H.15, next business day", "bdays:1"),
    _fred("DFF", "Effective federal funds rate", "percent per year", "daily (calendar days)",
          "New York Fed, 09:00 ET next business day", "bdays:1"),
    _fred("DFII10", "10-year TIPS constant-maturity real yield", "percent per year", "daily (business days)",
          "H.15, next business day", "bdays:1"),
    _fred("T10YIE", "10-year breakeven inflation (DGS10 - DFII10)", "percent per year", "daily (business days)",
          "St. Louis Fed, usually the evening of the same day", "bdays:1"),
    _fred("T10Y3M", "10-year minus 3-month Treasury spread", "percentage points", "daily (business days)",
          "St. Louis Fed, usually the evening of the same day", "bdays:1"),
    _fred("THREEFYTP10", "Kim-Wright 10-year term premium", "percent per year", "daily (business days)",
          "Federal Reserve Board staff model, updated with a lag of several days", "bdays:5", revisions="material",
          notes="Model output: history changes when the model is re-estimated."),
    _fred("USEPUINDXD", "Economic Policy Uncertainty index (daily, US newspapers)", "index (1985-2009 mean = 100)", "daily (calendar days)",
          "policyuncertainty.com via FRED, next day", "bdays:1", revisions="material",
          lic="Baker, Bloom and Davis; free for research with citation",
          notes="Daily newspaper counts are re-tabulated as archives change."),
    _fred("DTWEXBGS", "Nominal broad U.S. dollar index", "index (Jan 2006 = 100)", "daily (business days)",
          "Federal Reserve H.10, published weekly on Monday for the previous week", "h10_weekly", revisions="material",
          notes="Trade weights are revised annually, which revises history."),
    _fred("WALCL", "Federal Reserve total assets", "USD millions, Wednesday level", "weekly (Wednesday)",
          "H.4.1, Thursday 16:30 ET (after the equity close)", "bdays:2", revisions="rare"),
    _fred("WDTGAL", "Treasury General Account at the Fed", "USD millions, Wednesday level", "weekly (Wednesday)",
          "H.4.1, Thursday 16:30 ET", "bdays:2", revisions="rare",
          notes="Matches WALCL's Wednesday timing; replaces the week-average WTREGEN in net liquidity."),
    _fred("WTREGEN", "Treasury General Account at the Fed", "USD millions, week average", "weekly (Wednesday)",
          "H.4.1, Thursday 16:30 ET", "bdays:2", revisions="rare",
          notes="Week average: do not subtract from a Wednesday-level balance sheet. Kept only to reproduce C2 v1."),
    _fred("RRPONTSYD", "Overnight reverse repo, total accepted", "USD billions", "daily (business days)",
          "New York Fed ~13:15 ET same day; FRED next business day", "bdays:1"),
    _fred("GASREGW", "US regular retail gasoline price", "USD per gallon", "weekly (Monday)",
          "EIA Gasoline and Diesel Fuel Update, Monday ~17:00 ET", "bdays:1", revisions="rare"),
    _fred("BAMLH0A0HYM2", "ICE BofA US High Yield option-adjusted spread", "percentage points", "daily (business days)",
          "ICE via FRED, next business day", "bdays:1",
          lic="ICE Data Indices: FRED may show only the most recent 3 years; no redistribution", redistributable=False,
          notes="Direct credit-spread measure. Longer history requires an ICE or vendor licence."),
    _fred("UNRATE", "Unemployment rate", "percent", "monthly", "BLS Employment Situation, first Friday of the next month",
          "monthly:35", revisions="material"),
    _fred("GS10", "10-year Treasury yield, monthly average", "percent per year", "monthly", "H.15, first business day of next month", "monthly:3"),
    _fred("TB3MS", "3-month T-bill, monthly average", "percent per year, discount basis", "monthly", "H.15, first business day of next month", "monthly:3"),
    _fred("BAA", "Moody's Baa corporate bond yield, monthly average", "percent per year", "monthly", "Moody's via FRED, first days of next month", "monthly:3"),
    _fred("AAA", "Moody's Aaa corporate bond yield, monthly average", "percent per year", "monthly", "Moody's via FRED, first days of next month", "monthly:3"),
    _fred("USEPUINDXM", "Economic Policy Uncertainty index (monthly)", "index", "monthly", "policyuncertainty.com, early next month",
          "monthly:7", revisions="material", lic="Baker, Bloom and Davis; free for research with citation"),
]}

LLAMA = {
    "llama:stablecoins": SeriesMeta(
        key="llama:stablecoins", description="Total circulating USD-pegged stablecoins (all chains)",
        source="DefiLlama stablecoins API", source_url="https://stablecoins.llama.fi/stablecoincharts/all",
        units="USD", frequency="daily", timestamp="00:00 UTC snapshot of the stated day",
        release="continuous; a day's snapshot is complete after 00:00 UTC of the next day", available_rule="next_utc_day",
        revisions="restated", license="DefiLlama open API (free; cite DefiLlama)", redistributable=True,
        notes="History is restated when coins or chains are added, so past growth rates can change. No archived vintages exist before this project started saving snapshots.",
    ),
}


DERIVED = {
    "derived:netliq_bn": SeriesMeta(
        key="derived:netliq_bn", description="Fed net liquidity = WALCL - WDTGAL - RRPONTSYD, all on the same Wednesday",
        source="computed from FRED WALCL, WDTGAL, RRPONTSYD", source_url="https://fred.stlouisfed.org/series/WALCL",
        units="USD billions (WALCL and WDTGAL are USD millions / 1000; RRPONTSYD is already USD billions)",
        frequency="weekly (Wednesday)", timestamp="Wednesday of the H.4.1 week",
        release="H.4.1, Thursday 16:30 ET", available_rule="bdays:2", revisions="rare",
        license=_FRED_LIC, redistributable=True,
        notes="v1 (until 6 Nov 2026) subtracted the week-average TGA (WTREGEN) and the latest daily RRP from a Wednesday balance sheet; v2 aligns all three on Wednesday.",
    ),
}


def _yahoo_kind(sym: str) -> str:
    if sym.endswith("-USD"):
        return "crypto"
    if sym.endswith("=X"):
        return "fx"
    if sym.endswith("=F") or sym.endswith((".NYM", ".CMX", ".CBT", ".CME")):
        return "future"
    if sym.startswith("^") or sym in ("DX-Y.NYB",) or sym[:1].isdigit():
        return "index"
    return "us_listed"


_YAHOO_TIMING = {
    "us_listed": ("NYSE/Nasdaq regular-session bar; close = 16:00 ET closing auction", "available at the 16:00 ET close of the bar date", "same_close",
                  "price adjusted for splits and dividends (total-return close)"),
    "index": ("index level at the exchange's close on the bar date (local time zone of the exchange)", "available at that close", "same_close",
              "index points (price index, no dividends)"),
    "future": ("front-month continuous series (=F) or a single contract; bar dated by the CME/ICE trade date", "available after the session close", "same_close",
               "USD per contract unit; =F rolls without adjustment"),
    "crypto": ("UTC calendar-day bar, 00:00-24:00 UTC", "complete at 00:00 UTC the next day (19:00 or 20:00 ET on the bar date)", "next_utc_day",
               "USD per coin"),
    "fx": ("London-session daily bar reported by Yahoo", "available after the bar's close", "same_close", "units of quote currency per base"),
}


def yahoo_meta(sym: str) -> SeriesMeta:
    kind = _yahoo_kind(sym)
    ts, rel, rule, units = _YAHOO_TIMING[kind]
    notes = ""
    if sym == "^TNX":
        units, notes = "percent per year (CBOE 10-year yield index / 10)", "Closes 15:00 CT; not the same series as FRED DGS10."
    elif sym in ("^VIX", "^VIX3M"):
        notes = "CBOE volatility indices; close at 16:15 ET."
    elif sym in ("USO", "USL", "UGA", "BNO", "UNG"):
        notes = "Commodity fund that holds futures; its return includes roll yield and fund costs, so it is not a futures-curve measure."
    return SeriesMeta(
        key=sym, description=f"{sym} daily bar", source="Yahoo Finance chart API", source_url=_YAHOO_URL.format(sym=sym),
        units=units, frequency="daily (trading days)" if kind != "crypto" else "daily (calendar days, UTC)",
        timestamp=ts, release=rel, available_rule=rule,
        revisions="restated" if kind == "us_listed" else "rare", license=_YAHOO_LIC, redistributable=False,
        notes=notes or ("Adjusted closes are rescaled after every dividend, so file hashes change even when returns do not." if kind == "us_listed" else ""),
    )


def meta(name: str) -> SeriesMeta:
    if name in FRED:
        return FRED[name]
    if name in LLAMA:
        return LLAMA[name]
    if name in DERIVED:
        return DERIVED[name]
    if name.startswith("fred:"):
        sid = name.split(":", 1)[1]
        return _fred(sid, sid, "see FRED", "see FRED", "see FRED", "bdays:1", notes="not catalogued: default 1-business-day lag")
    return yahoo_meta(name)


# ---- available_at ----------------------------------------------------------------------
def available_dates(name: str, obs: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """First trading *date* on whose close each observation may be used.

    The engine decides at a bar's close and fills at the next bar's open, so a value that
    is published after the close of day D (e.g. H.4.1 at 16:30) is usable at D+1's close.
    """
    rule = meta(name).available_rule
    obs = pd.DatetimeIndex(obs)
    if rule == "same_close":
        return obs
    if rule == "next_utc_day":
        return obs + pd.Timedelta(days=1)
    if rule.startswith("bdays:"):
        return obs + BDay(int(rule.split(":")[1]))
    if rule.startswith("monthly:"):
        # monthly observations are dated the 1st of the month they describe
        return obs + pd.offsets.MonthBegin(1) + pd.Timedelta(days=int(rule.split(":")[1]))
    if rule == "h10_weekly":
        # H.10 is released on the Monday after the week that contains the observation,
        # at 16:15 ET (after the equity close), so it is usable at Tuesday's close.
        days_to_next_monday = 7 - obs.weekday
        return obs + pd.to_timedelta(days_to_next_monday, unit="D") + pd.Timedelta(days=1)
    raise ValueError(f"{name}: unknown rule {rule}")


def max_age_days(name: str) -> int:
    """Calendar days after which the latest observation counts as STALE in the monitor."""
    m = meta(name)
    f = m.frequency
    if f.startswith("monthly"):
        return 70
    if f.startswith("weekly"):
        return 13
    if m.available_rule == "h10_weekly":
        return 13
    if m.revisions == "material" and m.available_rule.startswith("bdays:5"):
        return 14
    return 5  # daily series: a long weekend plus one missed release
