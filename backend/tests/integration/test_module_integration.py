"""
Module integration test

Tests that all modules work together correctly
- Data Service
- Factor Service
- Strategy Service
- Signal Push Service
"""

import pytest

from app.domains.data.services import data_service
from app.domains.factors.services import factor_service
from app.domains.strategies.services import StrategyService
from app.domains.signals.services import signal_push_service


class TestModuleIntegration:
    """Test integration between all modules"""

    def test_all_services_initialized(self):
        """Test all services can be initialized"""
        assert data_service is not None
        assert factor_service is not None
        assert signal_push_service is not None

        strategy_service = StrategyService()
        assert strategy_service is not None

    def test_services_have_required_attributes(self):
        """Test all services have required attributes"""

        assert hasattr(data_service, "data_source_factory")
        assert hasattr(data_service, "fetch_data")

        assert hasattr(factor_service, "factors")
        assert hasattr(factor_service, "register_factor")

        assert hasattr(signal_push_service, "channels")
        assert hasattr(signal_push_service, "push_signal")

        strategy_service = StrategyService()
        assert hasattr(strategy_service, "strategies")
        assert hasattr(strategy_service, "run_backtest")

    def test_strategy_uses_data_and_factor_services(self):
        """Test that strategies integrate with data and factor services"""

        strategy_service = StrategyService()

        strategy_class = strategy_service.get_strategy("DualMovingAverageStrategy")
        assert strategy_class is not None

        assert hasattr(strategy_class, "__init__")

    def test_data_service_has_factory(self):
        """Test DataService has data source factory"""

        assert data_service.data_source_factory is not None
        assert hasattr(data_service.data_source_factory, "fetch_data_with_fallback")

    def test_factor_service_structure(self):
        """Test FactorService structure"""

        assert isinstance(factor_service.factors, dict)
        assert hasattr(factor_service, "list_factors")
        assert hasattr(factor_service, "get_factor")

        factors_list = factor_service.list_factors()
        assert isinstance(factors_list, list)

    def test_strategy_service_and_signal_push_integration(self):
        """Test StrategyService and SignalPushService integration"""

        strategy_service = StrategyService()

        assert strategy_service is not None
        assert signal_push_service is not None

        strategies = strategy_service.list_strategies()
        assert len(strategies) > 0, "Should have at least one strategy"

        assert len(signal_push_service.channels) > 0, "Should have at least one channel"

    @pytest.mark.asyncio
    async def test_complete_integration_flow(self):
        """Test complete integration flow: Data -> Factor -> Strategy -> Signal"""
        import pandas as pd
        from unittest.mock import AsyncMock, patch, MagicMock
        from app.domains.data.services import DataService
        from app.domains.strategies.enums import TradingMode

        def create_mock_data(start_date: str, end_date: str) -> pd.DataFrame:
            """Create mock OHLCV data for testing"""
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            dates = pd.date_range(start=start, end=end, freq="D")
            base_price = 10.0
            data = []
            for i, date in enumerate(dates):
                price = base_price + i * 0.1 + (i % 5) * 0.2
                data.append(
                    {
                        "timestamp": date,
                        "open": price * 0.99,
                        "high": price * 1.02,
                        "low": price * 0.98,
                        "close": price,
                        "volume": 1000000 + i * 10000,
                    }
                )
            return pd.DataFrame(data)

        mock_data = create_mock_data("2024-01-01", "2024-01-31")

        with patch.object(
            DataService, "fetch_data", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_data

            with patch.object(
                signal_push_service, "push_signal", new_callable=AsyncMock
            ) as mock_push:
                mock_push.return_value = {"test_channel": MagicMock(success=True)}

                strategy_service = StrategyService()
                original_data_service = strategy_service.data_service
                strategy_service.data_service = DataService()
                strategy_service.data_service.fetch_data = mock_fetch

                assert strategy_service.data_service is not None
                assert strategy_service.factor_service is not None

                result = await strategy_service.run_backtest(
                    strategy_name="DualMovingAverageStrategy",
                    symbol="000001.SZ",
                    start_date="2024-01-01",
                    end_date="2024-01-31",
                    initial_capital=1000000.0,
                    mode=TradingMode.BACKTEST,
                )

                strategy_service.data_service = original_data_service

                assert result is not None
                assert result["strategy_name"] == "DualMovingAverageStrategy"
                assert "performance" in result

                assert mock_fetch.called
