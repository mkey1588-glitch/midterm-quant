# Midterm event study with controls

Forward S&P 500 price returns from the close of election day (the Tuesday after the first Monday in November) for every year 1950-2025 (n = 76). Descriptive only.

## Midterm years vs all other years

| horizon | midterm n | midterm mean | midterm 90% CI | midterm %pos | other n | other mean | other 90% CI | other %pos | difference | permutation p (two-sided) |
|---|---|---|---|---|---|---|---|---|---|---|
| +1m | 19 | +1.3% | -0.4% to +2.9% | +73.7% | 57 | +1.1% | +0.1% to +2.0% | +70.2% | +0.2% | 0.84 |
| +3m | 19 | +7.1% | +4.7% to +9.3% | +89.5% | 57 | +2.6% | +1.0% to +4.1% | +66.7% | +4.5% | 0.02 |
| +6m | 19 | +13.4% | +10.9% to +15.7% | +100.0% | 57 | +4.0% | +2.0% to +6.0% | +66.7% | +9.4% | 0.00 |
| +12m | 19 | +14.6% | +11.6% to +17.7% | +100.0% | 57 | +7.3% | +3.6% to +10.9% | +68.4% | +7.3% | 0.07 |

## By year of the presidential cycle (12 months after the November election date)

| cycle | n | mean | median | %pos |
|---|---|---|---|---|
| Post-election | 19 | +3.4% | +8.6% | +57.9% |
| Midterm | 19 | +14.6% | +13.6% | +100.0% |
| Pre-election | 19 | +9.9% | +10.3% | +84.2% |
| Election | 19 | +8.4% | +8.6% | +63.2% |

Leave-one-election-out: the midterm 12-month mean ranges from +13.7% to +15.3%; the share positive never falls below 100%.

## Regression of the 12-month return on a midterm dummy and state controls (n = 73, HC1 standard errors)

| index | coef | se (HC1) | t |
|---|---|---|---|
| const | 0.0341 | 0.0591 | 0.577 |
| midterm | 0.0712 | 0.0354 | 2.014 |
| above200 | 0.0075 | 0.0557 | 0.1343 |
| trail12 | 0.0177 | 0.1753 | 0.101 |
| term_spread | 0.0068 | 0.0199 | 0.3428 |
| credit_spread | 0.0245 | 0.0413 | 0.5922 |

## Seasonal window (30 Sep to 30 Jun) for every year, by cycle year

| cycle | n | mean | median | %pos |
|---|---|---|---|---|
| Post-election | 19 | +1.9% | -1.0% | +47.4% |
| Midterm | 19 | +20.1% | +18.4% | +100.0% |
| Pre-election | 19 | +7.4% | +7.6% | +84.2% |
| Election | 19 | +5.9% | +6.9% | +63.2% |

# S&P 500 after one-day drops of 3.5% or more (1950 onward)

History to 2026-11-04: 38 events (first day of each cluster, 20-session gap) in 20 independent episodes; 27 pairs of events have overlapping 12-month windows. Groups are fixed on the drop day's close. The current case (2026-11-05: -4.4%, above its 200-day average, -1.7% from the 52-week high before the drop) is not in the history.

| group | n | episodes | 6m %pos | 6m negatives | 12m %pos | 12m negatives | 12m median | worst further fall 3m |
|---|---|---|---|---|---|---|---|---|
| all events | 38 | 20 | +84.2% | 6 | +78.9% | 8 | +16.2% | -36.9% |
| above 200-day after the drop | 13 | 11 | +100.0% | 0 | +84.6% | 2 | +19.7% | -10.7% |
| below 200-day after the drop | 25 | 12 | +76.0% | 6 | +76.0% | 6 | +15.9% | -36.9% |

**Post-hoc filter (not pre-specified).** The filter measures the distance from the 52-week high at the close before the drop. It was added on 5 Nov after seeing the current case (1.7% below its high before the drop, 5.9% after it); the 6% threshold was not specified in advance. Neighbouring thresholds:

| threshold | n | 6m %pos | 12m negatives | worst further fall 3m |
|---|---|---|---|---|
| +4.0% | 10 | +100.0% | 2 | -6.3% |
| +5.0% | 11 | +100.0% | 2 | -6.3% |
| +6.0% | 12 | +100.0% | 2 | -6.3% |
| +7.0% | 13 | +100.0% | 2 | -10.7% |
| +8.0% | 13 | +100.0% | 2 | -10.7% |
| +10.0% | 13 | +100.0% | 2 | -10.7% |

**Sensitivity to the event definition**

| threshold | gap | n all | episodes | n above200 | above200 6m %pos | above200 12m %pos | above200 12m negatives | all worst further fall 3m | above200 worst further fall 3m | 12m overlapping pairs |
|---|---|---|---|---|---|---|---|---|---|---|
| +3.0% | 20 | 55 | 22 | 22 | +95.5% | +86.4% | 3 | -38.6% | -30.6% | 52 |
| +3.0% | 63 | 38 | 23 | 18 | +94.4% | +83.3% | 3 | -38.6% | -30.6% | 16 |
| +3.5% | 20 | 38 | 20 | 13 | +100.0% | +84.6% | 2 | -36.9% | -10.7% | 27 |
| +3.5% | 63 | 28 | 20 | 11 | +100.0% | +81.8% | 2 | -36.9% | -10.7% | 8 |
| +4.0% | 20 | 25 | 14 | 5 | +100.0% | +80.0% | 1 | -36.9% | -4.2% | 15 |
| +4.0% | 63 | 20 | 14 | 5 | +100.0% | +80.0% | 1 | -36.9% | -4.2% | 6 |

# Does election information add predictive value? (nested walk-forward)

Target: next-month S&P 500 excess price return. Out-of-sample 1998-01 to 2026-08; 25 model configurations counted.

| step | months | R2_OS vs hist mean | Clark-West t vs hist mean | CW p | lambda (most used) | timing CAGR | timing Sharpe | timing MaxDD | timing Time invested | timing Switches/yr |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 trend | 344 | -1.3% | -1.58 | 0.94 | 1000.0 | +6.6% | 0.36 | -46.9% | +97.4% | 0.10 |
| 2 + season | 344 | -1.4% | -1.62 | 0.95 | 1000.0 | +6.6% | 0.36 | -46.9% | +97.4% | 0.10 |
| 3 + policy | 344 | -1.8% | -0.98 | 0.84 | 1000.0 | +6.4% | 0.35 | -46.9% | +94.8% | 0.38 |
| 4 + macro | 344 | -5.0% | -0.82 | 0.79 | 1000.0 | +6.8% | 0.37 | -46.3% | +95.9% | 0.10 |
| 5 + costs | 344 |  |  |  | nan | +6.8% | 0.37 | -46.3% | +95.9% | 0.10 |

| added | vs | delta R2_OS | Clark-West t | p |
|---|---|---|---|---|
| 2 + season | 1 trend | -0.1% | -0.01 | 0.50 |
| 3 + policy | 2 + season | -0.5% | -0.05 | 0.52 |
| 4 + macro | 3 + policy | -3.2% | -0.42 | 0.66 |

Buy-and-hold over the same months: Sharpe 0.41, CAGR +7.4%.

The policy block contains the only election feature available historically (a post-midterm dummy). Deviations from pre-election expectations need archived prediction-market or poll data, which this project does not have.

# Global transmission

Election window: last close on or before 2026-11-03 to last close on or before 2026-11-05.

| market | group | energy | local | fx vs USD | USD (local x FX) | US-listed ETF | hedged ETF |
|---|---|---|---|---|---|---|---|
| Euro area | Europe | importer | +1.4% | +0.4% | +1.8% | +0.9% | +1.8% |
| Germany | Europe | importer | +1.8% | +0.4% | +2.2% | +1.6% |  |
| Japan | Japan | importer | -3.2% | -0.3% | -3.4% | -4.7% | -4.8% |
| China (Shanghai Composite) | China and Asian supply chain | importer | +2.3% | -0.4% | +1.9% | +5.3% |  |
| Hong Kong | China and Asian supply chain | importer | +5.4% | +0.0% | +5.4% | +3.4% |  |
| Korea | China and Asian supply chain | importer | -4.7% | +0.4% | -4.4% | -15.1% |  |
| Taiwan | China and Asian supply chain | importer | -4.0% | -0.7% | -4.7% | -12.6% |  |
| India | Emerging markets | importer | +3.1% | +0.2% | +3.3% | +2.7% |  |
| Brazil | Emerging markets | exporter | +0.4% | -0.4% | -0.0% | +0.1% |  |
| Mexico | Emerging markets | exporter | +1.3% | -0.2% | +1.1% | +1.8% |  |
| Canada | Energy exporters | exporter | +0.2% | +0.1% | +0.3% | -0.1% |  |
| Norway | Energy exporters | exporter |  | +0.1% |  | -1.7% |  |
| Saudi Arabia | Energy exporters | exporter |  |  |  | +1.9% |  |
| EM broad (MSCI EM) | Emerging markets | mixed |  |  |  | -5.0% | -4.4% |
| Developed ex-US (MSCI EAFE) | Europe | importer |  |  |  | -0.4% | -0.9% |
| United States (SPY) | United States | producer | -2.8% | +0.0% | -2.8% | -2.8% |  |

U.S.-listed ETFs trade 09:30-16:00 ET, after Asian and most European closes, so on 5 Nov an Asian-market ETF had already absorbed the U.S. selloff while that market's local index had not. Local and ETF windows are therefore not comparable day by day.

Five-year monthly sensitivities (betas; t-statistics HC1):

| market | basis | beta dUS10y (pp) | beta USD broad | beta Brent | beta S&P 500 | t USD broad | t Brent | R2 |
|---|---|---|---|---|---|---|---|---|
| Euro area | local | 0.00 | -0.39 | -0.05 | 0.68 | -1.33 | -1.23 | 0.63 |
| Euro area | USD | 0.01 | -1.72 | -0.05 | 0.60 | -6.04 | -1.45 | 0.77 |
| Euro area | hedged ETF | -0.00 | -0.29 | -0.02 | 0.68 | -1.04 | -0.70 | 0.61 |
| Germany | local | 0.00 | -0.64 | -0.03 | 0.65 | -2.72 | -0.59 | 0.66 |
| Germany | USD | 0.01 | -1.97 | -0.03 | 0.57 | -8.87 | -0.83 | 0.79 |
| Japan | local | 0.04 | 0.21 | -0.13 | 0.99 | 0.48 | -2.18 | 0.50 |
| Japan | USD | 0.01 | -0.92 | -0.13 | 0.85 | -2.66 | -2.83 | 0.67 |
| Japan | hedged ETF | 0.02 | 0.20 | -0.05 | 0.66 | 0.63 | -1.27 | 0.48 |
| China (Shanghai Composite) | local | -0.00 | -0.87 | -0.10 | 0.06 | -1.92 | -1.96 | 0.19 |
| China (Shanghai Composite) | USD | -0.01 | -1.39 | -0.08 | 0.04 | -2.78 | -1.45 | 0.30 |
| Hong Kong | local | 0.00 | -2.64 | 0.04 | -0.18 | -3.44 | 0.49 | 0.30 |
| Hong Kong | USD | 0.00 | -2.68 | 0.04 | -0.20 | -3.47 | 0.45 | 0.30 |
| Korea | local | 0.05 | -0.83 | -0.20 | 1.24 | -0.98 | -1.51 | 0.38 |
| Korea | USD | 0.05 | -2.28 | -0.16 | 1.27 | -2.88 | -1.37 | 0.52 |
| Taiwan | local | 0.03 | -0.24 | -0.09 | 0.97 | -0.43 | -1.56 | 0.45 |
| Taiwan | USD | 0.03 | -0.94 | -0.12 | 1.01 | -1.52 | -1.98 | 0.50 |
| India | local | 0.01 | -0.49 | -0.08 | 0.36 | -1.25 | -1.41 | 0.33 |
| India | USD | -0.00 | -0.64 | -0.10 | 0.34 | -1.41 | -1.57 | 0.36 |
| Brazil | local | 0.05 | -1.66 | 0.04 | 0.20 | -3.66 | 0.72 | 0.29 |
| Brazil | USD | 0.08 | -3.13 | 0.09 | 0.33 | -4.67 | 1.09 | 0.44 |
| Mexico | local | -0.03 | -0.96 | 0.05 | 0.29 | -2.37 | 1.14 | 0.43 |
| Mexico | USD | 0.01 | -2.27 | 0.03 | 0.40 | -4.08 | 0.54 | 0.51 |
| Canada | local | -0.02 | -0.32 | 0.01 | 0.51 | -1.43 | 0.49 | 0.67 |
| Canada | USD | -0.02 | -1.10 | 0.04 | 0.54 | -4.79 | 1.81 | 0.80 |
| Norway | USD | -0.02 | -1.66 | 0.30 | 0.38 | -3.77 | 7.39 | 0.60 |
| Saudi Arabia | USD | -0.00 | -0.25 | 0.16 | 0.30 | -0.56 | 2.48 | 0.17 |
| EM broad (MSCI EM) | USD | 0.00 | -1.52 | -0.07 | 0.47 | -3.41 | -1.38 | 0.61 |
| EM broad (MSCI EM) | hedged ETF | 0.00 | -0.98 | -0.07 | 0.44 | -2.18 | -1.23 | 0.49 |
| Developed ex-US (MSCI EAFE) | USD | -0.02 | -1.37 | -0.02 | 0.46 | -7.26 | -0.84 | 0.86 |
| Developed ex-US (MSCI EAFE) | hedged ETF | -0.00 | -0.25 | -0.02 | 0.52 | -1.21 | -0.68 | 0.68 |

| market | years | unhedged ETF | hedged ETF | unhedged ann. | hedged ann. | currency effect ann. | note |
|---|---|---|---|---|---|---|---|
| Euro area | 1 | EZU | HEDJ | +9.8% | +11.7% | -2.0% | HEDJ tracks a different (exporter-tilted) index from EZU, so the hedged-unhedged gap mixes currency and composition |
| Euro area | 3 | EZU | HEDJ | +18.8% | +15.7% | +3.2% | HEDJ tracks a different (exporter-tilted) index from EZU, so the hedged-unhedged gap mixes currency and composition |
| Japan | 1 | EWJ | DBJP | +11.2% | +18.0% | -6.8% | same underlying index |
| Japan | 3 | EWJ | DBJP | +15.8% | +22.8% | -7.0% | same underlying index |
| EM broad (MSCI EM) | 1 | EEM | HEEM | +7.4% | +10.1% | -2.7% | same underlying index |
| EM broad (MSCI EM) | 3 | EEM | HEEM | +17.5% | +19.6% | -2.1% | same underlying index |
| Developed ex-US (MSCI EAFE) | 1 | EFA | HEFA | +12.8% | +17.2% | -4.4% | same underlying index |
| Developed ex-US (MSCI EAFE) | 3 | EFA | HEFA | +17.4% | +19.1% | -1.6% | same underlying index |

Not measured: Trade/tariff exposure by country (UN Comtrade and USITC DataWeb need registration keys); Hedged returns computed from local index plus interest carry (needs local short rates for every market); Local-currency index for Norway and Saudi Arabia (no free daily series found; ETF in USD only)

# Engine reconciliation (Backtrader vs independent pandas re-implementation)

| strategy | decisions compared | target mismatches | fills backtrader | fills reference | max fill price diff | commission backtrader | commission reference | max daily NAV rel diff |
|---|---|---|---|---|---|---|---|---|
| E1 | 1714 | 0 | 171 | 171 | 5.684341886080802e-14 | 49702.022073286666 | 49702.02207328668 | 6.661338147750939e-16 |
| C1 | 597 | 0 | 571 | 571 | 1.4551915228366852e-11 | 9076769.087760182 | 9076769.087760145 | 4.884981308350689e-15 |

# Scenario signposts (weekly, point-in-time)

| scenario | week_end | holding | of | which | gaps | state |
|---|---|---|---|---|---|---|
| B | 2026-11-05 | 2 | 6 | ['M4', 'E-b'] | [] | WATCHING |
| A | 2026-11-05 | 1 | 7 | ['E-c'] | [] | WATCHING |
| C | 2026-11-05 | 3 | 6 | ['M10', 'E-e', 'E-d'] | ['C-b STALE'] | WATCHING |
