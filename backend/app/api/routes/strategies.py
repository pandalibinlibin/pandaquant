"""
Strategy management API routes
"""

from fastapi import APIRouter
from app.models import BacktestResult
from sqlmodel import select

router = APIRouter(prefix="/strategies", tags=["strategies"])

from app.domains.strategies.services import StrategyService

strategy_service = StrategyService()

from typing import Any, List
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


class SignalInfo(BaseModel):
    """Signal information response model"""

    id: str = Field(..., description="Signal ID")
    signal_time: str = Field(..., description="Signal generation time (ISO 8601)")
    symbol: str = Field(..., description="Trading symbol")
    status: str = Field(..., description="Signal type (buy/sell/hold)")
    signal_strength: float = Field(..., description="Signal confidence (0-1)")
    price: Optional[float] = Field(None, description="Signal price")
    quantity: Optional[int] = Field(None, description="Suggested quantity")
    message: Optional[str] = Field(None, description="Signal message")


class SignalListResponse(BaseModel):
    """Signal list response model"""

    data: List[SignalInfo] = Field(..., description="List of signals")
    total: int = Field(..., description="Total number of signals")


@router.get("/", response_model=StrategiesList)
def list_strategies(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    List all available trading strategies

    Returns a comprehensive list of all registered trading strategies
    that can be used for backtesting and live trading.

    **Returns:**
    - **data**: List of strategy information with name and description
    - **count**: Total number of available strategies

    **Example Response:**
    ```json
    {
        "data": [
            {
                "name": "rsi_mean_reversion",
                "description": "RSI-based mean reversion strategy"
            }
        ],
        "count": 1
    }
    ```
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
    Get detailed information about a specific strategy

    Retrieves comprehensive details about a single trading strategy
    including its description, parameters, and configuration options.

    **Path Parameters:**
    - **strategy_name**: Name of the strategy to retrieve

    **Returns:**
    - **name**: Strategy name (identifier)
    - **description**: Detailed strategy description from docstring

    **Example:**
    GET /strategies/rsi_mean_reversion

    **Response:**
    ```json
    {
        "name": "rsi_mean_reversion",
        "description": "RSI-based mean reversion strategy that trades based on overbought/oversold conditions"
    }
    ```

    **Error Responses:**
    - 404: Strategy not found
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


class FactorInstanceInfo(BaseModel):
    """Factor instance information in DataGroup"""

    instance_name: str = Field(..., description="Factor instance name (e.g., MA_5_SMA)")
    factor_class: str = Field(
        ..., description="Factor class name (e.g., MovingAverageFactor)"
    )
    parameters: dict = Field(..., description="Factor instance parameters")


class DataGroupInfo(BaseModel):
    """DataGroup configuration information"""

    name: str = Field(..., description="DataGroup name")
    datagroup_class: str = Field(
        ..., description="DataGroup class name (e.g., DailyDataGroup)"
    )
    data_type: str = Field(..., description="Data type (e.g., daily, minute)")
    weight: float = Field(..., description="DataGroup weight in strategy")
    factors: List[FactorInstanceInfo] = Field(
        ..., description="Factor instances in this group"
    )


class StrategyDetailInfo(BaseModel):
    """Detailed strategy information including DataGroup configs"""

    name: str = Field(..., description="Strategy name")
    description: Optional[str] = Field(None, description="Strategy description")
    data_groups: List[DataGroupInfo] = Field(
        ..., description="DataGroup configurations"
    )


@router.get("/{strategy_name}/detail", response_model=StrategyDetailInfo)
def get_strategy_detail(
    strategy_name: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get detailed strategy information including DataGroup configurations

    Returns comprehensive strategy details including all DataGroup configs
    and factor instances used in the strategy.
    """
    from fastapi import HTTPException

    strategy_class = strategy_service.get_strategy(strategy_name)
    if not strategy_class:
        raise HTTPException(
            status_code=404, detail=f"Strategy {strategy_name} not found"
        )

    data_group_configs = strategy_class.get_data_group_configs()

    data_groups = []
    for config in data_group_configs:
        factors = [
            FactorInstanceInfo(
                instance_name=f["name"], factor_class=f["type"], parameters=f["params"]
            )
            for f in config.get("factors", [])
        ]

        data_groups.append(
            DataGroupInfo(
                name=config["name"],
                datagroup_class=config["type"],
                data_type=config.get("data_type", config["name"]),
                weight=config.get("weight", 1.0),
                factors=factors,
            )
        )

    return StrategyDetailInfo(
        name=strategy_name,
        description=getattr(strategy_class, "__doc__", None),
        data_groups=data_groups,
    )


@router.post("/{strategy_name}/backtest", response_model=BacktestResponse)
async def run_backtest(
    strategy_name: str,
    request: BacktestRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Run a backtest for a specific trading strategy

    Executes a historical backtest of the specified strategy using
    the provided parameters and returns comprehensive performance metrics.

    **Path Parameters:**
    - **strategy_name**: Name of the strategy to backtest

    **Request Body:**
    - **symbol**: Stock symbol (e.g., "000001.SZ")
    - **start_date**: Backtest start date (YYYY-MM-DD)
    - **end_date**: Backtest end date (YYYY-MM-DD)
    - **initial_capital**: Starting capital amount (default: 1000000.0)
    - **commission**: Commission rate (default: 0.0003)
    - **commtype**: Commission type - "PERC" or "FIXED" (default: "PERC")
    - **commmin**: Minimum commission (default: 5.0)
    - **stocklike**: Whether instrument is stock-like (default: true)
    - **leverage**: Leverage ratio (default: 1.0)
    - **margin**: Margin requirement (optional)
    - **mode**: Trading mode (default: "BACKTEST")

    **Returns:**
    - **backtest_id**: Unique identifier for the backtest result
    - **strategy_name**: Name of the backtested strategy
    - **performance**: Comprehensive performance metrics
    - **chart_path**: Path to performance chart (if generated)
    - **status**: Backtest execution status

    **Example Request:**
    ```json
    {
        "symbol": "000001.SZ",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 1000000.0
    }
    ```

    **Error Responses:**
    - 404: Strategy not found
    - 400: Invalid parameters or data
    - 500: Server error during backtest execution
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
            session=session,
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


@router.get("/{strategy_name}/backtests/{backtest_id}", response_model=BacktestResponse)
def get_backtest_result(
    strategy_name: str,
    backtest_id: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get detailed backtest result by ID

    Retrieves comprehensive backtest results including performance metrics,
    trade statistics, and chart data for a specific backtest execution.

    **Path Parameters:**
    - **strategy_name**: Name of the strategy
    - **backtest_id**: Unique identifier of the backtest result (UUID)

    **Returns:**
    - **backtest_id**: Unique identifier for the backtest
    - **strategy_name**: Strategy name used in the backtest
    - **symbol**: Stock symbol that was backtested
    - **start_date**: Backtest start date
    - **end_date**: Backtest end date
    - **initial_capital**: Starting capital used
    - **performance**: Detailed performance metrics
    - **chart_path**: Path to performance chart (if available)
    - **status**: Current status of the backtest

    **Example:**
    GET /strategies/rsi_mean_reversion/backtests/123e4567-e89b-12d3-a456-426614174000

    **Error Responses:**
    - 400: Invalid backtest ID format
    - 404: Backtest result not found
    """

    from fastapi import HTTPException
    from app.models import BacktestResult
    from sqlmodel import select
    from uuid import UUID
    import json

    try:
        backtest_uuid = UUID(backtest_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid backtest ID format")

    statement = select(BacktestResult).where(
        BacktestResult.id == backtest_uuid,
        BacktestResult.strategy_name == strategy_name,
    )
    result = session.exec(statement).first()

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Backtest result not found for strategy {strategy_name}",
        )

    result_data = json.loads(result.result_data) if result.result_data else {}
    performance_data = result_data.get("performance", {})

    performance_metrics = PerformanceMetrics(
        total_return=result.total_return,
        sharpe_ratio=result.sharpe_ratio,
        max_drawdown=result.max_drawdown,
        total_trades=result.total_trades,
        winning_trades=result.winning_trades,
        losing_trades=result.losing_trades,
        win_rate=result.win_rate,
        final_value=result.final_value,
        **performance_data,
    )

    return BacktestResponse(
        backtest_id=str(result.id),
        strategy_name=result.strategy_name,
        symbol=result.symbol,
        start_date=result.start_date,
        end_date=result.end_date,
        initial_capital=result.initial_capital,
        performance=performance_metrics,
        chart_path=result_data.get("chart_path"),
        status="completed",
    )


class BacktestHistoryItem(BaseModel):
    """Backtest history item model"""

    backtest_id: str
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    win_rate: float
    created_at: str


class BacktestHistoryList(BaseModel):
    """List of backtest history"""

    data: List[BacktestHistoryItem]
    count: int
    page: int
    size: int
    total_pages: int


@router.get("/{strategy_name}/backtests", response_model=BacktestHistoryList)
def get_backtest_history(
    strategy_name: str,
    session: SessionDep,
    current_user: CurrentUser,
    page: int = 1,
    size: int = 20,
) -> Any:
    """
    Get paginated list of backtest history for a strategy

    Retrieves all historical backtest results for a specific strategy
    with pagination support for efficient data retrieval.

    **Path Parameters:**
    - **strategy_name**: Name of the strategy

    **Query Parameters:**
    - **page**: Page number (default: 1, min: 1)
    - **size**: Items per page (default: 20, max: 100)

    **Returns:**
    - **data**: List of backtest history items with key metrics
    - **count**: Total number of backtest results
    - **page**: Current page number
    - **size**: Items per page
    - **total_pages**: Total number of pages

    **Example:**
    GET /strategies/rsi_mean_reversion/backtests?page=1&size=10

    **Response:**
    ```json
    {
        "data": [
            {
                "backtest_id": "123e4567-e89b-12d3-a456-426614174000",
                "strategy_name": "rsi_mean_reversion",
                "symbol": "000001.SZ",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 1000000.0,
                "final_value": 1050000.0,
                "total_return": 0.05,
                "sharpe_ratio": 1.2,
                "max_drawdown": -0.03,
                "total_trades": 25,
                "win_rate": 0.6,
                "created_at": "2023-12-31T23:59:59Z"
            }
        ],
        "count": 1,
        "page": 1,
        "size": 20,
        "total_pages": 1
    }
    ```
    """
    from fastapi import HTTPException
    from app.models import BacktestResult
    from sqlmodel import select, func
    from datetime import datetime

    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if size < 1 or size > 100:
        raise HTTPException(status_code=400, detail="Size must be between 1 and 100")

    offset = (page - 1) * size

    count_statement = select(func.count(BacktestResult.id)).where(
        BacktestResult.strategy_name == strategy_name
    )
    total_count = session.exec(count_statement).one()

    statement = (
        select(BacktestResult)
        .where(BacktestResult.strategy_name == strategy_name)
        .order_by(BacktestResult.created_at.desc())
        .offset(offset)
        .limit(size)
    )

    results = session.exec(statement).all()

    history_items = []
    for result in results:
        item = BacktestHistoryItem(
            backtest_id=str(result.id),
            strategy_name=result.strategy_name,
            symbol=result.symbol,
            start_date=result.start_date,
            end_date=result.end_date,
            initial_capital=result.initial_capital,
            final_value=result.final_value,
            total_return=result.total_return,
            sharpe_ratio=result.sharpe_ratio,
            max_drawdown=result.max_drawdown,
            total_trades=result.total_trades,
            win_rate=result.win_rate,
            created_at=result.created_at.isoformat(),
        )
        history_items.append(item)

    total_pages = (total_count + size - 1) // size

    return BacktestHistoryList(
        data=history_items,
        count=total_count,
        page=page,
        size=size,
        total_pages=total_pages,
    )


@router.get(
    "/{strategy_name}/backtests/{backtest_id}/signals",
    response_model=SignalListResponse,
)
def get_backtest_signals(
    strategy_name: str,
    backtest_id: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> SignalListResponse:
    """
    Get all signals for a specific backtest

     Args:
        strategy_name: Strategy name
        backtest_id: Backtest ID
        session: Database session
        current_user: Current authenticated user

    Returns:
        List of signals for the backtest

    Raises:
        HTTPException: If backtest not found
    """
    from uuid import UUID
    from app.models import Signal
    from sqlmodel import select

    backtest = session.get(BacktestResult, UUID(backtest_id))
    if not backtest:
        raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")

    statement = (
        select(Signal)
        .where(Signal.backtest_id == UUID(backtest_id))
        .order_by(Signal.signal_time)
    )
    signals = session.exec(statement).all()

    signal_list = []
    for signal in signals:
        signal_info = SignalInfo(
            id=str(signal.id),
            signal_time=signal.signal_time.isoformat() + "Z",
            symbol=signal.symbol,
            status=signal.status,
            signal_strength=signal.signal_strength,
            price=signal.price,
            quantity=signal.quantity,
            message=signal.message,
        )
        signal_list.append(signal_info)

    return SignalListResponse(data=signal_list, total=len(signal_list))


@router.delete("/{strategy_name}/backtests/{backtest_id}")
def delete_backtest_result(
    strategy_name: str,
    backtest_id: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Delete a specific backtest result

    Permanently removes a backtest result from the database.
    This action cannot be undone.

    **Path Parameters:**
    - **strategy_name**: Name of the strategy
    - **backtest_id**: Unique identifier of the backtest result (UUID)

    **Returns:**
    - **message**: Confirmation message indicating successful deletion

    **Example:**
    DELETE /strategies/rsi_mean_reversion/backtests/123e4567-e89b-12d3-a456-426614174000

    **Response:**
    ```json
    {
        "message": "Backtest result deleted successfully"
    }
    ```

    **Error Responses:**
    - 400: Invalid backtest ID format
    - 404: Backtest result not found
    """
    from fastapi import HTTPException
    from app.models import BacktestResult
    from sqlmodel import select
    from uuid import UUID

    try:
        backtest_uuid = UUID(backtest_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid backtest ID format")

    statement = select(BacktestResult).where(
        BacktestResult.id == backtest_uuid,
        BacktestResult.strategy_name == strategy_name,
    )
    result = session.exec(statement).first()

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Backtest result not found for strategy {strategy_name}",
        )

    session.delete(result)
    session.commit()

    return {"message": "Backtest result deleted successfully"}


@router.get(
    "/{strategy_name}/backtests/{backtest_id}/price_data",
)
async def get_backtest_price_data(
    strategy_name: str,
    backtest_id: str,
    session: SessionDep,
    current_user: CurrentUser,
):
    """
    Get price data for a specific backtest
    """
    from uuid import UUID
    from app.domains.data.services import DataService

    statement = (
        select(BacktestResult)
        .where(BacktestResult.id == UUID(backtest_id))
        .where(BacktestResult.strategy_name == strategy_name)
    )
    backtest = session.exec(statement).first()

    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")

    data_service = DataService()

    data_type = backtest.data_type

    measurement = data_type

    price_df = await data_service.get_data_from_influxdb(
        measurement=measurement,
        start_date=backtest.start_date,
        end_date=backtest.end_date,
        tags={"symbol": backtest.symbol},
        fields=["close"],
    )

    if price_df.empty:
        return {"data": [], "total": 0}

    price_data = []
    for _, row in price_df.iterrows():
        price_data.append(
            {
                "time": row["timestamp"].strftime("%Y-%m-%d"),
                "value": float(row["close"]),
            }
        )

    return {"data": price_data, "total": len(price_data)}
