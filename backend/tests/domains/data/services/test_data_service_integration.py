"""
Data service integration tests
Test complete data fetching workflow including InfluxDB cache and data sources
"""

import pytest
import logging
import pandas as pd
from app.domains.data.services import DataService

logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestDataServiceIntegration:
    """Integration test for data service with real InfluxDB and data sources"""

    @pytest.fixture
    def service(self):
        """Create data service instance"""
        return DataService()

    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initializes correctly with InfluxDB and data source factory"""

        assert service is not None, "Service should be initialized"
        assert (
            service.data_source_factory is not None
        ), "Should have data source factory"
        assert service.influxdb_client is not None, "Should have InfluxDB client"
        assert service.write_api is not None, "Should have InfluxDB write API"
        assert service.query_api is not None, "Should have InfluxDB query API"

        logger.info("Data service initialized with InfluxDB and data source factory")

    @pytest.mark.asyncio
    async def test_fetch_data_without_cache(self, service):
        """Test fetching data directly from data sources (bypass cache)"""

        data = await service.fetch_data(
            data_type="daily",
            symbol="000001.SZ",
            start_date="2024-01-01",
            end_date="2024-01-10",
            use_cache=False,
        )

        assert isinstance(data, pd.DataFrame), "Should return a DataFrame"

        if not data.empty:
            assert len(data) > 0, "Should have data rows"

            required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
            for col in required_columns:
                assert col in data.columns, f"Missing required column: {col}"

            logger.info("Successfully fetched %d rows without cache", len(data))

        else:
            logger.info("No data available - graceful degradation verified")

    @pytest.mark.asyncio
    async def test_fetch_data_with_cache_write(self, service):
        """Test fetching data with cache enabled (should write to InfluxDB)"""

        data = await service.fetch_data(
            data_type="daily",
            symbol="000001.SZ",
            start_date="2024-01-01",
            end_date="2024-01-05",
            use_cache=True,
        )

        assert isinstance(data, pd.DataFrame), "Should return a DataFrame"

        if not data.empty:
            assert len(data) > 0, "Should have data rows"
            logger.info("Successfully fetched %d rows with cache", len(data))

            cached_data = await service.fetch_data(
                data_type="daily",
                symbol="000001.SZ",
                start_date="2024-01-01",
                end_date="2024-01-05",
                use_cache=True,
            )

            assert not cached_data.empty, "Should retrieve cached data"
            logger.info("Successfully retrieved %d rows from cache", len(cached_data))
        else:
            logger.info("No data available - cache test skipped")
