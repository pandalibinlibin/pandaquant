"""
BaseStrategy abstract base class for all trading strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import backtrader as bt

from app.domains.data.services import DataService, data_service
from app.domains.factors.services import FactorService, factor_service
from app.domains.strategies.data_group import DataGroup
from app.domains.strategies.enums import TradingMode
from app.domains.signals.services import signal_push_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class StrategyMeta(type(bt.Strategy), type(ABC)):
    """Meta class to resolve metaclass conflict between Backtrader and ABC"""

    pass


class BaseStrategy(bt.Strategy, ABC, metaclass=StrategyMeta):
    """
    Base class for all strategies using DataGroup architecture with Backtrader
    """

    def __init__(self):
        super().__init__()

        self.mode = getattr(self.__class__, "_run_mode", TradingMode.BACKTEST)
        self.symbol = getattr(self.__class__, "_run_symbol", "unknown")
        self.signal_push_service = signal_push_service

        self.data_service: Optional[DataService] = data_service
        self.factor_service: Optional[FactorService] = factor_service
        self.data_groups: List[DataGroup] = []
        self._data_index_to_group: Dict[int, str] = {}

        self._init_data_groups()
        for group in self.data_groups:
            group.set_service(self.data_service, self.factor_service)

    @classmethod
    @abstractmethod
    def get_data_group_configs(cls) -> List[Dict[str, Any]]:
        """
        Get data group configurations without instantiating the strategy

        Returns list of data group configuration dictionaries
        This allows StrategyService to prepare data before creating cerebro
        """
        pass

    @abstractmethod
    def _init_data_groups(self):
        """Initialize data groups for this strategy"""
        pass

    def _get_group_name(self, data_index: int) -> Optional[str]:
        """
        Get DataGroup name for a given data feed index
        """

        if data_index < len(self.datas):
            data = self.datas[data_index]
            if hasattr(data, "_data_group_name"):
                return data._data_group_name

        return self._data_index_to_group.get(data_index)

    def next(self):
        """
        Backtrader's next method - called for each bar

        Access data via:
        - self.data0: Main data feed (first OHLCV DataGroup)
        - self.data1: Second DataGroup (if exists)
        - self.data2: Third DataGroup (if exists)
        - etc.

        To identify which DataGroup corresponds to which data feed:
        - Use self._get_group_name(0) for data0, self._get_group_name(1) for data1, etc.
        - Or access feed._data_group_name attribute directly
        """

        current_date = self.data0.datetime.datetime(0)

        group_data = {}
        for i, data in enumerate(self.datas):
            group_name = self._get_group_name(i) or f"data{i}"
            group_data[group_name] = data

        signals = self._generate_signals(group_data, current_date)

        self._execute_trades(signals, current_date)

    @abstractmethod
    def _generate_signals(
        self, group_data: Dict[str, bt.feeds.DataBase], current_date: pd.Timestamp
    ) -> List[Dict[str, Any]]:
        """
        Generate signals based on all group data

        """
        pass

    @abstractmethod
    def _execute_trades(
        self, signals: List[Dict[str, Any]], current_date: pd.Timestamp
    ):
        """
        Execute trades based on signals
        """
        pass

    async def _push_signal_if_needed(self, signal_data: dict):
        """Push signal if in paper/live trading mode"""
        if self.mode in [TradingMode.PAPER_TRADING, TradingMode.LIVE_TRADING]:
            await self.signal_push_service.push_signal(signal_data)
