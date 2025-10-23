import pytest
import pandas as pd
import numpy as np
from app.domains.factors.technical import MACDFactor, BollingerBandsFactor


class TestMACDFactor:
    def test_macd_initialization(self):
        macd = MACDFactor(fast_period=12, slow_period=26, signal_period=9)

        assert macd.name == "MACD_12_26_9"
        assert macd.fast_period == 12
        assert macd.slow_period == 26
        assert macd.signal_period == 9
        assert "MACD with fast=12, slow=26, signal=9" in macd.description

    def test_macd_qlib_integration(self):
        macd = MACDFactor()

        expression = macd.get_qlib_expression()
        assert "MACD($close, 12, 26, 9)" in expression

        dependencies = macd.get_qlib_dependencies()
        assert "$close" in dependencies

        params = macd.get_qlib_parameters()
        assert params["fast_period"] == 12
        assert params["slow_period"] == 26
        assert params["signal_period"] == 9


class TestBollingerBandsFactor:
    def test_bollinger_bands_initialization(self):
        bb = BollingerBandsFactor(period=20, std_dev=2.0)

        assert bb.name == "BB_20_2.0"
        assert bb.period == 20
        assert bb.std_dev == 2.0
        assert "Bollinger Bands with period=20, std_dev=2.0" in bb.description

    def test_bollinger_bands_qlib_integration(self):
        bb = BollingerBandsFactor()

        expression = bb.get_qlib_expression()
        assert "BBANDS($close, 20, 2.0)" in expression

        dependencies = bb.get_qlib_dependencies()
        assert "$close" in dependencies

        params = bb.get_qlib_parameters()
        assert params["period"] == 20
        assert params["std_dev"] == 2.0
