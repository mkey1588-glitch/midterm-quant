"""Assemble reports/results/results.json: the single artifact the website is generated from.

Reads the component outputs (backtests, monitor, event study, shock study, ablation, global,
reconciliation, scenarios), the evidence files (data manifest, test log, lock file) and the
git state, and adds the market-move table for the cutoff day with an explicit timestamp per
row. Nothing here recomputes research results.

Usage: .venv/bin/python scripts/build_results.py
"""
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET

import _bootstrap  # noqa: F401
import pandas as pd

from midterm_quant import __version__, config
from midterm_quant.data.sources import fetch_fred, fetch_yahoo
from midterm_quant.specs import all_specs
from midterm_quant.research.monitor import SPECS as IND_SPECS

R = config.RESULTS_DIR
E = config.EVIDENCE_DIR

MOVES = [
    ("^GSPC", "S&P 500", "index", "16:00 ET close"),
    ("^NDX", "Nasdaq-100", "index", "16:00 ET close"),
    ("^SOX", "PHLX Semiconductor index", "index", "16:00 ET close"),
    ("RSP", "Equal-weight S&P 500 (RSP)", "price", "16:00 ET close"),
    ("^RUT", "Russell 2000", "index", "16:00 ET close"),
    ("^VIX", "VIX", "vol", "16:15 ET close"),
    ("^TNX", "10-year Treasury yield, CBOE index (^TNX)", "yield", "15:00 CT close of the CBOE index; not FRED DGS10"),
    ("HYG", "High-yield bond ETF (HYG)", "price", "16:00 ET close"),
    ("DX-Y.NYB", "ICE dollar index", "index", "ICE settlement"),
    ("BZ=F", "Brent crude, front month", "usd", "ICE front-month settlement"),
    ("GC=F", "Gold, front month", "usd", "COMEX front-month settlement"),
    ("BTC-USD", "Bitcoin", "usd", "UTC day bar (00:00-24:00 UTC)"),
]


def git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=config.ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return ""


def load(name):
    p = R / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def moves(cutoff: pd.Timestamp) -> list[dict]:
    out = []
    for sym, label, kind, conv in MOVES:
        s = fetch_yahoo(sym)["close"].dropna()
        s = s[s.index <= cutoff]
        last_date = s.index[-1]
        row = {"symbol": sym, "label": label, "kind": kind, "timestamp": f"{last_date.date().isoformat()} {conv}",
               "bar_date": last_date.date().isoformat(), "is_cutoff_day": bool(last_date == cutoff),
               "value": float(s.iloc[-1]), "prev": float(s.iloc[-2]),
               "day_change": float(s.iloc[-1] / s.iloc[-2] - 1), "from_52w_high": float(s.iloc[-1] / s.iloc[-252:].max() - 1)}
        if kind in ("yield", "vol"):
            row["day_change_points"] = float(s.iloc[-1] - s.iloc[-2])
        out.append(row)
    d = fetch_fred("DGS10")
    d = d[d.index <= cutoff]
    out.insert(7, {"symbol": "fred:DGS10", "label": "10-year Treasury yield, FRED DGS10", "kind": "yield",
                   "timestamp": f"{d.index[-1].date().isoformat()} H.15 daily value (the {cutoff.date()} value is published the next business day)",
                   "bar_date": d.index[-1].date().isoformat(), "is_cutoff_day": bool(d.index[-1] == cutoff),
                   "value": float(d.iloc[-1]), "prev": float(d.iloc[-2]), "day_change": None,
                   "day_change_points": float(d.iloc[-1] - d.iloc[-2]), "from_52w_high": None})
    return out


def tests_summary() -> dict:
    p = E / "pytest-junit.xml"
    if not p.exists():
        return {"status": "no test log in this build"}
    root = ET.parse(p).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    return {"tests": int(suite.get("tests")), "failures": int(suite.get("failures")), "errors": int(suite.get("errors")),
            "skipped": int(suite.get("skipped", 0)), "time_s": float(suite.get("time")), "timestamp": suite.get("timestamp"),
            "log": "reports/evidence/pytest.log", "junit": "reports/evidence/pytest-junit.xml"}


def sha_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main():
    cutoff = pd.Timestamp(config.BACKTEST_END)
    bt = load("backtests")
    mon = load("monitor")
    manifest = json.loads((E / "data_manifest.json").read_text()) if (E / "data_manifest.json").exists() else {}
    ser = pd.DataFrame(manifest.get("series", []))
    retrieved = ser["retrieved_at_utc"].dropna() if len(ser) else pd.Series(dtype=str)
    readings = mon["readings"] if mon else []
    ok = [r for r in readings if r["status"] == "OK"]
    fred_obs = {r["code"]: r["observation_date"] for r in readings if r["code"] in ("M2", "M5", "M6", "M9", "M11")}
    head = git("rev-parse", "HEAD")
    dirty = bool(git("status", "--porcelain", "--untracked-files=no"))
    results = {
        "schema": "midterm-quant/results@2",
        "title": "Post-Midterm Market Playbook",
        "package_version": __version__,
        "timestamps": {
            "page_generated_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
            "market_data_cutoff": f"{cutoff.date()} U.S. close (16:00 ET); crypto: last completed UTC day bar on or before {cutoff.date()}",
            "data_retrieved_utc": {"first": retrieved.min() if len(retrieved) else None, "last": retrieved.max() if len(retrieved) else None},
            "indicator_observation_dates": {"earliest": min((r["observation_date"] for r in readings if r["observation_date"]), default=None),
                                            "latest": max((r["observation_date"] for r in readings if r["observation_date"]), default=None),
                                            "fred_examples": fred_obs},
            "backtest_end": config.BACKTEST_END,
            "standardised_metrics_through": "last complete month before the backtest end",
            "freeze_date": config.FREEZE_DATE, "prospective_start": config.PROSPECTIVE_START,
        },
        "code": {"commit": head, "dirty_tracked_files": dirty, "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
                 "repository": "https://github.com/mkey1588-glitch/midterm-quant",
                 "python": platform.python_version(), "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
                 "lockfile_sha256": sha_file(config.ROOT / "requirements.lock")},
        "evidence": {
            "tests": tests_summary(),
            "data_snapshot_id": manifest.get("snapshot_id"), "data_files": manifest.get("files"),
            "data_status_counts": manifest.get("status_counts"), "not_redistributable_files": manifest.get("not_redistributable"),
            "reconciliation": load("reconciliation"),
            "lean": {"status": "not run", "reason": "no Docker and no .NET SDK on the research machine; LEAN CLI also needs a QuantConnect organisation on a paid tier", "ports": ["lean/E1_midterm_trend/main.py", "lean/C1_crypto_trend/main.py"]},
            "trial_counts": {"strategy_configurations": bt["n_trials"] if bt else None,
                             "ablation_model_configurations": (load("ablation") or {}).get("n_trials"),
                             "shock_study_definitions": 12, "note": "Descriptive variants (shock-study grid and post-hoc cuts) are all reported; none was selected."},
            "holdout": {"exists": False, "reason": "All history through the backtest end was used during development.",
                        "prospective_start": config.PROSPECTIVE_START, "plan": "docs/07_validation_plan.md"},
            "independent_verification": "not yet: the test log and ledgers are self-produced; a third-party run of scripts/reproduce.sh is the missing step",
        },
        "market_moves": moves(cutoff),
        "monitor": mon,
        "monitor_summary": {"total": len(readings), "ok": len(ok),
                            "alert": sum(1 for r in ok if r["tone"] == "alert"),
                            "stale": sum(1 for r in readings if r["status"] == "STALE"),
                            "missing": sum(1 for r in readings if r["status"] == "MISSING")},
        "indicator_specs": {c: {k: v for k, v in s.__dict__.items() if k != "tones"} for c, s in IND_SPECS.items()},
        "strategy_specs": all_specs(),
        "backtests": bt,
        "event_study": load("event_study"), "shock_study": load("shock_study"), "ablation": load("ablation"),
        "global": load("global"), "scenarios": load("scenarios"),
        "data_manifest_summary": ser[["series", "kind", "units", "frequency", "release", "available_rule", "revisions",
                                      "redistributable", "retrieved_at_utc", "last_obs_used", "age_days_at_cutoff", "status",
                                      "source_url"]].to_dict(orient="records") if len(ser) else [],
    }
    R.mkdir(parents=True, exist_ok=True)
    (R / "results.json").write_text(json.dumps(results, indent=1, default=str))
    print(f"wrote {R / 'results.json'} ({(R / 'results.json').stat().st_size / 1e6:.1f} MB); commit {head[:10]} dirty={dirty}")


if __name__ == "__main__":
    sys.exit(main())
