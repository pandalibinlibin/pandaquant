"""
DualMovingAverageStrategy tests
"""

import pytest

from app.domains.strategies.dual_moving_average_strategy import (
    DualMovingAverageStrategy,
)


class TestDualMovingAverageStrategy:
    """Test DualMovingAverageStrategy class structure and configuration"""

    def test_strategy_is_a_class(self):
        """Test that DualMovingAverageStrategy is a class"""
        assert isinstance(DualMovingAverageStrategy, type)

    def test_strategy_has_required_methods(self):
        """Test strategy class has all required methods"""
        assert hasattr(DualMovingAverageStrategy, "__init__")
        assert hasattr(DualMovingAverageStrategy, "next")
        assert hasattr(DualMovingAverageStrategy, "_generate_signals")
        assert hasattr(DualMovingAverageStrategy, "_execute_trades")
        assert hasattr(DualMovingAverageStrategy, "_init_data_groups")

    def test_strategy_inheritance(self):
        """Test strategy inherits from correct base classes"""
        from app.domains.strategies.base_strategy import BaseStrategy

        assert issubclass(DualMovingAverageStrategy, BaseStrategy)
