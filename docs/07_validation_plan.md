# Prospective validation plan (pre-registered 6 Nov 2026)

There is no untouched historical sample: every price and macro series up to the 5 Nov 2026
close was seen while the 20 strategies were written, and the variants in the trial registry
were chosen on that same data. The only clean test is forward in time, on a version of the
code that can no longer change. This document fixes that test before any of it is observed.

## 1. What is frozen

| Item | Frozen as |
|---|---|
| Code, rules, parameters | the commit recorded in `reports/results/results.json` (`code.commit`) on branch `review-iteration-2`, tagged `frozen-2026-11-06` when merged |
| Data definitions and timing | `midterm_quant/data/catalog.py` at that commit |
| Evaluation | `midterm_quant/engine/evaluation.py` at that commit (monthly, DTB3, four benchmarks) |
| Signpost rule | `midterm_quant/research/scenarios.py` at that commit |
| Exposure baskets for 2028 | section 5 below |

A change to any frozen item starts a new version with its own prospective clock; it never
rewrites the record of the frozen one.

## 2. Window

* Start: the first scheduled decision after the freeze, **9 Nov 2026** (weekly and daily rules;
  monthly rules start 1 Dec 2026).
* Interim reads: 6 and 12 months (descriptive only, no changes allowed).
* Decision point: **24 months** (Nov 2028), which spans the 2027 debt-limit episode, the
  estimated April 2028 halving and the 2028 election.

## 3. Procedure (paper trading, no capital)

1. Each trading day after the close, run the frozen commit against freshly downloaded data
   (`scripts/run_backtests.py`, `scripts/run_monitor.py`).
2. Append, never overwrite: the data manifest (hashes and retrieval times), every strategy's
   model signal, the hypothetical orders at the next open, the fills at the published open price,
   commissions and the cash ledger. Each day's raw files go to `data_cache/vintages/` (already
   immutable) so any day can be replayed.
3. Record the stablecoin supply snapshot daily: from now on it is point-in-time, which the
   historical series is not.
4. Reconcile monthly: the paper ledger against a replay of the frozen engine on the archived
   data. Any difference is logged and explained before the next month starts.

Requirements not yet in place: a scheduled runner (cron or a hosted job) and storage for the
append-only ledger. Until they exist, no prospective record is being made.

## 4. Pre-registered metrics and decisions

Per strategy, on the prospective window only, with the same conventions as the development
tables (monthly, sqrt(12), excess over DTB3, net of the same costs):

| Metric | Pass | Retire or demote |
|---|---|---|
| Information ratio vs the primary benchmark (risk-matched; cash for N3, N5) | > 0 | < -0.25 |
| Maximum drawdown | within 1.5x the development maximum | beyond 1.5x at any time |
| Realised cost vs modelled cost (where fills can be checked) | within 10bp per trade | worse by > 10bp on average |
| Incremental contribution to its class blend (leave-one-out) | removing it lowers the blend Sharpe | removing it raises it |

Two years of monthly data cannot establish skill at conventional significance; the purpose is
to catch rules that fail clearly, not to certify winners. C3 is excluded from capital in any
case: only the 2028 halving can test its phase boundaries. N1 and N2 already fail the
incremental test in the development sample and stay in the book only so the prospective
record is complete.

## 5. Election-information test for 2028 (baskets frozen now)

The historical ablation could not use deviations from pre-election expectations because no
archived expectation data were available. For the 2028 election the inputs are fixed today:

| Basket | Constituents (equal weight, U.S.-listed ETFs) | Exposure hypothesis |
|---|---|---|
| Defence | ITA, XAR | higher under unified Republican control |
| Clean energy | ICLN, TAN | higher under unified Democratic control |
| Managed care and health | XLV, IHF | policy-sensitive either way |
| Regional banks | KRE | deregulation-sensitive |
| Crypto equities | COIN, (BITO as BTC proxy) | market-structure-law sensitive |
| Tariff-exposed importers | XRT | tariff-policy sensitive |

Expectation data to collect weekly from 1 Jan 2028 (requires access to be confirmed): prediction
market prices for chamber control and the presidency (Polymarket/Kalshi public endpoints), and a
polling average. The test regresses each basket's return over the election window on the
*surprise* (outcome minus the last pre-election price), against the same regression for a
placebo date. Event timestamps come from the official sources (AP calls, state certifications,
Congress.gov), recorded when they occur.

## 6. What would change this plan

Only a data-source failure (a series discontinued or its licence changed). Any such change is
dated and logged here; results from before the change are reported separately.
