"""
Full backtest flow integration test

Tests the complete flow: Data -> Factor -> Strategy -> Backtest
"""

import pytest

from app.domains.strategies.services import StrategyService
from app.domains.strategies.enums import TradingMode


class TestFullBacktestFlow:
    """Test complete backtest flow"""

    @pytest.mark.asyncio
    async def test_backtest_flow_with_real_data(self):
        """Test backtest flow with real data"""

        strategy_service = StrategyService()

        strategies = strategy_service.list_strategies()
        assert "DualMovingAverageStrategy" in strategies

        result = await strategy_service.run_backtest(
            strategy_name="DualMovingAverageStrategy",
            symbol="000001.SZ",
            start_date="2024-01-01",
            end_date="2024-01-31",
            initial_capital=1000000.0,
            mode=TradingMode.BACKTEST,
        )

        assert result is not None

        assert "strategy_name" in result, "Result should contain strategy_name"
        assert "symbol" in result, "Result should contain symbol"
        assert "initial_capital" in result, "Result should contain initial_capital"
        assert "final_value" in result, "Result should contain final_value"

        assert result["strategy_name"] == "DualMovingAverageStrategy"
        assert result["symbol"] == "000001.SZ"
        assert result["initial_capital"] == 1000000.0
        assert isinstance(result["final_value"], (int, float))

        assert "start_date" in result, "Result should contain start_date"
        assert "end_date" in result, "Result should contain end_date"
        assert "total_return" in result, "Result should contain total_return"
        assert "max_drawdown" in result, "Result should contain max_drawdown"
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-01-31"
        assert isinstance(result["total_return"], (int, float))
        assert isinstance(result["max_drawdown"], (int, float))

        assert "market_type" in result, "Result should contain market_type"
        assert "leverage" in result, "Result should contain leverage"
        assert "short_selling" in result, "Result should contain short_selling"
        assert result["market_type"] == "A-share"
        assert result["leverage"] == 1.0, "A-share should have no leverage"
        assert (
            result["short_selling"] is False
        ), "A-share should not allow short selling"

    @pytest.mark.asyncio
    async def test_backtest_invalid_strategy(self):
        """Test backtest with invalid strategy name raises error"""

        strategy_service = StrategyService()

        with pytest.raises(ValueError, match="Strategy .* not found"):
            await strategy_service.run_backtest(
                strategy_name="NonExistentStrategy",
                symbol="000001.SZ",
                start_date="2024-01-01",
                end_date="2024-01-31",
                initial_capital=1000000.0,
                mode=TradingMode.BACKTEST,
            )
