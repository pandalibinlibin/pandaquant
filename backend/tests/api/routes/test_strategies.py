"""
Tests for strategy API routes
"""

from fastapi.testclient import TestClient
from app.core.config import settings
import pytest
from unittest.mock import AsyncMock, patch


def test_list_strategies(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test listing all strategies"""
    response = client.get(
        f"{settings.API_V1_STR}/strategies/", headers=superuser_token_headers
    )

    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    assert isinstance(content["data"], list)
    assert isinstance(content["count"], int)


def test_get_strategy(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting strategy detail by name"""
    response = client.get(
        f"{settings.API_V1_STR}/strategies/DualMovingAverageStrategy",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    content = response.json()
    assert "name" in content
    assert content["name"] == "DualMovingAverageStrategy"
    assert "description" in content


def test_get_strategy_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test getting non-existent strategy returns 404"""
    response = client.get(
        f"{settings.API_V1_STR}/strategies/NonExistentStrategy",
        headers=superuser_token_headers,
    )

    assert response.status_code == 404
    content = response.json()
    assert "detail" in content
    assert "NonExistentStrategy" in content["detail"]


@pytest.mark.asyncio
async def test_run_backtest(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test running a backtest"""
    from app.api.routes import strategies

    mock_result = {
        "backtest_id": "test-backtest-id-123",
        "strategy_name": "DualMovingAverageStrategy",
        "symbol": "000001.SZ",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "initial_capital": 1000000.0,
        "performance": {
            "total_return": 10000.0,
            "total_return_pct": 1.0,
            "final_value": 1010000.0,
        },
        "status": "completed",
    }

    with patch.object(
        strategies.strategy_service, "run_backtest", new_callable=AsyncMock
    ) as mock_run_backtest:
        mock_run_backtest.return_value = mock_result

        response = client.post(
            f"{settings.API_V1_STR}/strategies/DualMovingAverageStrategy/backtest",
            headers=superuser_token_headers,
            json={
                "symbol": "000001.SZ",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "initial_capital": 1000000.0,
            },
        )

        assert response.status_code == 200
        content = response.json()
        assert "backtest_id" in content
        assert content["strategy_name"] == "DualMovingAverageStrategy"
        assert content["symbol"] == "000001.SZ"
        assert "performance" in content
        assert content["performance"]["total_return"] == 10000.0

        assert mock_run_backtest.called


@pytest.mark.asyncio
async def test_run_backtest_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test running backtest with non-existent strategy returns 404"""
    response = client.post(
        f"{settings.API_V1_STR}/strategies/NonExistentStrategy/backtest",
        headers=superuser_token_headers,
        json={
            "symbol": "000001.SZ",
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "initial_capital": 1000000.0,
        },
    )

    assert response.status_code == 404
    content = response.json()
    assert "detail" in content
    assert "NonExistentStrategy" in content["detail"]
