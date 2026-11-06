# LEAN migration: status and requirements

**Status: not run.** The two ports below were written on 6 Nov 2026 and have never executed.
The research machine has no Docker and no .NET SDK (checked: `which docker dotnet` → not
found; system Python 3.9.6, macOS 26.5, arm64). The Backtrader constraint stated in
docs/04 is therefore real, and Backtrader remains the system of record.

| Port | Strategy | Why this one | Reconciliation target |
|---|---|---|---|
| `E1_midterm_trend/main.py` | E1 seasonal + trend (SPY) | one ETF, weekly, long-only | `reports/evidence/ledgers/E1/` |
| `C1_crypto_trend/main.py` | C1 BTC/ETH trend + vol target | 7-day calendar, fractional sizes, 15 bp costs | `reports/evidence/ledgers/C1/` |

## What is needed to run them

| Need | Detail | Free? |
|---|---|---|
| Docker Desktop (or the .NET SDK to build LEAN from source) | the LEAN CLI runs the engine in Docker; "commands which run the LEAN engine locally also depend on Docker" (QuantConnect LEAN CLI docs) | Docker Desktop licence terms apply to larger organisations |
| `pip install lean` (LEAN CLI) on Python ≥ 3.9 | the CLI itself | free |
| QuantConnect account and `lean login` | needed for cloud commands and local live deployment; the CLI docs state CLI use requires membership of an organisation on a paid tier | paid tier |
| Market data in LEAN format | QuantConnect Data Library (paid), a third-party vendor, or a custom import of the same Yahoo/FRED files (Yahoo's terms prohibit redistribution) | varies |
| Brokerage permissions | only for live or paper trading through a broker | broker-specific |

The open-source LEAN engine (github.com/QuantConnect/Lean) is distinct from the CLI's paid
features, from data licences and from brokerage permissions; none of the four is implied by
another.

## Reconciliation procedure (to run once an environment exists)

1. Run each port with `lean backtest` on data identical to the Backtrader snapshot
   (`reports/evidence/data_manifest.json`, snapshot id).
2. Export LEAN's order events and daily equity.
3. Run `scripts/reconcile_lean.py <lean-output-dir> E1` (and `C1`): it compares decision
   dates, target weights, order sides and sizes, fill prices, fees and cash, and reports the
   first divergence. Tolerances: identical decisions; fill prices within one tick; NAV within
   10 bp after accounting for LEAN not paying interest on idle cash.

Until then, the engine check that *has* been run is `midterm_quant/research/reconcile.py`: an
independent pandas re-implementation of E1 and C1 that matches Backtrader's decisions, fills,
commissions and NAV to machine precision (`reports/evidence/reconciliation.json`).

## Futures: what a real migration needs (not done)

Replacing USO/GLD with futures is **not** a matter of switching to continuous-contract symbols
and calling `set_holdings`. LEAN's own documentation: "The continuous Futures contract isn't a
tradable security" - orders go to a specific contract (`future.mapped`). A futures version
needs, separately for each market (CL, BZ, GC, SI, PL, HG):

- contract selection and an explicit roll rule (`data_mapping_mode`, roll dates, handling of
  `SymbolChangedEvent`), with roll costs;
- contract multipliers and minimum price increments (CL 1,000 bbl; GC 100 oz; ...);
- initial and maintenance margin, and the cash left after margin (interest on it);
- exchange trading sessions and settlement times (which change the decision/fill timing);
- first-notice and last-trade dates, so no position is held into delivery;
- a back-adjustment choice for signals (`data_normalization_mode`) kept separate from the raw
  prices used for P&L.

None of this exists in the repository yet.
