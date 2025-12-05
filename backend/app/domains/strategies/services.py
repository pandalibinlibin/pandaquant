"""
Strategy service for managing and running strategies
"""

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
from app.models import BacktestResult
from uuid import UUID
from datetime import datetime
from sqlmodel import Session


from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.core.config import settings

logger = get_logger(__name__)


_DATA_GROUP_REGISTRY: Dict[str, Type[DataGroup]] = {}


def register_data_group_type(group_type: str, group_class: Type[DataGroup]):
    """
    Register a DataGroup type for factory creation

    Args:
        group_type: Type name (e.g., "DailyDataGroup")
        group_class: DataGroup class
    """
    _DATA_GROUP_REGISTRY[group_type] = group_class


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

    if not _DATA_GROUP_REGISTRY:
        register_data_group_type("DailyDataGroup", DailyDataGroup)

    group_type = config.get("type")
    if group_type not in _DATA_GROUP_REGISTRY:
        raise ValueError(
            f"Unsupported DataGroup type: {group_type}. "
            f"Available types: {list(_DATA_GROUP_REGISTRY.keys())}"
        )

    group_class = _DATA_GROUP_REGISTRY[group_type]
    return group_class(
        name=config["name"],
        weight=config.get("weight", 1.0),
        factors=config.get("factors", []),
    )


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
        session: Session,
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

        strategy_class._db_session = session
        strategy_class._backtest_id = backtest_id

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

        # Determine timeframe from the first feed for analyzer configuration
        # This ensures analyzers use the correct timeframe (Days, Minutes, etc.)
        primary_feed = feeds[0]
        analyzer_timeframe = getattr(primary_feed, "_timeframe", bt.TimeFrame.Days)
        logger.info(f"Using timeframe {analyzer_timeframe} for analyzers")

        cerebro = bt.Cerebro()
        for feed in feeds:
            cerebro.adddata(feed)

        cerebro.addstrategy(strategy_class)

        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        # SharpeRatio: set riskfreerate and annualize for proper calculation
        cerebro.addanalyzer(
            bt.analyzers.SharpeRatio,
            _name="sharpe",
            riskfreerate=0.03,  # 3% annual risk-free rate
            annualize=True,
            timeframe=analyzer_timeframe,
        )
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trade")

        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturn")
        cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name="timedrawdown")

        cerebro.addanalyzer(bt.analyzers.VWR, _name="vwr")
        # Calmar: set timeframe for proper calculation
        cerebro.addanalyzer(
            bt.analyzers.Calmar,
            _name="calmar",
            timeframe=analyzer_timeframe,
        )
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

        # Create BacktestResult record BEFORE running backtest
        # This allows signals to reference the backtest_id via foreign key
        backtest_result = BacktestResult(
            id=UUID(backtest_id),
            strategy_name=strategy_name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_value=initial_capital,  # Will be updated after backtest
            status="running",
            created_by=created_by,
        )
        session.add(backtest_result)
        session.commit()
        logger.info(f"Created backtest record with ID: {backtest_id}, status: running")

        try:
            loop = asyncio.get_running_loop()
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

            # Add debug logging
            logger.info("=== Starting analyzer extraction ===")
            logger.info(f"Available analyzers: {dir(analyzers)}")

            if hasattr(analyzers, "returns") and analyzers.returns:
                returns_data = analyzers.returns.get_analysis()
                performance["total_return"] = returns_data.get("rtot", 0.0)

            logger.info("Checking sharpe analyzer...")
            if hasattr(analyzers, "sharpe") and analyzers.sharpe:
                logger.info("Sharpe analyzer exists, extracting data...")
                sharpe_data = analyzers.sharpe.get_analysis()
                logger.info(f"Sharpe data: {sharpe_data}")
                sharpe_value = sharpe_data.get("sharperatio", None)
                # Sharpe ratio can be None if there's insufficient data or no variance
                if sharpe_value is not None:
                    performance["sharpe_ratio"] = sharpe_value
                    logger.info(f"Sharpe ratio extracted: {sharpe_value}")
                else:
                    logger.warning(
                        "Sharpe ratio is None - insufficient data or no variance in returns"
                    )
                    performance["sharpe_ratio"] = None
            else:
                logger.warning("Sharpe analyzer not found or is None")

            if hasattr(analyzers, "drawdown") and analyzers.drawdown:
                dd_data = analyzers.drawdown.get_analysis()
                max_dd_value = dd_data.get("max", {}).get("drawdown", 0.0)
                # Convert to float if it's a percentage string or ensure it's a number
                if isinstance(max_dd_value, str):
                    # Remove '%' if present and convert to decimal
                    max_dd_value = (
                        float(max_dd_value.rstrip("%")) / 100.0
                        if "%" in max_dd_value
                        else float(max_dd_value)
                    )
                # Convert percentage number to decimal (e.g., 19.39 -> 0.1939)
                performance["max_drawdown"] = (
                    max_dd_value / 100.0 if max_dd_value != 0.0 else None
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
                # Calculate win rate as decimal (e.g., 0.4 for 40%)
                if performance["total_trades"] > 0:
                    performance["win_rate"] = (
                        performance["winning_trades"] / performance["total_trades"]
                    )
                else:
                    performance["win_rate"] = 0.0

                performance["avg_win"] = (
                    trade_data.get("won", {}).get("pnl", {}).get("average", 0.0)
                )
                performance["avg_loss"] = (
                    trade_data.get("lost", {}).get("pnl", {}).get("average", 0.0)
                )

            logger.info("Checking annualreturn analyzer...")
            if hasattr(analyzers, "annualreturn") and analyzers.annualreturn:
                logger.info("AnnualReturn analyzer exists, extracting data...")
                annual_data = analyzers.annualreturn.get_analysis()
                logger.info(f"Annual data: {annual_data}")
                if annual_data:
                    # AnnualReturn analyzer returns dict with years as keys: {2023: -0.176, 2024: 0.05}
                    # Extract values (annual returns for each year)
                    annual_returns = list(annual_data.values())
                    logger.info(f"Annual returns extracted: {annual_returns}")
                    if annual_returns:
                        # Calculate average of all years
                        performance["avg_annual_return"] = sum(annual_returns) / len(
                            annual_returns
                        )
                        # Keep avg_annual_return_pct as decimal for consistency
                        performance["avg_annual_return_pct"] = performance[
                            "avg_annual_return"
                        ]
                        logger.info(
                            f"Avg annual return calculated: {performance.get('avg_annual_return')}"
                        )
                    else:
                        logger.warning("Annual returns list is empty")
                else:
                    logger.warning("Annual data is empty")
            else:
                logger.warning("AnnualReturn analyzer not found or is None")

            if hasattr(analyzers, "vwr") and analyzers.vwr:
                vwr_data = analyzers.vwr.get_analysis()
                performance["vwr"] = vwr_data.get("vwr", None)

            logger.info("Checking calmar analyzer...")
            if hasattr(analyzers, "calmar") and analyzers.calmar:
                logger.info("Calmar analyzer exists, extracting data...")
                calmar_data = analyzers.calmar.get_analysis()
                logger.info(f"Calmar data: {calmar_data}")
                # Calmar analyzer returns dict with dates as keys and calmar values
                # Get the last (most recent) non-NaN value
                calmar_values = [
                    v
                    for v in calmar_data.values()
                    if v is not None
                    and not (isinstance(v, float) and v != v)
                    and v != 0.0
                ]  # Filter out None, NaN, and 0.0

                # Try to use analyzer value if valid
                calmar_from_analyzer = None
                if calmar_values:
                    calmar_from_analyzer = calmar_values[-1]
                    # Check if the value is reasonable (absolute value > 0.001)
                    if abs(calmar_from_analyzer) > 0.001:
                        performance["calmar_ratio"] = calmar_from_analyzer
                        logger.info(
                            f"Calmar ratio extracted from analyzer: {performance['calmar_ratio']}"
                        )
                    else:
                        logger.warning(
                            f"Calmar ratio from analyzer too small ({calmar_from_analyzer}), will calculate manually"
                        )
                        calmar_from_analyzer = None  # Mark as invalid

                # If analyzer failed or returned invalid value, calculate manually
                if calmar_from_analyzer is None:
                    # Manually calculate Calmar ratio if analyzer fails
                    # Calmar = Annual Return / Max Drawdown
                    avg_annual_return = performance.get("avg_annual_return")
                    max_drawdown = performance.get("max_drawdown")
                    if (
                        avg_annual_return is not None
                        and max_drawdown is not None
                        and max_drawdown != 0
                    ):
                        performance["calmar_ratio"] = avg_annual_return / max_drawdown
                        logger.info(
                            f"Calmar ratio calculated manually: {performance['calmar_ratio']} "
                            f"(annual_return={avg_annual_return}, max_dd={max_drawdown})"
                        )
                    else:
                        logger.warning(
                            "Cannot calculate Calmar ratio - missing annual return or max drawdown"
                        )
                        performance["calmar_ratio"] = None
            else:
                logger.warning("Calmar analyzer not found or is None")

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
            # Calculate total_return_pct as decimal (e.g., -0.1766 for -17.66%)
            performance["total_return_pct"] = (
                final_value - initial_capital
            ) / initial_capital

            # Update BacktestResult record with final results
            backtest_result.final_value = final_value
            backtest_result.total_return = performance.get("total_return", 0.0)
            backtest_result.total_return_pct = performance.get("total_return_pct", 0.0)
            backtest_result.sharpe_ratio = performance.get("sharpe_ratio")
            backtest_result.max_drawdown = performance.get("max_drawdown")
            backtest_result.total_trades = performance.get("total_trades")
            backtest_result.winning_trades = performance.get("winning_trades")
            backtest_result.losing_trades = performance.get("losing_trades")
            backtest_result.win_rate = performance.get("win_rate")
            backtest_result.avg_win = performance.get("avg_win")
            backtest_result.avg_loss = performance.get("avg_loss")
            backtest_result.avg_annual_return = performance.get("avg_annual_return")
            backtest_result.vwr = performance.get("vwr")
            backtest_result.calmar_ratio = performance.get("calmar_ratio")
            backtest_result.sqn = performance.get("sqn")
            backtest_result.chart_path = chart_path
            backtest_result.status = "completed"
            session.commit()
            session.refresh(backtest_result)
            logger.info(f"Backtest result updated to completed: {backtest_id}")

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
