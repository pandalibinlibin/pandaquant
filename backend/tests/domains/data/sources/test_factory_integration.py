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
