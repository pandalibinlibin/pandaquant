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
            print(f"Error registering factor {factor.name}: {e}")
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
                print(f"Error calculating factor {factor_name}: {e}")
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

    def register_default_factors(self):
        from .technical import (
            MovingAverageFactor,
            RSIFactor,
            MACDFactor,
            BollingerBandsFactor,
            KDJFactor,
        )
        from .fundamental import FinancialRatioFactor
        from .report import MomentumFactor

        self.register_factor(MovingAverageFactor(period=5, ma_type="SMA"))
        self.register_factor(MovingAverageFactor(period=20, ma_type="SMA"))
        self.register_factor(RSIFactor(period=14))
        self.register_factor(
            MACDFactor(fast_period=12, slow_period=26, signal_period=9)
        )
        self.register_factor(BollingerBandsFactor(20, 2.0))
        self.register_factor(KDJFactor(9, 3, 3))

        self.register_factor(FinancialRatioFactor(ratio_type="pe_ratio"))
        self.register_factor(FinancialRatioFactor(ratio_type="pb_ratio"))

        self.register_factor(
            MomentumFactor(
                20, "金融工程报告", "动量因子研究", "量化研究团队", "2024-01-01"
            )
        )


factor_service = FactorService()
factor_service.register_default_factors()
