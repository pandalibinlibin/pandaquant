import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import MarketData
from app.core.db import get_db
from app.domains.data.sources.factory import DataSourceFactory, data_source_factory


class DataService:
    def __init__(self):
        self.data_source_factory = data_source_factory

        self.influxdb_url = settings.INFLUXDB_URL
        self.influxdb_token = settings.INFLUXDB_TOKEN
        self.influxdb_org = settings.INFLUXDB_ORG
        self.influxdb_bucket = settings.INFLUXDB_BUCKET

        self.influxdb_client = InfluxDBClient(
            url=self.influxdb_url, token=self.influxdb_token, org=self.influxdb_org
        )
        self.write_api = self.influxdb_client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.influxdb_client.query_api()

    async def fetch_stock_data(
        self, symbol: str, start_date: str, end_date: str, data_type: str = "daily"
    ) -> pd.DataFrame:
        try:
            data = await self.data_source_factory.fetch_data_with_fallback(
                data_type=data_type,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )

            if data.empty:
                return pd.DataFrame()

            return data

        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
