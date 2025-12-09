"""
BaseStrategy abstract base class for all trading strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import backtrader as bt

from app.domains.data.services import DataService, data_service
from app.domains.factors.services import FactorService, factor_service
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

        self._data_index_to_group: Dict[int, str] = {}

        self._db_session = getattr(self.__class__, "_db_session", None)
        self._backtest_id = getattr(self.__class__, "_backtest_id", None)
        self._strategy_name = self.__class__.__name__

    @classmethod
    @abstractmethod
    def get_data_group_configs(cls) -> List[Dict[str, Any]]:
        """
        Get data group configurations without instantiating the strategy

        Returns list of data group configuration dictionaries
        This allows StrategyService to prepare data before creating cerebro
        """
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

    def _save_signal_to_db(self, signal: Dict[str, Any], current_date: pd.Timestamp):
        """Save signal to database if backtest context is available"""
        if self._db_session is None or self._backtest_id is None:
            return

        try:
            from app.models import Signal
            from uuid import UUID
            from datetime import datetime

            # Convert pandas Timestamp to Python datetime
            if hasattr(current_date, "to_pydatetime"):
                signal_datetime = current_date.to_pydatetime()
            else:
                signal_datetime = current_date
            
            # For daily data, normalize to midnight (remove time component)
            # This ensures consistent signal times for daily strategies
            if isinstance(signal_datetime, datetime):
                signal_datetime = signal_datetime.replace(hour=0, minute=0, second=0, microsecond=0)

            # Create signal record
            signal_record = Signal(
                strategy_name=self._strategy_name,
                symbol=signal.get("symbol", self.symbol),
                signal_time=signal_datetime,
                status=signal.get("action", "unknown"),
                signal_strength=signal.get("confidence", 0.0),
                price=signal.get("price"),
                quantity=signal.get("quantity"),
                message=signal.get("reason", ""),
                backtest_id=(
                    UUID(self._backtest_id)
                    if isinstance(self._backtest_id, str)
                    else self._backtest_id
                ),
            )

            self._db_session.add(signal_record)
            self._db_session.commit()
            logger.debug(
                f"Saved signal: {signal.get('action')} {signal.get('symbol')} at {signal_datetime}"
            )

        except Exception as e:
            logger.error(f"Failed to save signal to database: {e}")
            if self._db_session:
                self._db_session.rollback()

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
