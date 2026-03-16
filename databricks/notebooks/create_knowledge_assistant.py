"""Resolve the Knowledge Assistant serving endpoint for the app.

This runtime does not always include the newer typed SDK module for
Knowledge Assistants, so this task falls back to endpoint discovery and emits
the endpoint name to wire into app config.
"""

from __future__ import annotations

from databricks.sdk import WorkspaceClient

PREFERRED_ENDPOINT = "ka-3c254141-endpoint"

client = WorkspaceClient()

all_endpoints = [ep.name for ep in client.serving_endpoints.list() if ep.name]

selected = None
if PREFERRED_ENDPOINT in all_endpoints:
    selected = PREFERRED_ENDPOINT
else:
    ka_like = [name for name in all_endpoints if "ka-" in name or "knowledge" in name.lower()]
    if ka_like:
        selected = sorted(ka_like)[0]

if not selected:
    raise RuntimeError(
        "No Knowledge Assistant serving endpoint found. "
        "Create one first, then set DATABRICKS_KA_ENDPOINT in app.yaml."
    )

print(f"Resolved Knowledge Assistant endpoint: {selected}")
print(f"DATABRICKS_KA_ENDPOINT={selected}")
