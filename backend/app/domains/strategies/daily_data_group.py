"""
DailyDataGroup implementation for daily stock data with OHLCV columns
"""

import pandas as pd
import backtrader as bt
from typing import Dict, Any, List
from app.domains.strategies.data_group import DataGroup
from app.core.logging import get_logger

logger = get_logger(__name__)


class DailyDataGroup(DataGroup):
    """Data group for daily stock data with OHLCV columns"""

    def __init__(
        self, name: str, weight: float = 1.0, factors: List[Dict[str, Any]] = None
    ):
        super().__init__(name, weight, factors)
        self.data_type = "daily"
        self._factor_objects = {}

    async def prepare_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Prepare daily data: fetch data and calculate factors

        Returns DataFrame with datetime index and OHLCV + factor columns
        """
        if not self.data_service:
            raise ValueError("DataService not set. Call set_service() first.")

        try:
            data = await self.data_service.fetch_data(
                data_type=self.data_type,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )

            if data.empty:
                logger.warning(f"Empty data for {symbol}")
                self._prepared_data = pd.DataFrame()
                return self._prepared_data

            if "timestamp" not in data.columns:
                logger.error(f"timestamp column not found in data for {symbol}")
                self._prepared_data = pd.DataFrame()
                return self._prepared_data

            data = data.copy()
            data["timestamp"] = pd.to_datetime(data["timestamp"])
            data.set_index("timestamp", inplace=True)
            data.sort_index(inplace=True)

            if self.factors and self.factor_service:
                data = await self._calculate_factors(data)

            self._prepared_data = data
            logger.info(
                f"Prepared data for {self.name}: {len(data)} rows, {len(data.columns)} columns"
            )
            return data

        except Exception as e:
            logger.error(f"Error preparing data for {self.name}: {e}")
            self._prepared_data = pd.DataFrame()
            raise

    def to_backtrader_feed(self) -> bt.feeds.PandasData:
        """
        Convert prepared data to Backtrader PandasData feed

        Returns:
            Backtrader PandasData feed ready for cerebro.adddata()
        """
        if self._prepared_data is None or self._prepared_data.empty:
            raise ValueError(
                f"Data not prepared for {self.name}. Call prepare_data() first."
            )

        if not isinstance(self._prepared_data.index, pd.DatetimeIndex):
            raise ValueError(
                f"Data index must be DatetimeIndex for {self.name}, got {type(self._prepared_data.index)}"
            )

        required_cols = ["open", "high", "low", "close", "volume"]
        missing_cols = [
            col for col in required_cols if col not in self._prepared_data.columns
        ]
        if missing_cols:
            raise ValueError(
                f"Missing required columns for {self.name}: {missing_cols}"
            )

        ohlcv_cols = ["open", "high", "low", "close", "volume"]
        factor_cols = [
            col for col in self._prepared_data.columns if col not in ohlcv_cols
        ]

        feed = bt.feeds.PandasData(
            dataname=self._prepared_data,
            datetime=None,
            open="open",
            high="high",
            low="low",
            close="close",
            volume="volume",
            openinterest=-1,
        )

        feed._factor_cols = {}
        for i, col in enumerate(factor_cols):
            line_idx = 6 + i
            feed._factor_cols[col] = line_idx

        feed._factor_col_names = factor_cols

        logger.info(
            f"Created Backtrader feed for {self.name} with {len(self._prepared_data)} bars"
        )

        return feed

    async def _calculate_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all configured factors for this group"""
        if not self.factor_service:
            logger.warning(f"No FactorService set for {self.name}")
            return data

        await self._create_and_register_factors()

        factor_data = data.copy()
        for factor_name, factor_obj in self._factor_objects.items():
            try:
                factor_result = await factor_obj.calculate(data)

                if isinstance(factor_result, pd.DataFrame):
                    factor_col_name = factor_obj.name
                    if factor_col_name in factor_result.columns:
                        factor_data[factor_col_name] = factor_result[factor_col_name]

                logger.debug(
                    f"Successfully calculated factor {factor_name} for {self.name}"
                )

            except Exception as e:
                logger.error(
                    f"Error calculating factor {factor_name} for {self.name}: {e}"
                )
                continue

        return factor_data

    async def _create_and_register_factors(self):
        """Create and register factors for this group"""
        if not self.factor_service:
            return

        for factor_config in self.factors:
            factor_name = factor_config.get("name")
            factor_class = factor_config.get("class")
            factor_params = factor_config.get("params", {})

            if factor_name in self._factor_objects:
                continue

            try:
                factor_obj = factor_class(
                    name=f"{self.name}_{factor_name}",
                    **factor_params,
                )

                self.factor_service.register_factor(factor_obj)
                self._factor_objects[factor_name] = factor_obj
                logger.debug(
                    f"Created and registered factor {factor_name} for group {self.name}"
                )

            except Exception as e:
                logger.error(
                    f"Error creating factor {factor_name} for group {self.name}: {e}"
                )
                continue
