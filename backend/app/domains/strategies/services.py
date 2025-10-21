"""
策略服务模块
负责策略的创建，回测和管理
"""

import asyncio
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import Strategy, Backtest, Factor
from app.core.db import get_db
from app.domains.data.services import DataService
from app.domains.factors.services import FactorService
import backtrader as bt


class StrategyService:

    def __init__(self):
        self.data_service = DataService()
        self.factor_service = FactorService()

    async def create_strategy(
        self,
        name: str,
        description: str,
        strategy_type: str,
        config: Dict[str, Any],
        created_by: str,
    ) -> Strategy:
        try:

            db = next(get_db())

            strategy = Strategy(
                name=name,
                description=description,
                strategy_type=strategy_type,
                config=json.dumps(config),
                created_by=created_by,
            )

            db.add(strategy)
            db.commit()
            db.refresh(strategy)

            return strategy

        except Exception as e:
            print(f"Error creating strategy: {e}")
            db.rollback()
            return None

        finally:
            db.close()

    async def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        try:
            db = next(get_db())
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            return strategy
        except Exception as e:
            print(f"Error getting strategy: {e}")
            return None
        finally:
            db.close()

    async def list_strategies(
        self, created_by: str = None, strategy_type: str = None, status: str = None
    ) -> List[Strategy]:
        try:
            db = next(get_db())
            query = db.query(Strategy)

            if created_by:
                query = query.filter(Strategy.created_by == created_by)
            if strategy_type:
                query = query.filter(Strategy.strategy_type == strategy_type)
            if status:
                query = query.filter(Strategy.status == status)

            strategies = query.all()
            return strategies

        except Exception as e:
            print(f"Error Listing strategies: {e}")
            return []
        finally:
            db.close()

    async def update_strategy(
        self,
        strategy_id: str,
        name: str = None,
        description: str = None,
        config: Dict[str, Any] = None,
        status: str = None,
    ) -> bool:
        try:
            db = next(get_db())
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

            if not strategy:
                return False

            if name:
                strategy.name = name

            if description:
                strategy.description = description

            if config:
                strategy.config = json.dumps(config)

            if status:
                strategy.status = status

            strategy.updated_at = datetime.utcnow()

            db.commit()

            return True

        except Exception as e:
            print(f"Error updating strategy: {e}")
            db.rollback()
            return False

        finally:
            db.close()

    async def delete_strategy(self, strategy_id: str) -> bool:
        try:
            db = next(get_db())
            strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

            if not strategy:
                return False

            db.delete(strategy)
            db.commit()

            return True

        except Exception as e:
            print(f"Error deleting strategy: {e}")
            db.rollback()
            return False

        finally:
            db.close()

    async def run_backtest(
        self,
        strategy_id: str,
        symbol: str,
        start_date: str,
        end_date: str,
        initial_cash: float = 100000.0,
        commission: float = 0.001,
    ) -> Dict[str, Any]:
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                return {"error": "Strategy not found"}

            config = json.loads(strategy.config)

            data = await self.data_service.get_data_from_influxdb(
                symbol,
                start_date,
                end_date,
                "daily",
            )

            if data.empty:
                return {"error": "No data available"}

            data = data.sort_values("timestamp")
            data = data.set_index("timestamp")

            cerebro = bt.Cerebro()

            data_feed = bt.feeds.PandasData(
                dataname=data,
                datetime=None,
                open="open",
                high="high",
                low="low",
                close="close",
                volume="volume",
                openinterest=None,
            )
            cerebro.adddata(data_feed)

            if strategy.strategy_type == "factor_mining":
                cerebro.addstrategy(FactorMiningStrategy, config=config)
            elif strategy.strategy_type == "backtest":
                cerebro.addstrategy(BacktestStrategy, config=config)
            else:
                return {"error": "Unsupported strategy type"}

            cerebro.broker.setcash(initial_cash)
            cerebro.broker.setcommission(commission)

            cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

            results = cerebro.run()

            strat = results[0]
            returns = strat.analyzers.returns.get_analysis()
            sharpe = strat.analyzers.sharpe.get_analysis()
            drawdown = strat.analyzers.drawdown.get_analysis()
            trades = strat.analyzers.trades.get_analysis()

            final_value = cerebro.broker.getvalue()
            total_return = (final_value - initial_cash) / initial_cash * 100

            backtest = Backtest(
                strategy_id=strategy_id,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                initial_cash=initial_cash,
                final_value=final_value,
                total_return=total_return,
                sharpe_ratio=sharpe.get("sharperatio", 0),
                max_drawdown=drawdown.get("max", {}).get("drawdown", 0),
                total_trades=trades.get("total", {}).get("total", 0),
                win_rate=trades.get("won", {}).get("total", 0)
                / max(trades.get("total", {}).get("total", 1), 1)
                * 100,
                result=json.dumps(
                    {
                        "returns": returns,
                        "sharpe": sharpe,
                        "drawdown": drawdown,
                        "trades": trades,
                    }
                ),
                created_by=strategy.created_by,
            )

            db = next(get_db())
            db.add(backtest)
            db.commit()

            return {
                "success": True,
                "backtest_id": str(backtest.id),
                "final_value": final_value,
                "total_return": total_return,
                "sharpe_ratio": sharpe.get("sharperatio", 0),
                "max_drawdown": drawdown.get("max", {}).get("drawdown", 0),
                "total_trades": trades.get("total", {}).get("total", 0),
                "win_rate": trades.get("won", {}).get("total", 0)
                / max(trades.get("total", {}).get("total", 1), 1)
                * 100,
            }

        except Exception as e:
            print(f"Error running backtest: {e}")
            return {"error": str(e)}

    async def get_backtest_results(
        self,
        strategy_id: str = None,
        symbol: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> List[Backtest]:
        try:
            db = next(get_db())
            query = db.query(Backtest)

            if strategy_id:
                query = query.filter(Backtest.strategy_id == strategy_id)
            if symbol:
                query = query.filter(Backtest.symbol == symbol)
            if start_date:
                query = query.filter(Backtest.start_date >= start_date)
            if end_date:
                query = query.filter(Backtest.end_date <= end_date)

            backtests = query.order_by(Backtest.created_at.desc()).all()
            return backtests

        except Exception as e:
            print(f"Error getting backtest results: {e}")
            return []
        finally:
            db.close()

    def close(self):
        if hasattr(self, "data_service"):
            self.data_service.close()
        if hasattr(self, "factor_service"):
            self.factor_service.close()


class FactorMiningStrategy(bt.Strategy):

    def __init__(self, config):
        self.config = config
        self.factors = config.get("factors", [])
        self.thresholds = config.get("thresholds", {})

    def next(self):
        pass


class BacktestStrategy(bt.Strategy):

    def __init__(self, config):
        self.config = config
        self.factors = config.get("factors", [])
        self.signals = config.get("signals", {})

    def next(self):
        pass
