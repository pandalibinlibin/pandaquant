"""
DataGroup abstract base class

Each DataGroup manages a specific type of data and factors.
All DataGroups are converted to Backtrader feeds and added via cerebro.adddata().
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import backtrader as bt
from app.domains.data.services import DataService
from app.domains.factors.services import FactorService
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataGroup(ABC):
    """
    Abstract base class for data groups

    Each DataGroup:
    1. Fetches data from DataService
    2. calculates factors via FactorService
    3. Converts to Backtrader feed format
    4. Returns a Backtrader feed that can be added via cerebro.adddata()
    """

    def __init__(
        self, name: str, weight: float = 1.0, factors: List[Dict[str, Any]] = None
    ):
        """
        Initialize DataGroup

        Args:
            name: Name of the data group
            weight: Weight for this data group (for signal aggregation)
            factors: List of factor configurations
        """
        self.name = name
        self.weight = weight
        self.factors = factors or []
        self.data_service: Optional[DataService] = None
        self.factor_service: Optional[FactorService] = None
        self._prepared_data: Optional[pd.DataFrame] = None

    def set_service(self, data_service: DataService, factor_service: FactorService):
        """Set data and factor services"""
        self.data_service = data_service
        self.factor_service = factor_service

    @abstractmethod
    async def prepare_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Prepare data for this group: fetch data and calculate factors

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with original data + factor columns, datetime index
        """
        pass

    @abstractmethod
    def to_backtrader_feed(self) -> bt.feeds.PandasData:
        """
        Convert prepared data to Backtrader feed

        Returns:
            Backtrader PandasData feed that can be added via cerebro.adddata()
        """
        pass
