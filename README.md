# midterm_quant: post-midterm cross-asset research and strategy library

Analysis of how the **3 Nov 2026 U.S. midterm results** affect U.S. equities, crypto, energy and precious metals. It includes a two-year observation framework with 33 quantified indicators and **20 quantitative strategies (5 per asset class)**, all implemented and backtested in **Backtrader**.

**Live page:** [midterm-quant.vercel.app](https://midterm-quant.vercel.app), the post-midterm market playbook built from `reports/midterm_playbook.html`.

> Research and education only, not investment advice. Backtests are hypothetical, use ETF proxies and are subject to the limitations listed in `docs/03_strategy_book.md`.

## Deliverables

| Document | Contents |
|---|---|
| [docs/01_midterm_market_impact.md](docs/01_midterm_market_impact.md) | Election outcome, policy-control map, market reaction, event study (1950–2022), asset-class deep dives, 24-month scenario matrix |
| [docs/02_observation_framework.md](docs/02_observation_framework.md) | Event calendar to Nov 2028, 33 indicators with formulas, thresholds and current readings, scenario signposts |
| [docs/03_strategy_book.md](docs/03_strategy_book.md) | 20 strategy specs, backtest results, current signals, research log of rejected specs |
| [docs/04_framework_selection.md](docs/04_framework_selection.md) | Comparison of 7 open-source frameworks, weighted scoring, architecture, migration path to LEAN/NautilusTrader |
| `reports/` | Generated: backtest summary, yearly returns, class blends, current signals, event study, monitor, equity-curve charts |

## Headline view (5 Nov 2026)

- **Outcome.** Democrats won both chambers. That means gridlock on fiscal policy, but tariffs, the Iran war and the agencies stay with the White House. Policy volatility does not fall.
- **Equities.** The S&P 500 rose over the following 12 months after all 19 midterms since 1950 (mean +14.6%). The base case is constructive with broadening leadership. Risks: a hawkish Fed (2Y − FF = +71bp), credit stress (HYG/IEF z −2.0) and AI-infrastructure regulation.
- **Crypto.** The legislative tailwind is gone (CLARITY failed 49–50). Liquidity indicators read "not yet": stablecoins −4% over 30 days, net liquidity draining. The 2027 debt-limit TGA cycle and the ~Apr 2028 halving are the catalysts.
- **Energy.** The Iran-war premium is the swing factor (Brent $95, gasoline $4.15). Expect two-way jump risk. The OBBBA clean-energy cliff falls at end-2027.
- **Metals.** Gold −23% from its ATH and below trend. Real yields of 2.6% and Senate vetting of Fed nominees are headwinds; central-bank buying and fiscal/war stress are the floor.

## Quickstart

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

```bash
.venv/bin/python -m pytest -q
```

```bash
.venv/bin/python scripts/run_backtests.py
```

```bash
.venv/bin/python scripts/run_monitor.py
```

```bash
.venv/bin/python scripts/run_event_study.py
```

- **Tests** (57, offline): indicators, alignment and lags, engine mechanics, smoke and no-look-ahead checks for every strategy.
- **Backtests:** all 20 strategies plus the rejected specs, written to `reports/` (about 70s on a warm cache).
- **Monitor:** the observation dashboard, written to `reports/monitor.md`. Run it weekly.
- **Event study:** midterm forward returns, written to `reports/event_study.md`.

Data comes from the Yahoo Finance chart API, FRED and DefiLlama (no API keys) and is cached in `data_cache/` for 20 hours. Run a subset with `scripts/run_backtests.py --codes E1 C2 P4`.

## Writing a new strategy

```python
from midterm_quant import indicators as ind
from midterm_quant.engine.base import TargetWeightStrategy

class MyStrategy(TargetWeightStrategy):
    CODE, NAME, ASSET_CLASS = "X1", "Example", "US Equities"
    ASSETS = ("SPY", "IEF")          # traded
    SIGNALS = ("fred:DFII10",)       # signal-only feeds (Yahoo symbol, fred:<id>, llama:stablecoins)
    START, REBALANCE, WARMUP = "2010-01-01", "W", 210
    THESIS = "why this should work"

    def target_weights(self):
        spy = self.series("SPY", 210)                    # history up to *this* bar only
        risk_on = spy[-1] > ind.sma(spy, 200)
        return {"SPY": 0.98} if risk_on else {"IEF": 0.98}
```

Register it in `midterm_quant/strategies/__init__.py`. The no-look-ahead test then covers it automatically.

## Layout

```
midterm_quant/   data/ (sources, point-in-time alignment) · indicators.py · engine/ (Backtrader base, runner, metrics)
                 strategies/ (equities, crypto, energy, metals) · research/ (event study, monitor)
scripts/         run_backtests.py · run_monitor.py · run_event_study.py
tests/           57 offline tests on synthetic data
docs/            the four analysis documents
reports/         generated outputs
```
