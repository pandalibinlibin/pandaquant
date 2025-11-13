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


def test_get_backtest_result_success(
    client: TestClient, superuser_token_headers: dict[str, str]
):
    """Test successful backtest result retrieval"""

    from app.models import BacktestResult
    from uuid import uuid4
    import json
    from unittest.mock import MagicMock

    backtest_result = BacktestResult(
        id=uuid4(),
        strategy_name="test_strategy",
        symbol="000001.SZ",
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=1000000.0,
        final_value=1050000.0,
        total_return=0.05,
        max_drawdown=-0.03,
        sharpe_ratio=1.2,
        total_trades=25,
        winning_trades=15,
        losing_trades=10,
        win_rate=0.6,
        result_data=json.dumps(
            {"performance": {"total_return_pct": 0.05, "calmar_ratio": 1.2}}
        ),
        created_by="test@example.com",
    )

    mock_session = MagicMock()
    mock_session.exec.return_value.first.return_value = backtest_result

    from app.api.deps import get_db
    from app.main import app

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get(
            f"/api/v1/strategies/test_strategy/backtests/{backtest_result.id}",
            headers=superuser_token_headers,
        )

        assert response.status_code == 200
        content = response.json()
        assert content["backtest_id"] == str(backtest_result.id)
        assert content["strategy_name"] == "test_strategy"
        assert content["symbol"] == "000001.SZ"
        assert content["performance"]["total_return"] == 0.05
        assert content["performance"]["calmar_ratio"] == 1.2

    finally:
        app.dependency_overrides.clear()


def test_get_backtest_result_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
):
    """Test backtest result not found"""

    with patch("sqlmodel.Session") as mock_session:
        mock_session.exec.return_value.first.return_value = None

        response = client.get(
            "/api/v1/strategies/test_strategy/backtests/123e4567-e89b-12d3-a456-426614174000",
            headers=superuser_token_headers,
        )

    assert response.status_code == 404
    content = response.json()
    assert "detail" in content
    assert "not found" in content["detail"]


def test_get_backtest_result_invalid_id(
    client: TestClient, superuser_token_headers: dict[str, str]
):
    """Test invalid backtest ID format"""
    response = client.get(
        "/api/v1/strategies/test_strategy/backtests/invalid-uuid",
        headers=superuser_token_headers,
    )

    assert response.status_code == 400
    content = response.json()
    assert "detail" in content
    assert "Invalid backtest ID format" in content["detail"]


def test_get_backtest_history_success(
    client: TestClient, superuser_token_headers: dict[str, str]
):
    """Test successful backtest history retrieval"""
    from app.models import BacktestResult
    from uuid import uuid4
    from datetime import datetime
    from unittest.mock import MagicMock

    backtest_results = [
        BacktestResult(
            id=uuid4(),
            strategy_name="test_strategy",
            symbol="000001.SZ",
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=1000000.0,
            final_value=1050000.0,
            total_return=0.05,
            max_drawdown=-0.03,
            sharpe_ratio=1.2,
            total_trades=25,
            winning_trades=15,
            losing_trades=10,
            win_rate=0.6,
            result_data="{}",
            created_by="test@example.com",
            created_at=datetime.utcnow(),
        )
    ]

    mock_session = MagicMock()
    mock_session.exec.return_value.one.return_value = 1
    mock_session.exec.return_value.all.return_value = backtest_results

    from app.api.deps import get_db
    from app.main import app

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get(
            "/api/v1/strategies/test_strategy/backtests?page=1&size=20",
            headers=superuser_token_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 1
    assert content["page"] == 1
    assert content["size"] == 20
    assert content["total_pages"] == 1
    assert len(content["data"]) == 1
    assert content["data"][0]["strategy_name"] == "test_strategy"


def test_get_backtest_history_pagination(
    client: TestClient, superuser_token_headers: dict[str, str]
):
    """Test backtest history pagination"""
    from unittest.mock import MagicMock

    mock_session = MagicMock()
    mock_session.exec.return_value.one.return_value = 25
    mock_session.exec.return_value.all.return_value = []

    from app.api.deps import get_db
    from app.main import app

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.get(
            "/api/v1/strategies/test_strategy/backtests?page=2&size=10",
            headers=superuser_token_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    content = response.json()
    assert content["count"] == 25
    assert content["page"] == 2
    assert content["size"] == 10
    assert content["total_pages"] == 3


def test_get_backtest_history_invalid_pagination(
    client: TestClient, superuser_token_headers: dict[str, str]
):
    """Test invalid pagination parameters"""
    response = client.get(
        "/api/v1/strategies/test_strategy/backtests?page=0&size=20",
        headers=superuser_token_headers,
    )
    assert response.status_code == 400

    response = client.get(
        "/api/v1/strategies/test_strategy/backtests?page=1&size=0",
        headers=superuser_token_headers,
    )
    assert response.status_code == 400

    response = client.get(
        "/api/v1/strategies/test_strategy/backtests?page=1&size=101",
        headers=superuser_token_headers,
    )
    assert response.status_code == 400


def test_delete_backtest_result_success(
    client: TestClient, superuser_token_headers: dict[str, str]
):
    """Test successful backtest result deletion"""
    from app.models import BacktestResult
    from uuid import uuid4
    from unittest.mock import MagicMock

    backtest_result = BacktestResult(
        id=uuid4(),
        strategy_name="test_strategy",
        symbol="000001.SZ",
        start_date="2023-01-01",
        end_date="2023-12-31",
        initial_capital=1000000.0,
        final_value=1050000.0,
        total_return=0.05,
        max_drawdown=-0.03,
        sharpe_ratio=1.2,
        total_trades=25,
        winning_trades=15,
        losing_trades=10,
        win_rate=0.6,
        result_data="{}",
        created_by="test@example.com",
    )

    mock_session = MagicMock()
    mock_session.exec.return_value.first.return_value = backtest_result

    from app.api.deps import get_db
    from app.main import app

    def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.delete(
            "/api/v1/strategies/test_strategy/backtests/" + str(backtest_result.id),
            headers=superuser_token_headers,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    content = response.json()
    assert "message" in content
    assert "deleted successfully" in content["message"]


def test_delete_backtest_result_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
):
    """Test delete non-existent backtest result"""
    with patch("sqlmodel.Session") as mock_session:
        mock_session.exec.return_value.first.return_value = None

        response = client.delete(
            "/api/v1/strategies/test_strategy/backtests/123e4567-e89b-12d3-a456-426614174000",
            headers=superuser_token_headers,
        )

    assert response.status_code == 404
    content = response.json()
    assert "detail" in content
    assert "not found" in content["detail"]


def test_delete_backtest_result_invalid_id(
    client: TestClient, superuser_token_headers: dict[str, str]
):
    """Test delete with invalid backtest ID format"""

    response = client.delete(
        "/api/v1/strategies/test_strategy/backtests/invalid-uuid",
        headers=superuser_token_headers,
    )

    assert response.status_code == 400
    content = response.json()
    assert "detail" in content
    assert "Invalid backtest ID format" in content["detail"]
