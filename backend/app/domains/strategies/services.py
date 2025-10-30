import pandas as pd
import backtrader as bt
import json
import os
import importlib
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from app.domains.strategies.base_strategy import BaseStrategy
from app.core.logging import get_logger
from app.api.deps import get_db
from app.models import BacktestResult
from app.domains.strategies.enums import TradingMode
from app.domains.signals.services import signal_push_service

logger = get_logger(__name__)


class StrategyService:
    """Strategy service for managing and running strategies"""

    def __init__(self):
        self.strategies: Dict[str, type[BaseStrategy]] = {}
        self._auto_discover_strategies()

    def _auto_discover_strategies(self):
        """Discover and register strategy classes"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))

            for filename in os.listdir(current_dir):
                if filename.endswith("_strategy.py") and filename != "__init__.py":
                    strategy_name = filename[:-3]

                    try:

                        module_name = f"app.domains.strategies.{strategy_name}"
                        module = importlib.import_module(module_name)

                        # 查找策略类
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (
                                isinstance(attr, type)
                                and issubclass(attr, BaseStrategy)
                                and attr != BaseStrategy
                            ):

                                # Store strategy class, not instance
                                self.strategies[attr_name] = attr
                                logger.info(
                                    f"Discovered and registered strategy class: {attr_name}"
                                )
                                break

                    except Exception as e:
                        logger.error(
                            f"Error discovering and registering strategy {strategy_name}: {e}"
                        )
                        continue
        except Exception as e:
            logger.error(f"Error discovering and registering strategies: {e}")

    def get_strategy(self, strategy_name: str) -> Optional[type[BaseStrategy]]:
        """Get strategy by name"""
        return self.strategies.get(strategy_name)

    def list_strategies(self) -> List[str]:
        """List all available strategies"""
        return list(self.strategies.keys())

    def register_strategy(self, name: str, strategy: type[BaseStrategy]):
        """Register a new strategy class"""
        self.strategies[name] = strategy
        logger.info(f"Registered strategy class: {name}")

    def unregister_strategy(self, name: str) -> bool:
        """Unregister a strategy"""
        if name in self.strategies:
            del self.strategies[name]
            logger.info(f"Unregistered strategy: {name}")
            return True
        return False

    def _add_default_analyzers(self, cerebro):
        """Add comprehensive default analyzers"""
        # Basic analyzers
        cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

        # Time-based analyzers
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name="timereturn")
        cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name="timedrawdown")

        # Risk analyzers
        cerebro.addanalyzer(
            bt.analyzers.VWR, _name="vwr"
        )  # Variability-Weighted Return
        cerebro.addanalyzer(bt.analyzers.Calmar, _name="calmar")  # Calmar Ratio
        cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")  # System Quality Number

        # Trading analyzers
        cerebro.addanalyzer(bt.analyzers.GrossLeverage, _name="grossleverage")
        cerebro.addanalyzer(bt.analyzers.PositionsValue, _name="positionsvalue")
        cerebro.addanalyzer(bt.analyzers.PyFolio, _name="pyfolio")

        # Statistical analyzers
        cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name="annualreturn")
        cerebro.addanalyzer(bt.analyzers.MonthlyReturn, _name="monthlyreturn")
        cerebro.addanalyzer(bt.analyzers.DailyReturn, _name="dailyreturn")

        # Volatility analyzers
        cerebro.addanalyzer(bt.analyzers.Volatility, _name="volatility")
        cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name="sharpe_a")

        # Drawdown analyzers
        cerebro.addanalyzer(bt.analyzers.DrawDown_Old, _name="drawdown_old")
        cerebro.addanalyzer(bt.analyzers.DrawDown_New, _name="drawdown_new")

        # Trade statistics analyzers
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades_detailed")
        cerebro.addanalyzer(bt.analyzers.Transactions, _name="transactions")
        cerebro.addanalyzer(bt.analyzers.LogReturns, _name="logreturns")

        logger.info("Added comprehensive default analyzers")

    def _analyze_backtest_results(
        self,
        strategy_instance,
        strategy_name: str,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_capital: float,
    ) -> Dict[str, Any]:
        """Analyze backtest results from analyzers"""
        try:
            # Get analyzer results
            returns_analyzer = strategy_instance.analyzers.returns.get_analysis()
            sharpe_analyzer = strategy_instance.analyzers.sharpe.get_analysis()
            drawdown_analyzer = strategy_instance.analyzers.drawdown.get_analysis()
            trades_analyzer = strategy_instance.analyzers.trades.get_analysis()

            # Calculate final value and total return
            final_value = strategy_instance.broker.getvalue()
            total_return = (final_value - initial_capital) / initial_capital

            # Build comprehensive result
            result = {
                "strategy_name": strategy_name,
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": initial_capital,
                "final_value": final_value,
                "total_return": total_return,
                "max_drawdown": drawdown_analyzer.get("max", {}).get("drawdown", 0),
                "sharpe_ratio": sharpe_analyzer.get("sharperatio", 0),
                "total_trades": trades_analyzer.get("total", {}).get("total", 0),
                "winning_trades": trades_analyzer.get("won", {}).get("total", 0),
                "losing_trades": trades_analyzer.get("lost", {}).get("total", 0),
                "win_rate": self._calculate_win_rate(trades_analyzer),
                "analyzer_results": self._extract_all_analyzer_results(
                    strategy_instance
                ),
            }

            return result

        except Exception as e:
            logger.error(f"Failed to analyze backtest results: {e}")
            # Return basic result on error
            return {
                "strategy_name": strategy_name,
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "initial_capital": initial_capital,
                "final_value": initial_capital,
                "total_return": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "analyzer_results": {},
            }

    def _calculate_win_rate(self, trades_analyzer: Dict[str, Any]) -> float:
        """Calculate win rate from trades analyzer"""
        total_trades = trades_analyzer.get("total", {}).get("total", 0)
        winning_trades = trades_analyzer.get("won", {}).get("total", 0)
        return winning_trades / max(total_trades, 1)

    def _extract_all_analyzer_results(self, strategy_instance) -> Dict[str, Any]:
        """Extract results from all analyzers"""
        analyzer_results = {}
        for analyzer_name in strategy_instance.analyzers._analyzers:
            try:
                analyzer = strategy_instance.analyzers._analyzers[analyzer_name]
                analyzer_results[analyzer_name] = analyzer.get_analysis()
            except Exception as e:
                logger.warning(
                    f"Failed to extract results from analyzer {analyzer_name}: {e}"
                )
                continue
        return analyzer_results

    async def _save_backtest_result(self, result: Dict[str, Any], created_by: str):
        """Save backtest result to database"""
        try:
            db = next(get_db())

            # Create backtest result record
            backtest_result = BacktestResult(
                strategy_name=result["strategy_name"],
                symbol=result["symbol"],
                start_date=result["start_date"],
                end_date=result["end_date"],
                initial_capital=result["initial_capital"],
                final_value=result["final_value"],
                total_return=result["total_return"],
                max_drawdown=result["max_drawdown"],
                sharpe_ratio=result["sharpe_ratio"],
                total_trades=result["total_trades"],
                winning_trades=result["winning_trades"],
                losing_trades=result["losing_trades"],
                win_rate=result["win_rate"],
                created_by=created_by,
                created_at=datetime.now(),
                result_data=json.dumps(result, indent=2),
            )

            db.add(backtest_result)
            db.commit()
            db.refresh(backtest_result)

            logger.info(
                f"Backtest result saved to database with ID: {backtest_result.id}"
            )

        except Exception as e:
            logger.error(f"Failed to save backtest result to database: {e}")
            raise

    async def run_backtest(
        self,
        strategy_name: str,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000.0,
        created_by: str = "system",
        commission: float = 0.0003,  # 0.03% commission (A股标准)
        min_commission: float = 5.0,  # Minimum commission 5元
        mode: TradingMode = TradingMode.BACKTEST,
        slippage: float = 0.001,  # 0.1% slippage (A股流动性较好)
        **kwargs,
    ) -> Dict[str, Any]:
        """Run backtest for a strategy (optimized for Chinese A-share market)"""
        strategy = self.get_strategy(strategy_name)
        if not strategy:
            raise ValueError(f"Strategy {strategy_name} not found")

        try:
            # Create backtest engine
            cerebro = bt.Cerebro()

            # Add strategy
            cerebro.addstrategy(strategy)

            # Set broker parameters for Chinese A-share market
            cerebro.broker.setcash(initial_capital)

            # Set commission for A-share market (0.03% + 5元最低佣金)
            cerebro.broker.setcommission(
                commission=commission,
                mult=1.0,  # 无杠杆
                commtype=bt.CommInfoBase.COMM_PERC,  # 百分比佣金
                stocklike=True,  # 股票类佣金
            )

            # Set slippage for A-share market
            cerebro.broker.set_slippage_perc(slippage)

            # A股市场特点设置
            cerebro.broker.set_shortcash(False)  # A股不允许做空
            cerebro.broker.set_checksubmit(True)  # 启用提交检查

            # Set position sizing (A股100股为1手)
            cerebro.addsizer(bt.sizers.FixedSize, stake=100)

            # Add comprehensive analyzers
            self._add_default_analyzers(cerebro)

            # Run backtest
            logger.info(
                f"Starting A-share backtest for {strategy_name} with commission={commission}, min_commission={min_commission}, slippage={slippage}"
            )
            results = cerebro.run()

            # Analyze results
            result = self._analyze_backtest_results(
                results[0], strategy_name, symbol, start_date, end_date, initial_capital
            )

            # Add A-share specific parameters to result
            result["commission"] = commission
            result["min_commission"] = min_commission
            result["slippage"] = slippage
            result["market_type"] = "A-share"
            result["leverage"] = 1.0  # A股无杠杆
            result["short_selling"] = False  # A股不允许做空

            # Save backtest result to database
            await self._save_backtest_result(result, created_by)

            logger.info(f"A-share backtest completed for {strategy_name}")
            return result

        except Exception as e:
            logger.error(f"Backtest failed for {strategy_name}: {e}")
            raise


strategy_service = StrategyService()
