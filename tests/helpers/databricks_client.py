from __future__ import annotations

from typing import Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState


def list_jobs(client: WorkspaceClient, *, limit: int = 100) -> list[dict[str, Any]]:
    response = client.api_client.do("GET", "/api/2.2/jobs/list", query={"limit": limit})
    return list(response.get("jobs", []))


def list_job_runs(client: WorkspaceClient, job_id: int, *, limit: int = 20) -> list[dict[str, Any]]:
    response = client.api_client.do(
        "GET",
        "/api/2.2/jobs/runs/list",
        query={"job_id": job_id, "limit": limit},
    )
    return list(response.get("runs", []))


def get_app(client: WorkspaceClient, app_name: str) -> dict[str, Any]:
    return client.api_client.do("GET", f"/api/2.0/apps/{app_name}")


def list_pipelines(client: WorkspaceClient) -> list[dict[str, Any]]:
    response = client.api_client.do("GET", "/api/2.0/pipelines")
    return list(response.get("statuses", []))


def find_job_by_suffix(client: WorkspaceClient, suffix: str) -> dict[str, Any] | None:
    for job in list_jobs(client):
        settings = job.get("settings", {})
        name = settings.get("name", "")
        if name.endswith(suffix):
            return job
    return None


def find_pipeline_by_name(client: WorkspaceClient, name: str) -> dict[str, Any] | None:
    for pipeline in list_pipelines(client):
        pipeline_name = pipeline.get("name", "")
        # Bundle development mode prefixes resource names, e.g. "[dev user] <name>"
        if pipeline_name == name or pipeline_name.endswith(name):
            return pipeline
    return None


def latest_terminated_run(runs: list[dict[str, Any]]) -> dict[str, Any] | None:
    terminated_states = {"TERMINATED", "INTERNAL_ERROR", "SKIPPED"}
    for run in runs:
        life_cycle_state = (
            run.get("state", {}).get("life_cycle_state")
            or run.get("status", {}).get("state")
            or ""
        )
        if life_cycle_state in terminated_states:
            return run
    return None


def run_sql(client: WorkspaceClient, warehouse_id: str, sql: str) -> list[dict[str, Any]]:
    execution = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout="40s",
    )
    state = execution.status.state if execution.status else None
    if state != StatementState.SUCCEEDED:
        raise RuntimeError(f"SQL failed with state={state}: {execution.status.error if execution.status else 'unknown'}")

    if not execution.result or not execution.result.data_array:
        return []

    # StatementExecutionResponse stores schema metadata in top-level manifest.
    columns = []
    if execution.manifest and execution.manifest.schema and execution.manifest.schema.columns:
        columns = execution.manifest.schema.columns

    names = [c.name for c in columns]
    if not names and execution.result.data_array:
        # Fallback when schema metadata is not returned.
        names = [f"col_{idx}" for idx in range(len(execution.result.data_array[0]))]

    rows: list[dict[str, Any]] = []
    for row in execution.result.data_array:
        rows.append({names[idx]: row[idx] if idx < len(row) else None for idx in range(len(names))})
    return rows
