import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.domains.factors.services import factor_service
from app.domains.factors.base import FactorType
from app.domains.factors.technical import MovingAverageFactor, RSIFactor, MACDFactor


class TestFactorService:

    def test_factor_service_initialization(self):
        """Test factor service is initialized correctly"""

        assert factor_service is not None
        assert isinstance(factor_service.list_factors(), list)

    def test_register_and_list_factors(self):
        """Test registering factors and listing them"""

        ma5 = MovingAverageFactor(period=5, ma_type="SMA")
        ma20 = MovingAverageFactor(period=20, ma_type="SMA")
        rsi14 = RSIFactor(period=14)
        macd = MACDFactor(fast_period=12, slow_period=26, signal_period=9)

        factor_service.register_factor(ma5)
        factor_service.register_factor(ma20)
        factor_service.register_factor(rsi14)
        factor_service.register_factor(macd)

        factors = factor_service.list_factors()
        assert isinstance(factors, list)
        assert len(factors) >= 4

        expected_factors = ["MA_5_SMA", "MA_20_SMA", "RSI_14", "MACD_12_26_9"]
        for factor in expected_factors:
            assert factor in factors

    def test_get_factor(self):
        """Test getting a specific factor"""
        ma5 = MovingAverageFactor(period=5, ma_type="SMA")
        factor_service.register_factor(ma5)

        factor = factor_service.get_factor("MA_5_SMA")
        assert factor is not None
        assert factor.name == "MA_5_SMA"
        assert factor.factor_type == FactorType.TECHNICAL

    def test_get_factors_by_type(self):
        """Test getting factors by type"""

        ma5 = MovingAverageFactor(period=5, ma_type="SMA")
        factor_service.register_factor(ma5)

        technical_factors = factor_service.get_factors_by_type(FactorType.TECHNICAL)
        assert len(technical_factors) >= 0

    def test_get_factor_status(self):
        """Test getting factor status"""

        ma5 = MovingAverageFactor(period=5, ma_type="SMA")
        factor_service.register_factor(ma5)

        status = factor_service.get_factor_status("MA_5_SMA")
        assert status is not None
        assert "name" in status
        assert "status" in status
        assert "is_available" in status
        assert status["name"] == "MA_5_SMA"
