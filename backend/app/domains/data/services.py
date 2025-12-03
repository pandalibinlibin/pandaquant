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
                    # Check if cached data covers the requested time range
                    from datetime import datetime
                    
                    cached_start = cached_data['timestamp'].min()
                    cached_end = cached_data['timestamp'].max()
                    requested_start = pd.to_datetime(start_date)
                    requested_end = pd.to_datetime(end_date)
                    
                    # Convert to timezone-naive for comparison if needed
                    if cached_start.tzinfo is not None:
                        cached_start = cached_start.tz_localize(None)
                    if cached_end.tzinfo is not None:
                        cached_end = cached_end.tz_localize(None)
                    
                    # Check if cache covers the full requested range
                    cache_covers_range = (cached_start <= requested_start and cached_end >= requested_end)
                    
                    # Calculate expected data points (rough estimate: trading days ~= 250/year)
                    expected_days = (requested_end - requested_start).days
                    expected_points = int(expected_days * 0.7)  # ~70% are trading days
                    actual_points = len(cached_data)
                    
                    # Cache is valid if it covers the range AND has reasonable amount of data
                    cache_is_sufficient = cache_covers_range and actual_points >= min(expected_points * 0.8, 10)
                    
                    if cache_is_sufficient:
                        logger.info(
                            f"Using cached {data_type} data for {symbol} from InfluxDB "
                            f"({actual_points} points, covers {cached_start.date()} to {cached_end.date()})"
                        )
                        return cached_data
                    else:
                        logger.info(
                            f"Cached data insufficient for {symbol}: "
                            f"requested {requested_start.date()} to {requested_end.date()}, "
                            f"cached {cached_start.date()} to {cached_end.date()} ({actual_points} points, expected ~{expected_points}). "
                            f"Fetching fresh data from source."
                        )
                else:
                    logger.info(
                        f"No cached data found for {symbol}, fetching from data source"
                    )

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
            logger.info(
                f"About to write {len(data)} rows to InfluxDB for measurement: {measurement}"
            )
            logger.info(
                f"Data timestamps: {data['timestamp'].tolist() if 'timestamp' in data.columns else 'No timestamp column'}"
            )

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
                    logger.info(
                        f"InfluxDB write - Row data: symbol={row.get('symbol', 'N/A')}, timestamp={row['timestamp']}, timestamp_type={type(row['timestamp'])}"
                    )
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
            end_date_plus_one = (
                datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            ).strftime("%Y-%m-%d")
            query = f"""
            from(bucket: "{self.influxdb_bucket}")
            |> range(start: {start_date}, stop: {end_date_plus_one})
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

            logger.info(f"InfluxDB read - Retrieved {len(result)} rows from cache")
            logger.info(
                f"InfluxDB read - Raw timestamps: {result['_time'].tolist() if '_time' in result.columns else 'No _time column'}"
            )

            result = result.rename(columns={"_time": "timestamp"})

            logger.info(
                f"InfluxDB read - After rename timestamps: {result['timestamp'].tolist() if 'timestamp' in result.columns else 'No timestamp column'}"
            )

            result = result.sort_values("timestamp")

            logger.info(
                f"InfluxDB read - After sort timestamps: {result['timestamp'].tolist() if 'timestamp' in result.columns else 'No timestamp column'}"
            )

            return result

        except Exception as e:
            logger.error(f"Error getting data from InfluxDB: {e}")
            return pd.DataFrame()


data_service = DataService()
