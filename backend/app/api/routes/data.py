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
    Fetch stock market data with caching support

    Supports three types of stock data:
    - **daily**: Daily OHLCV data with basic indicators
    - **minute**: Intraday minute-level data (1min, 5min, 15min, 30min, 60min)
    - **financial**: Financial statement data and ratios

    **Parameters:**
    - **data_type**: Type of data to fetch (daily/minute/financial)
    - **symbol**: Stock symbol in format like "000001.SZ" or "600000.SS"
    - **start_date**: Start date in YYYY-MM-DD format
    - **end_date**: End date in YYYY-MM-DD format
    - **freq**: Frequency for minute data (only required when data_type='minute')
    - **use_cache**: Whether to use cached data if available (default: true)

    **Returns:**
    - **data**: List of data records with OHLCV and other fields
    - **count**: Total number of records returned
    - **columns**: List of available column names

    **Example:**
    ```json
    {
        "data_type": "daily",
        "symbol": "000001.SZ",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "use_cache": true
    }
    ```
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

    Provides access to key macroeconomic indicators from official sources:
    - **gdp**: Gross Domestic Product data
    - **cpi**: Consumer Price Index (inflation indicator)
    - **ppi**: Producer Price Index (wholesale inflation)
    - **m2**: Money Supply M2 (monetary policy indicator)
    - **interest_rate**: SHIBOR interest rates (market rates)

    **Parameters:**
    - **data_type**: Always "macro" for this endpoint
    - **indicator**: Specific macro indicator to fetch (gdp/cpi/ppi/m2/interest_rate)
    - **start_date**: Start date in YYYY-MM-DD format
    - **end_date**: End date in YYYY-MM-DD format
    - **use_cache**: Whether to use cached data if available (default: true)

    **Returns:**
    - **data**: List of macro data records with timestamp and values
    - **count**: Total number of records returned
    - **columns**: List of available column names

    **Example:**
    ```json
    {
        "data_type": "macro",
        "indicator": "cpi",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "use_cache": true
    }
    ```
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
    Fetch industry classification and concept sector data

    Provides access to market classification data:
    - **industry**: Industry classification data (traditional sectors like finance, technology, etc.)
    - **concept**: Concept sector data (thematic sectors like AI, new energy, etc.)

    This endpoint returns static reference data that doesn't require time range parameters.

    **Parameters:**
    - **data_type**: Type of classification data (industry/concept)
    - **use_cache**: Whether to use cached data if available (default: true)

    **Returns:**
    - **data**: List of classification records with codes, names, and descriptions
    - **count**: Total number of records returned
    - **columns**: List of available column names

    **Example:**
    ```json
    {
        "data_type": "industry",
        "use_cache": true
    }
    ```

    **Note:** This endpoint returns reference data and doesn't require start_date/end_date parameters.
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
