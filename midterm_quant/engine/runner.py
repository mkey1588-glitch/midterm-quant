"""Build a Backtrader Cerebro for a strategy class, run it, and package the results."""
from __future__ import annotations

from dataclasses import dataclass, field

import backtrader as bt
import pandas as pd

from midterm_quant import config
from midterm_quant.data.align import Panel, build_panel
from midterm_quant.engine.base import FractionalPercentCommission, TargetWeightStrategy
from midterm_quant.engine.metrics import perf_stats

CASH_RATE = "fred:DTB3"


@dataclass
class BacktestResult:
    code: str
    name: str
    asset_class: str
    benchmark: str
    equity: pd.Series
    bench: pd.Series
    exposure: pd.DataFrame
    metrics: dict
    bench_metrics: dict
    last_target: dict
    last_rebalance: str
    turnover_per_year: float
    n_orders: int
    rejected: int
    rebalances: list = field(repr=False, default_factory=list)
    ledger: dict = field(repr=False, default_factory=dict)   # nav, positions, targets, orders
    version: str = "v1"
    evidence: str = "D1"
    signal_now: dict | None = None      # model target on the final bar (None target = "hold")
    input_last: dict = field(default_factory=dict)   # series -> last date with a real value
    rf: pd.Series | None = field(repr=False, default=None)

    def summary_row(self) -> dict:
        m, b = self.metrics, self.bench_metrics
        return {
            "Code": self.code,
            "Strategy": self.name,
            "Class": self.asset_class,
            "Start": m.get("Start"),
            "CAGR": m.get("CAGR"),
            "Vol": m.get("Vol"),
            "Sharpe": m.get("Sharpe"),
            "MaxDD": m.get("MaxDD"),
            "Calmar": m.get("Calmar"),
            "WorstYear": m.get("WorstYear"),
            "AvgGross": float(self.exposure["gross"].mean()),
            "Turnover/yr": self.turnover_per_year,
            "Bench": self.benchmark,
            "Bench CAGR": b.get("CAGR"),
            "Bench Sharpe": b.get("Sharpe"),
            "Bench MaxDD": b.get("MaxDD"),
        }


def required_series(cls: type[TargetWeightStrategy]) -> list[str]:
    return list(dict.fromkeys(list(cls.ASSETS) + list(cls.SIGNALS) + [CASH_RATE, cls.BENCHMARK]))


def load_panel_for(cls: type[TargetWeightStrategy], start=None, end=None, vintages: bool = True) -> Panel:
    start = pd.Timestamp(start or cls.START)
    end = end or config.BACKTEST_END
    lead = int(cls.WARMUP * (1.05 if cls.CALENDAR == "crypto" else 1.5)) + 15
    return build_panel(required_series(cls), cls.CALENDAR, start - pd.Timedelta(days=lead), end, vintages=vintages)


def run_backtest(
    cls: type[TargetWeightStrategy],
    start=None,
    end=None,
    cash: float = 1_000_000.0,
    panel: Panel | None = None,
    vintages: bool = True,
    **params,
) -> BacktestResult:
    start = pd.Timestamp(start or cls.START)
    end = end or config.BACKTEST_END
    panel = panel or load_panel_for(cls, start, end, vintages=vintages)
    names = required_series(cls)

    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.setcash(cash)
    cerebro.broker.set_checksubmit(False)
    for name in names:
        cerebro.adddata(bt.feeds.PandasData(dataname=panel.frames[name], openinterest=None), name=name)
        if name in cls.ASSETS:
            cerebro.broker.addcommissioninfo(
                FractionalPercentCommission(commission=config.cost_bps(name) / 1e4), name=name
            )
    inception_idx = {n: int(panel.calendar.get_loc(panel.inception[n])) for n in names}
    cerebro.addstrategy(cls, inception=inception_idx, trade_start=start.date(), **params)
    strat: TargetWeightStrategy = cerebro.run(runonce=False, preload=True)[0]

    rec = pd.DataFrame(strat.records, columns=["date", "value", "cash", "gross", "net",
                                               "interest_cum", "commission_cum", "borrow_cum"])
    rec["date"] = pd.to_datetime(rec["date"])
    rec = rec.set_index("date")
    first_bar = max(start, panel.calendar[min(cls.WARMUP - 1, len(panel.calendar) - 1)])
    rec = rec[rec.index >= first_bar]
    pos = pd.DataFrame({pd.Timestamp(d): w for d, w in strat.pos_log}).T.reindex(columns=list(cls.ASSETS)).fillna(0.0)
    pos = pos[pos.index >= first_bar]
    targets = pd.DataFrame([{"date": d.isoformat(), "asset": a, "target_weight": w}
                            for d, t in strat.rebalances for a, w in (t.items() or [("CASH", 1.0)])])
    orders = pd.DataFrame(strat.orders_log)
    equity = rec["value"] / rec["value"].iloc[0]
    bench = panel.close(cls.BENCHMARK).reindex(rec.index)
    bench = bench / bench.iloc[0]
    rf = panel.close(CASH_RATE)
    periods = 365 if cls.CALENDAR == "crypto" else 252
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-9)

    return BacktestResult(
        code=cls.CODE,
        name=cls.NAME,
        asset_class=cls.ASSET_CLASS,
        benchmark=cls.BENCHMARK,
        equity=equity,
        bench=bench,
        exposure=rec[["gross", "net"]],
        metrics=perf_stats(equity, periods, rf),
        bench_metrics=perf_stats(bench, periods, rf),
        last_target=strat.last_target,
        last_rebalance=strat.rebalances[-1][0].isoformat() if strat.rebalances else "",
        turnover_per_year=strat.turnover / years,
        n_orders=strat.n_orders,
        rejected=strat.rejected,
        rebalances=strat.rebalances,
        ledger={"nav": rec, "positions": pos, "targets": targets, "orders": orders, "cash0": cash},
        version=getattr(cls, "VERSION", "v1"),
        evidence=getattr(cls, "EVIDENCE", "D1"),
        signal_now=strat.signal_now,
        input_last={n: (panel.last_real.get(n).date().isoformat() if panel.last_real.get(n) is not None else None) for n in names},
        rf=rf,
    )
