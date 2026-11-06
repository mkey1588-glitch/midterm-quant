"""Static configuration: paths, transaction costs, political/crypto calendars."""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = Path(os.environ.get("MQ_CACHE_DIR", ROOT / "data_cache"))
REPORTS_DIR = ROOT / "reports"

# One-way cost per trade as a fraction of notional (commission + half-spread + slippage).
COST_BPS = {
    "crypto": 15.0,          # spot BTC/ETH/SOL on a major venue incl. slippage
    "commodity_etf": 5.0,    # USO, USL, UGA, GLD, SLV, PPLT, PALL, GDX ...
    "thematic_etf": 5.0,     # TAN, ICLN, XOP, KRE, XBI, ITA ...
    "core_etf": 2.0,         # SPY, QQQ, IWM, RSP, sector SPDRs, IEF
}
CRYPTO = {"BTC-USD", "ETH-USD", "SOL-USD"}
COMMODITY_ETF = {"USO", "USL", "UGA", "UNG", "BNO", "GLD", "SLV", "PPLT", "PALL", "GDX", "GDXJ"}
THEMATIC_ETF = {"TAN", "ICLN", "XOP", "KRE", "XBI", "ITA", "SMH", "URA", "PAVE"}

# Annual borrow fee charged on short positions (ETF hard-to-borrow is rare; 1% is conservative).
SHORT_BORROW_RATE = 0.01


def cost_bps(ticker: str) -> float:
    if ticker in CRYPTO:
        return COST_BPS["crypto"]
    if ticker in COMMODITY_ETF:
        return COST_BPS["commodity_etf"]
    if ticker in THEMATIC_ETF:
        return COST_BPS["thematic_etf"]
    return COST_BPS["core_etf"]


def midterm_election_day(year: int) -> dt.date:
    """US federal election day: the Tuesday after the first Monday in November."""
    d = dt.date(year, 11, 1)
    first_monday = d + dt.timedelta(days=(0 - d.weekday()) % 7)
    return first_monday + dt.timedelta(days=1)


MIDTERM_YEARS = list(range(1950, 2027, 4))  # 1950 ... 2026
MIDTERM_DATES = [midterm_election_day(y) for y in MIDTERM_YEARS]

# Bitcoin halvings (block 210k, 420k, 630k, 840k). The 1,050,000 block halving is an
# estimate (~10-minute blocks) and should be refreshed as the date approaches.
BTC_HALVINGS = [
    dt.date(2012, 11, 28),
    dt.date(2016, 7, 9),
    dt.date(2020, 5, 11),
    dt.date(2024, 4, 20),
    dt.date(2028, 4, 15),  # estimate
]
