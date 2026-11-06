"""Post-midterm (2026) cross-asset quantitative research and strategy library.

Layers:
    data/        free data sources with provenance, a data dictionary, ALFRED vintages, point-in-time alignment
    indicators   pure numpy indicator functions (unit tested, framework-agnostic)
    engine/      Backtrader integration: target-weight base strategy, runner, metrics
    strategies/  20 strategies: 5 each for US equities, crypto, energy, precious metals
    research/    midterm event study and the 2-year observation-indicator monitor
"""
__version__ = "0.2.0"
