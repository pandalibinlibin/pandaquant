import pandas as pd
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from app.core.logging import get_logger
from app.domains.factors.base import Factor

logger = get_logger(__name__)


class DataGroup(ABC):
    """Base class for data groups in strategies"""

    def __init__(
        self, name: str, weight: float = 1.0, factors: List[Dict[str, Any]] = None
    ):
        self.name = name
        self.weight = weight
        self.factors = factors or []
        self.data_service = None
        self.factor_service = None
        self._cached_data = None
        self._factor_data = None

    @abstractmethod
    async def get_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Get data for this group"""
        pass

    def get_current_data(self) -> pd.DataFrame:
        """Get current data for this group (synchronous)"""
        if self._cached_data is None:
            raise ValueError(f"No cached data available for group {self.name}")
        return self._cached_data

    def set_current_data(self, data: pd.DataFrame):
        """set current data for this group"""
        self._cached_data = data

    @abstractmethod
    async def calculate_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate factors for this group using factor module"""
        pass

    def get_factor_data(self) -> pd.DataFrame:
        """Get factor data for this group (synchronous)"""
        if self._factor_data is None:
            raise ValueError(f"No factor data available for group {self.name}")
        return self._factor_data

    def set_factor_data(self, data: pd.DataFrame):
        """set factor data for this group"""
        self._factor_data = data

    def set_services(self, data_service, factor_service):
        """Set services for this group"""
        self.data_service = data_service
        self.factor_service = factor_service

    def get_factors(self) -> List[Factor]:
        """Get factors for this group"""
        return self.factors

    def add_factor(self, factor: Factor):
        """Add a factor to this group"""
        if factor not in self.factors:
            self.factors.append(factor)

    def remove_factor(self, factor: Factor):
        """Remove a factor from this group"""
        if factor in self.factors:
            self.factors.remove(factor)

    def calculate_factors_sync(self, data: pd.DataFrame) -> pd.DataFrame:
        if self._factor_data is not None:
            return self._factor_data
        return data
