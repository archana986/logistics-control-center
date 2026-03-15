from __future__ import annotations

import pytest

from tests.helpers.api_client import get_json

pytestmark = pytest.mark.integration


def test_health_endpoint_is_available(api_base_url: str) -> None:
    status, payload = get_json(api_base_url, "/health")
    assert status == 200
    assert isinstance(payload, dict)
    assert payload.get("status") == "ok"
    assert "databricks_connected" in payload
    assert "database_connected" in payload
    assert "sql_warehouse_id" in payload
