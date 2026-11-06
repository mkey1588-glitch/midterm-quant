"""Backtrader integration: a target-weight strategy base class.

Every strategy in this library is a ``TargetWeightStrategy`` subclass that implements one
method, ``target_weights() -> {asset: weight}``, evaluated at the close of a bar. The base
class turns weights into orders that Backtrader fills at the *next bar's open* with
per-asset transaction costs, short-borrow fees and T-bill interest on idle cash.

Because the decision only sees Backtrader line history up to the current bar, signals
are causal by construction (there is no vectorised look-ahead to get wrong).
"""
from __future__ import annotations

import datetime as dt
import math

import backtrader as bt
import numpy as np

from midterm_quant import config


class FractionalPercentCommission(bt.CommInfoBase):
    """Percentage commission, fractional sizes (needed for BTC at $80k), borrow fee on shorts."""

    params = (
        ("stocklike", True),
        ("commtype", bt.CommInfoBase.COMM_PERC),
        ("percabs", True),
        ("commission", 0.0002),
        ("interest", config.SHORT_BORROW_RATE),
        ("interest_long", False),
    )

    def getsize(self, price, cash):
        return self.p.leverage * (cash / price)


class TargetWeightStrategy(bt.Strategy):
    # ---- declarative metadata (override in subclasses) -------------------------
    CODE = "X0"
    NAME = "base"
    ASSET_CLASS = ""
    ASSETS: tuple = ()          # tradeable instruments
    SIGNALS: tuple = ()         # signal-only series (Yahoo symbols or "fred:<id>")
    CALENDAR = "nyse"           # "nyse" (SPY trading days) or "crypto" (every day)
    BENCHMARK = "SPY"
    START = "2005-01-01"        # first date trading is allowed (after WARMUP bars)
    REBALANCE = "M"             # D | W | M  -- target_weights() is called on these bars
    WARMUP = 252                # bars of history required before the first decision
    MAX_GROSS = 1.0             # sum |w|
    MAX_LONG = 0.98             # sum of long weights (cash buffer for overnight gaps)
    THESIS = ""                 # one-line link to the midterm analysis

    params = (
        ("inception", None),     # {name: bar index of first real observation} (runner)
        ("trade_start", None),   # datetime.date; no orders before it
        ("min_trade", 0.02),     # ignore weight changes smaller than this
        ("cash_rate", "fred:DTB3"),
    )

    # ---- lifecycle ---------------------------------------------------------------
    def __init__(self):
        self._by_name = {d._name: d for d in self.datas}
        self._tradeables = [self._by_name[n] for n in self.ASSETS]
        self._last_period = None
        self.periods = 365 if self.CALENDAR == "crypto" else 252
        self.records = []            # (date, value, gross, net)
        self.rebalances = []         # (date, target dict)
        self.last_target: dict = {}
        self.turnover = 0.0          # sum of |filled notional| / equity
        self.n_orders = 0            # filled orders
        self.rejected = 0
        self.state: dict = {}        # free-form per-strategy state (entries, timers ...)
        self._target: dict = {}
        self._retry = False
        self._started = False        # first eligible bar always rebalances

    def notify_order(self, order):
        if order.status == order.Completed:
            value = self.broker.getvalue()
            if value > 0:
                self.turnover += abs(order.executed.size * order.executed.price) / value
            self.n_orders += 1
        elif order.status in (order.Margin, order.Rejected):
            # A buy can bounce when the next open gaps above the close used for sizing;
            # re-run the same target on the next bar (sells have filled by then).
            self.rejected += 1
            if order.isbuy():
                self._retry = True

    def next(self):
        self._accrue_cash_yield()
        value = self.broker.getvalue()
        gross = net = 0.0
        for d in self._tradeables:
            pos = self.getposition(d).size
            if pos:
                exp = pos * d.close[0] / value
                gross += abs(exp)
                net += exp
        self.records.append((self.today, value, gross, net))

        new_period = self._is_new_period()
        if len(self) < self.WARMUP:
            return
        if self.p.trade_start is not None and self.today < self.p.trade_start:
            return
        if not new_period and self._started:
            if self._retry:
                self._retry = False
                self.rebalance(self._target, record=False)
            return
        self._retry = False
        self._started = True
        target = self.target_weights()
        if target is not None:
            self.rebalance(target)

    # ---- to implement ----------------------------------------------------------
    def target_weights(self) -> dict | None:
        """Return {asset: weight} (fractions of equity; negative = short) or None to hold."""
        raise NotImplementedError

    # ---- data helpers ------------------------------------------------------------
    @property
    def today(self) -> dt.date:
        return self.datas[0].datetime.date(0)

    def series(self, name: str, n: int, field: str = "close") -> np.ndarray:
        """Last ``n`` values (oldest first, current bar last)."""
        line = getattr(self._by_name[name], field)
        n = min(int(n), len(line))
        return np.asarray(line.get(size=n), dtype=float)

    def last(self, name: str, field: str = "close") -> float:
        return float(getattr(self._by_name[name], field)[0])

    def available(self, name: str, lookback: int = 0) -> bool:
        """True once ``name`` has at least ``lookback`` real bars of history."""
        inc = (self.p.inception or {}).get(name)
        if inc is None:
            return True
        return (len(self) - 1 - inc) >= lookback

    def weight(self, name: str) -> float:
        d = self._by_name[name]
        value = self.broker.getvalue()
        return self.getposition(d).size * d.close[0] / value if value > 0 else 0.0

    # ---- mechanics ---------------------------------------------------------------
    def _is_new_period(self) -> bool:
        d = self.today
        if self.REBALANCE == "D":
            key = d
        elif self.REBALANCE == "W":
            key = d.isocalendar()[:2]
        elif self.REBALANCE == "M":
            key = (d.year, d.month)
        else:
            raise ValueError(self.REBALANCE)
        if key != self._last_period:
            self._last_period = key
            return True
        return False

    def _accrue_cash_yield(self):
        name = self.p.cash_rate
        if not name or name not in self._by_name:
            return
        rate = self.last(name) / 100.0
        if not math.isfinite(rate) or rate <= 0:
            return
        short_proceeds = sum(
            -self.getposition(d).size * d.close[0] for d in self._tradeables if self.getposition(d).size < 0
        )
        idle = self.broker.getcash() - short_proceeds
        if idle > 0:
            self.broker.add_cash(idle * rate / self.periods)

    def _sanitize(self, target: dict) -> dict:
        w = {k: float(v) for k, v in target.items() if k in self.ASSETS and v is not None and math.isfinite(v)}
        longs = sum(v for v in w.values() if v > 0)
        if longs > self.MAX_LONG:
            w = {k: (v * self.MAX_LONG / longs if v > 0 else v) for k, v in w.items()}
        gross = sum(abs(v) for v in w.values())
        if gross > self.MAX_GROSS:
            w = {k: v * self.MAX_GROSS / gross for k, v in w.items()}
        return w

    def rebalance(self, target: dict, record: bool = True):
        target = self._sanitize(target)
        self._target = target
        value = self.broker.getvalue()
        if value <= 0:
            return
        legs = []
        for d in self._tradeables:
            name = d._name
            price = d.close[0]
            pos = self.getposition(d).size
            cur = pos * price / value
            tgt = target.get(name, 0.0)
            delta = tgt - cur
            closing = tgt == 0.0 and pos != 0
            if abs(delta) < self.p.min_trade and not closing:
                continue
            legs.append((delta, d, -pos if closing else delta * value / price))
        legs.sort(key=lambda leg: leg[0])  # reduce/sell legs first to free cash
        for delta, d, size in legs:
            if size > 0:
                self.buy(data=d, size=size)
            elif size < 0:
                self.sell(data=d, size=-size)
        if record:
            self.last_target = {k: round(v, 4) for k, v in target.items() if abs(v) > 1e-9}
            self.rebalances.append((self.today, dict(self.last_target)))
