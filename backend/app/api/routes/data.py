"""
Data management API routes
"""

from fastapi import APIRouter
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field
from app.api.deps import CurrentUser, SessionDep
from app.domains.data.services import DataService
import pandas as pd

router = APIRouter(prefix="/data", tags=["data"])
data_service = DataService()


class StockDataRequest(BaseModel):
    """Stock data request model (for daily, minute, financial)"""

    data_type: str = Field(..., description="Data type: daily, minute, financial")
    symbol: str = Field(..., description="Stock symbol (e.g., 000001.SZ)")
    start_date: str = Field(..., description="Start date (e.g., 2022-01-01)")
    end_date: str = Field(..., description="End date (e.g., 2022-12-31)")
    use_cache: bool = Field(default=True, description="Use cached data if available")
    freq: Optional[str] = Field(
        default=None,
        description="Frequency for minute data (e.g., 1min, 5min, 15min, 30min, 60min). Only required when data_type='minute'",
    )


class MacroDataRequest(BaseModel):
    """Macro data request model"""

    data_type: str = Field(default="macro", description="Data type: macro")
    indicator: str = Field(
        ..., description="Macro indicator: gdp, cpi, ppi, m2, interest_rate"
    )
    start_date: str = Field(..., description="Start date (e.g., 2022-01-01)")
    end_date: str = Field(..., description="End date (e.g., 2022-12-31)")
    use_cache: bool = Field(default=True, description="Use cached data if available")


class IndustryConceptDataRequest(BaseModel):
    """Industry/Concept data request model"""

    data_type: str = Field(..., description="Data type: industry, concept")
    use_cache: bool = Field(default=True, description="Use cached data if available")


class DataResponse(BaseModel):
    """Data response model"""

    data: List[Dict[str, Any]]
    count: int
    columns: List[str]


@router.post("/stock", response_model=DataResponse)
async def fetch_stock_data(
    request: StockDataRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> DataResponse:
    """
    Fetch stock data (daily, minute, financial) with caching support
    """
    kwargs = {
        "data_type": request.data_type,
        "symbol": request.symbol,
        "start_date": request.start_date,
        "end_date": request.end_date,
        "use_cache": request.use_cache,
    }

    if request.data_type == "minute" and request.freq:
        kwargs["freq"] = request.freq

    df = await data_service.fetch_data(**kwargs)

    data = df.to_dict("records") if not df.empty else []
    columns = df.columns.tolist() if not df.empty else []

    return DataResponse(
        data=data,
        count=len(data),
        columns=columns,
    )


@router.post("/macro", response_model=DataResponse)
async def fetch_macro_data(
    request: MacroDataRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> DataResponse:
    """
    Fetch macro economic data with caching support
    """
    df = await data_service.fetch_data(
        data_type=request.data_type,
        symbol=request.indicator,
        start_date=request.start_date,
        end_date=request.end_date,
        use_cache=request.use_cache,
    )

    data = df.to_dict("records") if not df.empty else []
    columns = df.columns.tolist() if not df.empty else []

    return DataResponse(
        data=data,
        count=len(data),
        columns=columns,
    )


@router.post("/industry-concept", response_model=DataResponse)
async def fetch_industry_concept_data(
    request: IndustryConceptDataRequest, current_user: CurrentUser, session: SessionDep
) -> DataResponse:
    """
    Fetch industry or concept data
    """
    df = await data_service.fetch_data(
        data_type=request.data_type,
        symbol="",
        start_date="",
        end_date="",
        use_cache=request.use_cache,
    )

    data = df.to_dict("records") if not df.empty else []
    columns = df.columns.tolist() if not df.empty else []

    return DataResponse(
        data=data,
        count=len(data),
        columns=columns,
    )
