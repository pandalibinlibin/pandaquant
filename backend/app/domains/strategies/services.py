"""
Strategy service for managing and running strategies
"""

import os
import importlib
import inspect
from typing import Dict, Any, Optional, Type, List
import backtrader as bt
import asyncio

from app.core.logging import get_logger
from app.domains.data.services import DataService, data_service
from app.domains.factors.services import FactorService, factor_service
from app.domains.strategies.base_strategy import BaseStrategy
from app.domains.strategies.enums import TradingMode
from app.domains.strategies.data_group import DataGroup


from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.core.config import settings

logger = get_logger(__name__)


def create_data_group_from_config(config: Dict[str, Any]) -> DataGroup:
    """
    Factory function to create DataGroup instance from configuration

    Args:
        config: DataGroup configuration dictionary with 'type' key

    Returns:
        DataGroup instance
    """
    from app.domains.strategies.data_group import DataGroup
    from app.domains.strategies.daily_data_group import DailyDataGroup

    group_type = config.get("type")
    if group_type == "DailyDataGroup":
        return DailyDataGroup(
            name=config["name"],
            weight=config.get("weight", 1.0),
            factors=config.get("factors", []),
        )
    else:
        raise ValueError(f"Unsupported DataGroup type: {group_type}")


class StrategyService:
    """
    Manages strategy discovery, registration, and execution (backtest, paper, live)
    """

    def __init__(self):
        self.strategies: Dict[str, Type[BaseStrategy]] = {}
        self.data_service = data_service
        self.factor_service = factor_service
        self._auto_discover_strategies()

    def _auto_discover_strategies(self):
        """Auto-discover strategy classes by scanning Python files in app.domains.strategies package"""
        try:
            import pkgutil
            from pathlib import Path

            # Get the package path
            strategies_package = importlib.import_module("app.domains.strategies")
            package_path = Path(strategies_package.__file__).parent

            for importer, modname, ispkg in pkgutil.iter_modules([str(package_path)]):
                if ispkg:
                    continue

                if modname in [
                    "base_strategy",
                    "data_group",
                    "daily_data_group",
                    "enums",
                    "services",
                ]:
                    continue

                try:
                    module_name = f"app.domains.strategies.{modname}"
                    module = importlib.import_module(module_name)

                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (
                            issubclass(obj, BaseStrategy)
                            and obj is not BaseStrategy
                            and obj.__module__ == module_name
                        ):
                            self.register_strategy(name, obj)
                            logger.info(
                                f"Auto-discovered strategy: {name} from {module_name}"
                            )
                except Exception as e:
                    logger.warning(
                        f"Failed to import or scan module {module_name}: {e}"
                    )
                    continue
        except Exception as e:
            logger.error(f"Error auto-discovering strategies: {e}")

    def register_strategy(self, name: str, strategy_class: Type[BaseStrategy]):
        """Register a strategy class"""
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(f"{strategy_class} is not a subclass of BaseStrategy")

        self.strategies[name] = strategy_class
        logger.info(f"Registered strategy: {name}")

    def list_strategies(self) -> List[str]:
        """List all registered strategy names"""
        return list(self.strategies.keys())

    def get_strategy(self, name: str) -> Optional[Type[BaseStrategy]]:
        """Get a strategy class by name"""
        return self.strategies.get(name)

    async def run_backtest(
        self,
        strategy_name: str,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000.0,
        commission: float = 0.0003,
        commtype: str = "PERC",
        commmin: float = 5.0,
        stocklike: bool = True,
        leverage: float = 1.0,
        margin: Optional[float] = None,
        mode: TradingMode = None,
        created_by: str = "system",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run backtest for a strategy
        """

        if mode is None:
            mode = TradingMode.BACKTEST

        strategy_class = self.get_strategy(strategy_name)
        if not strategy_class:
            raise ValueError(f"Strategy {strategy_name} not found")

        logger.info(f"Starting backtest for {strategy_name} with symbol {symbol}")

        from uuid import uuid4

        backtest_id = str(uuid4())

        strategy_class._run_mode = mode
        strategy_class._run_symbol = symbol
        strategy_class._run_start_date = start_date
        strategy_class._run_end_date = end_date

        data_group_configs = strategy_class.get_data_group_configs()

        feeds = []
        for config in data_group_configs:
            group = create_data_group_from_config(config)
            group.set_service(self.data_service, self.factor_service)
            await group.prepare_data(
                symbol=symbol, start_date=start_date, end_date=end_date
            )
            if group._prepared_data is None or group._prepared_data.empty:
                logger.warning(
                    f"Data preparation failed for {group.name}, skipping this DataGroup"
                )
                continue

            feed = group.to_backtrader_feed()
            feed._data_group_name = group.name
            feeds.append(feed)

        if not feeds:
            raise ValueError(
                "No valid data feeds found. Ensure at least one DataGroup has OHLCV data."
            )

        cerebro = bt.Cerebro()
        for feed in feeds:
            cerebro.adddata(feed)

        cerebro.addstrategy(strategy_class)

        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trade")

        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturn")
        cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name="timedrawdown")

        cerebro.addanalyzer(bt.analyzers.VWR, _name="vwr")
        cerebro.addanalyzer(bt.analyzers.Calmar, _name="calmar")
        cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
        cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annualreturn")

        cerebro.addanalyzer(bt.analyzers.GrossLeverage, _name="grosseleverage")
        cerebro.addanalyzer(bt.analyzers.PositionsValue, _name="positionsvalue")

        cerebro.addanalyzer(bt.analyzers.PyFolio, _name="pyfolio")

        cerebro.addobserver(bt.observers.Broker)
        cerebro.addobserver(bt.observers.Trades)
        cerebro.addobserver(bt.observers.BuySell)

        cerebro.broker.setcash(initial_capital)

        commtype_val = (
            bt.CommInfoBase.COMM_PERC
            if commtype.upper() == "PERC"
            else bt.CommInfoBase.COMM_FIXED
        )

        comminfo = bt.CommInfoBase(
            commission=commission,
            commtype=commtype_val,
            stocklike=stocklike,
        )

        if commmin is not None:
            comminfo.commmin = commmin

        if leverage is not None:
            comminfo.p.leverage = leverage

        if margin is not None:
            comminfo.p.margin = margin

        cerebro.broker.addcommissioninfo(comminfo)

        try:
            loop = asyncio.get_event_loop()
            result_list = await loop.run_in_executor(None, cerebro.run)

            if not result_list:
                raise ValueError(
                    "Backtest returned no results. Check data feeds and strategy logic."
                )

            chart_path = None
            try:
                output_dir = Path(settings.BACKTEST_RESULTS_PATH)
                if not output_dir.exists():
                    output_dir.mkdir(parents=True, exist_ok=True)

                chart_filename = f"{backtest_id}.png"
                chart_path = str(output_dir / chart_filename)

                def save_chart():
                    fig = cerebro.plot(style="bar", volume=False)[0][0]
                    fig.savefig(chart_path, dpi=100, bbox_inches="tight")
                    plt.close(fig)

                await loop.run_in_executor(None, save_chart)
                logger.info(f"Backtest chart saved to {chart_path}")
            except Exception as chart_error:
                logger.warning(
                    f"Failed to save backtest chart: {chart_error}",
                    exc_info=True,
                )
                chart_path = None

            strategy_result = result_list[0]

            analyzers = strategy_result.analyzers
            performance = {}

            if hasattr(analyzers, "returns") and analyzers.returns:
                returns_data = analyzers.returns.get_analysis()
                performance["total_return"] = returns_data.get("rtot", 0.0)

            if hasattr(analyzers, "sharpe") and analyzers.sharpe:
                sharpe_data = analyzers.sharpe.get_analysis()
                performance["sharpe_ratio"] = sharpe_data.get("sharperatio", None)

            if hasattr(analyzers, "drawdown") and analyzers.drawdown:
                dd_data = analyzers.drawdown.get_analysis()
                performance["max_drawdown"] = dd_data.get("max", {}).get(
                    "drawdown", 0.0
                )

            if hasattr(analyzers, "trade") and analyzers.trade:
                trade_data = analyzers.trade.get_analysis()
                performance["total_trades"] = trade_data.get("total", {}).get(
                    "total", 0
                )
                performance["winning_trades"] = trade_data.get("won", {}).get(
                    "total", 0
                )
                performance["losing_trades"] = trade_data.get("lost", {}).get(
                    "total", 0
                )
                if performance["total_trades"] > 0:
                    performance["win_rate"] = (
                        performance["winning_trades"] / performance["total_trades"]
                    ) * 100
                else:
                    performance["win_rate"] = 0.0

                performance["avg_win"] = (
                    trade_data.get("won", {}).get("pnl", {}).get("average", 0.0)
                )
                performance["avg_loss"] = (
                    trade_data.get("lost", {}).get("pnl", {}).get("average", 0.0)
                )

            if hasattr(analyzers, "annualreturn") and analyzers.annualreturn:
                annual_data = analyzers.annualreturn.get_analysis()
                if annual_data:
                    annual_returns = annual_data.get("rtot", [])
                    if annual_returns:
                        performance["avg_annual_return"] = sum(annual_returns) / len(
                            annual_returns
                        )
                        performance["avg_annual_return_pct"] = (
                            performance["avg_annual_return"] * 100
                        )

            if hasattr(analyzers, "vwr") and analyzers.vwr:
                vwr_data = analyzers.vwr.get_analysis()
                performance["vwr"] = vwr_data.get("vwr", None)

            if hasattr(analyzers, "calmar") and analyzers.calmar:
                calmar_data = analyzers.calmar.get_analysis()
                performance["calmar_ratio"] = calmar_data.get("calmar", None)

            if hasattr(analyzers, "sqn") and analyzers.sqn:
                sqn_data = analyzers.sqn.get_analysis()
                performance["sqn"] = sqn_data.get("sqn", None)

            if hasattr(analyzers, "timereturn") and analyzers.timereturn:
                timereturn_data = analyzers.timereturn.get_analysis()
                if timereturn_data:
                    performance["time_return"] = timereturn_data

            if hasattr(analyzers, "timedrawdown") and analyzers.timedrawdown:
                timedrawdown_data = analyzers.timedrawdown.get_analysis()
                if timedrawdown_data:
                    performance["time_drawdown"] = timedrawdown_data

            if hasattr(analyzers, "grosseleverage") and analyzers.grosseleverage:
                leverage_data = analyzers.grosseleverage.get_analysis()
                if leverage_data:
                    performance["avg_gross_leverage"] = leverage_data.get("avg", None)
                    performance["max_gross_leverage"] = leverage_data.get("max", None)

            if hasattr(analyzers, "positionsvalue") and analyzers.positionsvalue:
                positions_data = analyzers.positionsvalue.get_analysis()
                if positions_data:
                    performance["avg_positions_value"] = positions_data.get("avg", None)
                    performance["max_positions_value"] = positions_data.get("max", None)

            if hasattr(analyzers, "pyfolio") and analyzers.pyfolio:
                try:
                    pyfolio_data = analyzers.pyfolio.get_analysis()
                    if pyfolio_data and isinstance(pyfolio_data, dict):
                        performance["pyfolio_metrics"] = pyfolio_data
                except Exception as pyfolio_error:
                    logger.warning(
                        f"PyFolio analyzer extraction failed: {pyfolio_error}"
                    )

            final_value = cerebro.broker.getvalue()
            performance["final_value"] = final_value
            performance["total_return_pct"] = (
                (final_value - initial_capital) / initial_capital
            ) * 100

            return {
                "backtest_id": backtest_id,
                "strategy_name": strategy_name,
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": initial_capital,
                "performance": performance,
                "chart_path": chart_path,
                "status": "completed",
            }

        except Exception as e:
            logger.error(
                f"Backtest failed for {strategy_name} with symbol {symbol}: {e}",
                exc_info=True,
            )
            raise
