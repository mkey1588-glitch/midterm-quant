"""Authored content for the page and docs: policy status, narrative, review matrix, sources.

Numbers that come from data are NOT written here: the page builder fills them in from
reports/results/results.json. Anything below that states a fact about the world carries a
date and a source; analysis is labelled as analysis.
"""

# ---------------------------------------------------------------------------------- policy --
# status: "projected" | "enacted, not yet effective" | "in force" | "scheduled" | "failed" | "estimate"
POLICY = [
    {"item": "Control of Congress", "status": "projected",
     "text": "Media decision desks projected Democratic majorities in both the House and the Senate on 4 Nov 2026. Projections are not official results: states certify their counts through November and December, and close races can still change seat totals.",
     "date": "projected 4 Nov 2026", "sources": ["cbs_senate", "nbc_live"]},
    {"item": "New Congress takes office", "status": "scheduled",
     "text": "The 120th Congress convenes at noon on 3 January 2027, the date set by the Twentieth Amendment unless Congress sets a different day by law. Newly elected members' terms begin then; until that day the current (lame-duck) Congress legislates.",
     "date": "3 Jan 2027", "sources": ["amend20"]},
    {"item": "GENIUS Act (payment stablecoins)", "status": "enacted, not yet effective",
     "text": "Enacted 18 July 2025. The Act and the OCC's implementing final rule (12 CFR 15) take effect on 18 January 2027 (OCC Bulletin 2026-50, 21 Oct 2026). Until then its issuer requirements do not apply.",
     "date": "effective 18 Jan 2027", "sources": ["occ_2026_50"]},
    {"item": "Wind and solar tax credits (sections 45Y and 48E)", "status": "in force (conditional deadline)",
     "text": "Under Public Law 119-21, wind and solar facilities whose construction begins after 4 July 2026 earn the credits only if placed in service by 31 December 2027. Facilities that began construction on or before 4 July 2026 are not subject to that deadline; under the continuity safe harbor (Notice 2025-42, section 4.04) they qualify if placed in service within four calendar years after the year construction began. For facilities whose construction had not begun before 2 September 2025, the notice limits 'beginning of construction' to the physical-work test; the 5% cost safe harbor remains only for solar facilities of 1.5 MW (AC) or less.",
     "date": "deadline 31 Dec 2027 for post-4 Jul 2026 starts", "sources": ["irs_2025_36"]},
    {"item": "CLARITY Act (crypto market structure)", "status": "failed",
     "text": "Failed a Senate cloture vote 49-50 in September 2026. A new bill would have to start again in the 120th Congress.",
     "date": "Sep 2026", "sources": ["ambanker_clarity"]},
    {"item": "Government funding", "status": "scheduled",
     "text": "Current funding runs to 11 December 2026; the next fiscal-year deadline is 30 September 2027. Each is a shutdown window.",
     "date": "11 Dec 2026; 30 Sep 2027", "sources": ["fortune_tariffs"]},
    {"item": "Debt limit", "status": "estimate",
     "text": "Market estimates put the binding date ('X-date') in late summer or autumn 2027 unless the lame-duck Congress raises the limit. No official X-date has been published.",
     "date": "estimate: H2 2027", "sources": ["fortune_tariffs"]},
]

CONTROL_MAP = {
    "congress": [
        ("Taxes and spending", "No new tax cuts or stimulus without both chambers; a lower fiscal impulse."),
        ("Appropriations and the debt limit", "Shutdown windows on 11 Dec 2026 and 30 Sep 2027; a debt-limit episode in 2027 (date estimated)."),
        ("Senate confirmations (from 3 Jan 2027)", "Fed Board nominees need the new Senate's consent."),
        ("Crypto market structure", "No market-structure law likely before 2029 after CLARITY failed."),
    ],
    "white_house": [
        ("Tariffs", "Set by the executive under Sections 301, 232 and 122."),
        ("The Iran war", "Congress has War Powers votes and funding requests only."),
        ("Agencies", "SEC, CFTC, EPA and FERC rule-making continues; oversight hearings add headline risk."),
        ("Energy permits and leasing", "Executive decisions; credits changed by P.L. 119-21 cannot be restored over a veto."),
    ],
}

# ------------------------------------------------------------------------------ outlook text --
# {placeholders} are filled from monitor readings by code: {M2.value}, {M2.date}, ...
OUTLOOK = {
    "US Equities": {
        "stance": "Constructive seasonally, fragile on credit and semis",
        "now": "S&P 500 {E-a.value} ({E-a.context}; {E-a.date}). VIX {E-b.value}, {E-b.context}. Equal-weight vs cap-weight {E-c.value}; semis vs SPY {E-e.value}.",
        "helps": "Election uncertainty resolved; the midterm-to-pre-election seasonal window (descriptive, see History); fiscal restraint under divided government.",
        "hurts": "Tariff actions; a rates market pricing a higher policy path (fed funds futures {M12.value}); the 11 Dec funding deadline and the 2027 debt limit.",
    },
    "Crypto": {
        "stance": "Range-bound until liquidity turns",
        "now": "Bitcoin Mayer multiple {C-a.value} ({C-a.date} UTC bar; {C-a.status}). Stablecoins {C-e.value}, {C-e.context}. Fed net liquidity {M9.value} ({M9.context}; Wednesday {M9.date}).",
        "helps": "The GENIUS Act takes effect on 18 Jan 2027, which gives regulated issuers a licensing path; a 2027 debt-limit episode would run down the Treasury's cash account (a liquidity injection) before rebuilding it.",
        "hurts": "No market-structure law before 2029; congressional oversight of crypto ventures from January; a firm dollar ({M7.context}).",
    },
    "Energy": {
        "stance": "War-driven; expect jumps both ways",
        "now": "Brent-WTI {N-a.value} ({N-a.context}). WTI curve {N-f.value} front vs 12th contract ({N-f.regime}). Gasoline {N-c.value} ({N-c.date}).",
        "helps": "Hormuz flows below pre-war levels keep a seaborne risk premium (part of the Brent-WTI spread, alongside quality, location and freight).",
        "hurts": "Pressure to end the war; demand loss at high pump prices. Clean energy: projects starting construction after 4 Jul 2026 face the 31 Dec 2027 placed-in-service deadline, earlier starts do not.",
    },
    "Precious Metals": {
        "stance": "Correction inside a long uptrend",
        "now": "Gold {P-a.value} ({P-a.context}). Real 10-year yield {M6.value} ({M6.date}). Gold/silver {P-b.value}.",
        "helps": "Central-bank buying; deficits near 6% of GDP; the 2027 debt-limit episode; the war.",
        "hurts": "Real yields above 2.5% and rising; a firm dollar; a Senate vetting Fed nominees from January, which lowers the 'politicised Fed' premium.",
    },
}

# ------------------------------------------------------------------------- review matrix --
# status: done | partial | not done.  evidence: repository paths (linked at the pinned commit)
MATRIX = [
    {"id": "P0-1", "finding": "Time labels: the 10-year yield 4.84% (CBOE ^TNX, 5 Nov) and 4.91% (FRED DGS10, 2 Nov) were both shown as 5 Nov closes; DFII10 2.62% (2 Nov) and T10YIE 2.30% (3 Nov) likewise; portfolio NAVs ended 4 Nov.",
     "change": "Every indicator reading now carries its observation date, publication rule (available_at), retrieval time and age. The page shows page time, market-data cutoff, indicator observation dates and backtest cutoff separately. ^TNX and DGS10 are separate, labelled rows. Backtests stop at a fixed BACKTEST_END = 2026-11-05.",
     "evidence": ["midterm_quant/research/monitor.py", "reports/monitor.md", "reports/results/results.json", "midterm_quant/config.py"],
     "status": "done", "missing": ""},
    {"id": "P0-2", "finding": "Data dictionary incomplete; BTC UTC bars mixed with 16:20 ET snapshots; seasonal-window start confused with post-election day 3; stablecoin level missing; later revisions could overwrite history.",
     "change": "A catalogue records units, frequency, timestamp convention, release time, available_at rule, revisions and licence for every series; each download writes a provenance sidecar (retrieval time, SHA-256, vintage) and an immutable snapshot. Crypto uses completed UTC bars only (the 5 Nov bar is missing at the source and is flagged STALE). E-g reports the seasonal window day and the trading day after the election separately. C-e shows level and 30-day change. Revision-prone FRED series use ALFRED first prints; a revision audit quantifies the changes.",
     "evidence": ["midterm_quant/data/catalog.py", "midterm_quant/data/sources.py", "midterm_quant/data/vintages.py", "reports/evidence/data_manifest.csv", "reports/evidence/revision_audit.csv", "reports/evidence/first_print_coverage.csv"],
     "status": "partial", "missing": "ALFRED holds no vintages before Mar 2019 (DTWEXBGS), Jun 2016 (THREEFYTP10) and Apr 2014 (USEPUINDXD); earlier observations come from the earliest vintage and are flagged pre-archive. DefiLlama keeps no vintages, so C5's history is not point-in-time; daily snapshots start now."},
    {"id": "P0-3", "finding": "Policy status misstated: GENIUS shown as in force; the end-2027 wind/solar deadline applied to all projects; projection, certification and taking office conflated.",
     "change": "GENIUS: enacted 18 Jul 2025, effective with the OCC rule on 18 Jan 2027. Wind/solar: the 31 Dec 2027 deadline applies to construction starting after 4 Jul 2026; earlier starts keep the continuity safe harbor. Congress: media projection (4 Nov) vs state certification (Nov-Dec) vs convening (3 Jan 2027).",
     "evidence": ["site_src/content.py", "docs/01_midterm_market_impact.md", "docs/02_observation_framework.md"],
     "status": "done", "missing": "senate.gov's New Congress FAQ refused automated access (HTTP 403); the Twentieth Amendment text is cited instead."},
    {"id": "P0-4", "finding": "No verifiable implementation evidence; '57 tests' and 'completed implementation' unverified.",
     "change": "Commit-pinned repository; requirements.lock; data manifest with hashes and a snapshot id; full parameter sets (docs/05, results.json); per-strategy daily NAV, target and actual positions, orders and fills with commissions, cash ledger (interest, commission, borrow); pytest log and JUnit XML; scripts/reproduce.sh; an independent pandas engine that reproduces E1 and C1 exactly. The page now labels the tests as self-run with the log attached.",
     "evidence": ["requirements.lock", "scripts/reproduce.sh", "reports/evidence/pytest.log", "reports/evidence/pytest-junit.xml", "reports/evidence/ledgers/", "reports/evidence/reconciliation.json", "reports/evidence/data_manifest.json"],
     "status": "partial", "missing": "Independent verification: nobody other than the author has run reproduce.sh. Yahoo prices may not be redistributed, so a reproducer must re-download them and compare against the manifest (scripts/verify_data.py)."},
    {"id": "P0-5", "finding": "C3's halving-cycle fit counted as a success; revised strategies (C5, P3) shown without their history of trials.",
     "change": "C3 is labelled D3 'in-sample research' and excluded from every success count. A registry re-runs all 46 configurations tried since 4 Nov (first specifications, 25 variants, C2 v1 and v2) with the results recorded at the time and the standardised rerun. No development data is called a holdout.",
     "evidence": ["midterm_quant/strategies/trials.py", "reports/evidence/trial_registry.csv", "reports/backtest_summary.md"],
     "status": "done", "missing": ""},
    {"id": "P1-6", "finding": "Misleading indicator names; missing direct measures; net-liquidity units and Wednesday/week-average mismatch.",
     "change": "Renamed with a 'what it is not' line each: credit risk-appetite proxy (HYG/IEF), semiconductor relative strength, crypto equity vs BTC, Brent-WTI spread, oil-fund roll proxy, gold/oil input-cost proxy, 2-year minus fed funds. Added HY OAS (M11), the fed funds futures path (M12) and the actual WTI contract curve (N-f). Net liquidity = WALCL - WDTGAL - RRP on the same Wednesday, in USD billions; C2 moved to v2 with v1 preserved.",
     "evidence": ["midterm_quant/research/monitor.py", "midterm_quant/indicators.py", "midterm_quant/data/align.py", "tests/test_review_iteration.py"],
     "status": "partial", "missing": "OIS-implied path (licensed: Bloomberg, LSEG or ICE; fed funds futures used instead); historical futures curves (CME DataMine or a vendor licence; only the current curve is built); HY OAS before Nov 2023 (ICE licence); miner AISC and cash flow (company filings, not collected)."},
    {"id": "P1-7", "finding": "Frequency studies read as probabilities; overlapping windows; post-hoc 6% filter; no controls.",
     "change": "Every year 1950-2025 is a control for the midterm window; permutation p-values, bootstrap intervals, leave-one-election-out and a regression with trend, momentum, term-spread and credit-spread controls. The selloff study fixes groups on the drop day, reports 38 events in 20 independent episodes (27 overlapping 12-month pairs), the 13 above-200-day cases (all positive at 6 months, 2 negative at 12), the worst further 3-month fall (-10.7% for those 13, -36.9% for all 38), and shows the near-the-high filter (6% from the 52-week high before the drop, added after seeing the current case) as post hoc, with 4-10% neighbours and a threshold/gap grid.",
     "evidence": ["midterm_quant/research/event_study.py", "midterm_quant/research/shock_study.py", "reports/research_controls.md", "reports/evidence/election_day_all_years.csv"],
     "status": "partial", "missing": "Valuation control (CAPE needs the Shiller dataset; not wired in). Recession dating is excluded because NBER decides it after the fact."},
    {"id": "P1-8", "finding": "Inconsistent risk-free rate, annualisation, cut-offs and costs; weak benchmarks; no incremental-contribution test.",
     "change": "One convention: month-end returns, sqrt(12), DTB3 for both Sharpe and cash interest, fixed cut-off, net of costs. Four benchmarks per strategy (cash, buy-and-hold, 10-month trend with costs, risk-matched); volatility, beta, gross and net exposure, turnover, CVaR, worst month, drawdown recovery, crisis correlations, risk contributions and leave-one-out for each class blend. Spread books (N3, N5) are compared with cash; the energy blend is not benchmarked to USO alone.",
     "evidence": ["midterm_quant/engine/evaluation.py", "reports/evidence/performance_risk.csv", "reports/evidence/class_blends.csv", "reports/evidence/blend_attribution.csv"],
     "status": "done", "missing": ""},
    {"id": "P1-9", "finding": "No test that election information adds predictive value; trial counts incomplete.",
     "change": "Nested walk-forward ablation (trend, then seasonality, then policy, then macro, then costs) on monthly S&P 500 excess returns, 25 model configurations counted; deflated Sharpe ratios use all 46 strategy trials. Result: no block adds out-of-sample value.",
     "evidence": ["midterm_quant/research/ablation.py", "reports/research_controls.md", "midterm_quant/engine/evaluation.py"],
     "status": "partial", "missing": "Deviations from pre-election expectations need archived prediction-market or polling data (not held); a verified policy-event timestamp database is not built; company-exposure baskets can only be frozen prospectively (defined in docs/07 for the 2028 election)."},
    {"id": "P1-10", "finding": "Indicators and strategies under-specified; scenario probabilities and the 'three signals, four weeks' rule undefined.",
     "change": "docs/05 specifies all 36 indicators and 20 strategies (inputs, formula, units, frequency, release, decision and execution time, entry, exit, invalidation, missing data, parameter provenance, benchmarks), generated from the code. Scenario weights are labelled subjective priors; scenarios are evaluated independently; the confirmation and revocation algorithm is implemented and run point-in-time for 16 weeks.",
     "evidence": ["docs/05_specifications.md", "midterm_quant/specs.py", "midterm_quant/research/scenarios.py", "reports/results/scenarios.json"],
     "status": "done", "missing": ""},
    {"id": "P2-11", "finding": "No global analysis beyond U.S.-listed ETFs.",
     "change": "Fifteen markets in local currency, in USD and through hedged ETFs: the election-window reaction and five-year sensitivities to U.S. rates, the dollar, Brent and U.S. equities; exporters and importers tagged; ETF time-zone mismatch measured.",
     "evidence": ["midterm_quant/research/global_transmission.py", "reports/results/global.json", "reports/research_controls.md"],
     "status": "partial", "missing": "Trade and tariff exposure by country (UN Comtrade and USITC DataWeb require registration keys); computed hedged returns (need local short rates for each market); local indices for Norway and Saudi Arabia."},
    {"id": "P2-12", "finding": "Backtrader constraints unverified; LEAN migration oversimplified.",
     "change": "Verified: no Docker, no .NET, system Python 3.9.6. LEAN ports of E1 and C1 written; the set_holdings/continuous-futures claim removed and replaced with the futures requirements (contracts, rolls, multipliers, margin, sessions, delivery); open-source engine, paid CLI tier, data licences and brokerage permissions separated.",
     "evidence": ["lean/README.md", "lean/E1_midterm_trend/main.py", "lean/C1_crypto_trend/main.py", "scripts/reconcile_lean.py", "docs/04_framework_selection.md"],
     "status": "partial", "missing": "The LEAN ports have not run: they need Docker (or a .NET SDK build of LEAN), a QuantConnect organisation on a paid tier for the CLI, and LEAN-format data."},
    {"id": "P2-13", "finding": "Page not generated from results; holdings, signals and targets conflated; stale inputs shown green; production deployment discussed prematurely.",
     "change": "The page is rendered by scripts/build_site.py from reports/results/results.json. It separates executed holdings (none), the backtest position, the model signal and the next decision; STALE and MISSING readings are grey with the reason; production deployment is replaced by a frozen prospective paper-trading plan.",
     "evidence": ["scripts/build_results.py", "scripts/build_site.py", "reports/results/results.json", "docs/07_validation_plan.md"],
     "status": "partial", "missing": "Forward paper trading has not started: it needs the frozen commit, a scheduled daily run and 24 months of records."},
]

DELIVERABLES = [
    ("Finding -> change -> evidence matrix", "docs/06_review_response.md"),
    ("Runnable source code (pinned commit)", "midterm_quant/"),
    ("One-command reproduction", "scripts/reproduce.sh"),
    ("Locked dependencies", "requirements.lock"),
    ("Data manifest with hashes", "reports/evidence/data_manifest.csv"),
    ("Standardised performance and risk table", "reports/evidence/performance_risk.csv"),
    ("Transaction-level trade ledgers", "reports/evidence/ledgers/"),
    ("Test logs", "reports/evidence/pytest.log"),
    ("Failed experiments and trial registry", "reports/evidence/trial_registry.csv"),
    ("Prospective validation plan", "docs/07_validation_plan.md"),
    ("Unified results artifact", "reports/results/results.json"),
]

NOT_RECEIVED = ("The brief refers to an accompanying Chinese-language DOCX (6 Nov 2026) with a strategy-by-strategy critique, "
                "30 independently proposed indicators and 20 independently specified rules. It was not provided with the brief, so "
                "none of its specific content is reflected here.")

SOURCES = {
    "cbs_senate": ("CBS News: Senate results", "https://www.cbsnews.com/live-updates/senate-election-results-2026/"),
    "nbc_live": ("NBC News: midterm results live blog", "https://www.nbcnews.com/politics/2026-election/live-blog/midterm-election-results-2026-news-trump-live-updates-rcna605763"),
    "amend20": ("U.S. Constitution, Twentieth Amendment", "https://constitution.congress.gov/constitution/amendment-20/"),
    "occ_2026_50": ("OCC Bulletin 2026-50: GENIUS Act final rule", "https://occ.treas.gov/news-issuances/bulletins/2026/bulletin-2026-50.html"),
    "irs_2025_36": ("IRS Bulletin 2025-36, Notice 2025-42", "https://www.irs.gov/irb/2025-36_IRB"),
    "ambanker_clarity": ("American Banker: CLARITY fails 49-50", "https://www.americanbanker.com/news/crypto-market-structure-bill-fails-in-senate-vote-49-50"),
    "fortune_tariffs": ("Fortune: tariffs, Iran, shutdown", "https://fortune.com/2026/11/03/wall-street-tariffs-iran-government-shutdown-questions/"),
    "fred_dgs10": ("FRED DGS10", "https://fred.stlouisfed.org/series/DGS10"),
    "fred_dfii10": ("FRED DFII10", "https://fred.stlouisfed.org/series/DFII10"),
    "fred_t10yie": ("FRED T10YIE", "https://fred.stlouisfed.org/series/T10YIE"),
    "fred_rt": ("FRED API: real-time periods and vintages", "https://fred.stlouisfed.org/docs/api/fred/realtime_period.html"),
    "lean_futures": ("QuantConnect: futures universes", "https://www.quantconnect.com/docs/v2/writing-algorithms/universes/futures"),
    "lean_cli": ("QuantConnect: LEAN CLI getting started", "https://www.quantconnect.com/docs/v2/lean-cli/key-concepts/getting-started"),
    "cnbc_markets": ("CNBC: markets live, 4 Nov", "https://www.cnbc.com/2026/11/03/stock-market-today-live-updates.html"),
    "yahoo_5nov": ("Yahoo Finance: markets live, 5 Nov", "https://finance.yahoo.com/markets/live/stock-market-today-thursday-november-5-dow-sp-500-nasdaq-oil-rises-chip-stocks-141439950.html"),
    "bbg_chips": ("Bloomberg: chip selloff, 5 Nov", "https://www.bloomberg.com/news/articles/2026-11-05/chips-selloff-worsens-as-fears-about-ai-trade-grip-stock-market"),
    "fomc_oct": ("Federal Reserve: FOMC statement, 28 Oct 2026", "https://www.federalreserve.gov/newsevents/pressreleases/monetary20261028a.htm"),
    "wharton_tariffs": ("Wharton Budget Model: effective tariff rates", "https://budgetmodel.wharton.upenn.edu/p/2026-10-14-effective-tariff-rates-and-revenues-updated-october-14-2026/"),
    "cnbc_oil": ("CNBC: Iran war oil timeline", "https://www.cnbc.com/2026/04/21/oil-price-iran-war-middle-east.html"),
    "troutman": ("Troutman Pepper Locke: after CLARITY", "https://www.troutman.com/insights/in-the-wake-of-clarity-acts-failure-agencies-move-forward-without-congressional-action-or-certainty/"),
    "wgc_q3": ("Asianet / WGC: Q3 central-bank gold buying", "https://newsable.asianetnews.com/business/central-bank-gold-purchases-soar-in-q3-2026-amidst-high-global-prices-articleshow-0tlhpyf"),
    "axios_energy": ("Axios: energy and a Democratic Congress", "https://www.axios.com/2026/10/30/energy-democrats-congress-midterms"),
}
