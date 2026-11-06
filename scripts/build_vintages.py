"""Download ALFRED vintages, build first-print series and audit revisions.

Writes reports/evidence/revision_audit.csv and reports/evidence/first_print_coverage.csv.
Vintage files are cached forever under data_cache/alfred/ (they never change).
"""
import _bootstrap  # noqa: F401
import pandas as pd

from midterm_quant import config
from midterm_quant.data import catalog
from midterm_quant.data.vintages import first_print, first_vintage, revision_audit

STRATEGY_FRED = ["DTWEXBGS", "THREEFYTP10", "USEPUINDXD", "WALCL", "WDTGAL", "WTREGEN", "RRPONTSYD",
                 "GASREGW", "DFII10", "DTB3"]
AUDIT_DATES = ["2016-01-04", "2020-01-02", "2023-01-03", "2025-01-02", "2026-06-01"]


def main():
    out = config.EVIDENCE_DIR
    out.mkdir(parents=True, exist_ok=True)
    audits = [revision_audit(sid, AUDIT_DATES) for sid in STRATEGY_FRED]
    audit = pd.concat(audits, ignore_index=True)
    audit.to_csv(out / "revision_audit.csv", index=False, float_format="%.6g")
    print(audit.to_string())
    cov = []
    for sid in STRATEGY_FRED:
        if catalog.meta(f"fred:{sid}").revisions != "material":
            continue
        fp = first_print(sid)
        fv = first_vintage(sid)
        if fp is None:
            cov.append({"series": sid, "first_vintage": fv, "rows": 0})
            continue
        cov.append({"series": sid, "first_vintage": fv, "rows": len(fp),
                    "pre_archive_rows": int(fp["pre_archive"].sum()),
                    "first_print_rows": int((~fp["pre_archive"]).sum()),
                    "vintages_used": int(fp["vintage"].nunique()),
                    "first_obs": fp.index.min().date().isoformat(), "last_obs": fp.index.max().date().isoformat()})
    cov = pd.DataFrame(cov)
    cov.to_csv(out / "first_print_coverage.csv", index=False)
    print(cov.to_string())


if __name__ == "__main__":
    main()
