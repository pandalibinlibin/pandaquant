from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime
from enum import Enum


class DataSourceStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class DataSource(ABC):
    def __init__(self, name: str, priority: int = 1):
        self.name = name
        self.priority = priority
        self.status = DataSourceStatus.ACTIVE
        self.last_check = None
        self.error_count = 0
        self.max_errors = 3

    @abstractmethod
    async def fetch_data(self, data_type: str, **kwargs) -> pd.DataFrame:
        pass

    @abstractmethod
    async def get_available_data_types(self) -> List[str]:
        pass

    @abstractmethod
    async def validate_params(self, data_type: str, **kwargs) -> bool:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    async def is_available(self) -> bool:
        if self.status == DataSourceStatus.INACTIVE:
            return False

        if self.error_count >= self.max_errors:
            self.status = DataSourceStatus.ERROR
            return False

        return await self.health_check()

    def record_error(self):
        self.error_count += 1
        self.last_check = datetime.now()
        if self.error_count >= self.max_errors:
            self.status = DataSourceStatus.ERROR

    def record_success(self):
        self.error_count = 0
        self.last_check = datetime.now()
        self.status = DataSourceStatus.ACTIVE
