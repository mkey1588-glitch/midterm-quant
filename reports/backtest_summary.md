# Backtest summary: development sample through 2026-11-05

**Evidence status.** Every figure below comes from data that was available while the rules were written (4 Nov 2026). None of it is out-of-sample. 46 configurations were tried in total (`reports/evidence/trial_registry.csv`); the deflated Sharpe ratio (DSR) is the probability that the true Sharpe exceeds the best of 46 unskilled trials. C3 is in-sample research and is not counted as a result.

**Conventions.** Month-end returns, sqrt(12) annualisation for every class, excess over the 3-month T-bill (FRED DTB3); strategy NAVs net of 2-15bp one-way costs, 1% short borrow, T-bill interest on idle cash; orders fill at the next bar's open; revision-prone FRED inputs use first-print (ALFRED) values. Benchmarks: buy-and-hold of the reference asset, a 10-month trend rule on it (with costs), and the reference scaled to the strategy's volatility (ex post).

| Code | Name | Evidence | Start | CAGR | Vol | Sharpe | DSR | MaxDD | MaxDD_days_to_recover | Beta_SPY | AvgGross | Turnover/yr | Ref | buy_hold_Sharpe | trend_Sharpe | risk_matched_Sharpe | IR_vs_risk_matched |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | Midterm-cycle seasonal + trend | D1 | 1994-02 | +9.3% | +9.6% | 0.73 | 0.08 | -25.0% | 401 | 0.59 | 0.70 | 1.34 | SPY | 0.59 | 0.70 | 0.59 | 0.31 |
| E2 | Policy-regime sector momentum | D1 | 2001-02 | +7.9% | +13.6% | 0.50 | 0.01 | -32.1% | 913 | 0.57 | 0.93 | 8.26 | SPY | 0.52 | 0.68 | 0.52 | -0.04 |
| E3 | Vol-target + VIX term-structure | D1 | 2008-02 | +8.2% | +9.2% | 0.75 | 0.17 | -17.6% | 301 | 0.52 | 0.72 | 5.82 | SPY | 0.69 | 0.69 | 0.69 | 0.04 |
| E4 | Broadening vs mega-cap rotation | D1 | 2004-07 | +10.8% | +14.6% | 0.65 | 0.07 | -36.4% | 482 | 0.88 | 0.91 | 15.89 | SPY | 0.66 | 0.68 | 0.66 | 0.00 |
| E5 | Political-shock reversal (credit-filtered) | D1 | 2008-07 | +8.4% | +9.9% | 0.73 | 0.14 | -22.4% | 207 | 0.37 | 0.30 | 51.92 | SPY | 0.73 | 0.69 | 0.73 | -0.05 |
| C1 | BTC/ETH trend + vol target | D1 | 2015-07 | +57.8% | +49.4% | 1.10 | 0.70 | -54.3% | 476 | 0.97 | 0.51 | 7.29 | BTC-USD | 1.01 | 1.10 | 1.01 | 0.16 |
| C2 | Dollar-liquidity regime BTC | D2 | 2015-07 | +59.1% | +48.2% | 1.14 | 0.75 | -41.5% | 890 | 0.80 | 0.50 | 5.39 | BTC-USD | 1.01 | 1.10 | 1.01 | 0.23 |
| C3 | Halving-cycle phase + trend | D3 | 2015-07 | +82.6% | +54.6% | 1.32 | 0.93 | -45.5% | 605 | 0.91 | 0.59 | 1.47 | BTC-USD | 1.01 | 1.10 | 1.01 | 0.65 |
| C4 | BTC/ETH/SOL dual-momentum rotation | D1 | 2018-04 | +43.3% | +68.6% | 0.79 | 0.27 | -66.1% | 172 | 1.43 | 0.53 | 13.25 | BTC-USD | 0.70 | 0.89 | 0.70 | 0.18 |
| C5 | Stablecoin-supply liquidity impulse | D2 | 2018-07 | +45.0% | +48.1% | 0.94 | 0.44 | -46.8% | 463 | 0.99 | 0.60 | 4.71 | BTC-USD | 0.73 | 0.96 | 0.73 | 0.56 |
| N1 | Crude trend + curve-shape filter | D1 | 2009-04 | -0.7% | +19.0% | -0.02 | 0.00 | -54.4% | not yet | -0.32 | 0.42 | 9.92 | USO | 0.11 | 0.19 | 0.11 | -0.09 |
| N2 | Geopolitical risk-premium fade | D1 | 2009-02 | -0.7% | +8.0% | -0.23 | 0.00 | -40.5% | not yet | 0.11 | 0.06 | 1.73 | USO | 0.11 | 0.19 | 0.11 | -0.30 |
| N3 | E&P equities vs crude relative value | D1 | 2007-07 | +2.0% | +10.0% | 0.10 | 0.00 | -30.4% | 1049 | -0.04 | 0.30 | 8.13 | XLE | 0.33 | 0.43 | 0.33 | -0.17 |
| N4 | Clean vs fossil policy rotation | D1 | 2009-10 | +9.5% | +22.4% | 0.45 | 0.02 | -44.9% | 328 | 0.78 | 0.87 | 5.80 | XLE | 0.41 | 0.49 | 0.41 | 0.02 |
| N5 | Gasoline crack seasonal mean-reversion | D1 | 2009-07 | +3.0% | +4.4% | 0.36 | 0.00 | -8.2% | 6 | -0.01 | 0.21 | 2.33 | USO | 0.07 | 0.20 | 0.07 | 0.21 |
| P1 | Gold trend with real-yield/USD tilt | D1 | 2007-04 | +7.3% | +11.7% | 0.53 | 0.02 | -29.7% | 1685 | 0.06 | 0.57 | 3.94 | GLD | 0.49 | 0.44 | 0.49 | 0.05 |
| P2 | Gold/silver ratio reversion | D1 | 2008-10 | +9.2% | +20.7% | 0.46 | 0.01 | -55.1% | 1477 | 0.33 | 0.83 | 5.99 | GLD | 0.46 | 0.41 | 0.46 | -0.00 |
| P3 | Miner margin rotation (gold/oil ratio) | D2 | 2007-07 | +5.8% | +24.2% | 0.29 | 0.00 | -45.3% | 1624 | 0.21 | 0.65 | 11.44 | GLD | 0.51 | 0.46 | 0.51 | -0.27 |
| P4 | Policy-stress gold overlay | D1 | 2008-02 | +4.9% | +9.4% | 0.41 | 0.01 | -24.1% | 1314 | 0.07 | 0.49 | 3.09 | GLD | 0.42 | 0.35 | 0.42 | -0.06 |
| P5 | Gold/silver/platinum/palladium dual momentum | D1 | 2011-04 | +8.8% | +20.1% | 0.44 | 0.02 | -47.5% | 966 | 0.26 | 0.73 | 5.32 | GLD | 0.35 | 0.25 | 0.35 | 0.13 |

## Class blends (equal weight, monthly rebalanced, excess-return Sharpe)

| Class | Variant | Start | CAGR | Vol | Sharpe | MaxDD | Ref | Ref Sharpe | Risk-matched Sharpe | Avg corr |
|---|---|---|---|---|---|---|---|---|---|---|
| US Equities | all five | 2008-07 | +9.6% | +9.8% | 0.84 | -16.0% | SPY | 0.73 | 0.73 | 0.65 |
| Crypto | all five | 2018-07 | +46.5% | +44.8% | 1.00 | -33.7% | BTC-USD | 0.73 | 0.73 | 0.80 |
| Crypto | excluding C3 | 2018-07 | +45.3% | +45.8% | 0.97 | -38.8% | BTC-USD | 0.73 | 0.73 | 0.79 |
| Energy | all five | 2009-10 | +3.6% | +6.0% | 0.38 | -7.5% | USO | 0.08 | 0.08 | -0.04 |
| Precious Metals | all five | 2011-04 | +6.7% | +14.7% | 0.40 | -34.6% | GLD | 0.35 | 0.35 | 0.74 |

## Does each sleeve earn its place? (risk contribution and leave-one-out)

| Class | Sleeve | Risk contribution | Blend Sharpe without it | Change if removed |
|---|---|---|---|---|
| US Equities | E1 | 19% | 0.83 | -0.00 |
| US Equities | E2 | 23% | 0.86 | +0.02 |
| US Equities | E3 | 17% | 0.82 | -0.01 |
| US Equities | E4 | 28% | 0.85 | +0.01 |
| US Equities | E5 | 13% | 0.78 | -0.06 |
| Crypto | C1 | 18% | 1.01 | +0.01 |
| Crypto | C2 | 16% | 0.98 | -0.02 |
| Crypto | C3 | 18% | 0.97 | -0.03 |
| Crypto | C4 | 28% | 1.01 | +0.01 |
| Crypto | C5 | 20% | 1.00 | -0.00 |
| Energy | N1 | 29% | 0.42 | +0.05 |
| Energy | N2 | 4% | 0.44 | +0.06 |
| Energy | N3 | 11% | 0.33 | -0.04 |
| Energy | N4 | 55% | 0.06 | -0.32 |
| Energy | N5 | 1% | 0.33 | -0.05 |
| Precious Metals | P1 | 14% | 0.41 | +0.00 |
| Precious Metals | P2 | 25% | 0.42 | +0.01 |
| Precious Metals | P3 | 28% | 0.43 | +0.02 |
| Precious Metals | P4 | 11% | 0.40 | -0.01 |
| Precious Metals | P5 | 22% | 0.36 | -0.05 |

## First-print vs latest-vintage inputs

| Code | Sharpe first-print | Sharpe latest-vintage | Identical rebalance targets |
|---|---|---|---|
| C2 | 1.14 | 1.15 | 590 of 597 |
| P1 | 0.53 | 0.53 | 382 of 1028 |
| P4 | 0.41 | 0.41 | 6 of 984 |

## Trial registry (all configurations tried)

| Trial | Family | Status | Recorded on | Params | Recorded CAGR / Sharpe (daily basis) | Rerun CAGR / Sharpe (monthly) | DSR |
|---|---|---|---|---|---|---|---|
| E1 | E1 | adopted | 2026-11-04 | `{}` | +9.5% / 0.64 | +9.3% / 0.73 | 0.08 |
| E2 | E2 | adopted | 2026-11-04 | `{}` | +7.4% / 0.40 | +7.9% / 0.50 | 0.01 |
| E3 | E3 | adopted | 2026-11-04 | `{}` | +8.1% / 0.70 | +8.2% / 0.75 | 0.17 |
| E4 | E4 | adopted | 2026-11-04 | `{}` | +10.9% / 0.61 | +10.8% / 0.65 | 0.07 |
| E5 | E5 | adopted | 2026-11-04 | `{}` | +8.3% / 0.69 | +8.4% / 0.73 | 0.14 |
| C1 | C1 | adopted | 2026-11-04 | `{}` | +58.7% / 1.29 | +57.8% / 1.10 | 0.70 |
| C2v1 | C2 | superseded | 2026-11-04 | `{}` | +54.1% / 1.22 | +59.5% / 1.15 | 0.76 |
| C3 | C3 | in-sample research | 2026-11-04 | `{}` | +83.1% / 1.49 | +82.6% / 1.32 | 0.93 |
| C4 | C4 | adopted | 2026-11-04 | `{}` | +40.0% / 0.84 | +43.3% / 0.79 | 0.27 |
| C5a | C5 | rejected | 2026-11-04 | `{}` | -1.2% / -0.03 | -1.2% / -0.06 | 0.00 |
| N1 | N1 | adopted | 2026-11-04 | `{}` | -1.4% / -0.06 | -0.7% / -0.02 | 0.00 |
| N2 | N2 | adopted | 2026-11-04 | `{}` | -0.7% / -0.22 | -0.7% / -0.23 | 0.00 |
| N3 | N3 | adopted | 2026-11-04 | `{}` | +2.0% / 0.10 | +2.0% / 0.10 | 0.00 |
| N4 | N4 | adopted | 2026-11-04 | `{}` | +9.3% / 0.45 | +9.5% / 0.45 | 0.02 |
| N5 | N5 | adopted | 2026-11-04 | `{}` | +3.0% / 0.33 | +3.0% / 0.36 | 0.00 |
| P1 | P1 | adopted | 2026-11-04 | `{}` | +7.5% / 0.54 | +7.3% / 0.53 | 0.02 |
| P2 | P2 | adopted | 2026-11-04 | `{}` | +8.8% / 0.45 | +9.2% / 0.46 | 0.01 |
| P3a | P3 | rejected | 2026-11-04 | `{}` | +2.8% / 0.18 | +2.7% / 0.17 | 0.00 |
| P4 | P4 | adopted | 2026-11-04 | `{}` | +5.3% / 0.40 | +4.9% / 0.41 | 0.01 |
| P5 | P5 | adopted | 2026-11-04 | `{}` | +8.9% / 0.45 | +8.8% / 0.44 | 0.02 |
| C5a-v1 | C5 | rejected | 2026-11-04 | `{"trend_floor": 1.0}` | +3.6% / 0.17 | +3.7% / 0.17 | 0.00 |
| C5a-v2 | C5 | rejected | 2026-11-04 | `{"shock_z": -2.0, "trend_floor": 1.0}` | +9.1% / 0.40 | +8.8% / 0.41 | 0.02 |
| C5a-v3 | C5 | rejected | 2026-11-04 | `{"shock_z": -3.0, "trend_floor": 1.0}` | +3.1% / 0.14 | +3.2% / 0.13 | 0.00 |
| C5a-v4 | C5 | rejected | 2026-11-04 | `{"max_hold": 3, "trend_floor": 1.0}` | +8.4% / 0.48 | +8.4% / 0.55 | 0.06 |
| C5a-v5 | C5 | rejected | 2026-11-04 | `{"max_hold": 14, "trend_floor": 1.0}` | +1.7% / 0.09 | +1.8% / 0.07 | 0.00 |
| N1b-1 | N1 | not adopted | 2026-11-04 | `{"agree": 1.0}` | +0.0% / -0.02 | +0.7% / 0.03 | 0.00 |
| N1b-2 | N1 | not adopted | 2026-11-04 | `{"agree": 1.0, "long_only": true}` | +0.5% / -0.05 | +0.9% / -0.00 | 0.00 |
| N1b-3 | N1 | not adopted | 2026-11-04 | `{"agree": 1.0, "use_curve": false}` | +1.4% / 0.08 | +2.1% / 0.12 | 0.00 |
| N1b-4 | N1 | not adopted | 2026-11-04 | `{"agree": 0.3, "long_only": true}` | +0.9% / 0.02 | +1.4% / 0.05 | 0.00 |
| N2s-1 | N2 | not adopted | 2026-11-04 | `{}` | +0.9% / -0.13 | +0.9% / -0.18 | 0.00 |
| N2s-2 | N2 | not adopted | 2026-11-04 | `{"gas_pct": 0.0}` | +0.0% / -0.14 | +0.0% / -0.14 | 0.00 |
| N2s-3 | N2 | not adopted | 2026-11-04 | `{"entry_z": 1.5}` | +1.2% / -0.02 | +1.2% / -0.05 | 0.00 |
| N2s-4 | N2 | not adopted | 2026-11-04 | `{"max_hold": 60}` | +0.9% / -0.13 | +0.9% / -0.18 | 0.00 |
| P3 | P3 | adopted | 2026-11-04 | `{}` | +5.4% / 0.28 | +5.8% / 0.29 | 0.00 |
| P3b-1 | P3 | not adopted | 2026-11-04 | `{"gdx_trend": false}` | +5.8% / 0.29 | +6.1% / 0.29 | 0.00 |
| C5 | C5 | adopted | 2026-11-04 | `{}` | +44.6% / 1.02 | +45.0% / 0.94 | 0.44 |
| C5x-1 | C5 | not adopted | 2026-11-04 | `{"lb": 14}` | +34.7% / 0.88 | +34.9% / 0.81 | 0.30 |
| C5x-2 | C5 | not adopted | 2026-11-04 | `{"lb": 60}` | +42.4% / 0.93 | +42.9% / 0.86 | 0.34 |
| C5x-3 | C5 | not adopted | 2026-11-04 | `{"trend": false}` | +32.2% / 0.91 | +32.6% / 0.86 | 0.35 |
| N1x-1 | N-alt | not adopted | 2026-11-04 | `{}` | -1.8% / -0.02 | -0.9% / 0.04 | 0.00 |
| N1x-2 | N-alt | not adopted | 2026-11-04 | `{"agree": 1.0}` | +2.7% / 0.16 | +3.6% / 0.20 | 0.00 |
| N1x-3 | N-alt | not adopted | 2026-11-04 | `{"tv": 0.08}` | -1.0% / -0.02 | -0.3% / 0.03 | 0.00 |
| N2x-1 | N-alt | not adopted | 2026-11-04 | `{}` | +0.5% / -0.28 | +0.3% / -0.29 | 0.00 |
| N2x-2 | N-alt | not adopted | 2026-11-04 | `{"window": 60}` | -1.0% / -0.60 | -1.0% / -0.43 | 0.00 |
| N2x-3 | N-alt | not adopted | 2026-11-04 | `{"entry": 1.5}` | +0.3% / -0.29 | +0.3% / -0.28 | 0.00 |
| C2 | C2 | adopted | 2026-11-06 | `{}` | n/a (new) | +59.1% / 1.14 | 0.75 |
