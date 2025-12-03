"""
Factor management API routes
"""

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/factors", tags=["factors"])

from typing import Any, List, Dict, Optional
from app.api.deps import CurrentUser, SessionDep
from pydantic import BaseModel, Field
from typing import Union
from enum import Enum

from app.domains.factors.services import factor_service
from app.domains.factors.base import Factor, FactorType
from app.domains.factors.base import FactorType
from app.core.logging import get_logger
from datetime import datetime

logger = get_logger(__name__)


class FactorTypeRequest(BaseModel):
    """Factor type filter request model"""

    factor_type: Optional[str] = Field(None, description="Filter by factor type")


class FactorCalculateRequest(BaseModel):
    """Factor calculation request model"""

    factor_name: str = Field(..., description="Name of the factor to calculate")
    data_type: str = Field(
        ...,
        description="Type of data: daily, minute, financial, macro, industry, concept",
    )
    symbol: Optional[str] = Field(None, description="Symbol for stock/fundamental data")
    indicator: Optional[str] = Field(None, description="Indicator for macro data")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    parameters: Optional[Dict[str, Any]] = Field(
        None, description="Additional parameters for factor calculation"
    )


class FactorInfo(BaseModel):
    """Factor information response model"""

    name: str = Field(..., description="Factor name")
    factor_type: str = Field(..., description="Factor type")
    factor_class: str = Field(..., description="Factor class name")
    description: str = Field(..., description="Factor description")
    parameters: Dict[str, Any] = Field(..., description="Factor parameters")
    required_fields: List[str] = Field(..., description="Required data fields")
    status: str = Field(..., description="Factor status")


class FactorCalculationResponse(BaseModel):
    """Factor calculation response model"""

    factor_name: str = Field(..., description="Factor name")
    symbol: str = Field(..., description="Symbol")
    calculation_time: str = Field(..., description="Calculation timestamp")
    data_points: int = Field(..., description="Number of data points calculated")
    result_data: Dict[str, Any] = Field(..., description="Calculation results")


class FactorStatusResponse(BaseModel):
    """Factor status response model"""

    name: str = Field(..., description="Factor name")
    status: str = Field(..., description="Current status")
    last_calculation: Optional[str] = Field(None, description="Last calculation time")
    error_count: int = Field(..., description="Number of errors")
    is_available: bool = Field(..., description="Whether factor is available")


@router.get("/classes", response_model=List[Dict[str, Any]])
async def list_factor_classes(
    current_user: CurrentUser = None,
) -> List[Dict[str, Any]]:
    """
    List all available factor classes (not instances)

    Returns:
        List of factor class metadta including class name, type and module
    """
    try:
        factor_classes = factor_service.list_factor_classes()
        logger.info(f"Listed {len(factor_classes)} factor classes")
        return factor_classes
    except Exception as e:
        logger.error(f"Error listing factor classes: {e}")
        raise


@router.get("/", response_model=List[FactorInfo])
async def list_factors(
    factor_type: Optional[str] = None,
    current_user: CurrentUser = None,
) -> List[FactorInfo]:
    """
    List all available factors with optional type filtering

    Args:
        factor_type: Optional factor type to filter by (technical, fundamental, custom, macro, sentiment)
        current_user: Current authenticated user

    Returns:
        List of factor information objects
    """

    try:
        if factor_type:
            try:
                factor_type_enum = FactorType(factor_type.lower())
                factors = factor_service.get_factors_by_type(factor_type_enum)
            except ValueError:
                logger.warning(f"Invalid factor type: {factor_type}")
                factors = []
        else:
            factor_names = factor_service.list_factors()
            factors = [factor_service.get_factor(name) for name in factor_names]

        factor_infos = []
        for factor in factors:
            if factor:
                factor_info = FactorInfo(
                    name=factor.name,
                    factor_type=factor.factor_type.value,
                    factor_class=factor.factor_class or "Unknown",
                    description=factor.description,
                    parameters=factor.parameters,
                    required_fields=factor.get_required_fields(),
                    status=factor.status.value,
                )
                factor_infos.append(factor_info)

        logger.info(f"Listed {len(factor_infos)} factors")
        return factor_infos

    except Exception as e:
        logger.error(f"Error listing factors: {e}")
        raise


@router.get("/{factor_name}", response_model=FactorInfo)
async def get_factor(
    factor_name: str,
    current_user: CurrentUser = None,
) -> FactorInfo:
    """
    Get detailed information about a specific factor

        Args:
        factor_name: Name of the factor
        current_user: Current authenticated user

    Returns:
        Detailed factor information

    Raises:
        HTTPException: If factor not found
    """
    try:
        factor = factor_service.get_factor(factor_name)
        if not factor:
            raise HTTPException(
                status_code=404, detail=f"Factor '{factor_name}' not found"
            )

        factor_info = FactorInfo(
            name=factor.name,
            factor_type=factor.factor_type.value,
            factor_class=factor.factor_class or "Unknown",
            description=factor.description,
            parameters=factor.parameters,
            required_fields=factor.get_required_fields(),
            status=factor.status.value,
        )

        logger.info(f"Retrieved factor info for: {factor_name}")
        return factor_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting factor {factor_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/calculate", response_model=FactorCalculationResponse)
async def calculate_factor(
    request: FactorCalculateRequest,
    current_user: CurrentUser = None,
) -> FactorCalculationResponse:
    """
    Calculate factor values for specific  data and data range

    Args:
        request: Factor calculation request
        current_user: Current authenticated user

    Returns:
        Factor calculation results

    Raises:
        HTTPException: If factor not found, data not available, or calculation fails
    """
    try:
        factor = factor_service.get_factor(request.factor_name)
        if not factor:
            raise HTTPException(
                status_code=404, detail=f"Factor '{request.factor_name}' not found"
            )

        from app.domains.data.services import data_service

        if request.data_type in ["daily", "minute", "financial"]:
            if not request.symbol:
                raise HTTPException(
                    status_code=400,
                    detail="Symbol is required for daily/minute/financial",
                )
            data = await data_service.fetch_data(
                data_type=request.data_type,
                symbol=request.symbol,
                start_date=request.start_date,
                end_date=request.end_date,
                use_cache=True,
            )
        elif request.data_type == "macro":
            if not request.indicator:
                raise HTTPException(
                    status_code=400, detail="Indicator is required for macro data type"
                )
            data = await data_service.fetch_data(
                data_type=request.data_type,
                symbol=request.indicator,
                start_date=request.start_date,
                end_date=request.end_date,
                use_cache=True,
            )
        elif request.data_type in ["industry", "concept"]:
            data = await data_service.fetch_data(
                data_type=request.data_type,
                symbol="",
                start_date="",
                end_date="",
                use_cache=True,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported data type: {request.data_type}",
            )

        if data.empty:
            data_identifier = request.symbol or request.indicator or "data"
            raise HTTPException(
                status_code=404,
                detail=f"No data found for {data_identifier} in the specified date range",
            )

        result = await factor_service.calculate_factor(
            request.factor_name, data, **(request.parameters or {})
        )

        calculation_time = datetime.now().isoformat()
        result_data = {
            "columns": result.columns.tolist() if not result.empty else [],
            "sample_values": result.head().to_dict() if not result.empty else {},
            "data_points": len(result),
        }
        response = FactorCalculationResponse(
            factor_name=request.factor_name,
            symbol=request.symbol or request.indicator or "unknown",
            calculation_time=calculation_time,
            data_points=len(result),
            result_data=result_data,
        )

        logger.info(
            f"Calculated factor {request.factor_name} for {request.data_type} data"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating factor {request.factor_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Factor calculation failed: {str(e)}"
        )


@router.get("/{factor_name}/status", response_model=FactorStatusResponse)
async def get_factor_status(
    factor_name: str,
    current_user: CurrentUser = None,
) -> FactorStatusResponse:
    """
    Get the current  status and statistics of a specific factor

    Args:
        factor_name: Name of the factor
        current_user: Current authenticated user

    Returns:
        Factor status information

    Raises:
        HTTPException: If factor not found
    """

    try:
        status_info = factor_service.get_factor_status(factor_name)
        if not status_info:
            raise HTTPException(
                status_code=404, detail=f"Factor '{factor_name}' not found"
            )
        response = FactorStatusResponse(**status_info)
        logger.info(f"Retrieved factor status for: {factor_name}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting factor status {factor_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


class FactorRegisterRequest(BaseModel):
    """Factor registration request model"""

    name: str = Field(..., description="Factor name")
    factor_class: str = Field(
        ..., description="Factor class name (e.g., MovingAverageFactor)"
    )
    description: str = Field(..., description="Factor description")
    parameters: Dict[str, Any] = Field(..., description="Factor parameters")


def create_factor_instance(
    factor_class: str, name: str, description: str, parameters: Dict[str, Any]
) -> Factor:
    """Factory method to create factor instances using auto-discovery"""
    factor_modules = {
        "MovingAverageFactor": "app.domains.factors.technical",
        "RSIFactor": "app.domains.factors.technical",
        "MACDFactor": "app.domains.factors.technical",
        "BollingerBandsFactor": "app.domains.factors.technical",
        "KDJFactor": "app.domains.factors.technical",
        "FinancialRatioFactor": "app.domains.factors.fundamental",
    }

    if factor_class not in factor_modules:
        raise ValueError(f"Unsupported factor class: {factor_class}")

    try:
        module = __import__(factor_modules[factor_class], fromlist=[factor_class])
        FactorClass = getattr(module, factor_class)

        return FactorClass(name=name, factor_class=factor_class, **parameters)
    except Exception as e:
        raise ValueError(f"Failed to create {factor_class}: {str(e)}")


@router.post("/register", response_model=FactorInfo)
async def register_factor(
    request: FactorRegisterRequest,
    current_user: CurrentUser = None,
) -> FactorInfo:
    """
    Register a new factor in the system

    Args:
        request: Factor registration request
        current_user: Current authenticated user

    Returns:
        Registered factor information

    Raises:
        HTTPException: If factor already exists or registration fails
    """
    try:
        existing_factor = factor_service.get_factor(request.name)
        if existing_factor:
            raise HTTPException(
                status_code=409, detail=f"Factor '{request.name}' already exists"
            )

        factor = create_factor_instance(
            factor_class=request.factor_class,
            name=request.name,
            description=request.description,
            parameters=request.parameters,
        )

        success = factor_service.register_factor(factor)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to register factor")

        response = FactorInfo(
            name=factor.name,
            factor_type=factor.factor_type,
            factor_class=request.factor_class,
            description=factor.description,
            parameters=factor.parameters,
            required_fields=factor.get_required_fields(),
            status="active",
        )

        logger.info(f"Successfully registered factor: {request.name}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering factor {request.name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Factor registration failed: {str(e)}"
        )


@router.delete("/{factor_name}", status_code=204)
async def unregister_factor(
    factor_name: str,
    current_user: CurrentUser = None,
) -> None:
    """
    Unregister/remvoe a factor from the system

    Args:
        factor_name: Name of the factor to remove
        current_user: Current authenticated user

    Raises:
        HTTPException: If factor not found or deletion fails
    """
    try:
        existing_factor = factor_service.get_factor(factor_name)
        if not existing_factor:
            raise HTTPException(
                status_code=404, detail=f"Factor '{factor_name}' not found"
            )

        success = factor_service.unregister_factor(factor_name)
        if not success:
            raise HTTPException(status_code=500, detail="FAiled to unregister factor")
        logger.info(f"Successfully unregistered factor: {factor_name}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering factor {factor_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Factor unregistration failed: {str(e)}"
        )
