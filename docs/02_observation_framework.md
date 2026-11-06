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
| Nov 2026 | Final calls (AK, MS Senate); certification | Size of the Senate majority (54–56) matters for confirmations and veto-proof math (it is not veto-proof) | All | — |
| Nov–Dec 2026 | **Lame-duck session**: possible GOP party-line reconciliation (defence money, **debt-limit increase**); CLARITY Act's last window | A debt-limit hike now removes the 2027 X-date (bearish for the BTC liquidity thesis, bullish for bills and volatility) | Bills, BTC, defence, crypto | M8, M9, C-d |
| **11 Dec 2026** | Continuing resolution expires; shutdown risk | Funding fight between a lame-duck GOP Congress and an incoming Democratic one | Equities volatility, T-bills | E-b, M8, M1 |
| Dec 2026 | FOMC (last of 2026) | After the Sept hike and Oct hold (two hawkish dissents): hike, or confirm the pause | Rates, gold, USD | M4, M6, M7 |
| **3 Jan 2027** | 120th Congress sworn in; Speaker vote; Democratic committee chairs | Start of subpoenas and oversight (tariffs, Iran war costs, crypto ventures, energy deals, AI) | COIN, semis, energy | C-d, E-e |
| Jan–Feb 2027 | State of the Union; FY2028 budget request | Opening bids on spending, tariffs, war funding | — | M1 |
| H1 2027 | New tariff actions (Goldman: effective rate +~2pp); Section 301/232 investigations; CIT litigation on post-IEEPA tariffs | Goods inflation, margins, retaliation | Industrials, retail, PGMs, USD | M5, E-f, P-e |
| H1 2027 | War Powers votes and supplemental requests for the Iran war ($47bn spent so far) | Congress's main lever on the oil risk premium | Oil, XLE, gold | N-a, N-d, M5 |
| 2027 (8 meetings) | FOMC. Warsh adds a strategy-only meeting from 2027 (no rate vote) | Fed path; reaction to oil-driven inflation | Rates, gold, BTC | M4, M5, M6 |
| 2027 | Senate confirmation fights over any Fed Board vacancies | A Democratic Senate gatekeeps; the "politicised Fed" premium fades | Gold, term premium | M3, P-a |
| **Late summer – fall 2027** | **Debt-limit X-date** (Deutsche Bank estimate) unless lifted in the lame duck | TGA run-down (liquidity injection), then rebuild (drain); 1M bill kink; brinkmanship volatility | BTC, gold, equities, bills | **M8, M9**, C-e, E-b |
| 30 Sep 2027 | FY2028 appropriations deadline | Second shutdown window | Equities, bills | E-b, M8 |
| **31 Dec 2027** | OBBBA wind/solar credit cliff: projects not started by 4 Jul 2026 must be **placed in service** by this date | 2027 installation rush, then a 2028 demand air pocket | ICLN/TAN, utilities | N-e |
| Jan–Mar 2028 | Presidential primaries (Iowa/NH → Super Tuesday) | Markets start pricing the 2029 policy regime (tariffs, crypto, energy, Fed) | All | M1 |
| **~Apr 2028** | Bitcoin halving (block 1,050,000; date is an estimate) | 4-year-cycle anchor; historically strong 12–18m afterwards | BTC, ETH | C-f, C-a |
| Summer 2028 | Party conventions | Platform clarity on tariffs, crypto, energy | All | — |
| **7 Nov 2028** | Presidential and congressional elections | End of the observation window; possible unified government | All | — |

**Recurring data releases** (not individually dated): CPI/PCE (inflation pass-through from oil and tariffs), payrolls (ADP printed +86k in Oct), weekly H.4.1 (Fed balance sheet and TGA), weekly EIA petroleum status, monthly WGC central-bank gold data, monthly OPEC+ meetings, and quarterly earnings (AI capex guidance from hyperscalers).

---

## 2. Quantitative indicators

Every indicator has a fixed formula and a pre-declared threshold, so the read-out is mechanical. Each is implemented in [`midterm_quant/research/monitor.py`](../midterm_quant/research/monitor.py). Readings are as of **4–5 Nov 2026**.

### 2.1 Macro and policy

| Code | Indicator | Formula / source | Threshold → regime | Reading | Read |
|---|---|---|---|---|---|
| M1 | Economic Policy Uncertainty | 30d avg of FRED `USEPUINDXD`; z vs 3y | z > +1.5 → STRESS | 294 (z −0.43) | NEUTRAL (high level, but below 2025) |
| M2 | 10Y Treasury yield | FRED `DGS10`; 63d change | > 5.0% or > +50bp/3m → STRESS | 4.91% (+21bp) | NEUTRAL |
| M3 | 10Y term premium | FRED `THREEFYTP10` (Kim–Wright); z of 63d change vs 3y | z > +1.5 → STRESS (fiscal / Fed-independence premium) | 0.91% (z −0.05) | NEUTRAL |
| M4 | Implied policy path | FRED `DGS2` − `DFF` | > +25bp hikes priced; < −50bp cuts priced | **+71bp** | **HIKES PRICED** |
| M5 | 10Y breakeven | FRED `T10YIE` | > 2.6% → de-anchoring STRESS | 2.30% (+7bp) | NEUTRAL |
| M6 | 10Y real yield | FRED `DFII10` | > 2.5% and rising → gold HEADWIND | 2.62% (+19bp) | **HEADWIND** |
| M7 | Broad dollar | FRED `DTWEXBGS` vs 200d SMA | above → STRONG USD | 121.7 (+1.8%) | STRONG USD |
| M8 | Bill-curve debt-limit gauge | FRED `DTB4WK` − `DTB3` | > +15bp → X-date STRESS | −13bp | NEUTRAL |
| M9 | Fed net liquidity | `WALCL` − `WTREGEN` − `RRPONTSYD`×1000; 13w change | > 0 → RISK-ON; < 0 → DRAIN | $5.75tn (−$80bn); TGA $1.00tn | **DRAIN** |
| M10 | Credit impulse | log(HYG/IEF) 20d change, z vs 2y | z < −1.5 → STRESS | **−1.96** | **STRESS** |

### 2.2 U.S. equities

| Code | Indicator | Formula / source | Threshold → regime | Reading | Read |
|---|---|---|---|---|---|
| E-a | S&P 500 trend | `^GSPC` vs 200d SMA; 1y drawdown | below SMA → RISK-OFF | 7,710 (+5.3%; DD −1.4%) | RISK-ON |
| E-b | Vol term structure | `^VIX` / `^VIX3M` | > 1.0 → STRESS; < 0.9 → CALM | 17.0 / ratio 0.89 | CALM |
| E-c | Breadth | RSP vs SPY, 63d relative return | > 0 → BROADENING | +2.2% | BROADENING |
| E-d | Size | IWM vs SPY, 63d | > 0 → BROADENING | −4.8% | NARROW |
| E-e | AI-infrastructure regulation risk | SMH vs SPY, 63d | < −5% → DERATING | **−11.9%** | **DERATING** |
| E-f | Policy baskets | ITA, XLV, TAN, KRE, XLE vs SPY, 63d | largest movers = where policy is priced | health +15%, defence −15%, solar −11% | Healthcare leads |
| E-g | Midterm-cycle clock | Days since election; sweet-spot flag | Oct midterm year → Dec pre-election year | Day 2 | **SWEET SPOT** |

### 2.3 Crypto

| Code | Indicator | Formula / source | Threshold → regime | Reading | Read |
|---|---|---|---|---|---|
| C-a | BTC Mayer multiple | price / 200d SMA | < 0.8 deep value; > 2.4 euphoric; 1.0 trend line | 1.10 ($80.2k; DD −24%) | UPTREND (barely) |
| C-b | BTC realised vol | 30d, annualised (365) | > 70% → STRESS | 32% | NEUTRAL |
| C-c | ETH/BTC | 90d change of the ratio | > +10% → ALT-SEASON | +2% | BTC DOMINANCE |
| C-d | U.S. regulatory sentiment | COIN vs BTC, 63d | < −10% → REG HEADWIND | **−20.1%** | **REG HEADWIND** |
| C-e | Stablecoin liquidity | DefiLlama total USD-pegged supply, 30d growth | > 0 → INFLOW | $295bn, **−4.0%** | **OUTFLOW** |
| C-f | Halving clock | Days since last / to next halving | expansion < 540d; bear 540–900d; accumulation > 900d | 527d to est. halving | ACCUMULATION |

### 2.4 Energy

| Code | Indicator | Formula / source | Threshold → regime | Reading | Read |
|---|---|---|---|---|---|
| N-a | War premium | Brent (`BZ=F`) − WTI (`CL=F`) | > $6 → WAR PREMIUM | $94.8 / $88.1, spread $6.7 | **WAR PREMIUM** |
| N-b | Curve shape | USO vs USL (front vs 12m strip), 63d | > 0 → BACKWARDATION | +2.7% | BACKWARDATION |
| N-c | Affordability politics | FRED `GASREGW`; 2y percentile | > $4.00 or > 70th pct → POLITICAL PAIN | $4.15 (87th) | **POLITICAL PAIN** |
| N-d | Oil shock detector | z of USO 20d log return vs 1y | > +2 SPIKE; < −2 CRASH | −0.44 | NORMAL |
| N-e | Clean vs fossil | ICLN vs XLE, 63d | > 0 → CLEAN LEADS | −17.7% | FOSSIL LEADS |

### 2.5 Precious metals

| Code | Indicator | Formula / source | Threshold → regime | Reading | Read |
|---|---|---|---|---|---|
| P-a | Gold trend | `GC=F` vs 200d SMA; drawdown from ATH | below SMA → DOWNTREND | $4,072 (−23% ATH; −9.7% vs 200d) | **DOWNTREND** |
| P-b | Gold/silver ratio | `GC=F`/`SI=F`; 2y z | z > +1 silver cheap; < −1 rich | 77.9 (z −0.02) | NEUTRAL |
| P-c | Miner margin proxy | Gold/WTI ratio vs 200d SMA | above → MARGINS EXPANDING | 46.2 (−14%) | MARGINS SQUEEZED |
| P-d | Miner confirmation | GDX vs GLD, 63d | > 0 → CONFIRMING | +5.0% | CONFIRMING |
| P-e | PGM stress | `PL=F`/`GC=F`; 1y z | z < −1 → PGM WEAK | 0.368 (z −1.41) | PGM WEAK |

### 2.6 Qualitative and manual inputs (no free API)

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

Each scenario is "confirmed" when **at least three** of its signposts hold for **four consecutive weekly readings**. That avoids reacting to a single headline.

| Scenario | Signposts (indicator → condition) | Current count |
|---|---|---|
| **A. Productive gridlock + war wind-down** | M2 < 4.75% · M4 between −50 and +25bp · N-a spread < $5 · N-c < 70th pct · E-c > 0 · M10 z > −1 · M9 > 0 | 1 / 7 (E-c) |
| **B. Confrontation** | M4 > +50bp · M8 > +15bp · N-a spread > $8 or N-d SPIKE · E-b ratio > 1 · M1 z > +1.5 · M5 > 2.6% | 1 / 6 (M4) |
| **C. AI/credit slowdown** | M10 STRESS · E-a below 200d · E-e DERATING · M4 < −50bp · C-b > 70% · E-d NARROW | 3 / 6 (M10, E-e, E-d), not yet confirmed: E-a is still RISK-ON and M4 still prices hikes |

**Reading today:** the market priced scenario A on election day, but the indicators are more consistent with a **late-cycle tug-of-war**. Credit stress (M10), semis de-rating (E-e) and narrow size leadership (E-d) lean toward C. A hawkish rate path (M4) and the war premium (N-a) lean toward B. The equity trend, vol and breadth (E-a, E-b, E-c) still support A. The strategies in [03_strategy_book.md](03_strategy_book.md) are built to adapt mechanically as these readings change, not to bet on one scenario.
