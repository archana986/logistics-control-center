from __future__ import annotations

import pytest

from tests.helpers.databricks_client import run_sql

pytestmark = pytest.mark.integration


def test_helper_views_exist(workspace_client, warehouse_id: str, catalog: str, schema: str) -> None:
    expected_views = {
        "api_shipments",
        "api_incidents",
        "api_capacity_lanes",
        "api_lane_health",
        "api_customer_rollup",
    }
    rows = run_sql(workspace_client, warehouse_id, f"SHOW VIEWS IN {catalog}.{schema}")
    view_names = {row.get("viewName") for row in rows}
    missing = sorted(expected_views - view_names)
    assert not missing, f"Missing helper views: {missing}"


def test_metric_views_exist(workspace_client, warehouse_id: str, catalog: str, schema: str) -> None:
    expected_metric_views = {
        "network_metrics",
        "shipment_metrics",
        "incident_metrics",
        "capacity_metrics",
    }
    rows = run_sql(workspace_client, warehouse_id, f"SHOW TABLES IN {catalog}.{schema}")
    table_names = {row.get("tableName") for row in rows}
    missing = sorted(expected_metric_views - table_names)
    assert not missing, f"Missing metric views: {missing}"


def test_helper_views_are_queryable(workspace_client, warehouse_id: str, catalog: str, schema: str) -> None:
    for view_name in ("api_shipments", "api_incidents", "api_capacity_lanes", "api_lane_health"):
        rows = run_sql(
            workspace_client,
            warehouse_id,
            f"SELECT COUNT(*) AS row_count FROM {catalog}.{schema}.{view_name}",
        )
        count = int(rows[0]["row_count"]) if rows else 0
        assert count > 0, f"Expected rows in helper view {catalog}.{schema}.{view_name}"


def test_metric_views_are_queryable(workspace_client, warehouse_id: str, catalog: str, schema: str) -> None:
    queries = [
        f"SELECT `Avg Delay Minutes` FROM {catalog}.{schema}.network_metrics LIMIT 1",
        f"SELECT `Total Packages` FROM {catalog}.{schema}.shipment_metrics LIMIT 1",
        f"SELECT `Incident Count` FROM {catalog}.{schema}.incident_metrics LIMIT 1",
        f"SELECT `Avg Utilization Pct` FROM {catalog}.{schema}.capacity_metrics LIMIT 1",
    ]
    for query in queries:
        rows = run_sql(workspace_client, warehouse_id, query)
        assert rows is not None


def test_reroute_has_active_lane_coverage(workspace_client, warehouse_id: str, catalog: str, schema: str) -> None:
    rows = run_sql(
        workspace_client,
        warehouse_id,
        f"""
        SELECT COUNT(DISTINCT i.laneId) AS incident_lanes_with_reroutes
        FROM {catalog}.{schema}.incidents i
        INNER JOIN {catalog}.{schema}.reroute_solutions r
          ON i.laneId = r.laneId
        WHERE i.active = true
        """,
    )
    covered = int(rows[0]["incident_lanes_with_reroutes"]) if rows else 0
    assert covered > 0, "Expected at least one active incident lane with reroute coverage"
