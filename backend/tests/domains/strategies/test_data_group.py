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
