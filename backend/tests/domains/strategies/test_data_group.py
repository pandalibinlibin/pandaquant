"""
DataGroup tests
"""

import pytest
from app.domains.strategies.daily_data_group import DailyDataGroup


class TestDailyDataGroup:
    """Test DailyGroup implementation"""

    def test_daily_data_group_initialization(self):
        """Test DailyDataGroup can be initialized correctly"""

        group = DailyDataGroup(name="daily_test", weight=1.0, factors=[])

        assert group is not None
        assert group.name == "daily_test"
        assert group.weight == 1.0
        assert group.data_type == "daily"
        assert group.factors == []

    def test_base_strategy_is_abstract(self):
        """Test that BaseStrategy cannot be instantiated directly"""
        from app.domains.strategies.base_strategy import BaseStrategy

        with pytest.raises(TypeError):
            BaseStrategy()

    def test_daily_data_group_set_service(self):
        """Test DailyDataGroup can set services"""
        from app.domains.data.services import data_service
        from app.domains.factors.services import factor_service

        group = DailyDataGroup(name="daily_test", weight=1.0, factors=[])

        assert group.data_service is None
        assert group.factor_service is None

        group.set_service(data_service, factor_service)

        assert group.data_service is not None
        assert group.factor_service is not None
