import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import pandas as pd
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from sqlalchemy.orm import Session
from app.core.config import settings
from app.domains.data.sources.factory import DataSourceFactory, data_source_factory
from app.core.logging import get_logger

logger = get_logger(__name__)


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

    async def fetch_data(
        self,
        data_type: str,
        symbol: str,
        start_date: str,
        end_date: str,
        use_cache=True,
    ) -> pd.DataFrame:
        try:
            if use_cache:
                cached_data = await self.get_data_from_influxdb(
                    measurement=data_type,
                    start_date=start_date,
                    end_date=end_date,
                    tags={"symbol": symbol},
                    fields=None,
                )

                if not cached_data.empty:
                    logger.info(
                        f"Using cached {data_type} data for {symbol} from InfluxDB"
                    )
                    return cached_data

            logger.info(f"Fetching {data_type} data for {symbol} from data source")
            data = await self.data_source_factory.fetch_data_with_fallback(
                data_type=data_type,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )

            if data.empty:
                return pd.DataFrame()

            if use_cache:
                fields = [
                    col for col in data.columns if col not in ["timestamp", "symbol"]
                ]
                await self.store_data_to_influxdb(
                    measurement=data_type,
                    data=data,
                    tags={"symbol": symbol},
                    fields=fields,
                )
                logger.info(f"Stored {data_type} data for {symbol} to InfluxDB")

            return data

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    async def store_data_to_influxdb(
        self,
        measurement: str,
        data: pd.DataFrame,
        tags: Dict[str, str] = None,
        fields: List[str] = None,
    ) -> bool:
        try:
            points = []
            for _, row in data.iterrows():
                point = Point(measurement)

                if tags:
                    for key, value in tags.items():
                        point = point.tag(key, value)

                if fields:
                    for field in fields:
                        if field in row and pd.notna(row[field]):
                            point = point.field(field, row[field])

                if "timestamp" in row and pd.notna(row["timestamp"]):
                    point = point.time(row["timestamp"])

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
            logger.error(f"Error storing data to InfluxDB: {e}")
            return False

    async def get_data_from_influxdb(
        self,
        measurement: str,
        start_date: str,
        end_date: str,
        tags: Dict[str, str] = None,
        fields: List[str] = None,
    ) -> pd.DataFrame:
        try:
            query = f"""
            from(bucket: "{self.influxdb_bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r["_measurement"] == "{measurement}")
            """

            if tags:
                for key, value in tags.items():
                    query += f'|> filter(fn: (r) => r["{key}"] == "{value}")\n'

            if fields:
                field_conditions = []
                for field in fields:
                    field_conditions.append(f'r["_field"] == "{field}"')
                field_filter = (
                    "|> filter(fn: (r) => " + " or ".join(field_conditions) + ")\n"
                )
                query += field_filter

            query += '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")\n'

            result = self.query_api.query_data_frame(query=query, org=self.influxdb_org)

            if result.empty:
                return pd.DataFrame()

            result = result.rename(columns={"_time": "timestamp"})
            result = result.sort_values("timestamp")

            return result

        except Exception as e:
            logger.error(f"Error getting data from InfluxDB: {e}")
            return pd.DataFrame()


data_service = DataService()
