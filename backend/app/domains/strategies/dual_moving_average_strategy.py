"""
Dual Moving Average Strategy

A simple strategy that uses two moving averages (short and long) to generate signals
"""

from typing import Dict, Any, List
import pandas as pd
import backtrader as bt
import asyncio

from app.domains.strategies.base_strategy import BaseStrategy
from app.domains.strategies.daily_data_group import DailyDataGroup
from app.core.logging import get_logger

logger = get_logger(__name__)


class DualMovingAverageStrategy(BaseStrategy):
    """
    Dual Moving Average implementation
    """

    def __init__(self):
        self.short_period = 5
        self.long_period = 20
        super().__init__()

    @classmethod
    def get_data_group_configs(cls) -> List[Dict[str, Any]]:
        """Get data gorup configurations without instantiating the strategy"""
        return [
            {
                "name": "daily",
                "type": "DailyDataGroup",
                "weight": 1.0,
                "factors": [
                    {
                        "name": "MA",
                        "type": "technical",
                        "params": {"period": 5, "column": "close"},
                    },
                    {
                        "name": "MA",
                        "type": "technical",
                        "params": {"period": 20, "column": "close"},
                    },
                ],
            }
        ]

    def _init_data_groups(self):
        """Initialize data groups with moving average factors"""
        daily_group = DailyDataGroup(
            name="daily",
            weight=1.0,
            factors=[
                {
                    "name": "MA",
                    "type": "technical",
                    "params": {"period": self.short_period, "column": "close"},
                },
                {
                    "name": "MA",
                    "type": "technical",
                    "params": {"period": self.long_period, "column": "close"},
                },
            ],
        )
        self.data_groups = [daily_group]

    def _generate_signals(
        self, group_data: Dict[str, bt.feeds.DataBase], current_date: pd.Timestamp
    ) -> List[Dict[str, Any]]:
        """Generate trading signals based on MA crossovers"""
        signals = []
        daily_data = group_data.get("daily")

        if daily_data is None:
            return signals

        if len(daily_data) < self.long_period:
            return signals

        current_price = daily_data.close[0]

        short_ma_name = f"MA_{self.short_period}_SMA"
        long_ma_name = f"MA_{self.long_period}_SMA"

        try:
            short_ma_value = None
            long_ma_value = None

            if hasattr(daily_data, "_factor_cols"):
                short_ma_idx = daily_data._factor_cols.get(short_ma_name)
                long_ma_idx = daily_data._factor_cols.get(long_ma_name)

                if short_ma_idx is not None:
                    short_ma_value = daily_data.lines[short_ma_idx]
                if long_ma_idx is not None:
                    long_ma_value = daily_data.lines[long_ma_idx]

            if short_ma_value is not None and long_ma_value is not None:
                short_ma_current = short_ma_value[0]
                long_ma_current = long_ma_value[0]

                if len(daily_data) > self.long_period:
                    short_ma_prev = short_ma_value[-1]
                    long_ma_prev = long_ma_value[-1]

                    if (
                        short_ma_prev <= long_ma_prev
                        and short_ma_current > long_ma_current
                    ):

                        ma_distance = abs(short_ma_current - long_ma_current)

                        confidence = min(ma_distance / long_ma_current, 1.0)

                        signals.append(
                            {
                                "action": "buy",
                                "symbol": self.symbol,
                                "price": current_price,
                                "confidence": confidence,
                                "reason": f"Golden cross: MA{self.short_period} crossed above MA{self.long_period}",
                            }
                        )

                    elif (
                        short_ma_prev >= long_ma_prev
                        and short_ma_current < long_ma_current
                    ):

                        ma_distance = abs(short_ma_current - long_ma_current)

                        confidence = min(ma_distance / long_ma_current, 1.0)

                        signals.append(
                            {
                                "action": "sell",
                                "symbol": self.symbol,
                                "price": current_price,
                                "confidence": confidence,
                                "reason": f"Death cross: MA{self.short_period} crossed below MA{self.long_period}",
                            }
                        )

        except Exception as e:
            logger.warning(f"Error accessing factor columns: {e}")

        return signals

    def _execute_trades(
        self, signals: List[Dict[str, Any]], current_date: pd.Timestamp
    ):
        """Execute trades based on signals using Backtrader's order methods"""
        for signal in signals:
            action = signal.get("action")
            symbol = signal.get("symbol", self.symbol)
            price = signal.get("price")

            if action == "buy":
                if not self.position:
                    size = int(self.broker.getcash() / price * 0.95)
                    if size > 0:
                        self.buy(size=size)
                        logger.info(
                            f"Buy order: {size} shares of {symbol} at {price:.2f} on {current_date}"
                        )

                        asyncio.create_task(
                            self._push_signal_if_needed(
                                {
                                    "action": "buy",
                                    "symbol": symbol,
                                    "price": price,
                                    "quantity": size,
                                    "timestamp": current_date,
                                    "reason": signal.get("reason", ""),
                                }
                            )
                        )
