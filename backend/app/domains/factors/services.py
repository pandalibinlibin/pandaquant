"""
因子服务模块
负责因子的计算, 存储和管理
"""

import asyncio
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import Factor, MarketData
from app.core.db import get_db
from app.domains.data.services import DataService
import technical.indicators as ti


class FactorService:
    def __init__(self):
        self.data_service = DataService()

    async def calculate_technical_factors(
        self, symbol: str, start_date: str, end_date: str, factors: List[str] = None
    ) -> pd.DataFrame:
        try:
            data = await self.data_service.get_data_from_influxdb(
                symbol, start_date, end_date, "daily"
            )

            if data.empty:
                return pd.DataFrame()

            data = data.sort_values("timestamp")

            result = data.copy()

            if factors is None:
                factors = [
                    "sma_5",
                    "sma_10",
                    "sma_20",
                    "sma_50",
                    "ema_5",
                    "ema_10",
                    "ema_20",
                    "ema_50",
                    "rsi_14",
                    "macd",
                    "bollinger_bands",
                    "atr_14",
                    "stoch_14",
                    "williams_r_14",
                ]

            if "sma_5" in factors:
                result["sma_5"] = ti.sma(data["close"], 5)
            if "sma_10" in factors:
                result["sma_10"] = ti.sma(data["close"], 10)
            if "sma_20" in factors:
                result["sma_20"] = ti.sma(data["close"], 20)
            if "sma_50" in factors:
                result["sma_50"] = ti.sma(data["close"], 50)

            if "ema_5" in factors:
                result["ema_5"] = ti.ema(data["close"], 5)
            if "ema_10" in factors:
                result["ema_10"] = ti.ema(data["close"], 10)
            if "ema_20" in factors:
                result["ema_20"] = ti.ema(data["close"], 20)
            if "ema_50" in factors:
                result["ema_50"] = ti.ema(data["close"], 50)

            if "rsi_14" in factors:
                result["rsi_14"] = ti.rsi(data["close"], 14)

            if "macd" in factors:
                macd_line, signal_line, histogram = ti.macd(data["close"])
                result["macd_line"] = macd_line
                result["macd_signal"] = signal_line
                result["macd_histogram"] = histogram

            if "bollinger_bands" in factors:
                upper, middle, lower = ti.bollinger_bands(data["close"], 20, 2)
                result["bb_upper"] = upper
                result["bb_middle"] = middle
                result["bb_lower"] = lower
                result["bb_width"] = (upper - lower) / middle
                result["bb_position"] = (data["close"] - lower) / (upper - lower)

            if "atr_14" in factors:
                result["atr_14"] = ti.atr(data["high"], data["low"], data["close"], 14)

            if "stoch_14" in factors:
                k_percent, d_percent = ti.stoch(
                    data["high"], data["low"], data["close"], 14
                )
                result["stoch_k"] = k_percent
                result["stoch_d"] = d_percent

            if "williams_r_14" in factors:
                result["williams_r"] = ti.williams_r(
                    data["high"], data["low"], data["close"], 14
                )

            return result

        except Exception as e:
            print(f"Error calculating technical factors for {symbol}: {e}")
            return pd.DataFrame()

    async def calculate_custom_factors(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        factor_configs: List[Dict[str, Any]],
    ) -> pd.DataFrame:
        try:
            data = await self.data_service.get_data_from_influxdb(
                symbol, start_date, end_date, "daily"
            )

            if data.empty:
                return pd.DataFrame()

            result = data.copy()

            for config in factor_configs:
                factor_name = config.get("name")
                factor_type = config.get("type")
                params = config.get("params", {})

                if factor_type == "price_ratio":
                    base_price = config.get("base_price", "close")
                    target_price = config.get("target_price", "sma_20")
                    result[f"{factor_name}"] = data[base_price] / data[target_price]

                elif factor_type == "volume_ratio":
                    base_volume = config.get("base_volume", "close")
                    target_volume = config.get("target_volume", "sma_20_volume")
                    result[f"{factor_name}"] = data[base_volume] / data[target_volume]

                elif factor_type == "momentum":
                    period = params.get("period", 20)
                    result[f"{factor_name}"] = data["close"].pct_change(period)

                elif factor_type == "volatility":
                    period = config.get("period", 20)
                    result[f"{factor_name}"] = data["close"].rolling(period).std()

                elif factor_type == "custom":
                    formula = config.get("formula")
                    if formula:
                        result[f"{factor_name}"] = eval(formula)

            return result

        except Exception as e:
            print(f"Error calculating custom factors for {symbol}: {e}")
            return pd.DataFrame()

    async def store_factors_to_postgres(
        self, symbol: str, factors_data: pd.DataFrame, factor_name: str, created_by: str
    ) -> bool:
        try:
            db = next(get_db())

            for _, row in factors_data.iterrows():
                factor = Factor(
                    name=factor_name,
                    symbol=symbol,
                    timestamp=row["timestamp"],
                    value=float(row.get(factor_name, 0)),
                    metadata=row.to_json(),
                    created_by=created_by,
                )
                db.add(factor)

            db.commit()
            return True

        except Exception as e:
            print(f"Error storing factors to PostgreSQL: {e}")
            db.rollback()
            return False

        finally:
            db.close()

    async def get_factors_from_postgres(
        self,
        symbol: str,
        factor_name: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        try:
            db = next(get_db())

            factors = (
                db.query(Factor)
                .filter(
                    Factor.symbol == symbol,
                    Factor.name == factor_name,
                    Factor.timestamp >= start_date,
                    Factor.timestamp <= end_date,
                )
                .all()
            )

            if not factors:
                return pd.DataFrame()

            data = []
            for factor in factors:
                data.append(
                    {
                        "timestamp": factor.timestamp,
                        "value": factor.value,
                        "metadata": factor.metadata,
                    }
                )

            return pd.DataFrame(data)

        except Exception as e:
            print(f"Error getting factors from PostgreSQL: {e}")
            return pd.DataFrame()
        finally:
            db.close()

    async def calculate_and_store_factors(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        factor_configs: List[Dict[str, Any]],
        created_by: str,
    ) -> bool:

        results = {}

        try:
            technical_factors = await self.calculate_technical_factors(
                symbol, start_date, end_date
            )

            if not technical_factors.empty:
                for factor_name in technical_factors.columns:
                    if factor_name not in [
                        "timestamp",
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                        "amount",
                    ]:
                        success = await self.store_factors_to_postgres(
                            symbol, technical_factors, factor_name, created_by
                        )
                        results[f"technical_{factor_name}"] = success

            custom_factors = await self.calculate_custom_factors(
                symbol, start_date, end_date, factor_configs
            )

            if not custom_factors.empty:
                for config in factor_configs:
                    factor_name = config.get("name")
                    if factor_name in custom_factors.columns:
                        success = await self.store_factors_to_postgres(
                            symbol, custom_factors, factor_name, created_by
                        )
                        results[f"custom_{factor_name}"] = success

            return results

        except Exception as e:
            print(f"Error calculating and storing factors for {symbol}: {e}")
            return {"error": False}

    def close(self):
        if hasattr(self, "data_service"):
            self.data_service.close()
