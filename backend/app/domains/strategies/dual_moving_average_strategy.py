import pandas as pd
from typing import Dict, Any, Optional, List
from app.domains.strategies.base_strategy import BaseStrategy
from app.domains.strategies.daily_data_group import DailyDataGroup
from app.domains.factors.technical import MovingAverageFactor
from app.core.logging import get_logger

logger = get_logger(__name__)


class DualMovingAverageStrategy(BaseStrategy):
    """Dual Moving Average Strategy using DataGroup architecture"""

    def _init_data_groups(self):
        """Initialize data groups for this strategy"""
        daily_group = DailyDataGroup(
            name="daily_ma5_ma20",
            weight=1.0,
            factors=[
                {
                    "name": "ma_5",
                    "class": MovingAverageFactor,
                    "params": {"period": 5, "ma_type": "SMA"},
                },
                {
                    "name": "ma_20",
                    "class": MovingAverageFactor,
                    "params": {"period": 20, "ma_type": "SMA"},
                },
            ],
        )
        self.data_groups = [daily_group]

        for group in self.data_groups:
            group.set_services(self.data_service, self.factor_service)

    def _generate_signals(
        self, group_data_with_factors: Dict[str, pd.DataFrame]
    ) -> List[Dict[str, Any]]:
        """Generate signals based on all group data and factors"""
        signals = []

        for group in self.data_groups:
            data = group_data_with_factors[group.name]
            if data.empty:
                continue

            current_data = data.iloc[0]

            if "ma_5" not in data.columns or "ma_20" not in data.columns:
                logger.warning(
                    f"Missing MA columns for group {group.name}, skipping signal generation"
                )
                continue

            ma_5 = current_data["ma_5"]
            ma_20 = current_data["ma_20"]
            close_price = current_data["close"]

            signal = None
            if ma_5 > ma_20:
                signal = {
                    "action": "buy",
                    "target_price": close_price,
                    "strength": (ma_5 - ma_20) / ma_20,
                    "group_name": group.name,
                    "group_type": group.__class__.__name__,
                    "weight": group.weight,
                }
            elif ma_5 < ma_20:
                signal = {
                    "action": "sell",
                    "target_price": close_price,
                    "strength": (ma_20 - ma_5) / ma_20,
                    "group_name": group.name,
                    "group_type": group.__class__.__name__,
                    "weight": group.weight,
                }

            if signal:
                signals.append(signal)

    def _execute_trades(self, signals: List[Dict[str, Any]]):
        """Execute trades based on signals"""
        if not signals:
            return

        for signal in signals:
            if signal["action"] == "buy":
                logger.info(
                    f"Buy signal: {signal['group_name']} at {signal['target_price']}"
                )
            elif signal["action"] == "sell":
                logger.info(
                    f"Sell signal: {signal['group_name']} at {signal['target_price']}"
                )
