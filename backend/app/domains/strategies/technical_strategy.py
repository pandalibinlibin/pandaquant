from typing import Dict, Any, Optional
import backtrader as bt
from .base_strategy import BaseStrategy


class DualMovingAverageStrategy(BaseStrategy):

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.short_ma = None
        self.long_ma = None
        self.position_size = self.config.get("position_size", 0.1)
        self.short_ma_period = self.config.get("short_ma_period", 10)
        self.long_ma_period = self.config.get("long_ma_period", 20)

    async def next(self):
        data = self._get_historical_data(symbol_index=0, data_type="daily")
        if data is None or len(data) < 20:
            return

        factor_values = {}
        for factor_name, factor_obj in self.factor_objects.items():
            try:
                factor_result = await factor_obj.calculate(data)
                factor_values[factor_name] = factor_result
            except Exception as e:
                print(f"Error calculating factor {factor_name}: {e}")
                factor_values[factor_name] = None

        self.short_ma = factor_values.get(f"ma_{self.short_ma_period}")
        self.long_ma = factor_values.get(f"ma_{self.long_ma_period}")

        if self.short_ma is None or self.long_ma is None:
            return

        current_price = data["close"].iloc[0]

        signal = self._generate_signal(current_price)

        if signal is not None:
            self._execute_trade(signal, current_price)

    def _generate_signal(self, current_price: float) -> Optional[Dict[str, Any]]:
        if self.short_ma is None or self.long_ma is None:
            return None

        if self.short_ma > self.long_ma and self.short_ma > current_price:
            return {
                "action": "buy",
                "target_price": current_price,
                "signal_strength": (self.short_ma - self.long_ma) / self.long_ma,
            }

        elif self.short_ma < self.long_ma and self.short_ma < current_price:
            return {
                "action": "sell",
                "target_price": current_price,
                "signal_strength": (self.long_ma - self.short_ma) / self.short_ma,
            }

        return None

    def _execute_trade(self, signal: Dict[str, Any]):
        action = signal.get("action")
        target_price = signal.get("target_price")

        if action == "buy" and not self.position:
            size = self.broker.getcash() * self.position_size / target_price
            self.buy(size=size)
            print(
                f"BUY signal: target_price={target_price}, size={size}, signal_strength={signal.get('signal_strength')}"
            )
        elif action == "sell" and self.position:
            self.sell(size=self.position.size)
            print(
                f"SELL signal: target_price={target_price}, size={self.position.size}, signal_strength={signal.get('signal_strength')}"
            )
