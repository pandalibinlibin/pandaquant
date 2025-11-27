"""
Signal management API routes
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/signals", tags=["signals"])

from typing import Any, List, Dict, Optional
from app.api.deps import CurrentUser, SessionDep
from pydantic import BaseModel, Field
from typing import Union
from enum import Enum

from app.domains.signals.services import signal_push_service
from app.core.logging import get_logger
from datetime import datetime

logger = get_logger(__name__)


class SignalTypeRequest(BaseModel):
    """Signal type filter request model"""

    signal_type: Optional[str] = Field(None, description="Filter by signal type")


class SignalInfo(BaseModel):
    """Signal information response model"""

    id: str = Field(..., description="Signal ID")
    symbol: str = Field(..., description="Trading symbol")
    action: str = Field(..., description="Signal action (buy/sell/hold)")
    confidence: float = Field(..., description="Signal confidence score")
    strategy_name: Optional[str] = Field(None, description="Strategy name")
    timestamp: str = Field(..., description="Signal timestamp")
    metadata: Dict[str, Any] = Field(..., description="Additional signal metadata")


class SignalListResponse(BaseModel):
    """Signal list response model"""

    signal: List[SignalInfo] = Field(..., description="List of signals")
    total: int = Field(..., description="Total number of signals")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")


@router.get("/", response_model=SignalListResponse)
async def list_signals(
    symbol: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user: CurrentUser = None,
) -> SignalListResponse:
    """
    List all signals with optional filtering

    Args:
        symbol: Filter by trading symbol
        page: Page number for pagination
        size: Page size for pagination
        current_user: Current authenticated user

    Returns:
        Paginated list of signals
    """

    try:
        signals = signal_push_service.list_signals(
            symbol=symbol,
            page=page,
            size=size,
        )

        signal_list = []
        for signal in signals.get("data", []):
            signal_info = SignalInfo(
                id=signal.get("id", ""),
                symbol=signal.get("symbol", ""),
                action=signal.get("action", ""),
                confidence=signal.get("confidence", 0.0),
                strategy_name=signal.get("strategy_name"),
                timestamp=signal.get("timestamp", ""),
                metadata=signal.get("metadata", {}),
            )
            signal_list.append(signal_info)

        response = SignalListResponse(
            signal=signal_list,
            total=signals.get("total", 0),
            page=page,
            size=size,
        )

        logger.info(f"Listed {len(signal_list)} signals")

        return response

    except Exception as e:
        logger.error(f"Error listing signals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{signal_id}", response_model=SignalInfo)
async def get_signal(
    signal_id: str,
    current_user: CurrentUser = None,
) -> SignalInfo:
    """
    Get specific signal by ID

    Args:
        signal_id: Signal ID
        current_user: Current authenticated user

    Returns:
        Signal information

    Raises:
        HTTPException: If signal not found
    """
    try:
        signal = signal_push_service.get_signal(signal_id)
        if not signal:
            raise HTTPException(
                status_code=404, detail=f"Signal '{signal_id}' not found"
            )

        response = SignalInfo(
            id=signal.get("id", ""),
            symbol=signal.get("symbol", ""),
            action=signal.get("action", ""),
            confidence=signal.get("confidence", 0.0),
            strategy_name=signal.get("strategy_name"),
            timestamp=signal.get("timestamp", ""),
            metadata=signal.get("metadata", {}),
        )

        logger.info(f"Retrieved signal {signal_id}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting signal {signal_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


class SignalCreateRequest(BaseModel):
    """Signal creation request model"""

    symbol: str = Field(..., description="Trading symbol")
    action: str = Field(..., description="Signal action (buy/sell/hold)")
    confidence: float = Field(..., description="Signal confidence score (0-1)")
    strategy_name: str = Field(..., description="Strategy name")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional signal metadata"
    )


@router.post("/", response_model=SignalInfo, status_code=201)
async def create_signal(
    request: SignalCreateRequest,
    current_user: CurrentUser = None,
) -> SignalInfo:
    """
    Create a new signal

    Args:
        request: Signal creation request
        current_user: Current authenticated user

    Returns:
        Created signal information

    Raises:
        HTTPException: If signal creation fails
    """
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        signal_data = {
            "symbol": request.symbol,
            "action": request.action,
            "confidence": request.confidence,
            "strategy_name": request.strategy_name,
            "metadata": request.metadata or {},
            "created_by": str(current_user.id) if current_user else None,
        }

        created_signal = signal_push_service.create_signal(signal_data)
        if not created_signal:
            raise HTTPException(status_code=500, detail="Failed to create signal")

        response = SignalInfo(
            id=created_signal.get("id", ""),
            symbol=created_signal.get("symbol", ""),
            action=created_signal.get("action", ""),
            confidence=created_signal.get("confidence", 0.0),
            strategy_name=created_signal.get("strategy_name"),
            timestamp=created_signal.get("timestamp", ""),
            metadata=created_signal.get("metadata", {}),
        )

        logger.info(f"Created signal: {response.id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating signal: {e}")
        raise HTTPException(status_code=500, detail=f"Signal creation failed: {str(e)}")
