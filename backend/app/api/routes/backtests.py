"""
Enhanced backtest management API routes
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Any, List, Dict, Optional
from datetime import datetime, date
from enum import Enum

from app.api.deps import CurrentUser, SessionDep
from pydantic import BaseModel, Field
from sqlmodel import select, func, and_, or_
from uuid import UUID
import json

from app.models import BacktestResult
from app.domains.strategies.services import StrategyService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/backtests", tags=["backtests"])
strategy_service = StrategyService()


class BacktestSTatus(str, Enum):
    """Backtest status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BacktestSortBy(str, Enum):
    """Backtest sorting options"""

    CREATED_AT = "created_at"
    START_DATE = "start_date"
    END_DATE = "end_date"
    TOTAL_RETURN = "total_return"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    TOTAL_TRADES = "total_trades"


class GlobalBacktestItem(BaseModel):
    """Global backtest item model"""

    backtest_id: str = Field(..., description="Backtest ID")
    strategy_name: str = Field(..., description="Strategy name")
    symbol: str = Field(..., description="Trading symbol")
    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    initial_capital: float = Field(..., description="Initial capital")
    final_value: float = Field(..., description="Final portfolio value")
    total_return: float = Field(..., description="Total return")
    total_return_pct: float = Field(..., description="Total return percentage")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown")
    total_trades: Optional[int] = Field(None, description="Total number of trades")
    winning_trades: Optional[int] = Field(None, description="Number of winning trades")
    losing_trades: Optional[int] = Field(None, description="Number of losing trades")
    win_rate: Optional[float] = Field(None, description="Win rate")
    avg_win: Optional[float] = Field(None, description="Average winning trade")
    avg_loss: Optional[float] = Field(None, description="Average losing trade")
    avg_annual_return: Optional[float] = Field(
        None, description="Average annual return"
    )
    vwr: Optional[float] = Field(None, description="Variability-weighted return")
    calmar_ratio: Optional[float] = Field(None, description="Calmar ratio")
    sqn: Optional[float] = Field(None, description="System quality number")
    status: str = Field(..., description="Backtest status")
    created_at: str = Field(..., description="Creation timestamp")
    created_by: Optional[str] = Field(None, description="Creator email")


class GlobalBacktestList(BaseModel):
    """Global backtest list response model"""

    data: List[GlobalBacktestItem] = Field(..., description="List of backtests")
    count: int = Field(..., description="Total number of backtests")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")


@router.get("/", response_model=GlobalBacktestList)
async def list_all_backtests(
    session: SessionDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Page size"),
    strategy_name: Optional[str] = Query(None, description="Filter by strategy name"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date_from: Optional[str] = Query(
        None, description="Filter by start date from"
    ),
    start_date_to: Optional[str] = Query(None, description="Filter by start date to"),
    status: Optional[str] = Query(None, description="Filter by status"),
    sort_by: BacktestSortBy = Query(
        BacktestSortBy.CREATED_AT, description="Sort by field"
    ),
    sort_desc: bool = Query(True, description="Sort descending"),
) -> GlobalBacktestList:
    """
    List all backtests with filtering and sorting

    Args:
        page: Page number for pagination
        size: Page size for pagination
        strategy_name: Filter by strategy name
        symbol: Filter by trading symbol
        start_date_from: Filter by start date from (YYYY-MM-DD)
        start_date_to: Filter by start date to (YYYY-MM-DD)
        status: Filter by status
        sort_by: Sort field
        sort_desc: Sort descending if True
        current_user: Current authenticated user

    Returns:
        Paginated list of all backtests

    Raises:
        HTTPException: If pagination parameters are invalid
    """
    try:
        conditions = []

        if strategy_name:
            conditions.append(BacktestResult.strategy_name.ilike(f"%{strategy_name}%"))

        if symbol:
            conditions.append(BacktestResult.symbol.ilike(f"%{symbol}%"))

        if start_date_from:
            try:
                datetime.strptime(start_date_from, "%Y-%m-%d")
                conditions.append(BacktestResult.start_date >= start_date_from)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detial="Invalid start_date_from format, use YYYY-MM-DD",
                )

        if start_date_to:
            try:
                datetime.strptime(start_date_to, "%Y-%m-%d")
                conditions.append(BacktestResult.start_date <= start_date_to)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid start_date_to format, use YYYY-MM-DD",
                )

        count_statement = select(func.count(BacktestResult.id))
        if conditions:
            count_statement = count_statement.where(and_(*conditions))

        total_count = session.exec(count_statement).one()

        statement = select(BacktestResult)
        if conditions:
            statement = statement.where(and_(*conditions))

        sort_column = getattr(BacktestResult, sort_by.value, BacktestResult.created_at)
        if sort_desc:
            statement = statement.order_by(sort_column.desc())
        else:
            statement = statement.order_by(sort_column.asc())

        offset = (page - 1) * size
        statement = statement.offset(offset).limit(size)

        results = session.exec(statement).all()

        backtest_items = []
        for result in results:
            result_data = json.loads(result.result_data) if result.result_data else {}

            item = GlobalBacktestItem(
                backtest_id=str(result.id),
                strategy_name=result.strategy_name,
                symbol=result.symbol,
                start_date=result.start_date,
                end_date=result.end_date,
                initial_capital=result.initial_capital,
                final_value=result.final_value or 0.0,
                total_return=result.total_return or 0.0,
                total_return_pct=result.total_return or 0.0,
                sharpe_ratio=result.sharpe_ratio,
                max_drawdown=result.max_drawdown,
                total_trades=result.total_trades,
                winning_trades=result.winning_trades,
                losing_trades=result.losing_trades,
                win_rate=result.win_rate,
                avg_win=result_data.get("performance", {}).get("avg_win"),
                avg_loss=result_data.get("performance", {}).get("avg_loss"),
                avg_annual_return=result_data.get("performance", {}).get(
                    "avg_annual_return"
                ),
                vwr=result_data.get("performance", {}).get("vwr"),
                calmar_ratio=result_data.get("performance", {}).get("calmar_ratio"),
                sqn=result_data.get("performance", {}).get("sqn"),
                status="completed",  # All stored results are completed
                created_at=result.created_at.isoformat(),
                created_by=result.created_by,
            )
            backtest_items.append(item)

        total_pages = (total_count + size - 1) // size

        logger.info(
            f"List {len(backtest_items)} backtests (page {page}, total {total_count})"
        )

        return GlobalBacktestList(
            data=backtest_items,
            count=len(backtest_items),
            page=page,
            size=size,
            total_pages=total_pages,
        )
    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error listing backtests: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


class BacktestComparisonItem(BaseModel):
    """Backtest comparison item model"""

    backtest_id: str = Field(..., description="Backtest ID")
    strategy_name: str = Field(..., description="Strategy name")
    symbol: str = Field(..., description="Trading symbol")
    start_date: str = Field(..., description="Start date")
    end_date: str = Field(..., description="End date")
    initial_capital: float = Field(..., description="Initial capital")
    final_value: float = Field(..., description="Final portfolio value")
    total_return: float = Field(..., description="Total return")
    total_return_pct: float = Field(..., description="Total return percentage")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown")
    total_trades: Optional[int] = Field(None, description="Total number of trades")
    winning_trades: Optional[int] = Field(None, description="Number of winning trades")
    losing_trades: Optional[int] = Field(None, description="Number of losing trades")
    win_rate: Optional[float] = Field(None, description="Win rate")
    avg_win: Optional[float] = Field(None, description="Average winning trade")
    avg_loss: Optional[float] = Field(None, description="Average losing trade")
    avg_annual_return: Optional[float] = Field(
        None, description="Average annual return"
    )
    vwr: Optional[float] = Field(None, description="Variability-weighted return")
    calmar_ratio: Optional[float] = Field(None, description="Calmar ratio")
    sqn: Optional[float] = Field(None, description="System quality number")
    created_at: str = Field(..., description="Creation timestamp")


class BacktestComparison(BaseModel):
    """Backtest comparison response model"""

    comparison_id: str = Field(..., description="Comparison ID")
    backtests: List[BacktestComparisonItem] = Field(
        ..., description="Compared backtests"
    )
    summary: Dict[str, Any] = Field(..., description="Comparison summary")
    created_at: str = Field(..., description="Comparison timestamp")


@router.post("/compare", response_model=BacktestComparison)
async def compare_backtests(
    backtest_ids: List[str],
    session: SessionDep,
    current_user: CurrentUser,
) -> BacktestComparison:
    """
    Compare multiple backtests

    Args:
        backtest_ids: List of backtest IDs to compare
        current_user: Current authenticated user

    Returns:
        Comparison results with summary statistics

    Raises:
        HTTPException: If backtest IDs are invalid or not found
    """
    try:
        if len(backtest_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 backtests are required for comparison",
            )
        if len(backtest_ids) > 10:
            raise HTTPException(
                status_code=400, detail="Maximum 10 backtests can be compared at once"
            )

        backtest_uuids = []
        for backtest_id in backtest_ids:
            try:
                backtest_uuids.append(UUID(backtest_id))
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid backtest ID: {backtest_id}"
                )

        statement = select(BacktestResult).where(BacktestResult.id.in_(backtest_uuids))
        results = session.exec(statement).all()

        if len(results) != len(backtest_uuids):
            found_ids = [str(r.id) for r in results]
            missing_ids = [bid for bid in backtest_ids if bid not in found_ids]
            raise HTTPException(
                status_code=404, detail=f"Backtests not found: {missing_ids}"
            )

        comparison_items = []
        for result in results:
            result_data = json.loads(result.result_data) if result.result_data else {}

            item = BacktestComparisonItem(
                backtest_id=str(result.id),
                strategy_name=result.strategy_name,
                symbol=result.symbol,
                start_date=result.start_date,
                end_date=result.end_date,
                initial_capital=result.initial_capital,
                final_value=result.final_value or 0.0,
                total_return=result.total_return or 0.0,
                total_return_pct=result.total_return or 0.0,
                sharpe_ratio=result.sharpe_ratio,
                max_drawdown=result.max_drawdown,
                total_trades=result.total_trades,
                winning_trades=result.winning_trades,
                losing_trades=result.losing_trades,
                win_rate=result.win_rate,
                avg_win=result_data.get("performance", {}).get("avg_win"),
                avg_loss=result_data.get("performance", {}).get("avg_loss"),
                avg_annual_return=result_data.get("performance", {}).get(
                    "avg_annual_return"
                ),
                vwr=result_data.get("performance", {}).get("vwr"),
                calmar_ratio=result_data.get("performance", {}).get("calmar_ratio"),
                sqn=result_data.get("performance", {}).get("sqn"),
                created_at=result.created_at.isoformat(),
            )
            comparison_items.append(item)

        returns = [item.total_return for item in comparison_items]
        sharpe_ratios = [
            item.sharpe_ratio
            for item in comparison_items
            if item.sharpe_ratio is not None
        ]
        drawdowns = [
            item.max_drawdown
            for item in comparison_items
            if item.max_drawdown is not None
        ]

        summary = {
            "count": len(comparison_items),
            "strategies": list(set(item.strategy_name for item in comparison_items)),
            "symbols": list(set(item.symbol for item in comparison_items)),
            "return_stats": {
                "best": max(returns),
                "worst": min(returns),
                "average": sum(returns) / len(returns),
                "range": max(returns) - min(returns),
            },
        }
        if sharpe_ratios:
            summary["sharpe_stats"] = {
                "best": max(sharpe_ratios),
                "worst": min(sharpe_ratios),
                "average": sum(sharpe_ratios) / len(sharpe_ratios),
            }

        if drawdowns:
            summary["drawdown_stats"] = {
                "best": max(drawdowns),  # Less negative is better
                "worst": min(drawdowns),
                "average": sum(drawdowns) / len(drawdowns),
            }

        best_backtest = max(comparison_items, key=lambda x: x.total_return_pct)
        worst_backtest = min(comparison_items, key=lambda x: x.total_return_pct)

        summary["best_performing"] = {
            "backtest_id": best_backtest.backtest_id,
            "strategy_name": best_backtest.strategy_name,
            "total_return": best_backtest.total_return,
            "total_return_pct": best_backtest.total_return_pct,
        }

        summary["worst_performing"] = {
            "backtest_id": worst_backtest.backtest_id,
            "strategy_name": worst_backtest.strategy_name,
            "total_return": worst_backtest.total_return,
            "total_return_pct": worst_backtest.total_return_pct,
        }

        comparison_id = (
            f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(backtest_ids)}"
        )

        logger.info(
            f"Created comparison {comparison_id} for {len(backtest_ids)} backtests"
        )

        return BacktestComparison(
            comparison_id=comparison_id,
            backtests=comparison_items,
            summary=summary,
            created_at=datetime.now().isoformat(),
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error comparing backtests: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
