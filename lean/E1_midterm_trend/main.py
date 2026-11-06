# LEAN port of E1 (midterm-cycle seasonal + 200-day trend). STATUS: written, NOT RUN.
# No Docker or .NET on the research machine, so this file has never executed. Reconcile it
# against reports/evidence/ledgers/E1/ with scripts/reconcile_lean.py before trusting it.
#
# Mapping of the Backtrader conventions (engine/base.py):
#   decide at the daily close of bar t       -> scheduled event after market close
#   fill at the next open                    -> MarketOnOpenOrder for the next session
#   2 bp one-way cost                        -> ConstantFeeModel is not proportional; use a custom fee model
#   T-bill interest on idle cash             -> not modelled by LEAN cash book; add as a daily cash adjustment
#   weekly rebalance on the first bar of an ISO week; 2pp minimum trade; 98% max long
from AlgorithmImports import *


class ProportionalFee(FeeModel):
    def __init__(self, bps):
        self.rate = bps / 1e4

    def get_order_fee(self, parameters):
        o = parameters.order
        return OrderFee(CashAmount(abs(o.quantity) * parameters.security.price * self.rate, "USD"))


class E1MidtermTrend(QCAlgorithm):
    def initialize(self):
        self.set_start_date(1994, 1, 3)
        self.set_end_date(2026, 11, 5)
        self.set_cash(1_000_000)
        self.spy = self.add_equity("SPY", Resolution.DAILY, data_normalization_mode=DataNormalizationMode.TOTAL_RETURN).symbol
        self.securities[self.spy].set_fee_model(ProportionalFee(2.0))
        self.sma = self.sma(self.spy, 200, Resolution.DAILY)
        self.set_warm_up(210, Resolution.DAILY)
        self.last_week = None
        self.schedule.on(self.date_rules.every_day(self.spy), self.time_rules.before_market_close(self.spy, 0), self.decide)

    def sweet(self, d):
        return (d.year % 4 == 2 and d.month >= 10) or d.year % 4 == 3

    def decide(self):
        if self.is_warming_up or not self.sma.is_ready:
            return
        wk = self.time.isocalendar()[:2]
        if wk == self.last_week:
            return
        self.last_week = wk
        up = self.securities[self.spy].price > self.sma.current.value
        w = (1.0 if up else 0.6) if self.sweet(self.time) else (0.7 if up else 0.3)
        w = min(w, 0.98)
        value = self.portfolio.total_portfolio_value
        cur = self.portfolio[self.spy].holdings_value / value
        if abs(w - cur) < 0.02:
            return
        qty = (w - cur) * value / self.securities[self.spy].price
        self.market_on_open_order(self.spy, qty)
