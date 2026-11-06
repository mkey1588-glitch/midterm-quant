"""Print and save the post-midterm observation dashboard (reports/monitor.md)."""
import _bootstrap  # noqa: F401
import datetime as dt

from midterm_quant import config
from midterm_quant.research.monitor import read_all


def main():
    rows = read_all()
    lines = [f"# Observation dashboard ({dt.date.today().isoformat()})", "",
             "| Group | Code | Indicator | Value | Context | Read | Rule |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r.group} | {r.code} | {r.name} | {r.value} | {r.context} | **{r.regime}** | {r.watch} |")
        print(f"{r.code:5s} {r.name[:44]:44s} {r.value:>16s}  {r.context[:46]:46s} {r.regime}")
    config.REPORTS_DIR.mkdir(exist_ok=True)
    (config.REPORTS_DIR / "monitor.md").write_text("\n".join(lines) + "\n")
    print("wrote reports/monitor.md")


if __name__ == "__main__":
    main()
