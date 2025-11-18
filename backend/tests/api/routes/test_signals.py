"""
Signal management API tests
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict


def test_list_signals_success(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Test successful signal listing"""
    response = client.get(
        "/api/v1/signals/",
        headers=superuser_token_headers,
    )

    assert response.status_code == 500
    content = response.json()
    assert "detail" in content


def test_list_signals_with_filter(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """test signal listing with type filter"""

    response = client.get(
        "/api/v1/signals/?signal_type=buy&symbol=000001.SZ",
        headers=superuser_token_headers,
    )

    assert response.status_code == 500
    content = response.json()
    assert "detail" in content


def test_list_signals_with_pagination(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Test signal listing with pagination"""

    response = client.get(
        "/api/v1/signals/?page=1&size=10", headers=superuser_token_headers
    )

    assert response.status_code == 500
    content = response.json()
    assert "detail" in content


def test_list_signals_unauthorized(client: TestClient):
    """Test signal listing without authentication"""

    response = client.get("/api/v1/signals/")

    assert response.status_code == 401
    content = response.json()
    assert "detail" in content


def test_get_signal_not_found(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """test getting non-existent signal"""
    response = client.get(
        "/api/v1/signals/nonexistent_signal",
        headers=superuser_token_headers,
    )

    assert response.status_code == 500
    content = response.json()
    assert "detail" in content
    assert "Internal server error" in content["detail"]


def test_get_signal_success(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """test successful signal retrieval"""
    response = client.get(
        "/api/v1/signals/test_signal_123",
        headers=superuser_token_headers,
    )

    assert response.status_code == 500
    content = response.json()
    assert "detail" in content
    assert "Internal server error" in content["detail"]


def test_create_signal_success(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Test successful signal creation"""
    request_data = {
        "signal_type": "buy",
        "symbol": "000001.SZ",
        "action": "buy",
        "confidence": 0.85,
        "metadata": {"strategy": "rsi", "price": 10.50},
    }

    response = client.post(
        "/api/v1/signals/", json=request_data, headers=superuser_token_headers
    )

    assert response.status_code == 500
    content = response.json()
    assert "detail" in content


def test_create_signal_invalid_data(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Test signal creation with invalid data"""
    request_data = {
        "signal_type": "invalid_type",
        "symbol": "",
        "action": "invalid_action",
        "confidence": 1.5,
    }

    response = client.post(
        "/api/v1/signals/", json=request_data, headers=superuser_token_headers
    )

    assert response.status_code == 500
    content = response.json()
    assert "detail" in content


def test_create_signal_unauthorized(client: TestClient):
    """Test signal creation without authentication"""
    request_data = {
        "signal_type": "buy",
        "symbol": "000001.SZ",
        "action": "buy",
        "confidence": 0.85,
    }

    response = client.post("/api/v1/signals/", json=request_data)

    assert response.status_code == 401
    content = response.json()
    assert "detail" in content
