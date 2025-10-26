import pandas as pd
import backtrader as bt
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from app.domains.data.services import data_service
from app.domains.factors.services import factor_service
from app.core.logging import get_logger
from app.domains.strategies.data_group import DataGroup

logger = get_logger(__name__)


class BaseStrategy(bt.Strategy, ABC):
    """Base class for all strategies using DataGroup architecture with Backtrader"""

    def __init__(self):
        super().__init__()
        self.data_service = data_service
        self.factor_service = factor_service
        self.data_groups: List[DataGroup] = []
        self._init_data_groups()

    @abstractmethod
    def _init_data_groups(self):
        """Initialize data groups for this strategy"""
        pass

    def next(self):
        """Backtrader's next method - called for each bar"""

        group_data = {}
        for group in self.data_groups:
            data = group.get_current_data()
            group_data[group.name] = data

        group_data_with_factors = {}
        for group in self.data_groups:
            data_with_factors = group.calculate_factors_sync(group_data[group.name])
            group_data_with_factors[group.name] = data_with_factors

        signals = self._generate_signals(group_data_with_factors)

        self._execute_trades(signals)

    @abstractmethod
    def _generate_signals(
        self, group_data_with_factors: Dict[str, pd.DataFrame]
    ) -> List[Dict[str, Any]]:
        """Generate signals based on all group data and factors"""
        pass

    @abstractmethod
    def _execute_trades(self, signals: List[Dict[str, Any]]):
        """Execute trades based on signals"""
        pass
