#!/usr/bin/env bash
# One-command reproduction of every result, document and the web page.
#   scripts/reproduce.sh            use the local data cache where fresh, download the rest
#   OFFLINE=1 scripts/reproduce.sh  never download (requires a complete data_cache/)
# Steps: environment -> data (+ALFRED vintages) -> tests with logs -> backtests -> monitor ->
#        research -> manifest + verification -> results.json -> docs -> page -> output hashes.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}
"$PY" -c 'import sys; assert sys.version_info[:2] >= (3, 9), "Python 3.9+ required"'
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/pip install -q -r requirements.lock
mkdir -p reports/evidence reports/results
if [ "${OFFLINE:-0}" = "1" ]; then export MQ_MAX_AGE_HOURS=100000; fi
[ -f reports/evidence/data_manifest.json ] && cp reports/evidence/data_manifest.json reports/evidence/data_manifest.reference.json || true
echo "== vintages and revision audit"; .venv/bin/python scripts/build_vintages.py > reports/evidence/build_vintages.log 2>&1
echo "== tests";      .venv/bin/python -m pytest -v -p no:cacheprovider --junitxml=reports/evidence/pytest-junit.xml 2>&1 | tee reports/evidence/pytest.log | tail -3
echo "== backtests";  .venv/bin/python scripts/run_backtests.py > reports/run_backtests.log 2>&1
echo "== monitor";    .venv/bin/python scripts/run_monitor.py > reports/evidence/run_monitor.log 2>&1
echo "== research";   .venv/bin/python scripts/run_event_study.py > reports/evidence/run_event_study.log 2>&1; .venv/bin/python scripts/run_research.py > reports/evidence/run_research.log 2>&1
echo "== manifest";   .venv/bin/python scripts/build_manifest.py
echo "== verify";     .venv/bin/python scripts/verify_data.py || echo "data differs from the reference snapshot: see above"
echo "== results";    .venv/bin/python scripts/build_results.py
echo "== docs";       .venv/bin/python scripts/build_docs.py
echo "== page";       .venv/bin/python scripts/build_site.py
# strip the absolute checkout path from logs before they are committed
for f in reports/evidence/*.log reports/run_backtests.log; do [ -f "$f" ] && sed -i.bak "s|$(pwd)/|./|g; s|$(pwd)|.|g" "$f" && rm -f "$f.bak"; done
shasum -a 256 reports/evidence/*.csv reports/results/results.json reports/midterm_playbook.html docs/05_specifications.md > reports/evidence/output_hashes.txt
echo "done: compare reports/evidence/output_hashes.txt with the committed copy"
