"""
AKShare data source integration tests
Real API calls to verify AKShare integration
"""

import pytest
import logging
from app.domains.data.sources.akshare import AkshareDataSource

logger = logging.getLogger(__name__)


@pytest.mark.integration
class TestAkshareIntegration:
    """Integration tests for AKShare data source with real API calls"""

    @pytest.fixture
    def akshare_source(self):
        """Create AKShare data source instance"""
        return AkshareDataSource(priority=2)

    @pytest.mark.asyncio
    async def test_akshare_initialization(self, akshare_source):
        """Test AKShare source is properly initialized"""
        assert akshare_source is not None
        assert akshare_source.name == "akshare"
        assert akshare_source.priority == 2
        logger.info("AKShare data source initialized successfully")

    @pytest.mark.asyncio
    async def test_health_check_real_api(self, akshare_source):
        """Test health check with real AKShare API Call"""
        is_healthy = await akshare_source.health_check()
        assert isinstance(is_healthy, bool)
        logger.info("AKShare health check result: %s", is_healthy)

    @pytest.mark.asyncio
    async def test_parameter_validation_valid(self, akshare_source):
        """Test parameter validation with valid params"""
        valid_params = {
            "symbol": "000001.SZ",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        }

        is_valid = await akshare_source.validate_params("daily", **valid_params)
        assert is_valid is True
        logger.info("Parameter validation passed for valid params")

    @pytest.mark.asyncio
    async def test_parameter_validation_missing_symbol(self, akshare_source):
        """Test paramter validation with missing symbol"""
        invalid_params = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
        }

        is_valid = await akshare_source.validate_params("daily", **invalid_params)
        assert is_valid is False
        logger.info("Parameter validation correctly rejected missing symbol")

    @pytest.mark.asyncio
    async def test_fetch_daily_data_real_api(self, akshare_source):
        """Test fetching real daily data from AKShare API"""
        symbol = "000001.SZ"
        start_date = "2024-01-02"
        end_date = "2024-01-31"

        df = await akshare_source._fetch_daily_data(
            symbol=symbol, start_date=start_date, end_date=end_date
        )

        assert not df.empty, "No data returned from AKShare API"
        assert "timestamp" in df.columns, "Missing timestamp column"
        assert len(df) > 0, "Data should contain trading days"
        logger.info("Successfully fetched %d records for %s", len(df), symbol)

    @pytest.mark.asyncio
    async def test_fetch_data_with_symbol_suffix(self, akshare_source):
        """Test fetching data with .SZ/.SH suffix (should be stripped)"""
        # Test with .SZ suffix
        symbol_sz = "000001.SZ"
        df_sz = await akshare_source._fetch_daily_data(
            symbol=symbol_sz,
            start_date="2024-01-02",
            end_date="2024-01-05",
        )
        assert not df_sz.empty, "Failed to fetch data for .SZ symbol"
        logger.info("Successfully fetched data for %s (suffix stripped)", symbol_sz)

        # Test with .SH suffix
        symbol_sh = "600000.SH"
        df_sh = await akshare_source._fetch_daily_data(
            symbol=symbol_sh,
            start_date="2024-01-02",
            end_date="2024-01-05",
        )
        assert not df_sh.empty, "Failed to fetch data for .SH symbol"
        logger.info("Successfully fetched data for %s (suffix stripped)", symbol_sh)

    @pytest.mark.asyncio
    async def test_get_available_data_types(self, akshare_source):
        """Test getting available data types"""
        data_types = await akshare_source.get_available_data_types()

        assert isinstance(data_types, list), "Data types should be a list"
        assert len(data_types) > 0, "Should have at least one data type"
        assert "daily" in data_types, "Should support daily data type"
        logger.info("Successfully fetched available data types: %s", data_types)
