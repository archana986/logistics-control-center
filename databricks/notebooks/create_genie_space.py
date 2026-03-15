"""Create or update the Logistics Control Center Genie space."""

from __future__ import annotations

import json

from databricks.sdk import WorkspaceClient

CATALOG = "demos"
SCHEMA = "logistics_control_center"
DISPLAY_NAME = "Logistics Control Center Metrics"
DESCRIPTION = "Natural language analytics over logistics control center metric views."
try:
    WAREHOUSE_ID = dbutils.widgets.get("warehouse_id")  # type: ignore[name-defined]
except Exception:
    WAREHOUSE_ID = ""

METRIC_VIEWS = [
    f"{CATALOG}.{SCHEMA}.network_metrics",
    f"{CATALOG}.{SCHEMA}.shipment_metrics",
    f"{CATALOG}.{SCHEMA}.incident_metrics",
    f"{CATALOG}.{SCHEMA}.capacity_metrics",
]


def _resolve_warehouse(client: WorkspaceClient, candidate_id: str) -> str:
    if candidate_id:
        return candidate_id
    for wh in client.warehouses.list():
        if wh.id:
            return wh.id
    raise RuntimeError("No SQL warehouse found for Genie space creation.")


def _serialized_space() -> str:
    payload = {
        "version": 2,
        "config": {
            "sample_questions": [
                {"question": ["Which lanes have the highest health risk score?"]},
                {"question": ["Show delayed shipment counts by lane."]},
                {"question": ["What are the active incidents by type?"]},
                {"question": ["Which lanes have the least available capacity?"]},
            ]
        },
        "data_sources": {
            "metric_views": [{"identifier": mv} for mv in sorted(METRIC_VIEWS)]
        },
        "instructions": {
            "text_instructions": [
                {
                    "id": "lcclanehealth001",
                    "content": [
                        "For network risk questions, prioritize network_metrics Avg Lane Health Score and Critical Lane Count.",
                        "For shipment service questions, prioritize shipment_metrics Delayed Shipment Count and In Transit Packages.",
                    ],
                }
            ]
        },
    }
    return json.dumps(payload)


client = WorkspaceClient()
warehouse_id = _resolve_warehouse(client, WAREHOUSE_ID)
serialized = _serialized_space()

existing = None
resp = client.genie.list_spaces()
for space in resp.spaces or []:
    if getattr(space, "title", None) == DISPLAY_NAME:
        existing = space
        break

if existing:
    updated = client.genie.update_space(
        space_id=existing.space_id,
        title=DISPLAY_NAME,
        description=DESCRIPTION,
        warehouse_id=warehouse_id,
        serialized_space=serialized,
    )
    print(f"Updated Genie space: {updated.space_id}")
else:
    created = client.genie.create_space(
        title=DISPLAY_NAME,
        description=DESCRIPTION,
        warehouse_id=warehouse_id,
        serialized_space=serialized,
    )
    print(f"Created Genie space: {created.space_id}")
