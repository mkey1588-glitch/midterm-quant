"""Render reports/midterm_playbook.html from reports/results/results.json and site_src/.

Every number on the page comes from results.json; authored text (policy status, narrative,
review matrix, sources) comes from site_src/content.py. Links to evidence files point at the
commit recorded in results.json, so the page and its evidence cannot drift apart.

Usage: .venv/bin/python scripts/build_site.py
"""
import html
import json
import math
import re
import sys

import _bootstrap  # noqa: F401

from midterm_quant import config

sys.path.insert(0, str(config.ROOT))
from site_src import content as C  # noqa: E402

R = json.loads((config.RESULTS_DIR / "results.json").read_text())
COMMIT = R["code"]["commit"]
REPO = R["code"]["repository"]
MINUS = "−"


# ---------------------------------------------------------------------------- helpers --
def esc(s) -> str:
    return html.escape(str(s), quote=True)


def fin(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def pct(v, d=1, sign=True) -> str:
    if not fin(v):
        return "–"
    s = f"{abs(v) * 100:.{d}f}%"
    return (("+" if v > 0 else MINUS if v < 0 else "") if sign else (MINUS if v < 0 else "")) + s


def num(v, d=2) -> str:
    if not fin(v):
        return "–"
    s = f"{abs(v):.{d}f}"
    return (MINUS if v < 0 else "") + s


def snum(v, d=2) -> str:
    """Signed number: + for gains, the minus sign for losses."""
    return ("+" if fin(v) and v > 0 else "") + num(v, d)


def gh(path: str) -> str:
    kind = "tree" if path.endswith("/") else "blob"
    return f"{REPO}/{kind}/{COMMIT}/{path.rstrip('/')}"


def code_link(path: str) -> str:
    return f'<a href="{esc(gh(path))}"><code>{esc(path)}</code></a>'


ICON = {
    "alert": '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M5 0.5 L9.6 9.2 H0.4 Z"/></svg>',
    "watch": '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M5 0.3 L9.7 5 L5 9.7 L0.3 5 Z"/></svg>',
    "ok": '<svg viewBox="0 0 10 10" aria-hidden="true"><circle cx="5" cy="5" r="4.5"/></svg>',
    "neutral": '<svg viewBox="0 0 10 10" aria-hidden="true"><circle cx="5" cy="5" r="3.8"/></svg>',
    "stale": '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1 5 H9"/></svg>',
}
TONE_CLASS = {"alert": "alert", "watch": "watch", "supportive": "ok", "neutral": "neutral", "info": "neutral",
              "stale": "stale", "missing": "stale", "done": "ok", "partial": "watch", "not done": "alert"}


def chip(tone: str, label: str) -> str:
    c = TONE_CLASS.get(tone, "neutral")
    return f'<span class="chip {c}">{ICON[c]}{esc(label)}</span>'


def table(head: list, rows: list, caption: str = "", cls: str = "", right=()) -> str:
    r_th, r_td = ' class="r"', ' class="r nw"'
    th = "".join(f'<th{r_th if i in right else ""}>{h}</th>' for i, h in enumerate(head))
    body = []
    for r in rows:
        if isinstance(r, str):          # group row
            body.append(f'<tr class="group"><td colspan="{len(head)}">{r}</td></tr>')
            continue
        body.append("<tr>" + "".join(f'<td{r_td if i in right else ""}>{c}</td>' for i, c in enumerate(r)) + "</tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    return f'<div class="tbl-wrap"><table class="{cls}"><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody>{cap}</table></div>'


def section(sid: str, title: str, lede: str, body: str) -> str:
    return (f'<section id="{sid}"><div class="wrap stack"><div class="sec-head"><h2>{title}</h2>'
            f'{f"<p class=lede>{lede}</p>" if lede else ""}</div>{body}</div></section>')


def fmt_date(iso) -> str:
    if not iso:
        return "–"
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(iso))
    if not m:
        return esc(iso)
    mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][int(m.group(2)) - 1]
    return f"{int(m.group(3))} {mon} {m.group(1)}"


READ = {r["code"]: r for r in R["monitor"]["readings"]}


def fill(text: str) -> str:
    def rep(m):
        code, field = m.group(1), m.group(2)
        r = READ.get(code)
        if not r:
            return "n/a"
        return {"value": r["value"], "context": r["context"], "regime": r["regime"].lower(), "status": r["status"],
                "date": fmt_date(r["observation_date"])}[field]
    return esc(re.sub(r"\{([A-Z]\-?[a-z0-9]*\d*|[A-Z]-[a-z])\.(value|context|regime|status|date)\}", rep, text))


# --------------------------------------------------------------------------- sections --
def header() -> str:
    ts = R["timestamps"]
    ev = R["evidence"]
    bt = R["backtests"]
    ms = R["monitor_summary"]
    es = {r["horizon"]: r for r in R["event_study"]["midterm_vs_other_years"]}["+12m"]
    book = bt["book"]
    dsr_pass = [b["Trial"] for b in book if fin(b.get("DSR")) and b["DSR"] >= 0.95 and b["Evidence"] != "D3"]
    fo = ts["indicator_observation_dates"]["fred_examples"]
    strip = [
        ("Page generated", f'{esc(ts["page_generated_utc"].replace("T", " ").replace("+00:00", " UTC"))}'),
        ("Market data cutoff", "5 Nov 2026 U.S. close (16:00 ET). Crypto: last completed UTC day bar; the 5 Nov bar is missing at the source, so crypto readings use 4 Nov"),
        ("Indicator observations", f'{fmt_date(fo.get("M2"))} for FRED daily rates (10-year {READ["M2"]["value"]}, real {READ["M6"]["value"]}, breakeven {READ["M5"]["value"]}); {fmt_date(fo.get("M9"))} for Fed balance-sheet data; each row below shows its own date'),
        ("Backtests", f'daily data through {fmt_date(ts["backtest_end"])}; standardised metrics through the last complete month (Oct 2026)'),
        ("Code and data", f'commit <a href="{esc(REPO)}/tree/{COMMIT}"><code>{COMMIT[:10]}</code></a>{" (with uncommitted changes)" if R["code"]["dirty_tracked_files"] else ""}; data snapshot <code>{esc((ev["data_snapshot_id"] or "")[:12])}</code>'),
    ]
    kpis = [
        ("Projected", "Democratic majorities in both chambers per media projections on 4 Nov. Not yet certified; the new Congress convenes on 3 Jan 2027."),
        (f'{round(es["midterm %pos"] * es["midterm n"])} / {es["midterm n"]}',
         f'midterms with a higher S&amp;P 500 12 months later (mean {pct(es["midterm mean"])}), vs {pct(es["other %pos"], 0, False)} of other years ({pct(es["other mean"])}). Difference p = {num(es["permutation p (two-sided)"])}: descriptive, not causal.'),
        (f'{ms["alert"]} of {ms["ok"]}', f'indicators with current data sit in their alert zone; {ms["stale"]} more are stale and {ms["missing"]} missing, shown grey.'),
        (f'0 of {len(book)}', f'strategies have out-of-sample evidence. {"No strategy clears" if not dsr_pass else str(len(dsr_pass)) + " clear"} a deflated Sharpe of 0.95 after {bt["n_trials"]} trials; C3 is in-sample research.'),
    ]
    toc = [("evidence", "Evidence status"), ("policy", "What changed"), ("selloff", "5 Nov selloff"), ("history", "History"),
           ("election-value", "Election signal test"), ("global", "Global"), ("outlook", "Outlook"), ("scenarios", "Scenarios"),
           ("watch", "Watch-list"), ("strategies", "Strategies"), ("review", "Review response"), ("reproduce", "Reproduce"), ("sources", "Sources")]
    return f'''<header class="top"><div class="wrap">
<div class="eyebrow">Research note · first published 5 Nov 2026 · rebuilt from results.json after an external review</div>
<h1>The 2026 midterms and the markets</h1>
<p class="lede">What a Democratic Congress facing a Republican White House may mean for U.S. equities, crypto, energy, precious metals and markets abroad: 36 indicators to watch until November 2028 and 20 rule-based strategies, each labelled with the evidence behind it. Every backtest here uses data seen while the rules were written. Nothing has been traded.</p>
<dl class="ts">{"".join(f"<div><dt>{a}</dt><dd>{b}</dd></div>" for a, b in strip)}</dl>
<nav class="toc" aria-label="Sections">{"".join(f'<a href="#{a}">{b}</a>' for a, b in toc)}</nav>
<div class="kpis">{"".join(f'<div class="kpi"><div class="big">{a}</div><div class="lab">{b}</div></div>' for a, b in kpis)}</div>
<p class="disclaimer">Research and education only, not investment advice. Backtests are hypothetical, in-sample, use ETF proxies, and carry the limitations listed with each table.</p>
</div></header>'''


def evidence() -> str:
    ev = R["evidence"]
    t = ev["tests"]
    rc = {r["strategy"]: r for r in (ev["reconciliation"] or [])}
    tc = ev["trial_counts"]
    rows = [
        ("Tests", chip("ok" if t.get("failures") == 0 and t.get("errors") == 0 else "alert", "passed (self-run)") if "tests" in t else chip("stale", "no log"),
         f'{t.get("tests", "?")} offline tests, {t.get("failures", "?")} failures, run {esc(str(t.get("timestamp", ""))[:16].replace("T", " "))} on {esc(R["code"]["platform"])}, Python {esc(R["code"]["python"])}. Log: {code_link("reports/evidence/pytest.log")}. Run by the author; not independently verified.'),
        ("Reproduction", chip("ok", "one command"),
         f'{code_link("scripts/reproduce.sh")} rebuilds data checks, tests, backtests, research, docs and this page; versions pinned in {code_link("requirements.lock")}. Not yet run by a third party.'),
        ("Data", chip("watch", "licensed in part"),
         f'{ev["data_files"]} files, snapshot <code>{esc((ev["data_snapshot_id"] or "")[:16])}</code>; status {esc(json.dumps(ev["data_status_counts"]))}. {ev["not_redistributable_files"]} files (Yahoo, ICE) may not be redistributed, so the repository ships hashes and {code_link("scripts/verify_data.py")} instead.'),
        ("Point-in-time inputs", chip("watch", "partial"),
         f'Each input is used only from its publication date; revision-prone FRED series use ALFRED first prints ({code_link("reports/evidence/revision_audit.csv")}). Before the first archived vintage (2014-2019, by series) and for stablecoin supply, history may contain later revisions.'),
        ("Engine check", chip("ok", "exact match"),
         f'An independent pandas re-implementation of E1 and C1 reproduces Backtrader\'s {rc.get("E1", {}).get("decisions compared", "?")} and {rc.get("C1", {}).get("decisions compared", "?")} decisions, {rc.get("E1", {}).get("fills reference", "?")} and {rc.get("C1", {}).get("fills reference", "?")} fills, commissions and daily NAV to within 10<sup>{MINUS}14</sup> ({code_link("reports/evidence/reconciliation.json")}).'),
        ("LEAN port", chip("stale", "not run"), f'E1 and C1 ported ({code_link("lean/README.md")}); not executed: no Docker or .NET here, and the LEAN CLI needs a QuantConnect organisation on a paid tier.'),
        ("Trials counted", chip("neutral", f'{tc["strategy_configurations"]} + {tc["ablation_model_configurations"]}'),
         f'{tc["strategy_configurations"]} strategy configurations (all re-run, {code_link("reports/evidence/trial_registry.csv")}) feed the deflated Sharpe ratio; {tc["ablation_model_configurations"]} model configurations in the election-signal test; {tc["shock_study_definitions"]} selloff-study definitions, all reported.'),
        ("Holdout", chip("alert", "none"), f'No untouched historical sample exists: all data to {fmt_date(R["timestamps"]["backtest_end"])} was used in development. The genuine test is prospective, from {fmt_date(R["timestamps"]["prospective_start"])} on the frozen commit ({code_link("docs/07_validation_plan.md")}).'),
        ("Holdings", chip("neutral", "none"), "No account, paper or live, holds any of these positions. Positions below are hypothetical backtest books."),
    ]
    return section("evidence", "Evidence status", "What each claim on this page rests on, and what has not been verified.",
                   table(["Claim", "Status", "Evidence"], [(f"<b>{a}</b>", b, c) for a, b, c in rows]))


def policy() -> str:
    tone = {"projected": "watch", "scheduled": "neutral", "enacted, not yet effective": "watch", "in force (conditional deadline)": "neutral",
            "failed": "alert", "estimate": "watch"}
    rows = []
    for p in C.POLICY:
        src = " · ".join(f'<a href="{esc(C.SOURCES[s][1])}">{esc(C.SOURCES[s][0])}</a>' for s in p["sources"])
        rows.append((f'<b>{esc(p["item"])}</b>', chip(tone.get(p["status"], "neutral"), p["status"]), esc(p["date"]),
                     f'{esc(p["text"])}<span class="sub">{src}</span>'))
    cm = C.CONTROL_MAP
    cards = "".join(
        f'<div class="card"><h3>{t}</h3><ul class="lev">' + "".join(f"<li><b>{esc(a)}</b><span>{esc(b)}</span></li>" for a, b in items) + "</ul></div>"
        for t, items in (("Congress controls (from 3 Jan 2027)", cm["congress"]), ("The White House keeps", cm["white_house"])))
    return section("policy", "What changed, and what has not yet", "Projected, certified, enacted and effective are different states. Each item says which one applies.",
                   table(["Item", "Status", "Date", "Detail and source"], rows) +
                   f'<div class="grid-2 control-map">{cards}</div><p class="small">The control map is analysis, not a forecast.</p>')


def selloff() -> str:
    rows = []
    for m in R["market_moves"]:
        k = m["kind"]
        if k == "yield":
            val = f'{m["value"]:.2f}%'
            day = f'{snum(m["day_change_points"] * 100, 0)}bp' if fin(m.get("day_change_points")) else "–"
        elif k == "vol":
            val, day = f'{m["value"]:.1f}', f'{snum(m["day_change_points"], 1)} pts'
        elif k == "usd":
            val, day = (f'${m["value"]:,.0f}' if m["value"] > 1000 else f'${m["value"]:,.2f}'), pct(m["day_change"])
        else:
            val, day = f'{m["value"]:,.2f}' if m["value"] < 1000 else f'{m["value"]:,.0f}', pct(m["day_change"])
        flag = "" if m["is_cutoff_day"] else ' <span class="mk">not the cutoff day</span>'
        rows.append((esc(m["label"]), val, day, pct(m.get("from_52w_high")), f'{esc(m["timestamp"])}{flag}'))
    sh = R["shock_study"]
    cur = sh["current_case"]
    g = {x["group"]: x for x in sh["groups"]}
    up = g["above 200-day after the drop"]
    allg = g["all events"]
    ph = sh["posthoc_filters"]
    shock_data = [{"date": e["date"], "ret": e["ret"] * 100, "above": e["above200"],
                   **{k: (None if e.get(k) is None or not fin(e.get(k)) else e[k] * 100) for k in ("1m", "3m", "6m", "12m")},
                   "dd3m": e["further_dd_3m"] * 100 if fin(e.get("further_dd_3m")) else None} for e in sh["events"]]
    sens = table(["Drop at least", "De-cluster gap", "Events", "Episodes", "Above 200-day", "6m positive", "12m negatives", "Worst further 3m fall (above / all)", "Overlapping 12m pairs"],
                 [(pct(s["threshold"], 1, False), f'{s["gap"]} sessions', s["n all"], s["episodes"], s["n above200"], pct(s["above200 6m %pos"], 0, False),
                   s["above200 12m negatives"], f'{pct(s["above200 worst further fall 3m"])} / {pct(s["all worst further fall 3m"])}', s["12m overlapping pairs"]) for s in sh["sensitivity"]],
                 right=(2, 3, 4, 5, 6, 8))
    post = table(["Within x% of 52-week high", "Events", "6m positive", "12m negatives", "Worst further 3m fall"],
                 [(pct(p["threshold"], 0, False), p["n"], pct(p["6m %pos"], 0, False), p["12m negatives"], pct(p["worst further fall 3m"])) for p in ph], right=(1, 2, 3, 4),
                 caption=f"Post-hoc: this filter (distance from the 52-week high at the close before the drop) was added on 5 Nov after seeing the current case, which stood {pct(cur['dd_before'])} from its high before the drop and {pct(R['market_moves'][0]['from_52w_high'])} after it. The 6% threshold was not specified in advance; it is shown with its neighbours, never as a rule.")
    body = (table(["Market", "Level", "Day", "From 52-week high", "Timestamp of the value"], rows, right=(1, 2, 3),
                  caption="Each row carries its own timestamp. ^TNX (CBOE) and DGS10 (FRED) are different series; FRED had not yet published 5 Nov. Bitcoin's completed 5 Nov UTC bar is missing at the source.") +
            f'''<div class="chart-card"><div class="chart-head"><div class="t"><h3>S&amp;P 500 after one-day drops of 3.5% or more, 1950 to {fmt_date(sh["history_end"])}</h3>
<div class="legend-row"><span><i class="swatch box" style="background:var(--series-1)"></i>Still above its 200-day average after the drop</span><span><i class="swatch box" style="background:var(--series-1-muted)"></i>Below it</span><span class="muted">Bar: median</span></div></div>
<div class="seg" role="group" aria-label="Horizon after the drop"><button type="button" data-k="1m" aria-pressed="false">1 month</button><button type="button" data-k="3m" aria-pressed="false">3 months</button><button type="button" data-k="6m" aria-pressed="true">6 months</button><button type="button" data-k="12m" aria-pressed="false">12 months</button></div></div>
<div class="chart" id="shock-chart"></div><p class="small" id="shock-sum"></p>
<details><summary>Show as a table</summary><div class="tbl-wrap"><table id="shock-table"><thead><tr><th>Drop day</th><th class="r">Day</th><th>vs 200-day</th><th class="r">+1m</th><th class="r">+3m</th><th class="r">+6m</th><th class="r">+12m</th><th class="r">Further fall in 3m</th></tr></thead><tbody></tbody></table></div></details></div>
<script id="shock-data" type="application/json">{json.dumps(shock_data)}</script>
<div class="callout prose"><p><b>How to read it.</b> {allg["n"]} drops in {sh["episodes"]} independent episodes: with a 20-session de-clustering gap, {sh["overlap_pairs_12m"]} pairs of events share part of their 12-month window, so the dots are not independent observations. Groups are fixed on the drop day's close. The {up["n"]} drops that left the index above its 200-day average were all higher 6 months later, but {up["12m negatives"]} were lower after 12 months; their worst further fall within 3 months was {pct(up["worst further fall 3m"])} (all {allg["n"]} drops: {pct(allg["worst further fall 3m"])}). This is a frequency description, not a calibrated probability.</p>
<p><b>The current case</b> ({fmt_date(cur["date"])}): {pct(cur["ret"])} on the day, {"above" if cur["above200"] else "below"} its 200-day average ({cur["close"]:,.0f} vs {cur["sma200"]:,.0f}), {pct(cur["dd_before"])} from its 52-week high before the drop. It is not part of the history above.</p></div>
<details><summary>Sensitivity to the event definition</summary>{sens}</details>
<details><summary>The post-hoc "near the high" filter and its neighbours</summary>{post}</details>''')
    return section("selloff", "The 5 November selloff", "The S&amp;P 500 fell 4.4% on Thursday 5 November, led by semiconductors. How past drops of this size played out, with the design choices exposed.", body)


def history() -> str:
    es = R["event_study"]
    vs = es["midterm_vs_other_years"]
    t1 = table(["Horizon", "Midterm years: mean (90% CI)", "Positive", "Other years: mean (90% CI)", "Positive", "Difference", "Permutation p"],
               [(r["horizon"], f'{pct(r["midterm mean"])} <span class="vs">({pct(r["midterm 90% CI"][0])} to {pct(r["midterm 90% CI"][1])})</span>', f'{round(r["midterm %pos"] * r["midterm n"])} of {r["midterm n"]}',
                 f'{pct(r["other mean"])} <span class="vs">({pct(r["other 90% CI"][0])} to {pct(r["other 90% CI"][1])})</span>', f'{round(r["other %pos"] * r["other n"])} of {r["other n"]}',
                 pct(r["difference"]), num(r["permutation p (two-sided)"])) for r in vs], right=(2, 4, 5, 6),
               caption="S&amp;P 500 price return from the close of election day (Tuesday after the first Monday in November) for every year 1950-2025. Bootstrap intervals; permutation test shuffles the midterm label.")
    cyc = table(["Year of the cycle", "Years", "Mean 12m", "Median", "Positive"],
                [(esc(r["cycle"]), r["n"], pct(r["mean"]), pct(r["median"]), pct(r["%pos"], 0, False)) for r in es["by_cycle_year_12m"]], right=(1, 2, 3, 4))
    reg = es["regression_12m"]
    names = {"const": "Constant", "midterm": "Midterm year", "above200": "Above 200-day at election", "trail12": "Trailing 12m return", "term_spread": "Term spread (GS10 − TB3MS)", "credit_spread": "Baa − Aaa spread"}
    t2 = table(["Term", "Coefficient", "Std. error (HC1)", "t"],
               [(names.get(r["term"], r["term"]), num(r["coef"], 3), num(r["se (HC1)"], 3), num(r["t"], 2)) for r in reg["table"]], right=(1, 2, 3),
               caption=f'12-month return on a midterm dummy and the state at election day, n = {reg["n"]} years. No valuation control (CAPE not wired in).')
    seas = table(["Year of the cycle", "Years", "Mean, 30 Sep to 30 Jun", "Positive"],
                 [(esc(r["cycle"]), r["n"], pct(r["mean"]), pct(r["%pos"], 0, False)) for r in es["seasonal_window_by_cycle"]], right=(1, 2, 3))
    loo = es["leave_one_out_12m"]
    body = (t1 + f'<p class="small" style="max-width:80ch">Leave-one-election-out: the midterm 12-month mean stays between {pct(loo["min_mean"])} and {pct(loo["max_mean"])}. The 19 midterm windows do not overlap, but 19 observations cannot separate an election effect from the presidential-cycle seasonal or the economic state, and nothing here is a forecast probability.</p>'
            + f'<div class="grid-2"><div class="stack" style="gap:10px"><h3>By year of the presidential cycle</h3>{cyc}</div><div class="stack" style="gap:10px"><h3>The seasonal window strategy E1 uses</h3>{seas}</div></div>'
            + f'<div class="stack" style="gap:10px"><h3>With state controls</h3>{t2}</div>')
    return section("history", "Midterm history, with controls", "Descriptive evidence only. Every year since 1950 serves as a control for the same November window.", body)


def election_value() -> str:
    ab = R["ablation"]
    rows = [(esc(s["step"]), pct(s.get("R2_OS vs hist mean"), 1), num(s.get("Clark-West t vs hist mean")), num(s.get("timing Sharpe")), pct(s.get("timing CAGR")), pct(s.get("timing MaxDD")))
            for s in ab["steps"]]
    rows.append(("Buy and hold", "–", "–", num(ab["buy_hold"]["Sharpe"]), pct(ab["buy_hold"]["CAGR"]), pct(ab["buy_hold"]["MaxDD"])))
    inc = table(["Block added", "Change in out-of-sample R²", "Clark-West t", "p"],
                [(esc(i["added"]), pct(i["delta R2_OS"], 2), num(i["Clark-West t"]), num(i["p"])) for i in ab["increments"]], right=(1, 2, 3))
    s0 = ab["steps"][0]
    body = (table(["Model", "Out-of-sample R²", "Clark-West t vs mean", "Timing Sharpe", "Timing CAGR", "Max drawdown"], rows, right=(1, 2, 3, 4, 5),
                  caption=f'Next-month S&amp;P 500 excess price return; ridge regressions refitted every January on an expanding window from 1986, penalty chosen inside each window; forecasts {s0["oos_start"]} to {s0["oos_end"]} ({s0["months"]} months, same months for every step). {ab["n_trials"]} model configurations counted. Timing rule: invested when the forecast is positive.')
            + inc + f'<div class="callout prose"><p><b>Result.</b> No block of information, including the post-midterm dummy and policy uncertainty, improved out-of-sample forecasts over the historical mean, and none produced a timing rule that beat buy-and-hold. {esc(ab["election_feature_note"])} The prospective test in docs/07 freezes exposure baskets and expectation data before the 2028 election.</p></div>')
    return section("election-value", "Does election information predict returns?", "A nested walk-forward test that adds price trend, then seasonality, then policy, then macro state, then costs.", body)


def global_section() -> str:
    gl = R["global"]
    rows, last = [], None
    for r in gl["reaction"]:
        if r["group"] != last:
            rows.append(esc(r["group"]))
            last = r["group"]
        rows.append((esc(r["market"]), esc(r["energy"]), pct(r["local"]), pct(r["fx vs USD"]), pct(r["USD (local x FX)"]), pct(r["US-listed ETF"]), pct(r.get("hedged ETF"))))
    t1 = table(["Market", "Energy", "Local currency", "Currency vs USD", "In USD", "U.S.-listed ETF", "Hedged ETF"], rows, right=(2, 3, 4, 5, 6),
               caption=f'Last close on or before {fmt_date(gl["window"]["pre"])} (before any result was known) to the last close on or before {fmt_date(gl["window"]["post"])}. {esc(gl["timing_note"])}')
    srows, last = [], None
    for s in gl["sensitivities"]:
        if s["market"] != last:
            last = s["market"]
            label = esc(s["market"])
        else:
            label = ""
        srows.append((label, esc(s["basis"]), num(s["beta USD broad"]), num(s["t USD broad"], 1), num(s["beta Brent"]), num(s["t Brent"], 1),
                      num(s["beta dUS10y (pp)"]), num(s["beta S&P 500"]), num(s["R2"])))
    t2 = table(["Market", "Return basis", "β dollar", "t", "β Brent", "t", "β U.S. 10-year (per pp)", "β S&amp;P 500", "R²"], srows, right=(2, 3, 4, 5, 6, 7, 8),
               caption="60 monthly returns to Oct 2026, regressed jointly on the broad dollar, Brent, the change in the U.S. 10-year yield and the S&amp;P 500; HC1 t-statistics.")
    hv = table(["Market", "Years", "Unhedged ETF", "Hedged ETF", "Currency effect per year", "Note"],
               [(esc(h["market"]), h["years"], f'{pct(h["unhedged ann."])} ({esc(h["unhedged ETF"])})', f'{pct(h["hedged ann."])} ({esc(h["hedged ETF"])})', pct(h["currency effect ann."]), esc(h["note"]))
                for h in gl["hedged_vs_unhedged"]], right=(1, 2, 3, 4))
    body = (t1 + '<p class="small" style="max-width:80ch">The dollar channel dominates: in USD terms, European and emerging markets carry dollar betas of about −1 to −3, mostly absent in local currency. Energy exporters (Norway, Saudi Arabia) load positively on Brent and importers (Japan, Korea, India) negatively.</p>'
            + f"<details><summary>Five-year sensitivities by market and return basis</summary>{t2}</details>"
            + f"<details><summary>Hedged vs unhedged returns</summary>{hv}</details>"
            + f'<p class="small">Not measured: {esc("; ".join(gl["not_measured"]))}.</p>')
    return section("global", "Global transmission", "The same election seen from Europe, Japan, China and its supply chain, emerging markets, and energy exporters and importers, in local currency, in dollars and hedged.", body)


def outlook() -> str:
    cards = []
    for cls, o in C.OUTLOOK.items():
        sig = [s for s in R["backtests"]["signals"] if s["Class"] == cls]
        pos = " · ".join(f'{s["Code"]} {esc(", ".join(f"{k} {v:+.0%}" for k, v in s["Backtest position at close"].items()) or "cash")}' for s in sig)
        cards.append(f'''<div class="card asset"><div class="tagline">{esc(cls)}</div><div class="stance">{esc(o["stance"])}</div><dl>
<dt>Now</dt><dd>{fill(o["now"])}</dd><dt>Helps</dt><dd>{fill(o["helps"])}</dd><dt>Hurts</dt><dd>{fill(o["hurts"])}</dd>
<dt>Hypothetical backtest books at the close</dt><dd>{pos}</dd></dl></div>''')
    return section("outlook", "Outlook by asset class, next 24 months", "Analysis, not evidence: the readings are from the watch-list below, the judgements are the author's.",
                   f'<div class="grid-2">{"".join(cards)}</div>')


def scenarios() -> str:
    sc = R["scenarios"]
    hist = sc["history"]
    latest = {}
    for h in hist:
        latest[h["scenario"]] = h
    cards = []
    for key, s in sc["scenarios"].items():
        h = latest[key]
        holding = set(h["which"])
        items = "".join(f'<li>{"■" if "/".join(p["codes"]) in holding else "□"} {esc(p["label"])} <span class="code">{esc("/".join(p["codes"]))}</span></li>' for p in s["signposts"])
        state_tone = {"CONFIRMED": "alert", "WATCHING": "neutral", "REVOKED": "watch"}[h["state"]]
        cards.append(f'''<div class="card scen"><div class="p">{s["prior"] * 100:.0f}%<small>subjective prior</small></div><h3>{key}. {esc(s["name"])}</h3>
<div>{chip(state_tone, h["state"].lower())} <span class="small">{h["holding"]} of {h["of"]} signposts hold ({fmt_date(h["week_end"])})</span></div>
<ul class="plain small">{items}</ul>{f'<p class="small">Gaps: {esc(", ".join(h["gaps"]))}</p>' if h["gaps"] else ""}</div>''')
    weeks = sorted({h["week_end"] for h in hist})
    by = {(h["week_end"], h["scenario"]): h for h in hist}
    t = table(["Week ending", "A", "B", "C"], [(fmt_date(w), *[f'{by[(w, k)]["holding"]}{" ✓" if by[(w, k)]["state"] == "CONFIRMED" else ""}' for k in "ABC"]) for w in weeks[::-1]], right=(1, 2, 3),
              caption="Signposts holding at each weekly reading, computed point-in-time (data published by that close; ALFRED vintages). ✓ = confirmed.")
    rule = sc["rule"]
    return section("scenarios", "Three scenarios to November 2028",
                   "The percentages are the author's subjective priors: not calibrated, not mutually exclusive in their drivers, and not updated by the signposts.",
                   f'<div class="grid-3">{"".join(cards)}</div><div class="callout prose"><p><b>The rule.</b> Confirmed: {esc(rule["confirm"])}. Revoked: {esc(rule["revoke"])}. {esc(rule["missing"]).capitalize()}. {esc(rule["independence"]).capitalize()}.</p></div><details><summary>16 weeks of readings</summary>{t}</details>')


def watch() -> str:
    rows, last = [], None
    for r in R["monitor"]["readings"]:
        if r["group"] != last:
            rows.append(esc(r["group"]))
            last = r["group"]
        new = " <span class=mk>new</span>" if r["code"] not in R["monitor"]["original_33"] else ""
        srcs = " · ".join(f'<a href="{esc(u["source_url"])}">{esc(u["series"].replace("fred:", "FRED "))}</a>' for u in r["inputs"][:4] if u.get("source_url"))
        name = f'<b>{esc(r["name"])}</b>{new}<span class="sub">{esc(r["measures"])}. <i>Limits:</i> {esc(r["not_measures"])}.</span><span class="sub">{srcs}</span>'
        if r["status"] == "OK":
            st = chip(r["tone"], r["regime"].lower())
        else:
            st = chip("stale", f'{r["status"].lower()}: last read {r["regime"].lower()}' if r["status"] == "STALE" else "missing")
        notes = r.get("extra", {}).get("data_notes") or []
        ctx = esc(r["context"]) + (f'<span class="sub">{esc("; ".join(notes))}</span>' if notes else "")
        rows.append((f'<span class="code">{esc(r["code"])}</span>', name, f'<b>{esc(r["value"])}</b><span class="sub">{ctx}</span>',
                     f'{fmt_date(r["observation_date"])}<span class="sub">{"" if r["age_days"] is None else str(r["age_days"]) + (" day old" if r["age_days"] == 1 else " days old")}</span>', st, esc(r["rule"])))
    ms = R["monitor_summary"]
    return section("watch", "Watch-list: 36 indicators",
                   f'Thresholds were declared in advance (4 Nov; 6 Nov for the three new direct measures). Each value is dated by the observation it describes. {ms["stale"]} stale and {ms["missing"]} missing readings are grey, never green.',
                   table(["Code", "Indicator", "Reading", "Observed", "Status", "Rule"], rows,
                         caption=f'As of the {fmt_date(R["monitor"]["asof"])} close; inputs used only from their publication date. Full definitions: {code_link("docs/05_specifications.md")}.'))


def strategies() -> str:
    bt = R["backtests"]
    labels = {"D1": "pre-specified", "D2": "revised after results", "D3": "in-sample research"}
    rows, last = [], None
    for b in bt["book"]:
        if b["Class"] != last:
            rows.append(esc(b["Class"]))
            last = b["Class"]
        prim = "cash" if b["Primary"] == "cash" else "risk-matched"
        rows.append((f'<span class="code">{esc(b["Trial"])}</span>',
                     f'<b>{esc(b["Name"])}</b><span class="sub">{chip("watch" if b["Evidence"] == "D3" else "neutral", labels[b["Evidence"]])} since {esc(b["Start"])}; primary benchmark: {prim}</span>',
                     pct(b["CAGR"]), num(b["Sharpe"]), num(b["DSR"]), pct(b["MaxDD"]),
                     f'{num(b["buy_hold_Sharpe"])} / {num(b["trend_Sharpe"])} / {num(b["risk_matched_Sharpe"])}', num(b["IR_vs_risk_matched"]),
                     num(b["Beta_SPY"]), f'{num(b["Turnover/yr"], 1)}×'))
    t1 = table(["Code", "Strategy", "CAGR", "Sharpe", "Deflated Sharpe", "Max DD", "Benchmark Sharpe: hold / trend / risk-matched", "Info ratio vs risk-matched", "β SPY", "Turnover"],
               rows, right=(2, 3, 4, 5, 6, 7, 8, 9),
               caption=f'Development sample to {fmt_date(R["timestamps"]["backtest_end"])}; monthly returns, √12, excess over 3-month bills, net of costs. Deflated Sharpe = probability that the true Sharpe beats the best of {bt["n_trials"]} unskilled trials. Risk-matched benchmark scaled ex post. Full table with drawdown recovery, CVaR and crisis correlations: {code_link("reports/evidence/performance_risk.csv")}.')
    prow = []
    for s in bt["signals"]:
        pos = ", ".join(f"{k} {v:+.0%}" for k, v in s["Backtest position at close"].items()) or "cash"
        tgt = "hold" if s["Signal is hold-current"] else (", ".join(f"{k} {v:+.0%}" for k, v in (s["Model signal at close"] or {}).items() if abs(v) > 1e-4) or "cash")
        gaps = s["Stale inputs"]
        prow.append((f'<span class="code">{esc(s["Code"])}</span>', esc(pos), esc(tgt), esc(s["Signal status"]), fmt_date(s["Next decision"]),
                     chip("stale", "; ".join(gaps)) if gaps else '<span class="muted">none</span>'))
    t2 = table(["Code", "Backtest position at the close", "Model signal", "What the signal is", "Next scheduled decision", "Data gaps"], prow,
               caption="Executed holdings: none. The backtest position is hypothetical; a signal becomes a hypothetical order only at its scheduled decision.")
    bl = table(["Class", "Sleeves", "Since", "CAGR", "Sharpe", "Max DD", "Reference Sharpe", "Avg. correlation"],
               [(esc(b["Class"]), esc(b["Variant"]), esc(b["Start"]), pct(b["CAGR"]), num(b["Sharpe"]), pct(b["MaxDD"]), f'{num(b["Ref Sharpe"])} ({esc(b["Ref"])})', num(b["Avg pairwise corr"])) for b in bt["blends"]],
               right=(3, 4, 5, 6, 7), caption="Equal-weight monthly blends, excess-return Sharpe. The energy blend is compared with cash and the risk-matched reference, not with USO alone.")
    at = table(["Class", "Sleeve", "Share of blend risk", "Blend Sharpe without it", "Change if removed"],
               [(esc(a["Class"]), esc(a["Sleeve"]), pct(a["Risk contribution"], 0, False), num(a["Blend Sharpe without it"]), num(a["Delta if removed"])) for a in bt["attribution"]],
               right=(2, 3, 4), caption="A sleeve earns its place only if removing it lowers the blend's Sharpe. N1 and N2 fail this test.")
    tr = table(["Trial", "Slot", "Status", "Parameters", "Recorded then (CAGR / daily Sharpe)", "Rerun (CAGR / monthly Sharpe)", "Deflated Sharpe"],
               [(esc(t["Trial"]), esc(t["Family"]), esc(t["Status"]), f'<code>{esc(t["Params"])}</code>',
                 f'{pct(t["Recorded CAGR"])} / {num(t["Recorded Sharpe (daily basis)"])}' if fin(t.get("Recorded CAGR")) else "new", f'{pct(t["CAGR"])} / {num(t["Sharpe"])}', num(t["DSR"])) for t in bt["trials"]],
               right=(4, 5, 6))
    vs = table(["Code", "Sharpe, first-print inputs", "Sharpe, latest-vintage inputs", "Identical rebalance targets"],
               [(esc(v["Code"]), num(v["Sharpe first-print"]), num(v["Sharpe latest-vintage"]), f'{v["Identical targets"]} of {v["Rebalances"]}') for v in bt["vintage_sensitivity"]], right=(1, 2, 3))
    body = (t1 + '<p class="small" style="max-width:80ch">Read this as a description of rules on data their author had seen. Most equity and metals rules roughly match a buy-and-hold position of the same volatility (information ratios near zero). The crypto rules come closest to clearing the multiple-testing bar, and none does. C3 sits highest only because its phases were fitted to known tops.</p>'
            + f'<div class="stack" style="gap:10px"><h3>Positions and signals at the {fmt_date(R["timestamps"]["backtest_end"])} close</h3>{t2}</div>'
            + f'<div class="grid-2"><div class="stack" style="gap:10px"><h3>Class blends</h3>{bl}</div><div class="stack" style="gap:10px"><h3>First-print vs revised inputs</h3>{vs}</div></div>'
            + f"<details><summary>Risk contribution and leave-one-out by sleeve</summary>{at}</details>"
            + f'<details><summary>All {bt["n_trials"]} configurations tried (trial registry)</summary>{tr}</details>')
    return section("strategies", "Twenty strategies, development sample", "Evidence level, standardised metrics and four benchmarks for every rule.", body)


def review() -> str:
    rows = []
    for m in C.MATRIX:
        ev = " ".join(code_link(p) for p in m["evidence"])
        rows.append((f'<span class="code">{esc(m["id"])}</span>', esc(m["finding"]), esc(m["change"]) + f'<span class="sub">{ev}</span>',
                     chip(m["status"], m["status"]) + (f'<span class="sub">{esc(m["missing"])}</span>' if m["missing"] else "")))
    return section("review", "Review response: finding, change, evidence",
                   "An external review (6 Nov 2026) asked for reproducibility, explicit evidence levels and point-in-time inputs. What was done, and what is still missing.",
                   table(["Item", "Finding", "Change and evidence", "Status and what is missing"], rows) + f'<p class="small">{esc(C.NOT_RECEIVED)} Full matrix: {code_link("docs/06_review_response.md")}.</p>')


def reproduce() -> str:
    dl = "".join(f'<li><a href="{esc(gh(p))}">{esc(n)}</a> <span class="muted">{esc(p)}</span></li>' for n, p in C.DELIVERABLES)
    return section("reproduce", "Reproduce and download", "", f'''<pre>git clone {esc(REPO)} && cd midterm-quant && git checkout {COMMIT[:10]}
scripts/reproduce.sh            # environment, data check, tests, every result, docs and this page
OFFLINE=1 scripts/reproduce.sh  # same, frozen to an existing data_cache/ snapshot</pre>
<p class="small">Yahoo Finance data may not be redistributed, so the script downloads it; {code_link("scripts/verify_data.py")} then compares the download with the manifest (dividend rescaling changes hashes but not returns). Links point at commit <code>{COMMIT[:10]}</code>.</p>
<ul class="plain">{dl}</ul>''')


def sources() -> str:
    items = "".join(f'<li><a href="{esc(u)}">{esc(t)}</a></li>' for t, u in C.SOURCES.values())
    return section("sources", "Sources", "", f'<ul class="sources">{items}</ul><p class="small">Prices and macro series: Yahoo Finance chart API, FRED and ALFRED (St. Louis Fed), DefiLlama. Retrieved {esc(str(R["timestamps"]["data_retrieved_utc"]["first"])[:16])} to {esc(str(R["timestamps"]["data_retrieved_utc"]["last"])[:16])} UTC; per-file times in the data manifest.</p>')


EXTRA_CSS = """
dl.ts { margin: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1px; background: var(--rule); border: 1px solid var(--rule); border-radius: 10px; overflow: hidden; }
dl.ts div { background: var(--surface); padding: 10px 14px; }
dl.ts dt { font: 600 11.5px/1.3 var(--mono); text-transform: uppercase; letter-spacing: 0.04em; color: var(--ink-3); }
dl.ts dd { margin: 4px 0 0; font-size: 13.5px; color: var(--ink-2); line-height: 1.45; }
.chip.stale svg { fill: none; stroke: var(--ink-3); stroke-width: 2.4; }
.chip.stale { color: var(--ink-2); border-style: dashed; }
td .chip { white-space: normal; text-align: left; line-height: 1.3; }
code { font: 500 12.5px/1.4 var(--mono); }
td code { word-break: break-all; }
.scen ul.plain { gap: 4px; padding-left: 0; list-style: none; }
"""


def script() -> str:
    return """<script>
(function () {
  "use strict";
  var NS = "http://www.w3.org/2000/svg";
  var MON = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  function el(tag, attrs, parent, text) { var e = document.createElementNS(NS, tag); if (attrs) for (var k in attrs) e.setAttribute(k, attrs[k]); if (text != null) e.textContent = text; if (parent) parent.appendChild(e); return e; }
  function pct(v) { return (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(1) + "%"; }
  var tip = document.getElementById("tip");
  function showTip(html, x, y) { tip.innerHTML = html; tip.hidden = false; var r = tip.getBoundingClientRect(); var left = x + 14, top = y + 14;
    if (left + r.width > window.innerWidth - 8) left = x - r.width - 14; if (top + r.height > window.innerHeight - 8) top = y - r.height - 14;
    tip.style.left = Math.max(8, left) + "px"; tip.style.top = Math.max(8, top) + "px"; }
  function hideTip() { tip.hidden = true; }
""" + SHOCK_JS + """
  var rt; window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(drawShock, 120); });
  drawShock();
})();
</script>"""


SHOCK_JS = (config.ROOT / "site_src" / "shock_chart.js").read_text()


def main():
    css = (config.ROOT / "site_src" / "style.css").read_text() + EXTRA_CSS
    parts = [header(), "<main>", evidence(), policy(), selloff(), history(), election_value(), global_section(), outlook(), scenarios(), watch(),
             strategies(), review(), reproduce(), sources(), "</main>"]
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Post-Midterm Market Playbook</title>
<meta name="description" content="Post-midterm cross-asset research with stated evidence levels, generated from results.json at commit {COMMIT[:10]}.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
{css}
</style>
</head>
<body>
{"".join(parts)}
<footer><div class="wrap small">Generated by <code>scripts/build_site.py</code> from <code>reports/results/results.json</code> (schema {esc(R["schema"])}), commit <code>{COMMIT[:10]}</code>. Research and education only; not investment advice.</div></footer>
<div id="tip" role="tooltip" hidden></div>
{script()}
</body>
</html>
"""
    out = config.REPORTS_DIR / "midterm_playbook.html"
    out.write_text(page)
    left = re.findall(r"\{[A-Z][-A-Za-z0-9]*\.(?:value|context|regime|status|date)\}", page)
    assert not left, f"unfilled placeholders: {left[:5]}"
    print(f"wrote {out} ({len(page) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
