"""
Strategy management API routes
"""

from fastapi import APIRouter

router = APIRouter(prefix="/strategies", tags=["strategies"])

from app.domains.strategies.services import StrategyService

strategy_service = StrategyService()

from typing import Any
from app.api.deps import CurrentUser, SessionDep
from pydantic import BaseModel
from typing import Optional

from pydantic import Field
from app.domains.strategies.enums import TradingMode


class StrategyInfo(BaseModel):
    """Strategy information model"""

    name: str
    description: Optional[str] = None


class StrategiesList(BaseModel):
    """List of strategies"""

    data: list[StrategyInfo]
    count: int


class BacktestRequest(BaseModel):
    """Backtest request model"""

    symbol: str = Field(..., description="Stock symbol (e.g., 000001.SZ)")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_capital: float = Field(default=1000000.0, description="Initial capital")
    commission: float = Field(default=0.0003, description="Commission rate")
    commtype: str = Field(default="PERC", description="Commission type: PERC or FIXED")
    commmin: float = Field(default=5.0, description="Minimum commission")
    stocklike: bool = Field(default=True, description="Stock-like instrument")
    leverage: float = Field(default=1.0, description="Leverage ratio")
    margin: Optional[float] = Field(default=None, description="Margin requirement")
    mode: Optional[str] = Field(default="BACKTEST", description="Trading mode")


class PerformanceMetrics(BaseModel):
    """Performance metrics model"""

    total_return: Optional[float] = None
    total_return_pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_trades: Optional[int] = None
    winning_trades: Optional[int] = None
    losing_trades: Optional[int] = None
    win_rate: Optional[float] = None
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    avg_annual_return: Optional[float] = None
    avg_annual_return_pct: Optional[float] = None
    vwr: Optional[float] = None
    calmar_ratio: Optional[float] = None
    sqn: Optional[float] = None
    avg_gross_leverage: Optional[float] = None
    max_gross_leverage: Optional[float] = None
    avg_positions_value: Optional[float] = None
    max_positions_value: Optional[float] = None
    final_value: Optional[float] = None
    time_return: Optional[dict] = None
    time_drawdown: Optional[dict] = None
    pyfolio_metrics: Optional[dict] = None


class BacktestResponse(BaseModel):
    """Backtest response model"""

    backtest_id: str
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    performance: PerformanceMetrics
    chart_path: Optional[str] = None
    status: str


@router.get("/", response_model=StrategiesList)
def list_strategies(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    List all available strategies
    """
    try:
        strategy_names = strategy_service.list_strategies()
        strategies = [
            StrategyInfo(name=name, description=None) for name in strategy_names
        ]
        return StrategiesList(data=strategies, count=len(strategies))
    except Exception as e:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=500, detail=f"Error listing strategies: {str(e)}"
        )


@router.get("/{strategy_name}", response_model=StrategyInfo)
def get_strategy(
    strategy_name: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get strategy details by name
    """
    from fastapi import HTTPException

    strategy_class = strategy_service.get_strategy(strategy_name)
    if not strategy_class:
        raise HTTPException(
            status_code=404, detail=f"Strategy {strategy_name} not found"
        )

    return StrategyInfo(
        name=strategy_name, description=getattr(strategy_class, "__doc__", None)
    )


@router.post("/{strategy_name}/backtest", response_model=BacktestResponse)
async def run_backtest(
    strategy_name: str,
    request: BacktestRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Run a backtest for a specific strategy
    """
    from fastapi import HTTPException

    strategy_class = strategy_service.get_strategy(strategy_name)
    if not strategy_class:
        raise HTTPException(
            status_code=404, detail=f"Strategy {strategy_name} not found"
        )

    try:
        mode = TradingMode.BACKTEST
        if request.mode:
            try:
                mode = TradingMode[request.mode.upper()]
            except KeyError:
                mode = TradingMode(request.mode.lower())

        result = await strategy_service.run_backtest(
            strategy_name=strategy_name,
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            commission=request.commission,
            commtype=request.commtype,
            commmin=request.commmin,
            stocklike=request.stocklike,
            leverage=request.leverage,
            margin=request.margin,
            mode=mode,
            created_by=current_user.email,
        )

        performance_metrics = PerformanceMetrics(**result.get("performance", {}))

        return BacktestResponse(
            backtest_id=result.get("backtest_id"),
            strategy_name=result["strategy_name"],
            symbol=result["symbol"],
            start_date=result["start_date"],
            end_date=result["end_date"],
            initial_capital=result["initial_capital"],
            performance=performance_metrics,
            chart_path=result.get("chart_path"),
            status=result["status"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running backtest: {str(e)}")
