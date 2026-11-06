# Framework selection: why Backtrader for this mandate

## The mandate's requirements

| # | Requirement | Why it matters here |
|---|---|---|
| R1 | **Multi-asset in one engine**: ETFs, crypto on a 7-day calendar, commodity ETFs, plus signal-only macro series | 20 strategies across 4 asset classes, ~45 instruments |
| R2 | **Event-driven, path-dependent logic** | Stateful entries/exits (E5, N2, N3, N5), time stops, pair legs, cycle clocks; these are awkward to express without look-ahead in vectorised code |
| R3 | **Arbitrary alternative data as first-class inputs** | FRED weekly/daily series with publication lags, DefiLlama stablecoins, election and halving calendars |
| R4 | **Realistic fills and costs** | Next-bar execution, per-asset commissions, short borrow, cash interest, fractional crypto sizing |
| R5 | **Runs on the user's machine today** | macOS, **system Python 3.9.6, no Docker, no .NET** (re-verified 6 Nov 2026) |
| R6 | **Stable over a 2-year research program** | Strategies must keep running unchanged through 2028 |
| R7 | **Path to paper/live trading** | Eventually route the target weights to a broker |
| R8 | **Licence and maintenance** | Open source; ideally actively maintained |

The frequency is **daily**, the instrument count is small, and there is no order-book microstructure. Raw speed and tick-level realism are therefore *not* deciding factors.

## Candidates

| Framework | Licence | Engine model | Multi-asset | Custom data | Local setup on this machine | Live trading | Maintenance |
|---|---|---|---|---|---|---|---|
| **Backtrader** | GPL-3.0 | Event-driven, pure Python | Any OHLCV feed; no native futures roll | Excellent (any pandas frame) | `pip install` on Python 3.9 ✔ | IB/Oanda stores (dated) | **Unmaintained** (last release 1.9.78.123, 2023) |
| QuantConnect **LEAN** | Apache-2.0 | Event-driven, C# core, Python API | Best in class (equities, options, futures with continuous contracts, FX, crypto) | Good (custom data classes) | Needs **Docker** + `lean` CLI; local data must be bought or converted | Many brokerages | Very active |
| **NautilusTrader** | LGPL-3.0 | Event-driven, Rust core, ns resolution | Strong (crypto venues, IB, Databento) | Good, but verbose instrument/bar definitions | Needs **Python ≥ 3.11** | Excellent research-to-live parity | Very active, fast-moving API |
| **vectorbt** (OSS) | Apache-2.0 + Commons Clause | Vectorised (NumPy/Numba) | Any array | Good | `pip` ✔ | None | Light (PRO version is paid) |
| **Zipline-reloaded** | Apache-2.0 | Event-driven | Equity-centric; futures/crypto awkward | Bundles; heavy ingestion | Medium | None built in | Community-maintained |
| **bt** | MIT | Allocation tree on ffn | Any price frame | Moderate | `pip` ✔ | None | Light |
| **Qlib** (Microsoft) | MIT | ML research pipeline | Equity/China A-share focus | Strong for factors | Medium | None | Active |

## Weighted scoring for *this* mandate (1 = poor, 5 = excellent)

| Criterion (weight) | Backtrader | LEAN | Nautilus | vectorbt | Zipline-r | bt | Qlib |
|---|---|---|---|---|---|---|---|
| R1 Multi-asset (15%) | 4 | 5 | 5 | 4 | 2 | 3 | 2 |
| R2 Path-dependent, event-driven (20%) | 5 | 5 | 5 | 2 | 4 | 2 | 2 |
| R3 Custom/alt data (15%) | 5 | 4 | 4 | 4 | 2 | 3 | 4 |
| R4 Fill/cost realism (10%) | 4 | 5 | 5 | 3 | 4 | 3 | 2 |
| R5 Runs here today (15%) | **5** | 1 | 2 | 5 | 3 | 5 | 3 |
| R6 Stable API (10%) | 5 | 4 | 2 | 4 | 3 | 4 | 3 |
| R7 Live path (10%) | 2 | 5 | 5 | 1 | 1 | 1 | 1 |
| R8 Maintenance (5%) | 1 | 5 | 5 | 3 | 3 | 3 | 4 |
| **Weighted score** | **4.25** | 4.15 | 4.10 | 3.30 | 2.80 | 3.00 | 2.55 |

The ranking is sensitive to R5. Drop the "runs here today" criterion and LEAN leads with 4.71, ahead of Nautilus (4.47) and Backtrader (4.12). Give the user Docker (LEAN's R5 rises to 4) and LEAN scores 4.60. Either way, **LEAN and NautilusTrader overtake Backtrader**. That is the honest trade-off, and it is why the code is structured to make migration cheap (below).

## Decision

**Backtrader is the implementation framework for research and backtesting.** It is:
- the only event-driven candidate that runs on the research machine as it is. Re-checked on 6 Nov 2026: `which docker dotnet` finds neither, and the only Python is the system 3.9.6 (macOS 26.5, arm64). The constraint is real, not assumed;
- fully capable for daily multi-asset strategies with heterogeneous calendars and macro inputs;
- on a frozen API, so code written now will still run in 2028.

**No production deployment is proposed.** Production is a question only after forward paper trading on a frozen version ([07_validation_plan.md](07_validation_plan.md)) has run and its trade and cash ledgers reconcile. If that happens, LEAN is a candidate for futures and brokerage execution and NautilusTrader for crypto venues; neither has been run here. Status of the LEAN ports and what they need: [`lean/README.md`](../lean/README.md).

## How the implementation uses Backtrader

```
midterm_quant/
├── data/sources.py      Yahoo chart API (total-return OHLCV), FRED, DefiLlama → CSV cache
├── data/catalog.py      data dictionary: units, release timing, available_at rules, revisions, licences
├── data/vintages.py     ALFRED first-print reconstruction and revision audit
├── data/align.py        point-in-time panel: available_at dating, calendar alignment, inception guards
├── indicators.py        pure NumPy indicator functions (framework-agnostic, unit-tested)
├── engine/base.py       TargetWeightStrategy(bt.Strategy): target_weights() → orders
├── engine/runner.py     builds Cerebro: PandasData feeds, per-asset CommInfo, runs, packages results
├── engine/metrics.py    native-calendar statistics (daily)
├── engine/evaluation.py standardised monthly metrics, four benchmarks, PSR/DSR, risk contributions
├── strategies/*.py      20 strategies, 2 rejected and 1 superseded specs, trials.py (all 46 configurations)
└── research/            event studies with controls, 36-indicator monitor, scenarios, ablation, global, reconciliation
```

Key engine choices:
- **One method per strategy.** A strategy subclasses `TargetWeightStrategy` and implements `target_weights() -> {asset: weight}`. It reads history with `self.series(name, n)`, which returns Backtrader line history up to the current bar only, so look-ahead is impossible by construction.
- **Signal-only feeds.** Macro series (`fred:DFII10`, `^VIX`, `llama:stablecoins` …) are added as ordinary Backtrader data feeds that are never traded. They are aligned onto the strategy's calendar *after* being shifted by their publication lag.
- **Execution.** Orders are issued as target-weight deltas, **sells first**, filled at the next open. Bounced buys (overnight gaps) are retried on the next bar. A `min_trade` band suppresses churn.
- **Realism.** A custom `FractionalPercentCommission` gives percentage costs per asset class, fractional sizes (BTC at $80k), and a 1% borrow fee on shorts. Idle cash accrues the 3M T-bill rate via `broker.add_cash`.
- **Verification.** `tests/test_strategies.py::test_no_lookahead` runs every strategy on full and truncated synthetic histories and asserts identical decisions up to the cut. The full offline suite and its result are in `reports/evidence/pytest.log` (JUnit XML alongside); these were run by the author and have not been independently re-run. Separately, `midterm_quant/research/reconcile.py` re-implements E1 and C1 in plain pandas and matches Backtrader's decisions, fills, commissions and NAV to machine precision.
- **Ledgers.** Every run writes daily NAV, cash, cumulative interest, commissions and borrow fees, target and actual weights, and every order and fill (`reports/evidence/ledgers/<code>/`).

## Migration path (not executed)

Each strategy's output is a target-weight dictionary, which makes the *signal* layer portable. Execution is not: matching this engine means reproducing its fill timing (next open), sizing rule, 2pp trade band, proportional costs and interest on idle cash, which LEAN does not do by default. The LEAN ports of E1 and C1 in `lean/` implement these explicitly and must be reconciled against the Backtrader ledgers (`scripts/reconcile_lean.py`) before any result from them is trusted. They have not been run.

| This repo | LEAN (Python) | NautilusTrader |
|---|---|---|
| `target_weights()` | explicit orders sized from weight deltas (`market_on_open_order`), with a custom proportional fee model | `Strategy.on_bar` → `order_factory.market` sized from weight deltas |
| `self.series(name, n)` | `self.history(sym, n, Resolution.DAILY)` | `self.cache.bars(bar_type)[:n]` |
| `fred:*` feeds | `self.add_data(Fred, …)` / custom `PythonData` | Custom `Data` subclass |
| USO/GLD proxies | Not a symbol swap: orders must go to individual contracts (`future.mapped`), with an explicit roll rule, contract multipliers, margin, session times and first-notice/delivery handling (see `lean/README.md`) | Venue instruments, same requirements |
| `REBALANCE="W"` | `self.schedule.on(date_rules.week_start(), …)` | Timer / `clock.set_timer` |

The indicator layer (`indicators.py`) has no Backtrader dependency and ports unchanged. The LEAN engine is open source (Apache-2.0); the LEAN CLI's documentation states that using it requires a QuantConnect organisation on a paid tier; market data in LEAN format and brokerage permissions are separate requirements again.

## Risks of the choice and mitigations

| Risk | Mitigation |
|---|---|
| Backtrader is unmaintained; future Python/pandas versions could break it | Exact versions in `requirements.lock`; engine coupling confined to `engine/`; the full test suite flags breakage; an independent pandas engine reproduces two strategies exactly |
| GPL-3.0 licence | Fine for internal research; review before redistributing derived code |
| No native futures roll or options | Strategies use ETF proxies, whose returns include roll costs; a futures version needs the contract-level work listed in `lean/README.md` |
| Single-threaded speed | 20 strategies × ~20 years of daily data run in about 70 seconds; acceptable at daily frequency |
