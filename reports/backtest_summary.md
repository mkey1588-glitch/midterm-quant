# Backtest summary (data through 2026-11-05)

Net of per-asset costs (2-15 bp one-way), 1% short borrow, idle cash earns 3M T-bill. Sharpe/Sortino are excess over T-bills. Orders fill at the next bar's open.

| Code | Class | Start | CAGR | Vol | Sharpe | MaxDD | Calmar | WorstYear | AvgGross | Turnover/yr | Bench | Bench CAGR | Bench Sharpe | Bench MaxDD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | US Equities | 1994-01-03 | +9.5% | +11.2% | 0.64 | -25.0% | 0.38 | -12.4% | 0.70 | 1.34 | SPY | +10.9% | 0.51 | -55.2% |
| E2 | US Equities | 2001-01-02 | +7.8% | +17.4% | 0.42 | -32.1% | 0.24 | -12.2% | 0.93 | 8.26 | SPY | +9.1% | 0.46 | -55.2% |
| E3 | US Equities | 2008-01-02 | +8.1% | +9.9% | 0.70 | -17.6% | 0.46 | -12.7% | 0.72 | 5.82 | SPY | +11.3% | 0.57 | -51.9% |
| E4 | US Equities | 2004-06-01 | +10.9% | +16.2% | 0.61 | -36.4% | 0.30 | -25.9% | 0.91 | 15.89 | SPY | +11.0% | 0.56 | -55.2% |
| E5 | US Equities | 2008-06-02 | +8.3% | +10.3% | 0.69 | -22.4% | 0.37 | -13.8% | 0.30 | 51.87 | SPY | +11.8% | 0.59 | -50.7% |
| C1 | Crypto | 2015-06-01 | +58.7% | +40.2% | 1.29 | -54.3% | 1.08 | -44.9% | 0.51 | 7.29 | BTC-USD | +67.3% | 1.08 | -83.4% |
| C2 | Crypto | 2015-06-01 | +54.1% | +40.1% | 1.22 | -56.3% | 0.96 | -29.0% | 0.50 | 5.29 | BTC-USD | +67.3% | 1.08 | -83.4% |
| C3 | Crypto | 2015-06-01 | +83.1% | +46.1% | 1.49 | -45.5% | 1.83 | -16.7% | 0.59 | 1.47 | BTC-USD | +67.3% | 1.08 | -83.4% |
| C4 | Crypto | 2018-03-01 | +39.5% | +55.4% | 0.84 | -66.1% | 0.60 | -30.4% | 0.53 | 13.25 | BTC-USD | +25.8% | 0.64 | -76.6% |
| C5 | Crypto | 2018-06-01 | +44.6% | +42.1% | 1.02 | -46.8% | 0.95 | -27.4% | 0.60 | 4.71 | BTC-USD | +32.4% | 0.72 | -76.6% |
| N1 | Energy | 2009-03-02 | -1.4% | +18.2% | -0.06 | -54.4% | -0.03 | -28.0% | 0.42 | 9.92 | USO | -1.7% | 0.10 | -95.3% |
| N2 | Energy | 2009-01-02 | -0.7% | +8.0% | -0.22 | -40.5% | -0.02 | -17.2% | 0.06 | 1.73 | USO | -3.7% | 0.05 | -95.3% |
| N3 | Energy | 2007-06-01 | +2.0% | +9.4% | 0.10 | -30.4% | 0.07 | -14.1% | 0.30 | 8.13 | XLE | +6.3% | 0.31 | -71.3% |
| N4 | Energy | 2009-09-01 | +9.3% | +22.5% | 0.45 | -44.9% | 0.21 | -20.0% | 0.87 | 5.80 | XLE | +9.0% | 0.40 | -71.3% |
| N5 | Energy | 2009-06-01 | +3.0% | +4.9% | 0.33 | -8.2% | 0.36 | -1.8% | 0.21 | 2.33 | USO | -4.1% | 0.03 | -95.3% |
| P1 | Precious Metals | 2007-03-01 | +7.4% | +11.8% | 0.54 | -29.0% | 0.26 | -9.5% | 0.57 | 4.05 | GLD | +9.2% | 0.49 | -45.6% |
| P2 | Precious Metals | 2008-09-02 | +8.8% | +20.3% | 0.45 | -55.1% | 0.16 | -21.1% | 0.83 | 5.99 | GLD | +8.9% | 0.49 | -45.6% |
| P3 | Precious Metals | 2007-06-01 | +5.3% | +24.9% | 0.27 | -45.3% | 0.12 | -21.2% | 0.65 | 11.44 | GLD | +9.3% | 0.50 | -45.6% |
| P4 | Precious Metals | 2008-01-02 | +5.3% | +10.7% | 0.41 | -24.1% | 0.22 | -10.9% | 0.49 | 3.14 | GLD | +8.2% | 0.44 | -45.6% |
| P5 | Precious Metals | 2011-03-01 | +8.8% | +20.2% | 0.44 | -47.5% | 0.19 | -13.3% | 0.73 | 5.33 | GLD | +6.4% | 0.36 | -45.6% |

## Equal-weight blend of the five sleeves per asset class

In this table both blend and benchmark Sharpe are computed vs zero (not excess of T-bills), so they are comparable with each other but not with the per-strategy table above.

| Class | Sleeves | Start | CAGR | Vol | Sharpe | MaxDD | Bench | Bench CAGR | Bench Sharpe | Bench MaxDD | Avg pairwise corr |
|---|---|---|---|---|---|---|---|---|---|---|---|
| US Equities | E1+E2+E3+E4+E5 | 2008-06-03 | +9.5% | +11.7% | 0.84 | -19.5% | SPY | +11.8% | 0.67 | -50.7% | 0.7 |
| Crypto | C1+C2+C3+C4+C5 | 2018-06-02 | +44.1% | +37.9% | 1.15 | -43.8% | BTC-USD | +32.2% | 0.77 | -76.6% | 0.79 |
| Energy | N1+N2+N3+N4+N5 | 2009-09-02 | +3.4% | +6.1% | 0.59 | -9.6% | USO | -3.8% | 0.08 | -95.3% | -0.01 |
| Precious Metals | P1+P2+P3+P4+P5 | 2011-03-02 | +6.8% | +14.7% | 0.52 | -36.8% | GLD | +6.4% | 0.46 | -45.6% | 0.74 |

## Rejected first specifications (research log)

| Code | Class | Start | CAGR | Vol | Sharpe | MaxDD | Calmar | WorstYear | AvgGross | Turnover/yr | Bench | Bench CAGR | Bench Sharpe | Bench MaxDD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C5a | Crypto | 2015-06-01 | -1.2% | +23.0% | -0.03 | -45.6% | -0.03 | -23.5% | 0.06 | 8.06 | BTC-USD | +67.3% | 1.08 | -83.4% |
| P3a | Precious Metals | 2007-06-01 | +2.3% | +25.3% | 0.16 | -71.5% | 0.03 | -29.6% | 0.66 | 14.85 | GLD | +9.3% | 0.50 | -45.6% |
