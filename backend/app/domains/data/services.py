"""
数据服务模块
负责市场数据的获取，存储和管理
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd
import tushare as ts
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import MarketData
from app.core.db import get_db


class DataService:
    def __init__(self):
        self.tushare_token = settings.TUSHARE_TOKEN
        self.influxdb_url = settings.INFLUXDB_URL
        self.influxdb_token = settings.INFLUXDB_TOKEN
        self.influxdb_org = settings.INFLUXDB_ORG
        self.influxdb_bucket = settings.INFLUXDB_BUCKET

        if self.tushare_token:
            ts.set_token(self.tushare_token)
            self.pro = ts.pro_api()

        self.influxdb_client = InfluxDBClient(
            url=self.influxdb_url,
            token=self.influxdb_token,
            org=self.influxdb_org,
        )
        self.write_api = self.influxdb_client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.influxdb_client.query_api()

    async def fetch_stock_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        data_type: str = "daily",
    ) -> pd.DataFrame:
        try:
            if data_type == "daily":
                df = self.pro.daily(
                    ts_code=symbol,
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                )
            elif data_type == "minute":
                df = self.pro.stk_mins(
                    ts_code=symbol,
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                    freq="1min",
                )
            else:
                raise ValueError(f"Unsupported data type: {data_type}")

            if df.empty:
                return pd.DataFrame()

            df = df.sort_values("trade_date")
            df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y%m%d")
            df = df.rename(columns={"trade_date": "timestamp"})

            return df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    async def store_data_to_influxdb(
        self, symbol: str, data: pd.DataFrame, data_type: str = "daily"
    ) -> bool:
        try:
            points = []
            for _, row in data.iterrows():
                point = (
                    Point("market_data")
                    .tag("symbol", symbol)
                    .tag("data_type", data_type)
                    .field("open", float(row.get("open", 0)))
                    .field("high", float(row.get("high", 0)))
                    .field("low", float(row.get("low", 0)))
                    .field("close", float(row.get("close", 0)))
                    .field("volume", float(row.get("vol", 0)))
                    .field("amount", float(row.get("amount", 0)))
                    .time(row["timestamp"])
                )

                points.append(point)

            if points:
                self.write_api.write(
                    bucket=self.influxdb_bucket,
                    org=self.influxdb_org,
                    record=points,
                )
                return True

            return False

        except Exception as e:
            print(f"Error storing data to InfluxDB: {e}")
            return False

    async def store_data_to_postgres(
        self, symbol: str, data: pd.DataFrame, data_type: str = "daily"
    ) -> bool:
        try:
            db = next(get_db())

            for _, row in data.iterrows():
                market_data = MarketData(
                    symbol=symbol,
                    data_type=data_type,
                    timestamp=row["timestamp"],
                    data=row.to_json(),
                )
                db.add(market_data)

            db.commit()
            return True
        except Exception as e:
            print(f"Error storing data to PostgreSQL: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    async def get_data_from_influxdb(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        data_type: str = "daily",
    ) -> pd.DataFrame:
        try:
            query = f"""
            from(bucket: "{self.influxdb_bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "market_data")
            |> filter(fn: (r) => r["symbol"] == "{symbol}")
            |> filter(fn: (r) => r["data_type"] == "{data_type}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            """
            result = self.query_api.query_data_frame(query=query, org=self.influxdb_org)
            if result.empty:
                return pd.DataFrame()

            result = result.rename(columns={"_time": "timestamp"})
            result = result.sort_values("timestamp")

            return result
        except Exception as e:
            print(f"Error getting data from InfluxDB: {e}")
            return pd.DataFrame()

    async def sync_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        data_type: str = "daily",
    ) -> Dict[str, bool]:
        results = {}

        for symbol in symbols:
            try:
                data = await self.fetch_stock_data(
                    symbol, start_date, end_date, data_type
                )
                if data.empty:
                    results[symbol] = False
                    continue

                influx_success = await self.store_data_to_influxdb(
                    symbol, data, data_type
                )
                postgres_success = await self.store_data_to_postgres(
                    symbol, data, data_type
                )

                results[symbol] = influx_success and postgres_success

            except Exception as e:
                print(f"Error syncing data for {symbol}: {e}")
                results[symbol] = False

        return results

    async def get_latest_data(
        self,
        symbol: str,
        data_type: str = "daily",
        days: int = 1,
    ) -> pd.DataFrame:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        return await self.get_data_from_influxdb(
            symbol, start_date, end_date, data_type
        )

    def close(self):
        if hasattr(self, "influx_client"):
            self.influxdb_client.close()
