from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
import pandas as pd
import numpy as np
from datetime import datetime
from enum import Enum


class FactorType(Enum):
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    CUSTOM = "custom"
    MACRO = "macro"
    SENTIMENT = "sentiment"


class FactorStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class Factor(ABC):
    def __init__(
        self,
        name: str,
        factor_type: FactorType,
        description: str = "",
        parameters: Dict[str, Any] = None,
    ):
        self.name = name
        self.factor_type = factor_type
        self.description = description
        self.parameters = parameters or {}
        self.status = FactorStatus.ACTIVE
        self.last_calculation = None
        self.error_count = 0
        self.max_errors = 3

    @abstractmethod
    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_required_fields(self) -> List[str]:
        pass

    @abstractmethod
    def validate_data(self, data: pd.DataFrame) -> bool:
        pass

    def get_factor_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.factor_type.value,
            "description": self.description,
            "parameters": self.parameters,
            "status": self.status.value,
            "last_calculation": self.last_calculation,
            "error_count": self.error_count,
        }

    def record_success(self):
        self.error_count = 0
        self.last_calculation = datetime.now()
        self.status = FactorStatus.ACTIVE

    def record_error(self):
        self.error_count += 1
        self.last_calculation = datetime.now()
        if self.error_count >= self.max_errors:
            self.status = FactorStatus.ERROR

    def is_available(self) -> bool:
        return self.status == FactorStatus.ACTIVE

    def reset_status(self):
        self.status = FactorStatus.ACTIVE
        self.error_count = 0

    @abstractmethod
    def get_qlib_expression(self) -> str:
        pass

    @abstractmethod
    def get_qlib_dependencies(self) -> List[str]:
        pass

    def is_qlib_compatible(self) -> bool:
        return hasattr(self, "get_qlib_expression")

    @abstractmethod
    def get_report_reference(self) -> Optional[str]:
        pass

    @abstractmethod
    def get_factor_formula(self) -> str:
        pass

    @abstractmethod
    def get_implementation_notes(self) -> str:
        pass

    def is_report_factor(self) -> bool:
        return (
            hasattr(self, "get_report_reference")
            and self.get_report_reference() is not None
        )
