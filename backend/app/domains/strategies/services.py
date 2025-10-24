import asyncio
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Union
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import Backtest, Strategy
from app.core.db import get_db
from app.domains.data.services import DataService
from app.domains.factors.services import factor_service
import backtrader as bt
from uuid import UUID
from .base_strategy import BaseStrategy


class StrategyService:

    def __init__(self):
        self.data_service = DataService()
        self.factor_service = factor_service
        self.qlib_initialized = False

        self.strategy_classes = {}

    def register_strategy_class(self, strategy_name: str, strategy_class):
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(
                f"Strategy class must inherit from BaseStrategy, got {strategy_class}"
            )

        self.strategy_classes[strategy_name] = strategy_class
        print(f"Registered strategy: {strategy_name} -> {strategy_class.__name__}")

    def unregister_strategy_class(self, strategy_name: str):
        if strategy_name in self.strategy_classes:
            del self.strategy_classes[strategy_name]
        else:
            print(f"Strategy {strategy_name} not found")

    def get_strategy_class(self, strategy_name: str):
        if strategy_name not in self.strategy_classes:
            available_strategies = list(self.strategy_classes.keys())
            raise ValueError(
                f"Strategy {strategy_name} not found. Available strategies: {available_strategies}"
            )
        return self.strategy_classes[strategy_name]

    def list_available_strategies(self) -> List[str]:
        return list(self.strategy_classes.keys())

    def get_strategy_info(self, strategy_name: str) -> Dict[str, Any]:
        if strategy_name not in self.strategy_classes:
            raise ValueError(f"Strategy {strategy_name} not found")

        strategy_class = self.get_strategy_class(strategy_name)
        return {
            "name": strategy_name,
            "class": strategy_class.__name__,
            "module": strategy_class.__module__,
            "doc": strategy_class.__doc__,
        }

    async def initialize_qlib(self, region: str = "cn"):
        try:
            import qlib
            from qlib.config import REG_CN, REG_US
            import os

            region_config = {
                "cn": {"region": REG_CN, "data_name": "cn_data"},
                "us": {"region": REG_US, "data_name": "us_data"},
            }

            if region not in region_config:
                raise ValueError(
                    f"Unsupported region: {region}. Supported regions: {list(region_config.keys())}"
                )

            config = region_config[region]
            qlib_data_path = os.path.expanduser(
                f"~/.qlib/qlib_data/{config['data_name']}"
            )

            if not os.path.exists(qlib_data_path):
                print(
                    f"Qlib {region} data not fuond. Downloading data automatically..."
                )
                try:
                    qlib.run.get_data(config["region"])
                    print(f"Qlib {region} data downloaded successfully.")

                except Exception as downlaod_error:
                    print(f"Error downloading Qlib {region} data: {downlaod_error}")
                    self.qlib_initialized = False
                    return False

            qlib.init(provider_uri=qlib_data_path, region=config["region"])
            self.qlib_initialized = True
            print(f"Qlib initialized successfully for {region} region.")
            return True
        except Exception as e:
            print(f"error initializing Qlib: {e}")
            self.qlib_initialized = False
            return False

    async def create_strategy(
        self,
        name: str,
        description: str,
        strategy_type: str,
        config: Dict[str, Any],
        created_by: str,
    ) -> Optional[Strategy]:
        try:
            db = next(get_db())
            existing_strategy = db.query(Strategy).filter(Strategy.name == name).first()
            if existing_strategy:
                raise ValueError(
                    f"Strategy name {name} already exists, please use a different name"
                )

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

    async def get_strategy(
        self,
        strategy_id: str = None,
        name: str = None,
    ) -> Optional[Strategy]:
        try:
            db = next(get_db())

            if strategy_id:
                strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
            elif name:
                strategy = db.query(Strategy).filter(Strategy.name == name).first()
            else:
                raise ValueError("Either strategy_id or name must be provided")

            return strategy
        except Exception as e:
            print(f"Error getting strategy: {e}")
            return None
        finally:
            db.close()

    async def list_strategies(
        self,
        created_by: str = None,
        strategy_type: str = None,
        status: str = None,
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
            print(f"Error listing strategies: {e}")
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

    async def delete_strategy(
        self,
        strategy_id: str,
    ) -> bool:
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
        start_date: str,
        end_date: str,
        created_by: str,
        initial_capital: float = 1000000.0,
        symbols: List[str] = None,
        commission: float = 0.0003,
        slippage: float = 0.001,
        margin: float = 1.0,
        leverage: float = 1.0,
        min_commission: float = 5.0,
        max_commission: float = 50.0,
        analyzers: List[str] = None,
    ) -> Dict[str, Any]:
        try:
            strategy = await self.get_strategy(strategy_id)
            if not strategy:
                raise ValueError(f"Strategy not found: {strategy_id}")

            cerebro = bt.Cerebro()

            cerebro.broker.setcash(initial_capital)

            cerebro.broker.setcommission(commission=commission)

            if slippage > 0:
                cerebro.broker.setslippage(slippage=slippage)

            cerebro.broker.set_margin(margin)
            cerebro.broker.set_leverage(leverage)

            cerebro.broker.set_min_commission(min_commission)
            cerebro.broker.set_max_commission(max_commission)

            if analyzers:
                for analyzer in analyzers:
                    cerebro.addanalyzer(analyzer)

            strategy_class = self.get_strategy_class(strategy.strategy_type)
            cerebro.addstrategy(strategy_class, config=json.loads(strategy.config))

            if symbols:
                for symbol in symbols:
                    data = await self._get_backtest_data(
                        symbol, start_date, end_date, data_type="daily"
                    )
                    if not data.empty:
                        datafeed = bt.feeds.PandasData(dataname=data)
                        cerebro.adddata(datafeed)

            results = cerebro.run()

            analysis = self._analyze_backtest_results(cerebro, results)

            await self._save_backtest_result(
                strategy_id, analysis, start_date, end_date, created_by
            )

            return analysis

        except Exception as e:
            print(f"Error running backtest: {e}")
            return {}

    async def _get_backtest_data(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None,
        data_type: str = "daily",
    ) -> pd.DataFrame:
        try:
            if not symbol:
                raise ValueError(f"Symbol is required for {data_type} data")

            data = await self.data_service.get_data_from_influxdb(
                measurement=data_type,
                start_date=start_date,
                end_date=end_date,
                tags={"symbol": symbol},
            )

            if data.empty:
                print(f"No {data_type} data found for {symbol}")
                return pd.DataFrame()

            data = data.set_index("timestamp")
            data = data.sort_index()

            return data
        except Exception as e:
            print(f"Error getting backtest data: {e}")
            return pd.DataFrame()

    async def _analyze_backtest_results(self, cerebro, results) -> Dict[str, Any]:
        try:
            initial_cash = cerebro.broker.get_cash()
            final_value = cerebro.broker.get_value()
            total_return = (final_value - initial_cash) / initial_cash

            analysis = {
                "initial_cash": initial_cash,
                "final_value": final_value,
                "total_return": total_return,
                "total_pnl": final_value - initial_cash,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            if results and len(results) > 0:
                strategy_results = results[0]

                for analyzer_name in cerebro.analyzers:
                    try:
                        analyzer = getattr(
                            strategy_results.analyzers, analyzer_name, None
                        )
                        if analyzer and hasattr(analyzer, "get_analysis"):
                            analyzer_result = analyzer.get_analysis()
                            analysis[f"analyzer_{analyzer_name}"] = analyzer_result
                        elif analyzer:
                            analyzer[f"analyzer_{analyzer_name}"] = str(analyzer)
                    except Exception as e:
                        print(f"Error getting analyzer {analyzer_name} result: {e}")
                        analysis[f"analyzer_{analyzer_name}"] = str(e)

            return analysis
        except Exception as e:
            print(f"Error analyzing backtest results: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _save_backtest_result(
        self,
        strategy_id: str,
        result: Dict[str, Any],
        start_date: str,
        end_date: str,
        created_by: str,
    ) -> bool:
        try:
            from app.core.db import get_session
            from app.models import Backtest
            from sqlmodel import select
            from datetime import datetime
            import json

            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            async with get_session() as session:
                backtest = Backtest(
                    name=f"Backtest_{strategy_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    strategy_id=strategy_id,
                    start_date=start_dt,
                    end_date=end_dt,
                    initial_capital=result.get("initial_cash", 1000000.0),
                    status="completed",
                    results=json.dumps(result, ensure_ascii=False, indent=2),
                    performance_metrics=json.dumps(
                        {
                            "total_return": result.get("total_return", 0.0),
                            "total_pnl": result.get("total_pnl", 0.0),
                            "final_value": result.get("final_value", 0.0),
                            "analyzer_count": len(
                                [k for k in result.keys() if k.startswith("analyzer_")]
                            ),
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    created_by=created_by,
                )

                session.add(backtest)
                await session.commit()
                await session.refresh(backtest)

                print(f"Backtest result saved successfully for strategy: {strategy_id}")
                print(
                    f"Saved {len([k for k in result.keys() if k.startswith('analyzer_')])} analyzers results"
                )
                return True
        except Exception as e:
            print(f"Error saving backtest result: {e}")
            return False
