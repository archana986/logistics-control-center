"""Resolve or create a Knowledge Assistant endpoint for the app setup flow.

Current Databricks runtimes do not consistently expose typed KA creation APIs
in the Python SDK. This task uses a best-effort strategy:
1) Resolve an existing KA endpoint (preferred explicit endpoint first)
2) Attempt creation only if a compatible Agent Bricks API is available
3) Fail with explicit remediation if KA creation APIs are unavailable
"""

from __future__ import annotations

import os
from typing import Any, Iterable, Optional

from databricks.sdk import WorkspaceClient

PREFERRED_ENDPOINT = os.getenv("DATABRICKS_KA_ENDPOINT", "ka-3c254141-endpoint").strip()
KA_NAME = os.getenv("DATABRICKS_KA_NAME", "logistics-control-center-knowledge-assistant").strip()
CATALOG = os.getenv("DATABRICKS_CATALOG", "demos").strip()
SCHEMA = os.getenv("DATABRICKS_SCHEMA", "logistics_control_center").strip()
DOCS_VOLUME = os.getenv("DATABRICKS_KA_DOCS_VOLUME", "documents").strip()
DOCS_VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{DOCS_VOLUME}"


def _non_empty_names(names: Iterable[Optional[str]]) -> list[str]:
    return [name for name in names if isinstance(name, str) and name.strip()]


def _existing_ka_endpoint(endpoints: list[str], preferred: str) -> Optional[str]:
    if preferred and preferred in endpoints:
        return preferred
    ka_like = [name for name in endpoints if name.startswith("ka-") or "knowledge" in name.lower()]
    return sorted(ka_like)[0] if ka_like else None


def _maybe_create_ka(client: WorkspaceClient, ka_name: str, volume_path: str) -> Optional[str]:
    """Best-effort KA create path for runtimes exposing Agent Bricks KA APIs."""
    api = getattr(client, "agent_bricks", None)
    if api is None:
        return None

    # Newer runtimes may expose these methods; this code path is forward-compatible.
    has_find = hasattr(api, "find_ka_by_name")
    has_create_or_update = hasattr(api, "create_or_update_ka")
    if not (has_find and has_create_or_update):
        return None

    found = api.find_ka_by_name(name=ka_name)
    if isinstance(found, dict) and found.get("found") and found.get("endpoint_name"):
        return str(found["endpoint_name"])
    if getattr(found, "found", False) and getattr(found, "endpoint_name", None):
        return str(found.endpoint_name)

    created = api.create_or_update_ka(
        name=ka_name,
        volume_path=volume_path,
        description="Logistics operations knowledge assistant for incident, SOP, and SLA docs.",
        instructions=(
            "You are a logistics operations assistant. Answer from indexed documents, "
            "cite relevant sources, and highlight actionable incident-response guidance."
        ),
    )
    endpoint_name = getattr(created, "endpoint_name", None)
    if endpoint_name:
        return str(endpoint_name)

    if isinstance(created, dict):
        endpoint_name = created.get("endpoint_name")
        if endpoint_name:
            return str(endpoint_name)
        tile_id = created.get("tile_id") or created.get("id")
        if tile_id:
            return f"ka-{tile_id}-endpoint"

    tile_id = getattr(created, "tile_id", None) or getattr(created, "id", None)
    if tile_id:
        return f"ka-{tile_id}-endpoint"

    return None


def _ready_state(client: WorkspaceClient, endpoint_name: str) -> Optional[str]:
    try:
        endpoint = client.serving_endpoints.get(endpoint_name)
    except Exception:
        return None
    state = getattr(endpoint, "state", None)
    return str(getattr(state, "ready", "")) if state else None


client = WorkspaceClient()
endpoint_names = _non_empty_names(getattr(ep, "name", None) for ep in client.serving_endpoints.list())

selected = _existing_ka_endpoint(endpoint_names, PREFERRED_ENDPOINT)
if not selected:
    selected = _maybe_create_ka(client, KA_NAME, DOCS_VOLUME_PATH)

if not selected:
    raise RuntimeError(
        "Knowledge Assistant endpoint is not available and this runtime does not expose a KA create API.\n"
        "Create the KA manually, then deploy with a bundle variable override:\n"
        "  databricks bundle deploy --target dev --var \"ka_endpoint=<ka-endpoint-name>\"\n"
        "Also ensure app runtime env sets DATABRICKS_KA_ENDPOINT."
    )

ready = _ready_state(client, selected)
print(f"Resolved Knowledge Assistant endpoint: {selected}")
print(f"Knowledge Assistant endpoint ready state: {ready or 'unknown'}")
print(f"DATABRICKS_KA_ENDPOINT={selected}")
