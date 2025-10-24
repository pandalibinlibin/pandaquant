import backtrader as bt
import pandas as pd
from typing import Dict, Any, Optional
from app.domains.factors.services import factor_service


class BaseStrategy(bt.Strategy):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.factors = config.get("factors", [])
        self.risk_params = config.get("risk_params", {})
        self.factor_objects = {}

        self._init_factors()

    def _init_factors(self):
        for factor_name in self.factors:
            factor = factor_service.get_factor(factor_name)
            if factor:
                self.factor_objects[factor_name] = factor
            else:
                print(f"Warning: Factor {factor_name} not found")

    async def next(self):
        raise NotImplemented("Subclasses must implement this method")

    def _get_historical_data(
        self, symbol_index: int = 0, data_type: str = "daily"
    ) -> pd.DataFrame:
        try:
            data = self.datas[symbol_index]

            from app.domains.data.sources.base import DataSource

            standard_fields = DataSource.STANDARD_FIELDS.get(
                data_type, DataSource.STANDARD_FIELDS["daily"]
            )

            base_data = {
                "timestamp": data.datetime.datetime(),
                "symbol": f"SYMBOL_{symbol_index}",
            }

            for field in standard_fields:
                if field in ["timestamp", "symbol"]:
                    continue

                field_value = None
                if hasattr(data, field):
                    try:
                        field_value = (
                            data[field][0] if data[field][0] is not None else None
                        )
                    except (IndexError, AttributeError):
                        field_value = None
                if field_value is not None:
                    base_data[field] = field_value
                else:
                    if field in ["open", "high", "low", "close", "price"]:
                        base_data[field] = -999999.0
                    elif field in ["volume", "amount"]:
                        base_data[field] = -999999.0
                    elif field in [
                        "pct_chg",
                        "change",
                        "turnover",
                        "pe",
                        "pb",
                        "ps",
                        "pcf",
                    ]:
                        base_data[field] = -999999.0
                    elif field in [
                        "market_cap",
                        "circulating_market_cap",
                        "total_shares",
                        "float_shares",
                    ]:
                        base_data[field] = -999999.0
                    elif field in [
                        "value",
                        "unit",
                        "description",
                        "category",
                        "subcategory",
                    ]:
                        base_data[field] = None
                    elif field in [
                        "revenue",
                        "profit",
                        "assets",
                        "liabilities",
                        "equity",
                    ]:
                        base_data[field] = -999999.0
                    elif field in ["factor_name", "factor_value", "factor_type"]:
                        base_data[field] = None
                    else:
                        # 其他字段使用None作为默认值
                        base_data[field] = None

            df = pd.DataFrame([base_data])
            return df

        except Exception as e:
            print(f"Error getting historical data: {e}")
            return pd.DataFrame()

    def _generate_signal(
        self, factor_values: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        raise NotImplementedError("Subclass must implement this method")

    def _execute_trade(self, signal: Dict[str, Any]):
        raise NotImplementedError("Subclass must implement this method")
