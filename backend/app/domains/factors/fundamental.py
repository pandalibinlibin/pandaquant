import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from .base import Factor, FactorType


class FinancialRatioFactor(Factor):
    def __init__(
        self, name: str, ratio_type: str = "pe_ratio", factor_class: str = None
    ):
        super().__init__(
            name=name,
            factor_type=FactorType.FUNDAMENTAL,
            description=f"Financial ratio factor: {ratio_type}",
            parameters={"ratio_type": ratio_type},
            factor_class=factor_class,
        )

    def get_required_fields(self) -> List[str]:
        return [
            "timestamp",
            "symbol",
            "market_cap",
            "pe_ratio",
            "pb_ratio",
            "roe",
            "roa",
        ]

    def validate_data(self, data: pd.DataFrame) -> bool:
        required_fields = self.get_required_fields()
        return all(field in data.columns for field in required_fields)

    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError(f"Invalid data for {self.name}, missing required fields")

        try:
            result = data.copy()

            if self.parameters["ratio_type"] == "pe_ratio":
                result[f"pe_ratio"] = data["pe_ratio"]
            elif self.parameters["ratio_type"] == "pb_ratio":
                result[f"pb_ratio"] = data["pb_ratio"]
            elif self.parameters["ratio_type"] == "roe":
                result[f"roe"] = data["roe"]
            elif self.parameters["ratio_type"] == "roa":
                result[f"roa"] = data["roa"]

            self.record_success()
            return result

        except Exception as e:
            self.record_error()
            raise e

    def get_qlib_expression(self) -> str:
        if self.parameters["ratio_type"] == "pe_ratio":
            return f"PE($close)"
        elif self.parameters["ratio_type"] == "pb_ratio":
            return f"PB($close)"
        elif self.parameters["ratio_type"] == "roe":
            return f"ROE($close)"
        elif self.parameters["ratio_type"] == "roa":
            return f"ROA($close)"
        return ""

    def get_qlib_dependencies(self) -> List[str]:
        return ["$close"]

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {"ratio_type": self.parameters["ratio_type"]}

    def get_report_reference(self) -> Optional[str]:
        return f"财务比率因子: {self.parameters['ratio_type']}, 用于基本面分析"
