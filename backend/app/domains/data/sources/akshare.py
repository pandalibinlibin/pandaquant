import asyncio
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import akshare as ak
from .base import DataSource

logger = logging.getLogger(__name__)


class AkshareDataSource(DataSource):
    def __init__(self, priority: int = 2):
        super().__init__(name="akshare", priority=priority)

    async def health_check(self) -> bool:
        try:
            test_data = ak.stock_zh_a_hist(
                symbol="000001",
                period="daily",
                start_date="20240101",
                end_date="20240102",
            )
            return not test_data.empty

        except Exception as e:
            logger.error(f"Akshare health check failed: {e}")
            return False

    async def validate_params(self, data_type: str, **kwargs) -> bool:
        try:
            if data_type == "daily":
                required_params = ["symbol", "start_date", "end_date"]
            elif data_type == "minute":
                required_params = ["symbol", "start_date", "end_date"]
            elif data_type == "macro":
                required_params = ["indicator", "start_date", "end_date"]
            else:
                return True

            for param in required_params:
                if param not in kwargs:
                    logger.error(f"Missing required parameter: {param}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Parameter validation failed: {e}")
            return False

    async def get_available_data_types(self) -> List[str]:
        return [
            "daily",
            "minute",
            "macro",
            "financial",
            "industry",
            "concept",
            "index",
            "fund",
        ]

    async def fetch_data(self, data_type: str, **kwargs) -> pd.DataFrame:
        try:
            if not await self.validate_params(data_type, **kwargs):
                return pd.DataFrame()

            self.record_success()

            if data_type == "daily":
                return await self._fetch_daily_data(**kwargs)
            else:
                logger.error(f"Unsupported data type: {data_type}")
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching {data_type} data: {e}")
            self.record_error()
            return pd.DataFrame()

    async def normalize_data(
        self, data: pd.DataFrame, symbol: str, data_type: str = "daily"
    ) -> pd.DataFrame:
        if data.empty:
            return data

        time_columns = ["date", "datetime", "time", "日期"]
        for col in time_columns:
            if col in data.columns:
                data = data.rename(columns={col: "timestamp"})
                break

        if "timestamp" in data.columns:
            data["timestamp"] = pd.to_datetime(data["timestamp"])

        standard_fields = self.get_standard_fields(data_type)
        for field in standard_fields:
            if field not in data.columns:
                if field == "timestamp":
                    continue
                elif field == "symbol":
                    data[field] = symbol
                elif field in ["open", "high", "low", "close", "volume", "amount"]:
                    data[field] = -999999.0
                elif field in [
                    "pct_chg",
                    "change",
                    "turnover",
                    "pe",
                    "pb",
                    "ps",
                    "pcf",
                ]:
                    data[field] = -999999.0
                elif field in [
                    "market_cap",
                    "circulating_market_cap",
                    "total_shares",
                    "float_shares",
                ]:
                    data[field] = -999999.0
                else:
                    data[field] = None

        return data

    async def _fetch_daily_data(
        self, symbol: str, start_date: str, end_date: str, **kwargs
    ) -> pd.DataFrame:
        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq",
            )

            if df.empty:
                return pd.DataFrame()

            df = df.rename(
                columns={
                    "日期": "timestamp",
                    "开盘": "open",
                    "最高": "high",
                    "最低": "low",
                    "收盘": "close",
                    "成交量": "volume",
                    "成交额": "amount",
                }
            )

            return df

        except Exception as e:
            logger.error(f"Error fetching daily data for {symbol}: {e}")
            return pd.DataFrame()
