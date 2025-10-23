import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from .base import Factor, FactorType


class ReportFactor(Factor):
    def __init__(
        self,
        name: str,
        description: str = "",
        parameters: Dict[str, Any] = None,
        report_source: str = "",
        report_title: str = "",
        report_author: str = "",
        report_date: str = "",
    ):
        super().__init__(
            name=name,
            factor_type=FactorType.CUSTOM,
            description=description,
            parameters=parameters,
        )
        self.report_source = report_source
        self.report_title = report_title
        self.report_author = report_author
        self.report_date = report_date

    def get_required_fields(self) -> List[str]:
        return ["timestamp", "symbol", "close", "volume", "market_cap"]

    def validate_data(self, data: pd.DataFrame) -> bool:
        required_fields = self.get_required_fields()
        return all(field in data.columns for field in required_fields)

    def get_qlib_expression(self) -> str:
        return ""

    def get_qlib_dependencies(self) -> List[str]:
        return []

    def get_report_reference(self) -> Optional[str]:
        return f"来源: {self.report_source}\n标题: {self.report_title}\n作者: {self.report_author}\n日期: {self.report_date}"

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {
            "report_source": self.report_source,
            "report_title": self.report_title,
            "report_author": self.report_author,
            "report_date": self.report_date,
        }


class MomentumFactor(ReportFactor):
    def __init__(
        self,
        lookback_period: int = 20,
        report_source: str = "金融工程报告",
        report_title: str = "动量因子研究",
        report_author: str = "量化研究团队",
        report_date: str = "2024-01-01",
    ):
        super().__init__(
            name=f"Momentum_{lookback_period}",
            description=f"动量因子, 回望期{lookback_period}天",
            parameters={"lookback_period": lookback_period},
            report_source=report_source,
            report_title=report_title,
            report_author=report_author,
            report_date=report_date,
        )
        self.lookback_period = lookback_period

    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError(f"Invalid data for {self.name}, missing required fields")

        try:
            result = data.copy()

            result[f"momentum_{self.lookback_period}"] = (
                data["close"] / data["close"].shift(self.lookback_period) - 1
            )

            self.record_success()
            return result

        except Exception as e:
            self.record_error()
            raise e

    def get_qlib_expression(self) -> str:
        return f"Ref($close, {self.lookback_period}) / $close - 1"

    def get_qlib_dependencies(self) -> List[str]:
        return ["$close"]

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {
            "lookback_period": self.lookback_period,
            "report_source": self.report_source,
            "report_title": self.report_title,
            "report_author": self.report_author,
            "report_date": self.report_date,
        }
