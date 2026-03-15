from __future__ import annotations

import pytest

from tests.helpers.api_client import get_json
from tests.helpers.databricks_client import run_sql

pytestmark = pytest.mark.integration


def _health_or_skip(api_base_url: str) -> dict:
    status, payload = get_json(api_base_url, "/health")
    assert status == 200, f"/health returned {status}"
    if not payload.get("database_connected"):
        pytest.skip("Database not connected according to /health; skipping SQL-backed endpoint checks.")
    return payload


def test_centers_endpoint_matches_sql_count(
    api_base_url: str,
    workspace_client,
    warehouse_id: str,
    catalog: str,
    schema: str,
) -> None:
    _health_or_skip(api_base_url)
    status, payload = get_json(api_base_url, "/centers")
    assert status == 200
    assert isinstance(payload, list)

    sql_rows = run_sql(workspace_client, warehouse_id, f"SELECT COUNT(*) AS row_count FROM {catalog}.{schema}.centers")
    expected = int(sql_rows[0]["row_count"]) if sql_rows else 0
    assert len(payload) == expected


def test_lanes_endpoint_matches_sql_count(
    api_base_url: str,
    workspace_client,
    warehouse_id: str,
    catalog: str,
    schema: str,
) -> None:
    _health_or_skip(api_base_url)
    status, payload = get_json(api_base_url, "/lanes")
    assert status == 200
    assert isinstance(payload, list)
    assert payload, "Expected non-empty lanes payload"

    sql_rows = run_sql(workspace_client, warehouse_id, f"SELECT COUNT(*) AS row_count FROM {catalog}.{schema}.lanes")
    expected = int(sql_rows[0]["row_count"]) if sql_rows else 0
    assert len(payload) == expected


def test_incidents_endpoint_supports_lane_filter(
    api_base_url: str,
    workspace_client,
    warehouse_id: str,
    catalog: str,
    schema: str,
) -> None:
    _health_or_skip(api_base_url)
    lane_rows = run_sql(
        workspace_client,
        warehouse_id,
        f"""
        SELECT laneId, COUNT(*) AS incident_count
        FROM {catalog}.{schema}.incidents
        GROUP BY laneId
        ORDER BY incident_count DESC
        LIMIT 1
        """,
    )
    assert lane_rows, "Expected at least one incident lane in SQL"
    lane_id = lane_rows[0]["laneId"]

    status, payload = get_json(api_base_url, f"/incidents?laneId={lane_id}")
    assert status == 200
    assert isinstance(payload, list)
    assert payload, f"Expected incidents for lane {lane_id}"
    assert all(item.get("laneId") == lane_id for item in payload)


def test_reroute_suggestions_endpoint_returns_data_for_incident_lane(
    api_base_url: str,
    workspace_client,
    warehouse_id: str,
    catalog: str,
    schema: str,
) -> None:
    _health_or_skip(api_base_url)
    lane_rows = run_sql(
        workspace_client,
        warehouse_id,
        f"""
        SELECT i.laneId
        FROM {catalog}.{schema}.incidents i
        INNER JOIN {catalog}.{schema}.reroute_solutions r
          ON i.laneId = r.laneId
        WHERE i.active = true
        LIMIT 1
        """,
    )
    assert lane_rows, "Expected at least one active incident lane with reroutes in SQL"
    lane_id = lane_rows[0]["laneId"]

    status, payload = get_json(api_base_url, f"/reroute-suggestions?laneId={lane_id}")
    assert status == 200
    assert isinstance(payload, list)
    assert payload, f"Expected reroute suggestions for lane {lane_id}"
