from fastapi import APIRouter

from app.api.routes import (
    items,
    login,
    private,
    users,
    utils,
    strategies,
    data,
    factors,
    signals,
    backtests,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(strategies.router)
api_router.include_router(data.router)
api_router.include_router(factors.router)
api_router.include_router(signals.router)
api_router.include_router(backtests.router)

if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
