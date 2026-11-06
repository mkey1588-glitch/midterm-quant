# Strategy book: 20 quantitative strategies (5 per asset class)

Every strategy is implemented in [`midterm_quant/strategies/`](../midterm_quant/strategies/) as a Backtrader `TargetWeightStrategy` (see [04_framework_selection.md](04_framework_selection.md)). Each one is tied to a specific transmission channel from the [impact analysis](01_midterm_market_impact.md).

**Backtest conventions (all strategies):**
- Decisions use the close of bar *t*; orders fill at the **open of bar t+1**.
- Costs: 2bp (core ETFs), 5bp (commodity/thematic ETFs) or 15bp (crypto) one-way. Shorts pay a 1% annual borrow fee.
- Idle cash earns the 3-month T-bill rate (FRED `DTB3`).
- FRED series are lagged to their publication date.
- Sharpe and Sortino are measured on returns in excess of T-bills.
- Data runs through 4–5 Nov 2026.
- Full tables: [`reports/backtest_summary.md`](../reports/backtest_summary.md); yearly returns: [`reports/yearly_returns.csv`](../reports/yearly_returns.csv); charts: `reports/equity_*.png`.

## Summary

| Code | Strategy | Since | CAGR | Vol | Sharpe | MaxDD | Benchmark (CAGR / Sharpe / MaxDD) | Current signal (4 Nov 2026) |
|---|---|---|---|---|---|---|---|---|
| **E1** | Midterm-cycle seasonal + trend | 1994 | 9.5% | 11.2% | **0.64** | −25% | SPY 10.9% / 0.51 / −55% | SPY 98% |
| **E2** | Policy-regime sector momentum | 2001 | 7.8% | 17.4% | 0.42 | −32% | SPY 9.1% / 0.46 / −55% | XLK, XLV, XLF 33% each |
| **E3** | Vol-target + VIX term structure | 2008 | 8.1% | 9.9% | **0.70** | −18% | SPY 11.3% / 0.57 / −52% | SPY 90% |
| **E4** | Broadening vs mega-cap rotation | 2004 | 10.9% | 16.2% | 0.61 | −36% | SPY 11.0% / 0.56 / −55% | RSP 69%, QQQ 29% |
| **E5** | Political-shock reversal (credit-filtered) | 2008 | 8.3% | 10.3% | **0.69** | −22% | SPY 11.8% / 0.59 / −51% | Flat (no setup) |
| **C1** | BTC/ETH trend + vol target | 2015 | 58.7% | 40.2% | **1.29** | −54% | BTC 67.3% / 1.08 / −83% | BTC 17%, ETH 17% |
| **C2** | Dollar-liquidity regime BTC | 2015 | 54.1% | 40.1% | 1.22 | −56% | BTC 67.3% / 1.08 / −83% | BTC 30% |
| **C3** | Halving-cycle phase + trend | 2015 | 83.1% | 46.1% | **1.49**\* | −46% | BTC 67.3% / 1.08 / −83% | BTC 70% |
| **C4** | BTC/ETH/SOL dual-momentum rotation | 2018 | 39.5% | 55.4% | 0.84 | −66% | BTC 25.8% / 0.64 / −77% | BTC 98% |
| **C5** | Stablecoin-supply liquidity impulse | 2018 | 44.6% | 42.1% | 1.02 | −47% | BTC 32.4% / 0.72 / −77% | BTC 18%, ETH 8% |
| **N1** | Crude trend + curve filter | 2009 | −1.4% | 18.2% | −0.07 | −54% | USO −1.7% / 0.10 / −95% | USO 48% long |
| **N2** | Geopolitical risk-premium fade | 2009 | −0.7% | 8.0% | −0.22 | −41% | USO −3.7% / 0.05 / −95% | Flat |
| **N3** | E&P equities vs crude relative value | 2007 | 2.0% | 9.4% | 0.10 | −30% | XLE 6.3% / 0.31 / −71% | Flat |
| **N4** | Clean vs fossil policy rotation | 2009 | 9.3% | 22.5% | 0.45 | −45% | XLE 9.0% / 0.40 / −71% | XLE 98% |
| **N5** | Gasoline-crack seasonal reversion | 2009 | 3.0% | 4.9% | 0.33 | **−8%** | USO −4.1% / 0.03 / −95% | Flat |
| **P1** | Gold trend + real-yield/USD tilt | 2007 | 7.4% | 11.8% | **0.54** | −29% | GLD 9.2% / 0.49 / −46% | GLD 11% |
| **P2** | Gold/silver ratio reversion | 2008 | 8.8% | 20.3% | 0.45 | −55% | GLD 8.9% / 0.49 / −46% | GLD 23%, SLV 27% |
| **P3** | Miner margin rotation (gold/oil) | 2007 | 5.3% | 24.9% | 0.27 | −45% | GLD 9.3% / 0.50 / −46% | Flat (gold below trend) |
| **P4** | Policy-stress gold overlay | 2008 | 5.3% | 10.7% | 0.41 | −24% | GLD 8.2% / 0.44 / −46% | GLD 41% |
| **P5** | Precious-metals dual momentum | 2011 | 8.8% | 20.2% | 0.44 | −48% | GLD 6.4% / 0.36 / −46% | Flat (none trending) |

\*C3 is fitted to only three complete halving cycles; see its caveat.

**Equal-weight blends** (`reports/class_blends.csv`; Sharpe vs zero for both blend and benchmark):

| Class blend | Since | CAGR | Vol | Sharpe | MaxDD | Benchmark | Avg pairwise corr |
|---|---|---|---|---|---|---|---|
| US equities E1–E5 | 2008 | 9.5% | 11.7% | **0.84** | **−20%** | SPY 11.8% / 0.67 / −51% | 0.70 |
| Crypto C1–C5 | 2018 | 44.1% | 37.9% | **1.15** | **−44%** | BTC 32.2% / 0.77 / −77% | 0.79 |
| Energy N1–N5 | 2009 | 3.4% | 6.1% | 0.59 | **−10%** | USO −3.8% / 0.08 / −95% | **−0.01** |
| Precious metals P1–P5 | 2011 | 6.8% | 14.7% | 0.52 | −37% | GLD 6.4% / 0.46 / −46% | 0.74 |

**How to read this honestly:**
- The equity and metals strategies mostly **trade return for risk**: lower CAGR than buy-and-hold, with higher Sharpe and much smaller drawdowns. The crypto strategies beat BTC on a risk-adjusted basis and, since 2018, in absolute terms too.
- **Energy is the weak asset class.** No ETF-based oil-timing rule tested here (trend, risk-premium fade, energy-complex trend, Brent–WTI spread) had a meaningful standalone edge from 2009 to 2026. That period includes two price collapses (2014–16, 2020) and USO's 2020 restructuring.
- The energy sleeves are nearly **uncorrelated with each other** (avg −0.01), so their blend has a Sharpe of 0.59 and a −10% max drawdown. That is how to use them: as a diversified sleeve, never as individual alpha bets.

---

## U.S. equities

### E1: Midterm-cycle seasonal + trend
- **Thesis.** The S&P 500 rose in the 12 months after all 19 midterms since 1950. The pre-election year averages +17%. A 200-day trend filter limits damage when a policy or macro shock overrides seasonality (2002, 2008, 2022).
- **Universe.** SPY (rest in T-bills).
- **Signal.** `sweet = (year%4==2 and month>=10) or year%4==3`; `up = close > SMA200`.
- **Rules.** In the sweet spot, weight = 100% if up, otherwise 60%. Outside it, 70% if up, otherwise 30%. Weekly rebalance.
- **Backtest (1994–2026).** 9.5% CAGR, Sharpe 0.64, MaxDD −25% vs SPY 10.9% / 0.51 / −55%.
- **Now.** Sweet spot and uptrend, so 98% SPY. The sweet spot runs to 31 Dec 2027.
- **Invalidation.** The seasonal edge is a well-known pattern (Hirsch, 1967). If 2027 underperforms with SPY above trend, downgrade the seasonal weight.

### E2: Policy-regime sector momentum
- **Thesis.** Policy shocks create persistent sector trends: tariffs, ACA subsidies, defence budgets, AI/data-centre scrutiny, clean-energy credits. Ride the strongest risk-adjusted trends.
- **Universe.** Nine SPDR sectors plus policy baskets (ITA defence, KRE regional banks, XBI biotech, TAN solar, SMH semis), with IEF as the defensive slot.
- **Signal.** 126-day return skipping the last 21 days, divided by realised vol. Eligible only if above the 200-day SMA and the score is > 0.
- **Rules.** Hold the top 3 equal-weight. Unused slots go to IEF if IEF is above its 200-day SMA, otherwise T-bills. Monthly rebalance.
- **Backtest (2001–2026).** 7.8% / Sharpe 0.42 / −32% vs SPY 9.1% / 0.46 / −55%. It trails in narrow mega-cap markets (2021: −6% vs +29%).
- **Now.** XLK, XLV, XLF. Healthcare entered on its policy-driven trend.
- **Note.** A thematic universe chosen in 2026 carries survivorship and selection bias.

### E3: Vol-target + VIX term structure
- **Thesis.** Gridlock removes fiscal tail risk but adds headline volatility (shutdowns, the debt limit, tariffs, Iran). Size equity exposure to realised risk, and halve it when the VIX curve inverts.
- **Rules.** `w = min(0.98, 12% / max(RV20, RV60))`, halved if VIX/VIX3M > 1. Evaluated daily, trades only if the weight changes by ≥ 5pp.
- **Backtest (2008–2026).** 8.1% / **0.70** / **−18%** vs SPY 11.3% / 0.57 / −52%.
- **Now.** 90% SPY; VIX/VIX3M = 0.89.

### E4: Broadening vs mega-cap rotation
- **Thesis.** AI-regulation risk under a Democratic Congress plus a lower term premium favour equal-weight and small caps over mega-cap growth, but only when the relative trend confirms.
- **Signal.** Score from 0 to 3 = [RSP/QQQ above its 100-day mean] + [10Y yield down over 20 days] + [IWM beat QQQ over 63 days].
- **Allocation.** 3 → RSP 50 / IWM 50; 2 → RSP 70 / QQQ 30; 1 → RSP 30 / QQQ 70; 0 → QQQ 100. Halve everything if both RSP and QQQ are below their 200-day SMAs. Weekly rebalance.
- **Backtest (2004–2026).** 10.9% / 0.61 / −36% vs SPY 11.0% / 0.56 / −55%. Turnover is high (~16x a year) but on cheap ETFs.
- **Now.** Score 2: RSP 69%, QQQ 29%.

### E5: Political-shock reversal (credit-filtered)
- **Thesis.** Shutdown, debt-limit and tariff headlines cause sharp dips that revert *when credit does not confirm them*. The 2011, 2013, 2018–19 and 2023 standoffs are examples.
- **Entry.** RSI(2) < 10, and either SPY is above its 200-day SMA or credit is calm (z of the 10-day change in log(HYG/IEF) > −1).
- **Exit.** Close above the 5-day SMA, 10 days elapsed, or a −8% stop.
- **Backtest (2008–2026).** 8.3% / 0.69 / −22% with only **30% average exposure**, so most of the time the capital sits in T-bills. It can be layered on a core position.
- **Now.** No setup. Credit (M10) is already stressed, so a break below the 200-day SMA would **not** be bought.

## Crypto

### C1: BTC/ETH trend + vol target
- **Rules.** For each asset: score = share of {20, 60, 120}-day returns that are > 0. Weight = ½ × score × min(1, 60% / RV30). Weekly rebalance.
- **Backtest (2015–2026).** 58.7% / 1.29 / −54% vs BTC 67.3% / 1.08 / −83%.
- **Now.** BTC 17%, ETH 17% (partial trend).

### C2: Dollar-liquidity regime
- **Thesis.** The 2027 debt-limit cycle drives the TGA, and therefore Fed net liquidity, which leads BTC.
- **Score.** 0.4 × [net liquidity 13-week change > 0] + 0.3 × [broad USD below its 100-day SMA] + 0.3 × [BTC above its 100-day SMA]. Weekly rebalance.
- **Backtest.** 54.1% / 1.22 / −56%.
- **Now.** Only the trend leg is on (liquidity draining, strong USD): BTC 30%.
- **Watch.** TGA drawdown ahead of the X-date (M9, M8).

### C3: Halving-cycle phase + trend
- **Rules.** Phase by days since the last halving: expansion (< 540d) 100%; bear (540–900d) 20%; accumulation (> 900d) 70%. Multiply by 0.5 if BTC is below its 200-day SMA. Weekly rebalance.
- **Backtest.** 83.1% / 1.49 / −46%.
- **⚠ Caveat.** The phase boundaries were chosen with knowledge of the 2017, 2021 and 2025 tops. That is in-sample, with only three cycles. Treat it as a structural prior and size it smaller than the others. ETF-driven demand may also be flattening the cycle.
- **Now.** Accumulation phase (day ~930), above the 200-day: 70%.

### C4: BTC/ETH/SOL dual-momentum rotation
- **Thesis.** With market-structure legislation dead, regulatory risk falls hardest on alt-coins. Hold only majors with positive absolute *and* relative momentum.
- **Rules.** Eligible if the 90-day return is > 0 and the price is above its 100-day SMA. Score = risk-adjusted 30-day plus 90-day momentum. Hold the top 2, inverse-vol weighted, otherwise cash. Weekly rebalance.
- **Backtest (2018–2026).** 39.5% / 0.84 / −66% vs BTC 25.8% / 0.64 / −77%.
- **Now.** BTC 98% (ETH and SOL fail the filters).

### C5: Stablecoin-supply liquidity impulse *(replaced the original C5; see the research log)*
- **Thesis.** Stablecoins are crypto's on-chain dollar base. The GENIUS Act is already law, so issuance continues even without CLARITY. Net creation is the marginal bid.
- **Score.** 0.5 × [30-day supply growth > 0] + 0.25 × [30-day growth > ⅓ of 90-day growth (accelerating)] + 0.25 × [BTC above its 100-day SMA]. Split 70/30 BTC/ETH. Weekly rebalance.
- **Data.** DefiLlama total USD-pegged supply, lagged 1 day.
- **Backtest (2018–2026).** 44.6% / 1.02 / −47%. Robust to the lookback: Sharpe 0.88–1.02 for 14, 30 and 60 days.
- **Now.** Supply is contracting (−4%), so only the trend leg is on: BTC 18%, ETH 8%.

## Energy

### N1: Crude trend + curve-shape filter
- **Rules.** TSMOM score over 63/126/252 days on USO. Go long if score > 0 *and* USO beat USL over 63 days (backwardation). Go short if both are negative. Size to 20% vol. Weekly rebalance.
- **Backtest (2009–2026).** −1.4% / −0.07 / −54%. **No standalone edge.** Returns come in regime breaks (2014 +36%, 2015 +17%, 2020 +44%, 2026 +22%) and bleed in chop.
- **Role.** A convex hedge for war-driven regime shifts in the portfolio, not alpha.
- **Now.** Long USO 48% (uptrend, backwardation).

### N2: Geopolitical risk-premium fade
- **Rules.** z = USO 20-day log return vs 1 year. Short spikes (z > +2) **only** when gasoline is above its 70th percentile over 2 years (political pain invites offsets). Buy crashes (z < −2). Exit at |z| < 0.5 or after 30 days. Size to 20% vol.
- **Backtest.** −0.7% / −0.22 / −41%, exposure ~6%. The losses come from the crash-buying leg in 2014 and 2020.
- **Status.** Kept as **pre-specified**. A short-only variant traded too rarely to evaluate (gross exposure 1%). Treat it as an event playbook, not alpha.
- **Now.** Flat.

### N3: E&P equities vs crude relative value
- **Rules.** z of log(XOP/USO) over 60 days. If z > 2: short XOP / long USO, 40% each; if z < −2: the reverse. Exit at |z| < 0.5, |z| > 4 (stop) or after 40 days.
- **Backtest (2007–2026).** 2.0% / 0.10 / −30%. It works except for USO's April 2020 negative-price dislocation (−14% that year).
- **Now.** Flat.

### N4: Clean vs fossil policy rotation
- **Thesis.** Congressional control shifts sentiment between clean and fossil energy, but clean energy is long-duration and rate-sensitive.
- **Rules.** If ICLN beat XLE over 63 days and the 10Y rose < 25bp: ICLN. If ICLN led but yields jumped: 50/50. Otherwise XLE. Halve any leg below its 200-day SMA. Monthly rebalance.
- **Backtest (2009–2026).** 9.3% / 0.45 / −45% vs XLE 9.0% / 0.40 / −71%.
- **Now.** XLE 98%. The election-day TAN pop has not changed the 63-day relative trend.
- **Watch.** The 2027 OBBBA placed-in-service rush.

### N5: Gasoline-crack seasonal reversion
- **Thesis.** Gasoline is the political price. Cracks widen into the driving season and narrow after it.
- **Rules.** z of log(UGA/USO) over 250 days. In Jan–Mar, if z < −1: long UGA / short USO. In Aug–Oct, if z > +1: the reverse. Legs of 40%. Exit when z crosses 0 or after 60 days.
- **Backtest (2009–2026).** 3.0% / 0.33 / **−8%**, vol 4.9%. A small but consistent edge; UGA liquidity limits size.
- **Now.** Flat.

## Precious metals

### P1: Gold trend + real-yield/USD tilt
- **Rules.** Weight = 0.6 × trend (share of {above SMA50, above SMA200, 126-day return > 0}) + 0.2 × real-yield tilt (falling 50bp → 1, rising 50bp → 0) + 0.2 × dollar tilt (−3% → 1, +3% → 0). Weekly rebalance.
- **Backtest (2007–2026).** 7.4% / 0.54 / −29% vs GLD 9.2% / 0.49 / −46%.
- **Now.** Trend broken, real yields up, dollar up: GLD 11%.

### P2: Gold/silver ratio reversion
- **Rules.** z of log(GLD/SLV) over 2 years. Silver weight = clip(0.5 + 0.25z, 0, 1); gold gets the rest. Halve everything if both metals are below their 200-day SMAs. Weekly rebalance.
- **Backtest (2008–2026).** 8.8% / 0.45 / −55%.
- **Now.** Ratio neutral (z ≈ 0), both metals below trend: GLD 23%, SLV 27%.

### P3: Miner margin rotation (gold/oil ratio) *(revised specification; see the research log)*
- **Thesis.** Miner margins are the gold price minus costs, roughly 20–25% of which is energy. Own miners only when gold, the gold/oil ratio and GDX are all above their 200-day SMAs. Hold bullion when only gold trends. Otherwise cash.
- **Backtest (2007–2026).** 5.3% / 0.27 / −45% vs GLD 9.3% / 0.50 / −46%. GDX's 2011–15 bear market still weighs on it.
- **Now.** Gold is below trend, so flat.
- **Watch.** The oil decline is lifting the ratio. GDX/GLD (P-d) is already confirming.

### P4: Policy-stress gold overlay
- **Thesis.** Gridlock-era stress events show up in policy uncertainty, VIX and term premium. Scale gold with a composite stress z-score.
- **Rules.** stress = mean(z of 30-day EPU vs 3 years, z of VIX vs 1 year, z of the 63-day term-premium change vs 3 years). w = 0.10 + 0.88 × sigmoid(1.5 × stress), × 0.6 if gold is below its 200-day SMA. Weekly rebalance.
- **Backtest (2008–2026).** 5.3% / 0.41 / −24%.
- **Now.** GLD 41%.

### P5: Precious-metals dual momentum
- **Rules.** Universe GLD, SLV, PPLT, PALL. Eligible if the 126-day return is > 0 and the price is above its 200-day SMA. Hold the top 2 by risk-adjusted momentum, inverse-vol weighted, otherwise cash. Monthly rebalance.
- **Backtest (2011–2026).** 8.8% / 0.44 / −48% vs GLD 6.4% / 0.36 / −46%.
- **Now.** No metal trending, so 100% T-bills.

---

## Research log: what was changed and why

Changing a strategy after seeing its backtest is a researcher degree of freedom. These are all such changes, kept runnable in `strategies.REJECTED`:

| Original | Result as first specified | Diagnosis | Action |
|---|---|---|---|
| **C5a** liquidation-shock reversal (buy −2.5σ BTC days) | −1.2% CAGR, Sharpe −0.03 (2015–26) | Crashes in early bear phases cascade (2020: −24%; 2025: −18%). Only a stricter trend filter plus a 3-day hold worked, and that was parameter-fragile (Sharpe 0.14–0.48 across neighbours) | **Replaced** by C5 stablecoin impulse, which was robust across lookbacks |
| **P3a** gold-momentum minus 0.25 × oil-momentum miner rotation | 2.3% CAGR, MaxDD −72% | Whipsawed through the 2011–15 miner bear market | **Revised** to the gold/oil ratio plus 200-day trend gates (MaxDD −45%) |
| N1 variants (full horizon agreement, long-only, no curve filter) | Sharpe −0.05 to +0.08 | No variant had an edge | **Kept the original**, labelled as a hedge |
| N2 short-only variant | Gross exposure 1%, Sharpe −0.13 | Too few qualifying episodes | **Kept the original**, labelled as an event playbook |
| Energy-complex TSMOM (USO/UGA/UNG/XLE) and Brent–WTI spread | Sharpe −0.02 to 0.16, and −0.28 respectively | No edge | Not adopted |

## Known limitations

- **Small samples for event effects.** The midterm seasonal has 19 observations, the halving cycle three.
- **ETF proxies.** USO, UGA and USL carry roll costs and had the 2020 restructuring. There are no futures-curve data.
- **Survivorship in thematic universes.** TAN, SMH and ICLN were chosen with 2026 hindsight.
- **Data quality.** Yahoo adjusted closes can be revised. DefiLlama history gets restated. FRED lags are approximations of release times.
- **No capacity, borrow-availability or tax modelling.** Crypto is modelled as spot with no funding or staking.
- **Regime dependence.** 2026 combines a hawkish Fed, a war-driven oil price and AI concentration, a combination with no clean historical precedent.
