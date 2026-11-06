"""Write the data manifest: every input file with provenance, hash and status.

Outputs reports/evidence/data_manifest.csv and reports/evidence/data_manifest.json.

Columns: series, kind, description, source, source_url, units, frequency, timestamp convention,
release timing, available_at rule, revisions, license, redistributable, retrieved_at_utc,
vintage_id, sha256, bytes, rows, first_obs, last_obs, age_days (vs BACKTEST_END), status.

``snapshot_id`` (sha256 over the sorted file hashes) identifies the exact data used. Yahoo data
may not be redistributed, so the repository ships this manifest rather than the files; anyone
re-downloading can compare hashes with ``scripts/verify_data.py``. Adjusted ETF closes are
rescaled after every dividend, so a later download can differ in hash while returns agree;
the verifier therefore also compares returns.
"""
import hashlib
import json

import _bootstrap  # noqa: F401
import pandas as pd

from midterm_quant import config
from midterm_quant.data import catalog
from midterm_quant.data.sources import read_meta

KIND_PREFIX = {"yahoo": "", "fred": "fred:", "defillama": "llama:"}


def series_name(kind: str, stem: str) -> str:
    if kind == "defillama":
        return "llama:stablecoins"
    if kind == "fred":
        return f"fred:{stem}"
    meta_file = config.CACHE_DIR / kind / f"{stem}.meta.json"
    if meta_file.exists():
        return json.loads(meta_file.read_text()).get("name", stem)
    return stem.replace("IDX_", "^").replace("_F", "=F")


def main():
    end = pd.Timestamp(config.BACKTEST_END)
    rows = []
    for kind in ("yahoo", "fred", "defillama"):
        for path in sorted((config.CACHE_DIR / kind).glob("*.csv")):
            name = series_name(kind, path.stem)
            m = catalog.meta(name)
            info = read_meta(path)
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            idx = df.index[df.iloc[:, 0].notna()]
            idx_cut = idx[idx <= end]
            last = idx_cut.max() if len(idx_cut) else None
            age = int((end - last).days) if last is not None else None
            status = "MISSING" if last is None else ("STALE" if age > catalog.max_age_days(name) else "OK")
            if name.endswith((".CBT", ".NYM", ".CMX", ".CME")):
                status = status if status != "STALE" else "EXPIRED/INACTIVE CONTRACT"
            gaps = None
            if kind == "yahoo":
                k = catalog._yahoo_kind(name)
                lo = end - pd.Timedelta(days=30)
                have = set(idx[(idx > lo) & (idx <= end)])
                if k == "crypto":
                    expect = set(pd.date_range(lo + pd.Timedelta(days=1), end, freq="D"))
                elif k == "us_listed":
                    spy = pd.read_csv(config.CACHE_DIR / "yahoo" / "SPY.csv", index_col=0, parse_dates=True).index
                    expect = set(spy[(spy > lo) & (spy <= end)])
                else:
                    expect = set()
                missing = sorted(expect - have)
                gaps = ", ".join(d.date().isoformat() for d in missing) if missing else ""
                if missing and status == "OK":
                    status = "GAP"
            rows.append({
                "series": name, "kind": kind, "file": str(path.relative_to(config.ROOT)) if config.CACHE_DIR.is_relative_to(config.ROOT) else path.name,
                **{k: v for k, v in m.as_dict().items() if k != "key"},
                "retrieved_at_utc": info.get("retrieved_at_utc"), "vintage_id": info.get("vintage_id"),
                "sha256": info.get("sha256"), "bytes": info.get("bytes"), "rows": int(len(idx)),
                "first_obs": idx.min().date().isoformat() if len(idx) else None,
                "last_obs_file": idx.max().date().isoformat() if len(idx) else None,
                "last_obs_used": last.date().isoformat() if last is not None else None,
                "age_days_at_cutoff": age, "missing_bars_last_30d": gaps, "status": status,
            })
    alfred = sorted((config.CACHE_DIR / "alfred").glob("*.csv"))
    by_series = {}
    for p in alfred:
        sid, _, vd = p.stem.rpartition("_")
        by_series.setdefault(sid, []).append(vd)
    for sid, vds in sorted(by_series.items()):
        m = catalog.meta(f"fred:{sid}")
        h = hashlib.sha256("".join(read_meta(config.CACHE_DIR / "alfred" / f"{sid}_{v}.csv")["sha256"] for v in sorted(vds)).encode()).hexdigest()
        rows.append({"series": f"alfred:{sid}", "kind": "alfred", "file": f"data_cache/alfred/{sid}_<vintage>.csv",
                     **{k: v for k, v in m.as_dict().items() if k != "key"},
                     "source": f"ALFRED {sid} (archived vintages)", "source_url": f"https://alfred.stlouisfed.org/series?seid={sid}",
                     "retrieved_at_utc": None, "vintage_id": f"{len(vds)} vintages {min(vds)}..{max(vds)}",
                     "sha256": h, "bytes": None, "rows": None, "first_obs": None, "last_obs_file": None, "last_obs_used": None,
                     "age_days_at_cutoff": None, "status": "OK"})
    df = pd.DataFrame(rows)
    snapshot = hashlib.sha256("".join(sorted(str(s) for s in df["sha256"])).encode()).hexdigest()
    out = config.EVIDENCE_DIR
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "data_manifest.csv", index=False)
    (out / "data_manifest.json").write_text(json.dumps({
        "snapshot_id": snapshot, "backtest_end": config.BACKTEST_END, "files": len(df),
        "status_counts": df["status"].value_counts().to_dict(),
        "not_redistributable": int((~df["redistributable"].astype(bool)).sum()),
        "series": df.to_dict(orient="records")}, indent=1, default=str))
    print(f"snapshot {snapshot[:16]}  files {len(df)}  status {df['status'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
