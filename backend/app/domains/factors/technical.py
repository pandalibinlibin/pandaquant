import pandas as pd
import numpy as np
import talib
from typing import Dict, Any, List
from .base import Factor, FactorType


class TechnicalFactor(Factor):
    def __init__(
        self,
        name: str,
        description: str = "",
        parameters: Dict[str, Any] = None,
    ):
        super().__init__(
            name=name,
            factor_type=FactorType.TECHNICAL,
            description=description,
            parameters=parameters,
        )

    def get_required_fields(self) -> List[str]:
        return ["timestamp", "open", "high", "low", "close", "volume"]

    def validate_data(self, data: pd.DataFrame) -> bool:
        required_fields = self.get_required_fields()

        return all(field in data.columns for field in required_fields)


class MovingAverageFactor(TechnicalFactor):
    def __init__(self, period: int = 20, ma_type: str = "SMA"):
        super().__init__(
            name=f"MA_{period}_{ma_type}",
            description=f"{ma_type.upper()} Moving Average of {period} periods",
            parameters={"period": period, "ma_type": ma_type},
        )
        self.period = period
        self.ma_type = ma_type

    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError(f"Invalid data for {self.name}, missing required fields")

        try:
            result = data.copy()

            if self.ma_type == "SMA":
                result[f"ma_{self.period}"] = talib.SMA(
                    data["close"], timeperiod=self.period
                )
            elif self.ma_type == "EMA":
                result[f"ema_{self.period}"] = talib.EMA(
                    data["close"], timeperiod=self.period
                )

            self.record_success()
            return result

        except Exception as e:
            self.record_error()
            raise e
