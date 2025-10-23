import pytest
import pandas as pd
import numpy as np
from app.domains.factors.technical import (
    MACDFactor,
    BollingerBandsFactor,
    KDJFactor,
    MovingAverageFactor,
    RSIFactor,
)


class TestMovingAverageFactor:
    def test_ma_initialization(self):
        ma = MovingAverageFactor(period=20, ma_type="SMA")

        assert ma.name == "MA_20_SMA"
        assert ma.period == 20
        assert ma.ma_type == "SMA"
        assert "SMA Moving Average of 20 periods" in ma.description

    def test_ema_initialization(self):
        ema = MovingAverageFactor(period=20, ma_type="EMA")

        assert ema.name == "MA_20_EMA"
        assert ema.period == 20
        assert ema.ma_type == "EMA"
        assert "EMA Moving Average of 20 periods" in ema.description

    def test_ma_qlib_integration(self):
        ma = MovingAverageFactor(period=20, ma_type="SMA")

        expression = ma.get_qlib_expression()
        assert "Mean($close, 20)" in expression

        dependencies = ma.get_qlib_dependencies()
        assert "$close" in dependencies

        params = ma.get_qlib_parameters()
        assert params["period"] == 20
        assert params["ma_type"] == "SMA"

    def test_ema_qlib_integration(self):
        ema = MovingAverageFactor(period=20, ma_type="EMA")

        expression = ema.get_qlib_expression()
        assert "EMA($close, 20)" in expression

        dependencies = ema.get_qlib_dependencies()
        assert "$close" in dependencies

        params = ema.get_qlib_parameters()
        assert params["period"] == 20
        assert params["ma_type"] == "EMA"


class TestRSIFactor:
    def test_rsi_initialization(self):
        rsi = RSIFactor(period=14)

        assert rsi.name == "RSI_14"
        assert rsi.period == 14
        assert "Relative Strength Index of 14 periods" in rsi.description

    def test_rsi_qlib_integration(self):
        rsi = RSIFactor()

        expression = rsi.get_qlib_expression()
        assert "RSI($close, 14)" in expression

        dependencies = rsi.get_qlib_dependencies()
        assert "$close" in dependencies

        params = rsi.get_qlib_parameters()
        assert params["period"] == 14


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


class TestKDJFactor:
    def test_kdj_initialization(self):
        kdj = KDJFactor(k_period=9, d_period=3, j_period=3)

        assert kdj.name == "KDJ_9_3_3"
        assert kdj.k_period == 9
        assert kdj.d_period == 3
        assert kdj.j_period == 3
        assert "KDJ Stochastic Oscillator with k=9, d=3, j=3" in kdj.description

    def test_kdj_qlib_integration(self):
        kdj = KDJFactor()

        expression = kdj.get_qlib_expression()
        assert "STOCH($high, $low, $close, 9, 3, 3)" in expression

        dependencies = kdj.get_qlib_dependencies()
        assert "$high" in dependencies
        assert "$low" in dependencies
        assert "$close" in dependencies

        params = kdj.get_qlib_parameters()
        assert params["k_period"] == 9
        assert params["d_period"] == 3
        assert params["j_period"] == 3
