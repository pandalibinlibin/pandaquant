import pandas as pd
from typing import Dict, Any, Optional, List
from app.domains.strategies.data_group import DataGroup
from app.core.logging import get_logger
from app.domains.factors.base import Factor

logger = get_logger(__name__)


class DailyDataGroup(DataGroup):
    """Data group for daily stock data with specific factors"""

    def __init__(
        self, name: str, weight: float = 1.0, factors: List[Dict[str, Any]] = None
    ):
        super().__init__(name, weight, factors)
        self.data_type = "daily"
        self._historical_data = None
        self._factor_objects = {}

    async def get_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Get daily data for this group"""
        try:
            data = await self.data_service.fetch_data(
                data_type=self.data_type,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )
            self._historical_data = data
            return data

        except Exception as e:
            logger.error(f"Error getting daily data for {symbol}: {e}")
            raise

    def get_current_bar_data(self, bt_data) -> pd.DataFrame:
        """Get current bar data from Backtrader data feed"""
        try:
            current_data = pd.DataFrame(
                {
                    "datetime": [bt_data.datetime.datetime(0)],
                    "open": [bt_data.open[0]],
                    "high": [bt_data.high[0]],
                    "low": [bt_data.low[0]],
                    "close": [bt_data.close[0]],
                    "volume": [bt_data.volume[0]],
                }
            )

            return current_data

        except Exception as e:
            logger.error(f"Error getting curretn bar data for {self.name}: {e}")

            return pd.DataFrame()

    async def calculate_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate factors for this group"""
        try:
            if not self.factors:
                logger.warning(f"No factors specified for {self.name}")
                return data

            await self._create_and_register_factors()

            factor_data = data.copy()
            for factor_name, factor_obj in self._factor_objects.items():
                try:
                    factor_data = await factor_obj.calculate(data)
                    logger.debug(
                        f"Successfully calculated factor {factor_name} for group {self.name}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error calculating factor {factor_name} for group {self.name}: {e}"
                    )
                    continue

            self.set_factor_data(factor_data)
            return factor_data
        except Exception as e:
            logger.error(f"Failed to calculate factors for {self.name}: {e}")
            raise

    async def _create_and_register_factors(self):
        """Create and register factors for this group"""
        for factor_config in self.factors:
            factor_name = factor_config.get("name")
            factor_class = factor_config.get("class")
            factor_params = factor_config.get("params", {})

            try:
                factor_obj = factor_class(
                    name=f"{self.name}_{factor_name}",
                    **factor_params,
                )

                self.factor_service.register_factor(factor_obj)
                self._factor_objects[factor_name] = factor_obj
            except Exception as e:
                logger.error(
                    f"Error creating and registering factor {factor_name}: {e}"
                )
                continue
