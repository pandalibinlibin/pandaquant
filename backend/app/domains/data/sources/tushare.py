from app.domains.data.sources.base import DataSource
import tushare as ts
import pandas as pd
from app.core.config import settings
import logging
from typing import List

logger = logging.getLogger(__name__)


class TushareDataSource(DataSource):
    def __init__(self, token: str = None, priority: int = 1):
        super().__init__(name="tushare", priority=priority)

        self.token = token or settings.TUSHARE_TOKEN
        if token:
            ts.set_token(token)
            self.pro = ts.pro_api()

        else:
            self.pro = None
            logger.warning("Tushare token not provided, some data may not be available")

    async def health_check(self) -> bool:

        try:
            if not self.pro:
                return False

            test_data = self.pro.trade_cal(
                exchange="SSE", start_date="20240101", end_date="20240102"
            )
            return not test_data.empty
        except Exception as e:
            logger.error(f"Tushare health check failed: {e}")
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
            logger.error(f"Parameter validataion failed: {e}")
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

            elif data_type == "minute":
                return await self._fetch_minute_data(**kwargs)
            elif data_type == "macro":
                return await self._fetch_macro_data(**kwargs)
            elif data_type == "financial":
                return await self._fetch_financial_data(**kwargs)
            elif data_type == "industry":
                return await self._fetch_industry_data(**kwargs)
            elif data_type == "concept":
                return await self._fetch_concept_data(**kwargs)
            else:
                logger.error(f"Unsupported data type: {data_type}")
                return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error fetching {data_type} data: {e}")
            self.record_error()
            return pd.DataFrame()

    async def _fetch_daily_data(
        self, symbol: str, start_date: str, end_date: str, **kwargs
    ) -> pd.DataFrame:
        try:
            if not self.pro:
                logger.error("Tushare pro API not initialized")
                return pd.DataFrame()

            df = self.pro.daily(
                ts_code=symbol,
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                **kwargs,
            )

            if df.empty:
                return pd.DataFrame()

            df = df.sort_values("trade_date")
            df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
            df = df.rename(columms={"trade_date": "timestamp"})

            return df

        except Exception as e:
            logger.error(f"Error fetching daily data for {symbol}: {e}")
            return pd.DataFrame()

    async def _fetch_minute_data(
        self, symbol: str, start_date: str, end_date: str, freq: str = "1min", **kwargs
    ) -> pd.DataFrame:
        try:
            if not self.pro:
                logger.error("Tushare pro API not initialized")
                return pd.DataFrame()

            df = self.pro.stk_mins(
                ts_code=symbol,
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                freq=freq,
                **kwargs,
            )

            if df.empty:
                return pd.DataFrame()

            df = df.sort_values("trade_time")
            df["trade_time"] = pd.to_datetime(df["trade_time"])
            df = df.rename(columns={"trade_time": "timestamp"})

            return df

        except Exception as e:
            logger.error(f"Error fetching minute data for {symbol}: {e}")
            return pd.DataFrame()

    async def _fetch_macro_data(
        self, indicator: str, start_date: str, end_date: str, **kwargs
    ) -> pd.DataFrame:
        try:
            if not self.pro:
                logger.error("Tushare pro API not initialized")
                return pd.DataFrame()

            if indicator == "gdp":
                df = self.pro.cn_gdp()
            elif indicator == "cpi":
                df = self.pro.cn_cpi()
            elif indicator == "ppi":
                df = self.pro.cn_ppi()
            elif indicator == "m2":
                df = self.pro.cn_m2()
            elif indicator == "interest_rate":
                df = self.pro.shibor()
            else:
                logger.error(f"Unsupported macro indicator: {indicator}")
                return pd.DataFrame()

            if df.empty:
                return pd.DataFrame()

            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
                df = df.rename({"date": "timestamp"})
            elif "period" in df.columns:
                df["period"] = pd.to_datetime(df["period"])
                df = df.rename({"period": "timestamp"})

            if start_date and end_date:
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                df = df[(df["timestamp"] >= start_dt) & (df["timestamp"] <= end_dt)]

            return df
        except Exception as e:
            logger.error(f"Error fetching macro data for {indicator}: {e}")
            return pd.DataFrame()

    async def _fetch_financial_data(
        self, symbol: str, start_date: str, end_date: str, **kwargs
    ) -> pd.DataFrame:
        try:
            if not self.pro:
                logger.error("Tushare pro API not initialized")
                return pd.DataFrame()

            df = self.pro.fina_indicator(
                ts_code=symbol,
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                **kwargs,
            )

            if df.empty:
                return pd.DataFrame()

            df = df.sort_values("end_date")
            df["end_date"] = pd.to_datetime(df["end_date"])
            df = df.rename(columns={"end_date": "timestamp"})

            return df

        except Exception as e:
            logger.error(f"Error fetching financial data for {symbol}: {e}")
            return pd.DataFrame()

    async def _fetch_industry_data(self, **kwargs) -> pd.DataFrame:
        try:
            if not self.pro:
                logger.error("Tushare pro API not initialized")
                return pd.DataFrame()

            df = self.pro.sotck_basic(exchange="", list_status="L")

            if df.empty:
                return pd.DataFrame()

            return df
        except Exception as e:
            logger.error(f"Error fetching industry data: {e}")
            return pd.DataFrame()

    async def _fetch_concept_data(self, **kwargs) -> pd.DataFrame:
        try:
            if not self.pro:
                logger.error("Tushare pro API not initialized")
                return pd.DataFrame()

            df = self.pro.concept()

            if df.empty:
                return pd.DataFrame()

            return df
        except Exception as e:
            logger.error(f"Error fetching concept data: {e}")
            return pd.DataFrame()

    async def normalize_data(self, data: pd.DataFrame) -> pd.DataFrame:
        if data.empty:
            return data

        time_columns = ["trade_date", "trade_time", "date", "period"]
        for col in time_columns:
            if col in data.columns:
                data = data.rename(columns={col: "timestamp"})
                break

        if "timestamp" in data.columns:
            data["timestamp"] = pd.to_datetime(data["timestamp"])

        return data
