"""
Strategy enums
"""

from enum import Enum


class TradingMode(str, Enum):
    """Trading mode enum"""

    BACKTEST = "backtest"
    PAPER_TRADING = "paper_trading"
    LIVE_TRADING = "live_trading"
