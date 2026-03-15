from __future__ import annotations

import pytest

from tests.helpers.api_client import get_json, post_json

pytestmark = pytest.mark.integration


def test_customer_update_returns_message(api_base_url: str) -> None:
    health_status, health_payload = get_json(api_base_url, "/health")
    assert health_status == 200
    assert isinstance(health_payload, dict)

    payload = {
        "customerName": "techcorp",
        "laneId": "BNA-STL-AIR",
        "strategy": {
            "strategy": "AIR-VIA-ATL",
            "deltaETAminutes": -25,
            "addedCostUSD": 420.0,
            "capacityUsedPct": 61.0,
            "notes": "Test payload",
        },
        "incidentSummary": "Thunderstorm reroute test scenario",
    }

    status, response = post_json(api_base_url, "/generate-customer-update", payload)
    assert status == 200
    assert isinstance(response, dict)
    assert response.get("message")
    assert response.get("source") in {"databricks", "fallback"}

    if health_payload.get("databricks_connected"):
        # In connected environments we expect model-serving output.
        if response.get("source") != "databricks":
            pytest.skip("Databricks connected but model endpoint not ready; fallback returned.")
