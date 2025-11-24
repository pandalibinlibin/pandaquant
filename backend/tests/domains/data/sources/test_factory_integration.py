"""
Data source factory integration tests
Test multi-source fallback and priority management
"""

import pytest
import logging
from app.domains.data.sources.factory import DataSourceFactory
from app.core.config import settings

logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestDataSourceFactoryIntegration:
    """Integration test for data source factory with real data sources"""

    @pytest.fixture
    def factory(self):
        """Create data source factory with real configuration"""
        return DataSourceFactory()

    @pytest.mark.asyncio
    async def test_factory_initialization(self, factory):
        """Test factory initializes all configured data sources"""
        assert factory is not None
        assert len(factory.sources) >= 2, "Should have at least Tushare and Akshare"

        tushare_source = next((s for s in factory.sources if s.name == "tushare"), None)
        assert tushare_source is not None, "Tushare source should be initialized"
        assert tushare_source.priority == 1, "Tushare should have priority 1"

        akshare_source = next((s for s in factory.sources if s.name == "akshare"), None)
        assert akshare_source is not None, "Akshare source should be initialized"
        assert akshare_source.priority == 2, "Akshare should have priority 2"

        logger.info("Factory initialized with %d data sources", len(factory.sources))

    @pytest.mark.asyncio
    async def test_fetch_with_fallback_mechanism(self, factory):
        """Test factory fallback mechanism when primary source fails"""

        data = await factory.fetch_data_with_fallback(
            data_type="daily",
            symbol="000001.SZ",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        assert not data.empty, "Should fetch data from available sources"
        assert len(data) > 0, "Should have at least some data"

        required_columns = ["timestamp", "open", "high", "low", "close", "volume"]
        for col in required_columns:
            assert col in data.columns, f"Missing required column: {col}"

        logger.info("Fallback mechanism test passed with %d rows", len(data))

    @pytest.mark.asyncio
    async def test_source_priority_ordering(self, factory):
        """Test the sources are tried in priority order"""

        available_sources = await factory.get_available_sources("daily")

        assert len(available_sources) > 0, "should have available sources"

        priorities = [source.priority for source in available_sources]
        assert priorities == sorted(priorities), "Sources should be ordered by priority"

        if len(available_sources) >= 2:
            assert available_sources[0].name == "tushare", "Tushare should be first"
            assert available_sources[1].name == "akshare", "AkShare should be second"

        logger.info(
            "Priority ordering verified: %s", [s.name for s in available_sources]
        )

    @pytest.mark.asyncio
    async def test_health_check_all_sources(self, factory):
        """Test health check for all configured sources"""
        health_status = await factory.health_check_all()

        assert "tushare" in health_status, "Should check Tushare health"
        assert "akshare" in health_status, "Should check AKShare health"

        healthy_count = sum(1 for status in health_status.values() if status)
        assert healthy_count > 0, "At least one source should be healthy"

        logger.info("Health check results: %s", health_status)

    @pytest.mark.asyncio
    async def test_get_source_status(self, factory):
        """Test getting status information for all sources"""

        status = factory.get_source_status()

        assert "tushare" in status, "Should have Tushare status"
        assert "akshare" in status, "Should have AKShare status"

        for source_name, source_status in status.items():
            assert "priority" in source_status, f"{source_name} should have priority"
            assert "status" in source_status, f"{source_name} should have status"
            assert (
                "error_count" in source_status
            ), f"{source_name} should have error_count"

        logger.info("Source status: %s", status)
