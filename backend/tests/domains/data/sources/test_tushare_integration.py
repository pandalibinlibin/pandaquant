"""
Tushare data source integration tests
Real API calls to verify Tushare integration
"""

import pytest
import logging
from app.domains.data.sources.tushare import TushareDataSource
from app.core.config import settings

logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestTushareIntegration:
    """Integration tests for Tushare data source with real API calls"""

    @pytest.fixture
    def tushare_source(self):
        """Create Tushare data source with real toekn from settings"""
        return TushareDataSource(token=settings.TUSHARE_TOKEN, priority=1)

    @pytest.mark.asyncio
    async def test_tushare_initialization(self, tushare_source):
        """Test Tushare data source is properly initialized"""
        assert tushare_source is not None
        assert tushare_source.name == "tushare"
        assert tushare_source.priority == 1
        logger.info("Tushare data source initialized successfully")

    @pytest.mark.asyncio
    async def test_health_check_real_api(self, tushare_source):
        """Test health check with real Tushare API call"""
        is_healthy = await tushare_source.health_check()
        assert isinstance(is_healthy, bool)

        logger.info("Tushare health check result: %s", is_healthy)

    @pytest.mark.asyncio
    async def test_fetch_daily_data_real_api(self, tushare_source):
        """Test fetching real daily data from Tushare API"""
        symbol = "000001.SZ"
        start_date = "2024-01-02"
        end_date = "2024-01-31"

        df = await tushare_source._fetch_daily_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
        )

        assert not df.empty, "No data returned from Tushare API"
        assert "timestamp" in df.columns
        assert len(df) > 0
        logger.info(f"Successfully fetched {len(df)} records for {symbol}")
