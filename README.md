# midterm_quant: post-midterm cross-asset research and strategy library

Analysis of how the **3 Nov 2026 U.S. midterm results** may affect U.S. equities, crypto, energy, precious metals and markets abroad. It includes a two-year observation framework (36 indicators) and **20 rule-based strategies (5 per asset class)** implemented in **Backtrader**, with every result labelled by the evidence behind it.

**Live page:** [midterm-quant.vercel.app](https://midterm-quant.vercel.app), generated from `reports/results/results.json` by `scripts/build_site.py`.

> Research and education only, not investment advice. **Every backtest uses data that was seen while the rules were written (development sample); there is no out-of-sample or live result.** Nothing has been traded. The prospective test starts on 9 Nov 2026 ([docs/07](docs/07_validation_plan.md)).

## Evidence levels

| Level | Meaning | Strategies |
|---|---|---|
| D1 | Rule and parameters written before the first backtest run | 16 |
| D2 | Revised after seeing results (C5, P3) or for a data-definition fix (C2 v2) | 3 |
| D3 | In-sample research: parameters fitted to known outcomes; not counted as a result | C3 |

46 configurations were tried in total and are all re-run (`reports/evidence/trial_registry.csv`); deflated Sharpe ratios use that count. None of the 19 non-research strategies clears a deflated Sharpe of 0.95.

## Documents

| Document | Contents |
|---|---|
| [docs/01_midterm_market_impact.md](docs/01_midterm_market_impact.md) | Election outcome (projected, not yet certified), policy-control map, market reaction, event study, asset-class analysis, scenarios (subjective priors) |
| [docs/02_observation_framework.md](docs/02_observation_framework.md) | Event calendar to Nov 2028, the 36 indicators, scenario signposts and the confirmation/revocation rule |
| [docs/03_strategy_book.md](docs/03_strategy_book.md) | 20 strategies, standardised development-sample results, research log |
| [docs/04_framework_selection.md](docs/04_framework_selection.md) | Framework comparison; why Backtrader; what a LEAN migration really requires |
| [docs/05_specifications.md](docs/05_specifications.md) | Generated: complete specification of every indicator and strategy |
| [docs/06_review_response.md](docs/06_review_response.md) | Generated: finding -> change -> evidence matrix for the 6 Nov 2026 review, with what is still missing |
| [docs/07_validation_plan.md](docs/07_validation_plan.md) | Pre-registered prospective validation (frozen code, paper ledger, decision rules) |
| [lean/README.md](lean/README.md) | LEAN ports of E1 and C1 (not run) and their requirements |

## Reproduce everything

```bash
scripts/reproduce.sh
```

It creates `.venv` from `requirements.lock`, downloads or reuses data (Yahoo chart API, FRED and ALFRED, DefiLlama; no keys), runs the offline tests with a log, every backtest and study, writes the data manifest and verifies it, then rebuilds `results.json`, the generated docs and the page. To reproduce the committed numbers exactly you need the same data snapshot: run with `OFFLINE=1` against a `data_cache/` whose hashes match `reports/evidence/data_manifest.json` (`scripts/verify_data.py`). Yahoo data may not be redistributed, so it is not in the repository.

Individual steps:

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
.venv/bin/python scripts/run_research.py
```

## Evidence produced by a run (`reports/evidence/`)

- `pytest.log`, `pytest-junit.xml`: the offline test suite (synthetic data; no network).
- `data_manifest.csv/.json`: every input file with units, release timing, availability rule, licence, retrieval time, SHA-256, last observation used and status; `revision_audit.csv` and `first_print_coverage.csv` for ALFRED vintages.
- `trial_registry.csv`, `performance_risk.csv`, `class_blends.csv`, `blend_attribution.csv`, `vintage_sensitivity.csv`.
- `ledgers/<CODE>/`: daily NAV and cash (interest, commissions, borrow), target and actual weights, every order and fill.
- `reconciliation.json`: an independent pandas engine reproduces E1 and C1 exactly.

## Writing a new strategy

```python
from midterm_quant import indicators as ind
from midterm_quant.engine.base import TargetWeightStrategy

class MyStrategy(TargetWeightStrategy):
    CODE, NAME, ASSET_CLASS = "X1", "Example", "US Equities"
    ASSETS = ("SPY", "IEF")          # traded
    SIGNALS = ("fred:DFII10",)       # signal-only feeds (Yahoo symbol, fred:<id>, llama:stablecoins, derived:netliq_bn)
    START, REBALANCE, WARMUP = "2010-01-01", "W", 210
    EVIDENCE = "D1"
    THESIS = "why this should work"

    def target_weights(self):
        spy = self.series("SPY", 210)                    # history up to *this* bar only
        risk_on = spy[-1] > ind.sma(spy, 200)
        return {"SPY": 0.98} if risk_on else {"IEF": 0.98}
```

Register it in `midterm_quant/strategies/__init__.py`, add its specification to `midterm_quant/specs.py` and a `Trial` to `strategies/trials.py`. The no-look-ahead and specification tests then cover it; every new series needs a catalogue entry (`data/catalog.py`).

## Layout

```
midterm_quant/   data/ (sources + provenance, catalog, vintages, point-in-time alignment) · indicators.py
                 engine/ (Backtrader base and ledgers, runner, metrics, standardised evaluation)
                 strategies/ (four classes, trials.py) · research/ (monitor, scenarios, event and shock
                 studies, ablation, global transmission, reconciliation) · specs.py
scripts/         reproduce.sh · run_backtests · run_monitor · run_research · build_vintages ·
                 build_manifest · verify_data · build_results · build_docs · build_site · reconcile_lean
site_src/        page stylesheet, chart script, authored content (policy status, narrative, review matrix)
lean/            LEAN ports of E1 and C1 (not run)
tests/           offline tests on synthetic data
reports/         generated outputs; results/ (JSON for the page); evidence/ (logs, manifests, ledgers)
```
