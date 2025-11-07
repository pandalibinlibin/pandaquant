"""
Full backtest flow integration test

Tests the complete flow: Data -> Factor -> Strategy -> Backtest
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.domains.strategies.services import StrategyService
from app.domains.strategies.enums import TradingMode
from app.domains.data.services import DataService


class TestFullBacktestFlow:
    """Test complete backtest flow"""

    @pytest.mark.asyncio
    async def test_backtest_flow_with_real_data(self):
        """Test backtest flow with real data"""

        data_service = DataService()
        try:
            test_data = await data_service.fetch_data(
                data_type="daily",
                symbol="000001.SZ",
                start_date="2024-01-01",
                end_date="2024-01-05",
            )
            if test_data is None or test_data.empty:
                pytest.skip("Data sources are not available, skipping integration test")
        except Exception as e:
            pytest.skip("Data sources are not available, skipping integration test")

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
        assert "performance" in result, "Result should contain performance"

        assert result["strategy_name"] == "DualMovingAverageStrategy"
        assert result["symbol"] == "000001.SZ"
        assert result["initial_capital"] == 1000000.0
        assert isinstance(result["performance"]["final_value"], (int, float))

        assert "start_date" in result, "Result should contain start_date"
        assert "end_date" in result, "Result should contain end_date"
        assert (
            "total_return" in result["performance"]
        ), "Result should contain total_return"
        assert (
            "max_drawdown" in result["performance"]
        ), "Result should contain max_drawdown"
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-01-31"
        assert isinstance(result["performance"]["total_return"], (int, float))
        assert isinstance(result["performance"]["max_drawdown"], (int, float))

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

    @pytest.mark.asyncio
    async def test_backtest_flow_with_mock_data(self):
        """Test backtest flow with mock data"""
        import pandas as pd

        def create_mock_data(start_date: str, end_date: str) -> pd.DataFrame:
            """Create mock OHLCV data for testing"""

            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            dates = pd.date_range(start=start, end=end, freq="D")

            base_price = 10.0
            data = []
            for i, date in enumerate(dates):
                price = base_price + i * 0.1 + (i % 5) * 0.2
                high = price * 1.02
                low = price * 0.98
                open_price = price * 0.99
                close_price = price
                volume = 1000000 + i * 10000

                data.append(
                    {
                        "timestamp": date,
                        "open": open_price,
                        "high": high,
                        "low": low,
                        "close": close_price,
                        "volume": volume,
                    }
                )

            df = pd.DataFrame(data)
            return df

        mock_data = create_mock_data("2024-01-01", "2024-01-31")

        with patch.object(
            DataService, "fetch_data", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_data

            strategy_service = StrategyService()

            original_data_service = strategy_service.data_service
            strategy_service.data_service = DataService()
            strategy_service.data_service.fetch_data = mock_fetch

            result = await strategy_service.run_backtest(
                strategy_name="DualMovingAverageStrategy",
                symbol="000001.SZ",
                start_date="2024-01-01",
                end_date="2024-01-31",
                initial_capital=1000000.0,
                mode=TradingMode.BACKTEST,
            )

            strategy_service.data_service = original_data_service

            assert result is not None
            assert result["strategy_name"] == "DualMovingAverageStrategy"
            assert result["symbol"] == "000001.SZ"
            assert result["initial_capital"] == 1000000.0
            assert isinstance(result["performance"]["final_value"], (int, float))
            assert "total_return" in result["performance"]
            assert "max_drawdown" in result["performance"]

    @pytest.mark.asyncio
    async def test_backtest_result_completeness(self):
        """Test that backtest result contains all required performance metrics"""
        import pandas as pd
        from unittest.mock import AsyncMock, patch
        from app.domains.data.services import DataService

        def create_mock_data(start_date: str, end_date: str) -> pd.DataFrame:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            dates = pd.date_range(start=start, end=end, freq="D")
            base_price = 10.0
            data = []
            for i, date in enumerate(dates):
                price = base_price + i * 0.1 + (i % 5) * 0.2
                data.append(
                    {
                        "timestamp": date,
                        "open": price * 0.99,
                        "high": price * 1.02,
                        "low": price * 0.98,
                        "close": price,
                        "volume": 1000000 + i * 10000,
                    }
                )

            return pd.DataFrame(data)

        mock_data = create_mock_data("2024-01-01", "2024-01-31")

        with patch.object(
            DataService, "fetch_data", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_data
            strategy_service = StrategyService()
            original_data_service = strategy_service.data_service
            strategy_service.data_service = DataService()
            strategy_service.data_service.fetch_data = mock_fetch

            result = await strategy_service.run_backtest(
                strategy_name="DualMovingAverageStrategy",
                symbol="000001.SZ",
                start_date="2024-01-01",
                end_date="2024-01-31",
                initial_capital=1000000.0,
                mode=TradingMode.BACKTEST,
            )

            strategy_service.data_service = original_data_service

            assert "backtest_id" in result
            assert "strategy_name" in result
            assert "symbol" in result
            assert "start_date" in result
            assert "end_date" in result
            assert "initial_capital" in result
            assert "performance" in result
            assert "chart_path" in result
            assert "status" in result

            perf = result["performance"]
            assert "final_value" in perf
            assert "total_return" in perf
            assert "total_return_pct" in perf
            assert "max_drawdown" in perf

    @pytest.mark.asyncio
    async def test_backtest_with_different_initial_capital(self):
        """Test backtest with different initial capital amounts"""

        import pandas as pd
        from unittest.mock import AsyncMock, patch
        from app.domains.data.services import DataService

        def create_mock_data(start_date: str, end_date: str) -> pd.DataFrame:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            dates = pd.date_range(start=start, end=end, freq="D")
            base_price = 10.0
            data = []
            for i, date in enumerate(dates):
                price = base_price + i * 0.1 + (i % 5) * 0.2
                data.append(
                    {
                        "timestamp": date,
                        "open": price * 0.99,
                        "high": price * 1.02,
                        "low": price * 0.98,
                        "close": price,
                        "volume": 1000000 + i * 10000,
                    }
                )

            return pd.DataFrame(data)

        mock_data = create_mock_data("2024-01-01", "2024-01-31")
        with patch.object(
            DataService, "fetch_data", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = mock_data
            strategy_service = StrategyService()
            original_data_service = strategy_service.data_service
            strategy_service.data_service = DataService()
            strategy_service.data_service.fetch_data = mock_fetch

            test_capitals = [100000.0, 500000.0, 1000000.0, 5000000.0]

            for initial_capital in test_capitals:
                result = await strategy_service.run_backtest(
                    strategy_name="DualMovingAverageStrategy",
                    symbol="000001.SZ",
                    start_date="2024-01-01",
                    end_date="2024-01-31",
                    initial_capital=initial_capital,
                    mode=TradingMode.BACKTEST,
                )

                assert result["initial_capital"] == initial_capital
                assert result["performance"]["final_value"] > 0
                assert result["performance"]["final_value"] >= initial_capital * 0.5
                assert result["performance"]["final_value"] <= initial_capital * 2.0

            strategy_service.data_service = original_data_service
