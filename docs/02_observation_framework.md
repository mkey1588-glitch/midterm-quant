# Two-year observation framework (Nov 2026 – Nov 2028)

This is the watch-list for the gridlock window between the 2026 midterms and the 2028 presidential election. It has three parts:

1. **Calendar**: the dated political, policy and market events that can move the four asset classes.
2. **Quantitative indicators**: 33 mechanical indicators with fixed formulas, data sources and thresholds. `scripts/run_monitor.py` computes all of them and writes `reports/monitor.md`.
3. **Scenario signposts**: which indicator combinations confirm scenario A, B or C from [the impact analysis](01_midterm_market_impact.md#5-cross-asset-scenario-matrix-24-months).

Run it weekly (Friday after the H.4.1 release) and after any event in the calendar:

```bash
.venv/bin/python scripts/run_monitor.py
```

---

## 1. Event calendar

| When | Event | Why it matters | Primary assets | Indicators to check |
|---|---|---|---|---|
| Nov-Dec 2026 | Final media calls (AK, MS Senate); state certification of results (projections become official only then) | Size of the Senate majority (54–56) matters for confirmations and veto-proof math (it is not veto-proof) | All | — |
| Nov–Dec 2026 | **Lame-duck session**: possible GOP party-line reconciliation (defence money, **debt-limit increase**); CLARITY Act's last window | A debt-limit hike now removes the 2027 X-date (bearish for the BTC liquidity thesis, bullish for bills and volatility) | Bills, BTC, defence, crypto | M8, M9, C-d |
| **11 Dec 2026** | Continuing resolution expires; shutdown risk | Funding fight between a lame-duck GOP Congress and an incoming Democratic one | Equities volatility, T-bills | E-b, M8, M1 |
| Dec 2026 | FOMC (last of 2026) | After the Sept hike and Oct hold (two hawkish dissents): hike, or confirm the pause | Rates, gold, USD | M4, M6, M7 |
| **3 Jan 2027** | 120th Congress convenes at noon (Twentieth Amendment) and members are sworn in; Speaker vote; Democratic committee chairs | Start of subpoenas and oversight (tariffs, Iran war costs, crypto ventures, energy deals, AI) | COIN, semis, energy | C-d, E-e |
| Jan–Feb 2027 | State of the Union; FY2028 budget request | Opening bids on spending, tariffs, war funding | — | M1 |
| H1 2027 | New tariff actions (Goldman: effective rate +~2pp); Section 301/232 investigations; CIT litigation on post-IEEPA tariffs | Goods inflation, margins, retaliation | Industrials, retail, PGMs, USD | M5, E-f, P-e |
| H1 2027 | War Powers votes and supplemental requests for the Iran war ($47bn spent so far) | Congress's main lever on the oil risk premium | Oil, XLE, gold | N-a, N-d, M5 |
| 2027 (8 meetings) | FOMC. Warsh adds a strategy-only meeting from 2027 (no rate vote) | Fed path; reaction to oil-driven inflation | Rates, gold, BTC | M4, M5, M6 |
| 2027 | Senate confirmation fights over any Fed Board vacancies | A Democratic Senate gatekeeps; the "politicised Fed" premium fades | Gold, term premium | M3, P-a |
| **Late summer – fall 2027** | **Debt-limit X-date** (Deutsche Bank estimate) unless lifted in the lame duck | TGA run-down (liquidity injection), then rebuild (drain); 1M bill kink; brinkmanship volatility | BTC, gold, equities, bills | **M8, M9**, C-e, E-b |
| 30 Sep 2027 | FY2028 appropriations deadline | Second shutdown window | Equities, bills | E-b, M8 |
| **31 Dec 2027** | Wind/solar credit deadline (P.L. 119-21; IRS Notice 2025-42): facilities whose construction **begins after 4 Jul 2026** must be **placed in service** by this date; earlier starts are exempt from it (four-year continuity safe harbor) | 2027 installation rush, then a 2028 demand air pocket | ICLN/TAN, utilities | N-e |
| Jan–Mar 2028 | Presidential primaries (Iowa/NH → Super Tuesday) | Markets start pricing the 2029 policy regime (tariffs, crypto, energy, Fed) | All | M1 |
| **~Apr 2028** | Bitcoin halving (block 1,050,000; date is an estimate) | 4-year-cycle anchor; historically strong 12–18m afterwards | BTC, ETH | C-f, C-a |
| Summer 2028 | Party conventions | Platform clarity on tariffs, crypto, energy | All | — |
| **7 Nov 2028** | Presidential and congressional elections | End of the observation window; possible unified government | All | — |

**Recurring data releases** (not individually dated): CPI/PCE (inflation pass-through from oil and tariffs), payrolls (ADP printed +86k in Oct), weekly H.4.1 (Fed balance sheet and TGA), weekly EIA petroleum status, monthly WGC central-bank gold data, monthly OPEC+ meetings, and quarterly earnings (AI capex guidance from hyperscalers).

---

## 2. Quantitative indicators

Every indicator has a fixed formula and a threshold declared before it was read: 33 on 4 Nov 2026 and three direct measures (M11, M12, N-f) on 6 Nov. Several were renamed on 6 Nov so that the name says what is measured (for example, HYG/IEF is a *credit risk-appetite proxy*, not a credit impulse; SMH vs SPY is *semiconductor relative strength*, not AI-regulation risk). Full specifications, including what each indicator does **not** measure, are in [05_specifications.md](05_specifications.md); dated readings, with the observation date and age of every value, are in [`reports/monitor.md`](../reports/monitor.md). No reading is quoted here, because a reading without its observation date is what the review flagged.

<!-- BEGIN INDICATORS (generated by scripts/build_docs.py) -->
| Code | Group | Indicator | Formula | Rule (declared) |
|---|---|---|---|---|
| M1 | Macro and policy | Economic policy uncertainty (30-day average) | mean30(USEPUINDXD); z vs trailing 756 obs | z > +1.5 STRESS; z < -0.5 CALM (2026-11-04) |
| M2 | Macro and policy | 10-year Treasury yield (FRED DGS10) | DGS10 level; 63-business-day change | > 5.0% or +50bp in 63 days STRESS (2026-11-04) |
| M3 | Macro and policy | 10-year term premium (Kim-Wright) | z of the 63-day change vs 756 days | z > +1.5 STRESS (2026-11-04) |
| M4 | Macro and policy | 2-year yield minus effective fed funds | DGS2 - DFF on the same date | > +25bp HIGHER RATES PRICED; < -50bp CUTS PRICED (2026-11-04) |
| M5 | Macro and policy | 10-year breakeven inflation | T10YIE level; 63-day change | > 2.6% STRESS (2026-11-04) |
| M6 | Macro and policy | 10-year real yield (TIPS) | DFII10 level; 63-day change | > 2.5% and rising: gold HEADWIND (2026-11-04) |
| M7 | Macro and policy | Broad trade-weighted dollar | DTWEXBGS / SMA200 - 1 | above SMA200 STRONG USD (2026-11-04) |
| M8 | Macro and policy | 4-week minus 3-month bill yield | DTB4WK - DTB3 | > +15bp X-DATE STRESS (2026-11-04) |
| M9 | Macro and policy | Fed net liquidity (same-Wednesday basis) | WALCL/1000 - WDTGAL/1000 - RRPONTSYD(Wednesday); 13-week change | 13-week change > 0 EXPANDING, < 0 DRAINING (2026-11-04) |
| M10 | Macro and policy | Credit risk-appetite proxy: HYG vs IEF | z of the 20-day change of log(HYG/IEF) vs 500 obs | z < -1.5 STRESS (2026-11-04) |
| M11 | Macro and policy | High-yield option-adjusted spread (ICE BofA) | BAMLH0A0HYM2 level; 63-day change | >= 5.0pp or +1.0pp in 63 days STRESS; >= 4.0pp WATCH (2026-11-06) |
| M12 | Macro and policy | Fed funds futures: implied policy path | 100 - ZQ price for each month; path change = Jun-2027 implied minus current effective rate | Jun-27 implied minus effective > +25bp HIKES PRICED; < -25bp CUTS PRICED (2026-11-06) |
| E-a | U.S. equities | S&P 500 trend | ^GSPC / SMA200 - 1 | below SMA200 RISK-OFF (2026-11-04) |
| E-b | U.S. equities | VIX term structure | ^VIX / ^VIX3M | > 1.0 STRESS; < 0.9 CALM (2026-11-04) |
| E-c | U.S. equities | Breadth: equal-weight vs cap-weight | ret63(RSP) - ret63(SPY) | > 0 BROADENING (2026-11-04) |
| E-d | U.S. equities | Small caps vs large caps | ret63(IWM) - ret63(SPY) | > 0 BROADENING (2026-11-04) |
| E-e | U.S. equities | Semiconductor relative strength: SMH vs SPY | ret63(SMH) - ret63(SPY) | < -5% SEMIS LAGGING (2026-11-04) |
| E-f | U.S. equities | Policy-sensitive sector baskets vs SPY | ret63(X) - ret63(SPY) | informational (2026-11-04) |
| E-g | U.S. equities | Midterm seasonal window and election clock | calendar arithmetic | 1 Oct midterm year - 31 Dec pre-election year IN WINDOW (2026-11-04) |
| C-a | Crypto | Bitcoin Mayer multiple | BTC-USD / SMA200 | < 0.8 DEEP VALUE; > 2.4 EUPHORIC; else above/below 1 (2026-11-04) |
| C-b | Crypto | Bitcoin 30-day realised volatility | rv30 * sqrt(365) | > 70% STRESS (2026-11-04) |
| C-c | Crypto | ETH/BTC ratio | ETH/BTC; ret90 | > +10% ALT-SEASON (2026-11-04) |
| C-d | Crypto | Crypto equity vs bitcoin: COIN vs BTC | ret63(COIN) - ret63(BTC) on common dates | < -10% CRYPTO EQUITY LAGS (2026-11-04) |
| C-e | Crypto | Stablecoin supply: level and 30-day growth | level; level/level[-30] - 1 | 30-day growth > 0 INFLOW (2026-11-04) |
| C-f | Crypto | Halving-cycle clock | calendar arithmetic | phase by days since halving (in-sample boundaries) (2026-11-04) |
| N-a | Energy | Brent minus WTI (front-month futures) | BZ=F - CL=F on common dates | > $6 WIDE (2026-11-04) |
| N-b | Energy | Oil-fund roll proxy: USO vs USL | ret63(USO) - ret63(USL) | > 0 FRONT OUTPERFORMING (2026-11-04) |
| N-f | Energy | WTI futures curve: 1st vs 12th contract | CL[1] - CL[12] on the asof date | > 0 BACKWARDATION; < 0 CONTANGO (2026-11-06) |
| N-c | Energy | U.S. retail gasoline price | GASREGW; percentile rank vs 104 weeks | > $4.00 or > 70th percentile AFFORDABILITY PRESSURE (2026-11-04) |
| N-d | Energy | Oil shock detector (USO 20-day return z) | return_zscore(USO, 20, 250) | > +2 SPIKE; < -2 CRASH (2026-11-04) |
| N-e | Energy | Clean vs fossil energy equities | ret63(ICLN) - ret63(XLE) | > 0 CLEAN LEADS (2026-11-04) |
| P-a | Precious metals | Gold trend | GC=F / SMA200 - 1 | below SMA200 DOWNTREND (2026-11-04) |
| P-b | Precious metals | Gold/silver ratio | GC=F / SI=F; z vs 504 | z > +1 SILVER CHEAP; z < -1 SILVER RICH (2026-11-04) |
| P-c | Precious metals | Gold/oil price ratio (input-cost proxy) | GC=F / CL=F (CL > $5); vs SMA200 | above SMA200 COST TAILWIND (2026-11-04) |
| P-d | Precious metals | Miners vs bullion: GDX vs GLD | ret63(GDX) - ret63(GLD) | > 0 CONFIRMING (2026-11-04) |
| P-e | Precious metals | Platinum/gold ratio | PL=F / GC=F; z vs 252 | z < -1 PGM WEAK (2026-11-04) |
<!-- END INDICATORS -->

### 2.1 Qualitative and manual inputs (no free API)

| Item | Source | Use |
|---|---|---|
| Prediction-market odds (shutdown, debt-limit deal, Iran ceasefire, CLARITY, 2028 nominee) | Kalshi / Polymarket | Probability updates for scenarios A/B/C |
| Hormuz tanker transits vs pre-war | Shipping trackers, EIA | Confirms or refutes N-a moves |
| U.S. commercial crude inventories vs 5y seasonal | EIA Weekly Petroleum Status Report | Tightness filter for the oil strategies |
| Central-bank gold purchases | World Gold Council (monthly/quarterly) | Structural floor under gold |
| Spot BTC/ETH ETF flows | Issuer data / aggregators | Confirms C-e |
| CFTC Commitments of Traders (crude, gold, silver) | cftc.gov | Positioning extremes for the reversal strategies |
| Data-centre moratorium bills (TX, GA, VA, federal) | State legislatures, Congress.gov | E-e regime context |

---

## 3. Scenario signposts

The scenario weights in [01](01_midterm_market_impact.md) (40% / 35% / 25%) are subjective priors: not calibrated, not updated by the signposts, and not mutually exclusive in their drivers. The signposts decide each scenario's *state* with an explicit rule (`midterm_quant/research/scenarios.py`):

1. **Reading time.** Weekly, at the close of the last trading day of the ISO week, using only data published by that close (ALFRED vintages for revision-prone series).
2. **Signpost test.** A signpost holds when its indicator status is OK and its condition is true. A MISSING or STALE input never holds and is listed as a gap.
3. **Confirmation.** A scenario is CONFIRMED when at least **3** of its signposts hold in each of **4** consecutive weekly readings.
4. **Revocation.** A confirmed scenario is REVOKED after 2 consecutive weekly readings with at most 1 signpost holding; a count of 2 neither confirms nor revokes.
5. **Independence.** Scenarios are evaluated separately; several, or none, can be confirmed at once.

<!-- BEGIN SIGNPOSTS (generated by scripts/build_docs.py) -->
| Scenario | Prior (subjective) | Signposts |
|---|---|---|
| **A. Productive gridlock and a war wind-down** | 40% | M2: 10-year yield below 4.75% · M4: 2-year minus fed funds between -50 and +25bp · N-a: Brent-WTI below $5 · N-c: Gasoline below its 70th percentile of 2 years · E-c: Equal-weight beating cap-weight (63d) · M10: HYG/IEF z above -1 · M9: Net liquidity rising over 13 weeks |
| **B. Confrontation** | 35% | M4: 2-year minus fed funds above +50bp · M8: 4-week bill 15bp above 3-month · N-a/N-d: Brent-WTI above $8, or an oil spike (USO 20-day z above +2) · E-b: VIX above VIX3M · M1: Policy uncertainty z above +1.5 · M5: Breakeven above 2.6% |
| **C. AI-capex and credit slowdown** | 25% | M10: HYG/IEF z below -1.5 · E-a: S&P 500 below its 200-day average · E-e: Semis lagging SPY by more than 5% (63d) · M4: 2-year minus fed funds below -50bp · C-b: Bitcoin 30-day volatility above 70% · E-d: Small caps lagging large caps (63d) |

Latest point-in-time weekly reading (`reports/results/scenarios.json`):

| Scenario | Week ending | Signposts holding | Which | Gaps | State |
|---|---|---|---|---|---|
| A | 2026-11-05 | 1 of 7 | E-c | - | WATCHING |
| B | 2026-11-05 | 2 of 6 | M4, E-b | - | WATCHING |
| C | 2026-11-05 | 3 of 6 | M10, E-e, E-d | C-b STALE | WATCHING |
<!-- END SIGNPOSTS -->
