import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.domains.factors.services import factor_service
from app.domains.factors.base import FactorType


class TestFactorService:

    def test_factor_service_initialization(self):
        assert factor_service is not None
        assert len(factor_service.list_factors()) > 0

    def test_list_factors(self):
        factors = factor_service.list_factors()
        assert isinstance(factors, list)
        assert len(factors) > 0

        expected_factors = ["MA_5_SMA", "MA_20_SMA", "RSI_14", "MACD_12_26_9"]
        for factor in expected_factors:
            assert factor in factors

    def test_get_factor(self):
        factor = factor_service.get_factor("MA_5_SMA")
        assert factor is not None
        assert factor.name == "MA_5_SMA"
        assert factor.factor_type == FactorType.TECHNICAL

    def test_get_factors_by_type(self):
        technical_factors = factor_service.get_factors_by_type(FactorType.TECHNICAL)
        assert len(technical_factors) > 0

        fundamental_factors = factor_service.get_factors_by_type(FactorType.FUNDAMENTAL)
        assert len(fundamental_factors) > 0

    def test_get_factor_status(self):
        status = factor_service.get_factor_status("MA_5_SMA")
        assert status is not None
        assert "name" in status
        assert "status" in status
        assert "is_available" in status
        assert status["name"] == "MA_5_SMA"
