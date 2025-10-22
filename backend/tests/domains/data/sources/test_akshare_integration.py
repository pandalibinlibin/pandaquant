import pytest
from app.domains.data.sources.factory import data_source_factory


class TestAkshareIntegration:

    @pytest.fixture
    def akshare_source(self):
        for source in data_source_factory.sources:
            if source.name == "akshare":
                return source

        return None

    def test_akshare_source_exists(self, akshare_source):
        assert akshare_source is not None, "Akshare source not found"
        assert akshare_source.name == "akshare"
        assert akshare_source.priority == 2

    @pytest.mark.asyncio
    async def test_akshare_health_check(self, akshare_source):
        if akshare_source:
            is_healthy = await akshare_source.health_check()
            assert isinstance(is_healthy, bool), "Health check must return a boolean"

    @pytest.mark.asyncio
    async def test_parameter_validation(self, akshare_source):
        if akshare_source:

            valid_params = {
                "symbol": "000001",
                "start_date": "2024-01-01",
                "end_date": "2024-01-05",
            }

            is_valid = await akshare_source.validate_params("daily", **valid_params)
            assert is_valid, "Parameter validation should return True for valid params"

            invalid_params = {
                "symbol": "000001",
            }
            is_valid = await akshare_source.validate_params("daily", **invalid_params)
            assert (
                not is_valid
            ), "Parameter validation should return False for invalid params"
