"""
StrategyService tests
"""

import pytest
from app.domains.strategies.services import StrategyService


class TestStrategyService:
    """Test StrategyService implementation"""

    def test_service_initialization(self):
        """Test service can be initialized correctly"""
        service = StrategyService()

        assert service is not None

    def test_auto_discover_strategies(self):
        """Test service can auto-discover strategies"""
        service = StrategyService()

        strategies = service.list_strategies()

        assert len(strategies) > 0
        assert "DualMovingAverageStrategy" in strategies

    def test_get_strategy(self):
        """Test service can get a strategy by name"""
        service = StrategyService()

        strategy_class = service.get_strategy("DualMovingAverageStrategy")
        assert strategy_class is not None

    def test_register_strategy(self):
        """Test service can register a new strategy"""
        service = StrategyService()

        from app.domains.strategies.dual_moving_average_strategy import (
            DualMovingAverageStrategy,
        )

        service.register_strategy("TestStrategy", DualMovingAverageStrategy)

        strategies = service.list_strategies()
        assert "TestStrategy" in strategies
