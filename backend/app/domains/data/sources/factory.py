import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from .base import DataSource, DataSourceStatus
from .tushare import TushareDataSource
from .akshare import AkshareDataSource
from app.core.config import settings

logger = logging.getLogger(__name__)


class DataSourceFactory:
    def __init__(self):
        self.sources: List[DataSource] = []
        self._initialize_sources()

    def _initialize_sources(self):
        tushare_source = TushareDataSource(
            token=settings.TUSHARE_TOKEN,
            priority=1,
        )
        self.sources.append(tushare_source)

        akshare_source = AkshareDataSource(priority=2)
        self.sources.append(akshare_source)

        logger.info(f"Initialized {len(self.sources)} data sources")

    async def get_available_sources(self, data_type: str) -> List[DataSource]:

        available_sources = []

        for source in self.sources:
            if source.status == DataSourceStatus.ACTIVE:
                try:
                    available_types = await source.get_available_data_types()
                    if data_type in available_types:
                        available_sources.append(source)
                except Exception as e:
                    logger.warning(
                        f"Error checking data type support for {source.name}: {e}"
                    )
                    source.record_error()

        available_sources.sort(key=lambda x: x.priority)
        return available_sources

    async def fetch_data_with_fallback(
        self,
        data_type: str,
        **kwargs,
    ) -> pd.DataFrame:

        available_sources = await self.get_available_sources(data_type)

        if not available_sources:
            logger.error(f"No available sources for data type: {data_type}")
            return pd.DataFrame()

        last_error = None

        for source in available_sources:
            try:
                logger.info(f"Trying to fetch {data_type} data from {source.name}")

                if not await source.is_available():
                    logger.warning(f"Souce {source.name} is not available, skipping")
                    continue

                data = await source.fetch_data(data_type, **kwargs)

                if not data.empty:
                    data = await source.normalize_data(data, data_type)
                    logger.info(f"Successfully fetched data from {source.name}")
                    source.record_success()
                    return data
                else:
                    logger.warning(f"Empty data returned from {source.name}")
                    source.record_error()

            except Exception as e:
                logger.error(f"Error fetching data from {source.name}: {e}")
                source.record_error()
                last_error = e
                continue

        logger.error(f"All sources failed for data type {data_type}")
        if last_error:
            logger.error(f"Last error: {last_error}")

        return pd.DataFrame()

    async def health_check_all(self) -> Dict[str, bool]:
        results = {}

        for source in self.sources:
            try:
                is_healthy = await source.health_check()
                results[source.name] = is_healthy

                if is_healthy:
                    source.record_success()
                else:
                    source.record_error()

            except Exception as e:
                logger.error(f"Health check failed for {source.name}: {e}")
                source.record_error()
                results[source.name] = False

        return results

    def get_source_status(self) -> Dict[str, Dict[str, Any]]:
        status = {}

        for source in self.sources:
            status[source.name] = {
                "priority": source.priority,
                "status": source.status.value,
                "error_count": source.error_count,
                "last_check": source.last_check,
                "max_errors": source.max_errors,
            }

        return status


data_source_factory = DataSourceFactory()
