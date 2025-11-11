"""
Test cases for data management API routes
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
import pandas as pd


def test_fetch_stock_data_daily(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test fetching daily stock data
    """
    mock_df = pd.DataFrame(
        {
            "timestamp": ["2022-01-01", "2022-01-02"],
            "open": [10.0, 11.0],
            "close": [10.5, 11.5],
            "high": [10.8, 11.8],
            "low": [10.2, 11.2],
            "volume": [1000, 1100],
        }
    )

    with patch(
        "app.api.routes.data.data_service.fetch_data", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_df

        response = client.post(
            "/api/v1/data/stock",
            headers=superuser_token_headers,
            json={
                "data_type": "daily",
                "symbol": "000001.SZ",
                "start_date": "2022-01-01",
                "end_date": "2022-01-02",
                "use_cache": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["data"]) == 2
        assert "timestamp" in data["columns"]


def test_fetch_macro_data(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test fetching macro economic data
    """
    mock_df = pd.DataFrame(
        {
            "timestamp": ["2022-01-01", "2022-02-01"],
            "value": [100.5, 101.2],
        }
    )

    with patch(
        "app.api.routes.data.data_service.fetch_data", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_df

        response = client.post(
            "/api/v1/data/macro",
            headers=superuser_token_headers,
            json={
                "data_type": "macro",
                "indicator": "cpi",
                "start_date": "2022-01-01",
                "end_date": "2022-01-02",
                "use_cache": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["data"]) == 2


def test_fetch_industry_concept_data(
    client: AsyncClient, superuser_token_headers: dict[str, str]
) -> None:
    """
    Test fetching industry or concept data
    """
    mock_df = pd.DataFrame(
        {
            "code": ["001", "002"],
            "name": ["Industry1", "Industry2"],
        }
    )

    with patch(
        "app.api.routes.data.data_service.fetch_data", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_df

        response = client.post(
            "/api/v1/data/industry-concept",
            headers=superuser_token_headers,
            json={
                "data_type": "industry",
                "use_cache": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["data"]) == 2
