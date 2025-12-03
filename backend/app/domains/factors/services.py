"""
因子服务模块
负责因子的计算, 存储和管理
"""

import asyncio
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Union
from app.core.config import settings
from app.domains.data.services import DataService
from .base import Factor, FactorType
from app.core.logging import get_logger

logger = get_logger(__name__)


class FactorService:
    def __init__(self):
        self.factors: Dict[str, Factor] = {}
        self.factor_types: Dict[FactorType, List[str]] = {
            FactorType.TECHNICAL: [],
            FactorType.FUNDAMENTAL: [],
            FactorType.CUSTOM: [],
            FactorType.MACRO: [],
            FactorType.SENTIMENT: [],
        }

    def register_factor(self, factor: Factor):
        try:
            if factor.name in self.factors:
                return False

            self.factors[factor.name] = factor
            self.factor_types[factor.factor_type].append(factor.name)
            return True
        except Exception as e:
            logger.error(f"Error registering factor {factor.name}: {e}")
            return False

    def get_factor(self, name: str) -> Optional[Factor]:
        return self.factors.get(name)

    def get_factors_by_type(self, factor_type: FactorType) -> List[Factor]:
        factor_names = self.factor_types.get(factor_type, [])
        return [self.factors[name] for name in factor_names if name in self.factors]

    def list_factors(self) -> List[str]:
        return list(self.factors.keys())

    def unregister_factor(self, name: str) -> bool:
        if name not in self.factors:
            return False

        factor = self.factors[name]
        self.factor_types[factor.factor_type].remove(name)
        del self.factors[name]
        return True

    async def calculate_factor(
        self, factor_name: str, data: pd.DataFrame, **kwargs
    ) -> pd.DataFrame:
        factor = self.get_factor(factor_name)
        if not factor:
            raise ValueError(f"Factor {factor_name} not found")

        if not factor.is_available():
            raise ValueError(f"Factor {factor_name} is not available")

        if not factor.validate_data(data):
            raise ValueError(f"Data validation failed for factor {factor_name}")

        try:
            result = await factor.calculate(data, **kwargs)
            factor.record_success()
            return result
        except Exception as e:
            factor.record_error()
            raise e

    async def calculate_multiple_factors(
        self, factor_names: List[str], data: pd.DataFrame, **kwargs
    ) -> Dict[str, pd.DataFrame]:
        results = {}

        for factor_name in factor_names:
            try:
                result = await self.calculate_factor(factor_name, data, **kwargs)
                results[factor_name] = result
            except Exception as e:
                logger.error(f"Error calculating factor {factor_name}: {e}")
                results[factor_name] = pd.DataFrame()

        return results

    def get_factor_status(self, name: str) -> Dict[str, Any]:
        factor = self.get_factor(name)
        if not factor:
            return None

        return {
            "name": factor.name,
            "status": factor.status.value,
            "last_calculation": factor.last_calculation,
            "error_count": factor.error_count,
            "is_available": factor.is_available(),
        }

    def list_factor_classes(self) -> List[Dict[str, Any]]:
        """
        List all available factor classes (not instances)
        Automatically discovers all Factor subclasses with detailed metadata
        """
        import inspect
        from . import technical, fundamental, report

        def get_class_metadata(cls, factor_type: str, module: str) -> Dict[str, Any]:
            """Extract metadata from a factor class"""
            # Get __init__ signature to extract parameters
            sig = inspect.signature(cls.__init__)
            parameters = []

            for param_name, param in sig.parameters.items():
                if param_name in ["self", "name", "factor_class"]:
                    continue

                param_info = {
                    "name": param_name,
                    "type": (
                        param.annotation.__name__
                        if param.annotation != inspect.Parameter.empty
                        else "any"
                    ),
                }

                # Get default value if exists
                if param.default != inspect.Parameter.empty:
                    param_info["default"] = param.default

                parameters.append(param_info)

            # Get required fields by creating a temporary instance
            try:
                temp_instance = cls(name="temp")
                required_fields = temp_instance.get_required_fields()
            except:
                required_fields = []

            # Get docstring as description
            description = (
                cls.__doc__.strip() if cls.__doc__ else f"{cls.__name__} factor class"
            )

            return {
                "class_name": cls.__name__,
                "display_name": cls.__name__,
                "factor_type": factor_type,
                "module": module,
                "description": description,
                "parameters": parameters,
                "required_fields": required_fields,
            }

        factor_classes = []

        # Scan technical factors
        for name, obj in inspect.getmembers(technical, inspect.isclass):
            if obj.__module__ == "app.domains.factors.technical" and name.endswith(
                "Factor"
            ):
                factor_classes.append(get_class_metadata(obj, "technical", "technical"))

        # Scan fundamental factors
        for name, obj in inspect.getmembers(fundamental, inspect.isclass):
            if obj.__module__ == "app.domains.factors.fundamental" and name.endswith(
                "Factor"
            ):
                factor_classes.append(
                    get_class_metadata(obj, "fundamental", "fundamental")
                )

        # Scan report factors
        for name, obj in inspect.getmembers(report, inspect.isclass):
            if obj.__module__ == "app.domains.factors.report" and name.endswith(
                "Factor"
            ):
                factor_classes.append(get_class_metadata(obj, "report", "report"))

        return factor_classes


factor_service = FactorService()
