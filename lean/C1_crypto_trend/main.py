# LEAN port of C1 (BTC/ETH multi-horizon trend + 60% vol target). STATUS: written, NOT RUN.
# Data: Yahoo BTC-USD/ETH-USD UTC daily bars are not available inside LEAN; use a licensed
# exchange feed (e.g. Coinbase via the QuantConnect data library) and expect small differences.
# 15 bp one-way proportional cost; weekly decisions on UTC-day closes; fills at the next open.
from AlgorithmImports import *
import numpy as np


class ProportionalFee(FeeModel):
    def __init__(self, bps):
        self.rate = bps / 1e4

    def get_order_fee(self, parameters):
        o = parameters.order
        return OrderFee(CashAmount(abs(o.quantity) * parameters.security.price * self.rate, "USD"))


class C1CryptoTrend(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2015, 6, 1)
        self.set_end_date(2026, 11, 5)
        self.set_account_currency("USD")
        self.set_cash(1_000_000)
        self.set_brokerage_model(BrokerageName.COINBASE, AccountType.CASH)
        self.coins = [self.add_crypto(t, Resolution.DAILY, Market.COINBASE).symbol for t in ("BTCUSD", "ETHUSD")]
        for s in self.coins:
            self.securities[s].set_fee_model(ProportionalFee(15.0))
        self.last_week = None

    def on_data(self, data):
        wk = self.time.isocalendar()[:2]
        if wk == self.last_week:
            return
        hist = self.history(self.coins, 125, Resolution.DAILY)
        live = [s for s in self.coins if s in hist.index.get_level_values(0) and len(hist.loc[s]) >= 125]
        if not live:
            return
        self.last_week = wk
        value = self.portfolio.total_portfolio_value
        for s in live:
            px = hist.loc[s]["close"].to_numpy()
            score = np.mean([px[-1] / px[-1 - n] - 1 > 0 for n in (20, 60, 120)])
            lr = np.diff(np.log(px[-31:]))
            rv = np.std(lr, ddof=1) * np.sqrt(365)
            w = score * min(1.0, 0.6 / rv) / len(live) if rv > 0 else 0.0
            cur = self.portfolio[s].holdings_value / value
            if abs(w - cur) >= 0.02 or (w == 0 and self.portfolio[s].invested):
                self.market_order(s, (w - cur) * value / self.securities[s].price)
