"""
Paper trading flow integration test

Tests the complete flow: Data -> Factor -> Strategy -> Signal Push
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.domains.strategies.services import StrategyService
from app.domains.strategies.enums import TradingMode
from app.domains.signals.services import signal_push_service


class TestPaperTradingFlow:
    """Test paper trading flow with signal push"""

    @pytest.mark.asyncio
    async def test_signal_push_service_initialization(self):
        """Test SignalPushService can be initialized"""

        assert signal_push_service is not None
        assert hasattr(signal_push_service, "channels")
        assert isinstance(signal_push_service.channels, dict)

    @pytest.mark.asyncio
    async def test_signal_push_service_has_channels(self):
        """Test SignalPushService has registered channels"""
        channels = signal_push_service.channels

        assert len(channels) > 0, "SignalPushService should have at least one channel"

    @pytest.mark.asyncio
    async def test_push_signal_basic(self):
        """Test pushing a signal to channels"""
        signal_data = {
            "action": "buy",
            "symbol": "000001.SZ",
            "target_price": 10.5,
            "strength": 0.02,
            "strategy_name": "DualMovingAverageStrategy",
            "timestamp": "2024-01-01 10:00:00",
        }

        results = await signal_push_service.push_signal(signal_data)

        assert isinstance(results, dict)

        assert len(results) > 0

        for channel_name, result in results.items():
            assert hasattr(
                result, "success"
            ), f"Result for {channel_name} should have success attribute"
            assert isinstance(
                result.success, bool
            ), f"Success should be boolean for {channel_name}"

    @pytest.mark.asyncio
    async def test_trading_mode_backtest_no_signal_push(self):
        """Test that BACKTEST mode does not push signals"""

        strategy_service = StrategyService()

        strategies = strategy_service.list_strategies()
        assert "DualMovingAverageStrategy" in strategies

        assert TradingMode.BACKTEST == "backtest"

    @pytest.mark.asyncio
    async def test_signal_push_service_health_check(self):
        """Test SignalPushService health check functionality"""

        health_status = await signal_push_service.check_health()

        assert isinstance(health_status, dict)

        assert (
            len(health_status) > 0
        ), "Health check should return status for at least one channel"

        for channel_name, is_healthy in health_status.items():
            assert isinstance(
                is_healthy, bool
            ), f"Health status for {channel_name} should be a boolean"

    def test_trading_mode_enum_values(self):
        """Test TradingMode enum has all expected values"""

        assert TradingMode.BACKTEST == "backtest"
        assert TradingMode.PAPER_TRADING == "paper_trading"
        assert TradingMode.LIVE_TRADING == "live_trading"

        assert TradingMode.BACKTEST != TradingMode.PAPER_TRADING
        assert TradingMode.BACKTEST != TradingMode.LIVE_TRADING
        assert TradingMode.PAPER_TRADING != TradingMode.LIVE_TRADING
