import pandas as pd
import numpy as np
import talib
from typing import Dict, Any, List, Optional
from .base import Factor, FactorType


class MovingAverageFactor(Factor):
    def __init__(
        self,
        name: str,
        period: int = 20,
        ma_type: str = "SMA",
        factor_class: str = None,
    ):
        super().__init__(
            name=name,
            factor_type=FactorType.TECHNICAL,
            description=f"{ma_type.upper()} Moving Average of {period} periods",
            parameters={"period": period, "ma_type": ma_type},
            factor_class=factor_class,
        )

    def get_required_fields(self) -> List[str]:
        return ["timestamp", "open", "high", "low", "close", "volume"]

    def validate_data(self, data: pd.DataFrame) -> bool:
        required_fields = self.get_required_fields()
        return all(field in data.columns for field in required_fields)

    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError(f"Invalid data for {self.name}, missing required fields")

        try:
            result = data.copy()

            if self.parameters["ma_type"] == "SMA":
                result[self.name] = talib.SMA(
                    data["close"], timeperiod=self.parameters["period"]
                )
            elif self.parameters["ma_type"] == "EMA":
                result[self.name] = talib.EMA(
                    data["close"], timeperiod=self.parameters["period"]
                )

            self.record_success()
            return result

        except Exception as e:
            self.record_error()
            raise e

    def get_qlib_expression(self) -> str:
        if self.parameters["ma_type"] == "SMA":
            return f"Mean($close, {self.parameters['period']})"
        elif self.parameters["ma_type"] == "EMA":
            return f"EMA($close, {self.parameters['period']})"
        return ""

    def get_qlib_dependencies(self) -> List[str]:
        return ["$close"]

    def get_report_reference(self) -> Optional[str]:
        return None

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {
            "period": self.parameters["period"],
            "ma_type": self.parameters["ma_type"],
        }


class RSIFactor(Factor):
    def __init__(self, name: str, period: int = 14, factor_class: str = None):
        super().__init__(
            name=name,
            factor_type=FactorType.TECHNICAL,
            description=f"Relative Strength Index of {period} periods",
            parameters={"period": period},
            factor_class=factor_class,
        )

    def get_required_fields(self) -> List[str]:
        return ["timestamp", "close"]

    def validate_data(self, data: pd.DataFrame) -> bool:
        required_fields = self.get_required_fields()
        return all(field in data.columns for field in required_fields)

    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError(f"Invalid data for {self.name}, missing required fields")

        try:
            result = data.copy()
            result[self.name] = talib.RSI(
                data["close"], timeperiod=self.parameters["period"]
            )
            self.record_success()
            return result
        except Exception as e:
            self.record_error()
            raise e

    def get_qlib_expression(self) -> str:
        return f"RSI($close, {self.parameters['period']})"

    def get_qlib_dependencies(self) -> List[str]:
        return ["$close"]

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {"period": self.parameters["period"]}

    def get_report_reference(self) -> Optional[str]:
        return None


class MACDFactor(Factor):
    def __init__(
        self,
        name: str,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        factor_class: str = None,
    ):
        super().__init__(
            name=name,
            factor_type=FactorType.TECHNICAL,
            description=f"MACD with fast={fast_period}, slow={slow_period}, signal={signal_period}",
            parameters={
                "fast_period": fast_period,
                "slow_period": slow_period,
                "signal_period": signal_period,
            },
            factor_class=factor_class,
        )

    def get_required_fields(self) -> List[str]:
        return ["timestamp", "close"]

    def validate_data(self, data: pd.DataFrame) -> bool:
        required_fields = self.get_required_fields()
        return all(field in data.columns for field in required_fields)

    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError(f"Invalid data for {self.name}, missing required fields")

        try:
            result = data.copy()

            macd_line, signal_line, histogram = talib.MACD(
                data["close"],
                fastperiod=self.parameters["fast_period"],
                slowperiod=self.parameters["slow_period"],
                signalperiod=self.parameters["signal_period"],
            )

            result[
                f"macd_{self.parameters['fast_period']}_{self.parameters['slow_period']}"
            ] = macd_line
            result[f"macd_signal_{self.parameters['signal_period']}"] = signal_line
            result[f"macd_histogram"] = histogram

            self.record_success()

            return result

        except Exception as e:
            self.record_error()
            raise e

    def get_qlib_expression(self) -> str:
        return f"MACD($close, {self.parameters['fast_period']}, {self.parameters['slow_period']}, {self.parameters['signal_period']})"

    def get_qlib_dependencies(self) -> List[str]:
        return ["$close"]

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {
            "fast_period": self.parameters["fast_period"],
            "slow_period": self.parameters["slow_period"],
            "signal_period": self.parameters["signal_period"],
        }

    def get_report_reference(self) -> Optional[str]:
        return "MACD技术指标, 用于趋势分析和买卖信号识别"


class BollingerBandsFactor(Factor):
    def __init__(
        self,
        name: str,
        period: int = 20,
        std_dev: float = 2.0,
        factor_class: str = None,
    ):
        super().__init__(
            name=name,
            factor_type=FactorType.TECHNICAL,
            description=f"Bollinger Bands with period={period}, std_dev={std_dev}",
            parameters={"period": period, "std_dev": std_dev},
            factor_class=factor_class,
        )

    def get_required_fields(self) -> List[str]:
        return ["timestamp", "close"]

    def validate_data(self, data: pd.DataFrame) -> bool:
        required_fields = self.get_required_fields()
        return all(field in data.columns for field in required_fields)

    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError(f"Invalid data for {self.name}, missing required fields")

        try:
            result = data.copy()

            upper_band, middle_band, lower_band = talib.BBANDS(
                data["close"],
                timeperiod=self.parameters["period"],
                nbdevup=self.parameters["std_dev"],
                nbdevdn=self.parameters["std_dev"],
            )

            result[f"bb_upper_{self.parameters['period']}"] = upper_band
            result[f"bb_middle_{self.parameters['period']}"] = middle_band
            result[f"bb_lower_{self.parameters['period']}"] = lower_band

            result[f"bb_width_{self.parameters['period']}"] = (
                upper_band - lower_band
            ) / middle_band
            result[f"bb_position_{self.parameters['period']}"] = (
                data["close"] - lower_band
            ) / (upper_band - lower_band)

            self.record_success()

            return result

        except Exception as e:
            self.record_error()
            raise e

    def get_qlib_expression(self) -> str:
        return (
            f"BBANDS($close, {self.parameters['period']}, {self.parameters['std_dev']})"
        )

    def get_qlib_dependencies(self) -> List[str]:
        return ["$close"]

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {
            "period": self.parameters["period"],
            "std_dev": self.parameters["std_dev"],
        }

    def get_report_reference(self) -> Optional[str]:
        return "Bollinger Bands技术指标, 用于波动性分析和超买超卖判断"


class KDJFactor(Factor):
    def __init__(
        self,
        name: str,
        k_period: int = 9,
        d_period: int = 3,
        j_period: int = 3,
        factor_class: str = None,
    ):
        super().__init__(
            name=name,
            factor_type=FactorType.TECHNICAL,
            description=f"KDJ Stochastic Oscillator with k={k_period}, d={d_period}, j={j_period}",
            parameters={
                "k_period": k_period,
                "d_period": d_period,
                "j_period": j_period,
            },
            factor_class=factor_class,
        )

    def get_required_fields(self) -> List[str]:
        return ["timestamp", "high", "low", "close"]

    def validate_data(self, data: pd.DataFrame) -> bool:
        required_fields = self.get_required_fields()
        return all(field in data.columns for field in required_fields)

    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError(f"Invalid data for {self.name}, missing required fields")

        try:
            result = data.copy()

            k_value, d_value = talib.STOCH(
                data["high"],
                data["low"],
                data["close"],
                fastk_period=self.parameters["k_period"],
                slowk_period=self.parameters["d_period"],
                slowd_period=self.parameters["d_period"],
            )

            j_value = 3 * k_value - 2 * d_value

            result[f"kdj_k_{self.parameters['k_period']}"] = k_value
            result[f"kdj_d_{self.parameters['d_period']}"] = d_value
            result[f"kdj_j_{self.parameters['j_period']}"] = j_value

            self.record_success()
            return result
        except Exception as e:
            self.record_error()
            raise e

    def get_qlib_expression(self) -> str:
        return f"STOCH($high, $low, $close, {self.parameters['k_period']}, {self.parameters['d_period']}, {self.parameters['d_period']})"

    def get_qlib_dependencies(self) -> List[str]:
        return ["$high", "$low", "$close"]

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {
            "k_period": self.parameters["k_period"],
            "d_period": self.parameters["d_period"],
            "j_period": self.parameters["j_period"],
        }

    def get_report_reference(self) -> Optional[str]:
        return "KDJ随机指标, 用于超买超卖判断和趋势分析"
