"""
Data API integration tests - End-to-end tests with real data sources
"""

import pytest
import logging

logger = logging.getLogger(__name__)


@pytest.mark.integration
def test_fetch_stock_data_with_real_api(
    client, superuser_token_headers: dict[str, str]
) -> None:
    """Test fetching stock data with real data sources (no mock)"""
    response = client.post(
        "/api/v1/data/stock",
        headers=superuser_token_headers,
        json={
            "data_type": "daily",
            "symbol": "000001.SZ",
            "start_date": "2024-01-01",
            "end_date": "2024-01-10",
            "use_cache": True,
        },
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()

    assert "data" in data, "Response should contain 'data' field"
    assert "count" in data, "Response should contain 'count' field"
    assert "columns" in data, "Response should contain 'columns' field"

    if data["count"] > 0:
        assert len(data["data"]) > 0, "Should have data rows"
        assert "timestamp" in data["columns"], "Should have timestamp column"
        assert "open" in data["columns"], "Should have open column"
        assert "close" in data["columns"], "Should have close column"

        logger.info("Successfully fetched %d rows via API", data["count"])

    else:
        logger.info("No data available - API returned empty result")
