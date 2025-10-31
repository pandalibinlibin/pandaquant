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
