import pandas as pd
import numpy as np
import talib
from typing import Dict, Any, List, Optional
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
                result[self.name] = talib.SMA(data["close"], timeperiod=self.period)
            elif self.ma_type == "EMA":
                result[self.name] = talib.EMA(data["close"], timeperiod=self.period)

            self.record_success()
            return result

        except Exception as e:
            self.record_error()
            raise e

    def get_qlib_expression(self) -> str:
        if self.ma_type == "SMA":
            return f"Mean($close, {self.period})"
        elif self.ma_type == "EMA":
            return f"EMA($close, {self.period})"
        return ""

    def get_qlib_dependencies(self) -> List[str]:
        return ["$close"]

    def get_report_reference(self) -> Optional[str]:
        return None

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {"period": self.period, "ma_type": self.ma_type}


class RSIFactor(TechnicalFactor):
    def __init__(self, period: int = 14):
        super().__init__(
            name=f"RSI_{period}",
            description=f"Relative Strength Index of {period} periods",
            parameters={"period": period},
        )
        self.period = period

    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError(f"Invalid data for {self.name}, missing required fields")

        try:
            result = data.copy()
            result[self.name] = talib.RSI(data["close"], timeperiod=self.period)
            self.record_success()
            return result
        except Exception as e:
            self.record_error()
            raise e

    def get_qlib_expression(self) -> str:
        return f"RSI($close, {self.period})"

    def get_qlib_dependencies(self) -> List[str]:
        return ["$close"]

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {"period": self.period}

    def get_report_reference(self) -> Optional[str]:
        return None


class MACDFactor(TechnicalFactor):
    def __init__(
        self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9
    ):
        super().__init__(
            name=f"MACD_{fast_period}_{slow_period}_{signal_period}",
            description=f"MACD with fast={fast_period}, slow={slow_period}, signal={signal_period}",
            parameters={
                "fast_period": fast_period,
                "slow_period": slow_period,
                "signal_period": signal_period,
            },
        )

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError(f"Invalid data for {self.name}, missing required fields")

        try:
            result = data.copy()

            macd_line, signal_line, histogram = talib.MACD(
                data["close"],
                fastperiod=self.fast_period,
                slowperiod=self.slow_period,
                signalperiod=self.signal_period,
            )

            result[f"macd_{self.fast_period}_{self.slow_period}"] = macd_line
            result[f"macd_signal_{self.signal_period}"] = signal_line
            result[f"macd_histogram"] = histogram

            self.record_success()

            return result

        except Exception as e:
            self.record_error()
            raise e

    def get_qlib_expression(self) -> str:
        return f"MACD($close, {self.fast_period}, {self.slow_period}, {self.signal_period})"

    def get_qlib_dependencies(self) -> List[str]:
        return ["$close"]

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
            "signal_period": self.signal_period,
        }

    def get_report_reference(self) -> Optional[str]:
        return "MACD技术指标, 用于趋势分析和买卖信号识别"


class BollingerBandsFactor(TechnicalFactor):
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__(
            name=f"BB_{period}_{std_dev}",
            description=f"Bollinger Bands with period={period}, std_dev={std_dev}",
            parameters={"period": period, "std_dev": std_dev},
        )
        self.period = period
        self.std_dev = std_dev

    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError(f"Invalid data for {self.name}, missing required fields")

        try:
            result = data.copy()

            upper_band, middle_band, lower_band = talib.BBANDS(
                data["close"],
                timeperiod=self.period,
                nbdevup=self.std_dev,
                nbdevdn=self.std_dev,
            )

            result[f"bb_upper_{self.period}"] = upper_band
            result[f"bb_middle_{self.period}"] = middle_band
            result[f"bb_lower_{self.period}"] = lower_band

            result[f"bb_width_{self.period}"] = (upper_band - lower_band) / middle_band
            result[f"bb_position_{self.period}"] = (data["close"] - lower_band) / (
                upper_band - lower_band
            )

            self.record_success()

            return result

        except Exception as e:
            self.record_error()
            raise e

    def get_qlib_expression(self) -> str:
        return f"BBANDS($close, {self.period}, {self.std_dev})"

    def get_qlib_dependencies(self) -> List[str]:
        return ["$close"]

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {"period": self.period, "std_dev": self.std_dev}

    def get_report_reference(self) -> Optional[str]:
        return "Bollinger Bands技术指标, 用于波动性分析和超买超卖判断"


class KDJFactor(TechnicalFactor):
    def __init__(self, k_period: int = 9, d_period: int = 3, j_period: int = 3):
        super().__init__(
            name=f"KDJ_{k_period}_{d_period}_{j_period}",
            description=f"KDJ Stochastic Oscillator with k={k_period}, d={d_period}, j={j_period}",
            parameters={
                "k_period": k_period,
                "d_period": d_period,
                "j_period": j_period,
            },
        )

        self.k_period = k_period
        self.d_period = d_period
        self.j_period = j_period

    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError(f"Invalid data for {self.name}, missing required fields")

        try:
            result = data.copy()

            k_value, d_value = talib.STOCH(
                data["high"],
                data["low"],
                data["close"],
                fastk_period=self.k_period,
                slowk_period=self.d_period,
                slowd_period=self.d_period,
            )

            j_value = 3 * k_value - 2 * d_value

            result[f"kdj_k_{self.k_period}"] = k_value
            result[f"kdj_d_{self.d_period}"] = d_value
            result[f"kdj_j_{self.j_period}"] = j_value

            self.record_success()
            return result
        except Exception as e:
            self.record_error()
            raise e

    def get_qlib_expression(self) -> str:
        return f"STOCH($high, $low, $close, {self.k_period}, {self.d_period}, {self.d_period})"

    def get_qlib_dependencies(self) -> List[str]:
        return ["$high", "$low", "$close"]

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {
            "k_period": self.k_period,
            "d_period": self.d_period,
            "j_period": self.j_period,
        }

    def get_report_reference(self) -> Optional[str]:
        return "KDJ随机指标, 用于超买超卖判断和趋势分析"
