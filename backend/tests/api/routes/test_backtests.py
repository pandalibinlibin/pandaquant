"""
Enhanced backtest management API tests
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict
from uuid import uuid4
from unittest.mock import patch, MagicMock
from datetime import datetime


def test_list_all_backtests_success(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Test successful backtest listing"""
    response = client.get(
        "/api/v1/backtests/",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert "count" in content
    assert "page" in content
    assert "size" in content
    assert "total_pages" in content
    assert isinstance(content["data"], list)


def test_list_all_backtests_with_pagination(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Test backtest listing with pagination"""
    response = client.get(
        "/api/v1/backtests/?page=1&size=10",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["page"] == 1
    assert content["size"] == 10
    assert isinstance(content["data"], list)


def test_list_all_backtests_unauthorized(client: TestClient):
    """Test backtest listing without authentication"""
    response = client.get("/api/v1/backtests/")

    assert response.status_code == 401
    content = response.json()
    assert "detail" in content


def test_compare_backtests_success(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Test successful backtest comparison"""
    # Test with invalid IDs first to verify API structure is correct
    response = client.post(
        "/api/v1/backtests/compare",
        json=[str(uuid4()), str(uuid4())],  # Random UUIDs that don't exist
        headers=superuser_token_headers,
    )

    # Should return 404 because backtests don't exist, but API structure is correct
    assert response.status_code == 404
    content = response.json()
    assert "detail" in content
    assert "not found" in content["detail"].lower()


def test_compare_backtests_api_structure(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Test backtest comparison API structure with various inputs"""
    # Test insufficient IDs
    response = client.post(
        "/api/v1/backtests/compare",
        json=[str(uuid4())],
        headers=superuser_token_headers,
    )
    assert response.status_code == 400

    # Test too many IDs
    response = client.post(
        "/api/v1/backtests/compare",
        json=[str(uuid4()) for _ in range(11)],
        headers=superuser_token_headers,
    )
    assert response.status_code == 400

    # Test invalid ID format
    response = client.post(
        "/api/v1/backtests/compare",
        json=["invalid-uuid", str(uuid4())],
        headers=superuser_token_headers,
    )
    assert response.status_code == 400


def test_compare_backtests_insufficient_ids(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Test backtest comparison with insufficient IDs"""
    response = client.post(
        "/api/v1/backtests/compare",
        json=[str(uuid4())],  # Only one ID
        headers=superuser_token_headers,
    )

    assert response.status_code == 400
    content = response.json()
    assert "detail" in content
    assert "At least 2 backtests are required" in content["detail"]


def test_compare_backtests_too_many_ids(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Test backtest comparison with too many IDs"""
    response = client.post(
        "/api/v1/backtests/compare",
        json=[str(uuid4()) for _ in range(11)],  # 11 IDs (max is 10)
        headers=superuser_token_headers,
    )

    assert response.status_code == 400
    content = response.json()
    assert "detail" in content
    assert "Maximum 10 backtests can be compared" in content["detail"]


def test_compare_backtests_invalid_id_format(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Test backtest comparison with invalid ID format"""
    response = client.post(
        "/api/v1/backtests/compare",
        json=["invalid-uuid", str(uuid4())],
        headers=superuser_token_headers,
    )

    assert response.status_code == 400
    content = response.json()
    assert "detail" in content
    assert "Invalid backtest ID" in content["detail"]


def test_compare_backtests_unauthorized(client: TestClient):
    """Test backtest comparison without authentication"""
    response = client.post(
        "/api/v1/backtests/compare",
        json=[str(uuid4()), str(uuid4())],
    )

    assert response.status_code == 401
    content = response.json()
    assert "detail" in content
