"""Scenario signposts and the "three signals, four weeks" confirmation rule.

Algorithm (declared 6 Nov 2026; the signposts themselves were declared on 4 Nov):

1. **Reading time.** Once a week, at the close of the last trading day of the ISO week
   (normally Friday), every signpost indicator is read point-in-time with
   ``monitor.read_one(code, asof, live=False)``: only data published by that close, and
   ALFRED vintages for revision-prone series.
2. **Signpost test.** A signpost *holds* when its indicator status is OK and its condition is
   true. A MISSING or STALE input never holds; it is listed so the gap is visible.
3. **Confirmation.** A scenario is CONFIRMED in week *w* if at least 3 of its signposts hold
   in each of the 4 consecutive weekly readings *w-3 ... w*.
4. **Revocation.** A confirmed scenario stays confirmed until 2 consecutive weekly readings
   have fewer than 2 signposts holding; it is then REVOKED (state returns to WATCHING).
   Counts of exactly 2 neither confirm nor revoke (hysteresis).
5. **Independence.** Scenarios are evaluated separately. Their signposts overlap in cause
   (a credit shock moves several), so more than one can be confirmed at once, or none.
   The rule produces states, not probabilities: the 40% / 35% / 25% weights in docs/01 are
   subjective priors that are neither calibrated nor updated by this rule.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from midterm_quant.research import monitor

CONFIRM_MIN, CONFIRM_WEEKS = 3, 4
REVOKE_MAX, REVOKE_WEEKS = 1, 2   # fewer than 2 holding = at most 1


@dataclass(frozen=True)
class Signpost:
    codes: tuple
    label: str
    test: object   # callable(dict[code, Reading]) -> bool


def sp(code, label, fn):
    """Single-indicator signpost: ``fn`` receives that indicator's Reading."""
    return Signpost((code,), label, lambda rs: fn(rs[code]))


def _v(r):
    return r.value_num


SCENARIOS = {
    "A": ("Productive gridlock and a war wind-down", 0.40, [
        sp("M2", "10-year yield below 4.75%", lambda r: _v(r) < 4.75),
        sp("M4", "2-year minus fed funds between -50 and +25bp", lambda r: -50 <= _v(r) <= 25),
        sp("N-a", "Brent-WTI below $5", lambda r: _v(r) < 5),
        sp("N-c", "Gasoline below its 70th percentile of 2 years", lambda r: r.extra.get("pctile", 1.0) < 0.7),
        sp("E-c", "Equal-weight beating cap-weight (63d)", lambda r: _v(r) > 0),
        sp("M10", "HYG/IEF z above -1", lambda r: _v(r) > -1),
        sp("M9", "Net liquidity rising over 13 weeks", lambda r: _v(r) > 0),
    ]),
    "B": ("Confrontation", 0.35, [
        sp("M4", "2-year minus fed funds above +50bp", lambda r: _v(r) > 50),
        sp("M8", "4-week bill 15bp above 3-month", lambda r: _v(r) > 15),
        Signpost(("N-a", "N-d"), "Brent-WTI above $8, or an oil spike (USO 20-day z above +2)",
                 lambda rs: _v(rs["N-a"]) > 8 or _v(rs["N-d"]) > 2),
        sp("E-b", "VIX above VIX3M", lambda r: _v(r) > 1.0),
        sp("M1", "Policy uncertainty z above +1.5", lambda r: r.extra.get("z", 0.0) > 1.5),
        sp("M5", "Breakeven above 2.6%", lambda r: _v(r) > 2.6),
    ]),
    "C": ("AI-capex and credit slowdown", 0.25, [
        sp("M10", "HYG/IEF z below -1.5", lambda r: _v(r) < -1.5),
        sp("E-a", "S&P 500 below its 200-day average", lambda r: _v(r) < 0),
        sp("E-e", "Semis lagging SPY by more than 5% (63d)", lambda r: _v(r) < -0.05),
        sp("M4", "2-year minus fed funds below -50bp", lambda r: _v(r) < -50),
        sp("C-b", "Bitcoin 30-day volatility above 70%", lambda r: _v(r) > 0.70),
        sp("E-d", "Small caps lagging large caps (63d)", lambda r: _v(r) < 0),
    ]),
}


def week_ends(last: pd.Timestamp, n: int) -> list[pd.Timestamp]:
    """Last trading day of each of the ``n`` ISO weeks up to and including ``last``'s week."""
    from midterm_quant.data.sources import fetch_yahoo

    days = fetch_yahoo("SPY").index
    days = days[days <= last]
    wk = pd.Series(days, index=days).groupby([days.isocalendar().year, days.isocalendar().week]).last()
    return list(wk.iloc[-n:])


def weekly_counts(dates) -> pd.DataFrame:
    rows = []
    codes = sorted({c for _, _, sps in SCENARIOS.values() for s_ in sps for c in s_.codes})
    for d in dates:
        readings = {c: monitor.read_one(c, d, live=False) for c in codes}
        for key, (_, _, sps) in SCENARIOS.items():
            holding, gaps = [], []
            for s_ in sps:
                bad = [c for c in s_.codes if readings[c].status != "OK"]
                tag = "/".join(s_.codes)
                if bad:
                    gaps.append(f"{tag} {readings[bad[0]].status}")
                    continue
                try:
                    if s_.test(readings):
                        holding.append(tag)
                except Exception:
                    gaps.append(f"{tag} error")
            rows.append({"week_end": d.date().isoformat(), "scenario": key, "holding": len(holding),
                         "of": len(sps), "which": holding, "gaps": gaps})
    return pd.DataFrame(rows)


def states(counts: pd.DataFrame) -> pd.DataFrame:
    out = []
    for key, g in counts.groupby("scenario"):
        g = g.sort_values("week_end").reset_index(drop=True)
        state = "WATCHING"
        for i, row in g.iterrows():
            last4 = g.loc[max(0, i - CONFIRM_WEEKS + 1): i, "holding"]
            last2 = g.loc[max(0, i - REVOKE_WEEKS + 1): i, "holding"]
            if state != "CONFIRMED" and len(last4) == CONFIRM_WEEKS and (last4 >= CONFIRM_MIN).all():
                state = "CONFIRMED"
            elif state == "CONFIRMED" and len(last2) == REVOKE_WEEKS and (last2 <= REVOKE_MAX).all():
                state = "REVOKED"
            elif state == "REVOKED":
                state = "WATCHING"
            out.append({**row.to_dict(), "state": state})
    return pd.DataFrame(out)
