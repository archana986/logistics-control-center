from __future__ import annotations

import pytest

from tests.helpers.databricks_client import run_sql

pytestmark = pytest.mark.integration


def test_schema_exists(workspace_client, warehouse_id: str, catalog: str, schema: str) -> None:
    rows = run_sql(
        workspace_client,
        warehouse_id,
        f"""
        SELECT schema_name
        FROM {catalog}.information_schema.schemata
        WHERE schema_name = '{schema}'
        LIMIT 1
        """,
    )
    assert rows, f"Schema {catalog}.{schema} does not exist"


def test_volumes_exist(workspace_client, warehouse_id: str, catalog: str, schema: str) -> None:
    rows = run_sql(workspace_client, warehouse_id, f"SHOW VOLUMES IN {catalog}.{schema}")
    volume_names = {row.get("volume_name") for row in rows}
    assert "raw_data" in volume_names
    assert "documents" in volume_names


def test_serving_tables_exist(workspace_client, warehouse_id: str, catalog: str, schema: str) -> None:
    expected_tables = {
        "centers",
        "customers",
        "lanes",
        "shipments",
        "incidents",
        "customer_interactions",
        "capacity_lanes",
        "capacity_actions",
        "agent_activities",
        "sales_opportunities",
        "reroute_solutions",
    }
    rows = run_sql(workspace_client, warehouse_id, f"SHOW TABLES IN {catalog}.{schema}")
    table_names = {row.get("tableName") for row in rows}
    missing = sorted(expected_tables - table_names)
    assert not missing, f"Missing serving tables: {missing}"


def test_raw_event_tables_exist(workspace_client, warehouse_id: str, catalog: str, schema: str) -> None:
    expected_tables = {
        "raw_sensor_events",
        "raw_shipment_events",
        "raw_incident_events",
        "raw_capacity_events",
    }
    rows = run_sql(workspace_client, warehouse_id, f"SHOW TABLES IN {catalog}.{schema}")
    table_names = {row.get("tableName") for row in rows}
    missing = sorted(expected_tables - table_names)
    assert not missing, f"Missing raw event tables: {missing}"


def test_core_tables_have_data(workspace_client, warehouse_id: str, catalog: str, schema: str) -> None:
    for table in ("centers", "lanes", "shipments", "incidents", "reroute_solutions"):
        rows = run_sql(
            workspace_client,
            warehouse_id,
            f"SELECT COUNT(*) AS row_count FROM {catalog}.{schema}.{table}",
        )
        count = int(rows[0]["row_count"]) if rows else 0
        assert count > 0, f"Expected data in {catalog}.{schema}.{table}, got {count}"
