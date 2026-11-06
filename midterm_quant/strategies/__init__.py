"""Strategy registry: 5 strategies per asset class (20 total).

``REJECTED`` holds first specifications that failed their backtest and were replaced;
they stay runnable so the research log is reproducible.
"""
from midterm_quant.strategies import crypto, energy, equities, metals

ALL = equities.STRATEGIES + crypto.STRATEGIES + energy.STRATEGIES + metals.STRATEGIES
BY_CODE = {cls.CODE: cls for cls in ALL}
REJECTED = crypto.REJECTED + metals.REJECTED

assert len(ALL) == 20 and len(BY_CODE) == 20
