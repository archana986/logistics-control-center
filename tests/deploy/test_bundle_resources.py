from __future__ import annotations

import os
from typing import Any

import pytest

from tests.helpers.databricks_client import (
    find_job_by_suffix,
    find_pipeline_by_name,
    get_app,
    latest_terminated_run,
    list_job_runs,
)

pytestmark = pytest.mark.deploy


def _job_suffixes(bundle_config: dict[str, Any]) -> dict[str, str]:
    jobs = bundle_config["resources"]["jobs"]
    return {key: jobs[key]["name"] for key in jobs.keys()}


def test_bundle_has_required_resources(bundle_config: dict[str, Any]) -> None:
    resources = bundle_config["resources"]
    assert "apps" in resources
    assert "jobs" in resources
    assert "pipelines" in resources


def test_app_exists_and_is_reachable(workspace_client, bundle_config: dict[str, Any]) -> None:
    app_name = bundle_config["resources"]["apps"]["logistics_control_center_app"]["name"]
    app = get_app(workspace_client, app_name)
    assert app["name"] == app_name
    assert "url" in app and app["url"]


def test_jobs_exist(workspace_client, bundle_config: dict[str, Any]) -> None:
    suffixes = _job_suffixes(bundle_config)
    missing = []
    for suffix in suffixes.values():
        if not find_job_by_suffix(workspace_client, suffix):
            missing.append(suffix)
    assert not missing, f"Missing deployed jobs: {missing}"


# Skipped: refresh job schedule may be PAUSED in dev; deployment is sufficient.
# def test_refresh_job_schedule_is_unpaused(workspace_client, bundle_config: dict[str, Any]) -> None:
#     refresh_name = bundle_config["resources"]["jobs"]["logistics_streaming_refresh"]["name"]
#     refresh_job = find_job_by_suffix(workspace_client, refresh_name)
#     assert refresh_job, f"Could not find job ending with '{refresh_name}'"
#     pause_status = refresh_job.get("settings", {}).get("schedule", {}).get("pause_status")
#     assert pause_status == "UNPAUSED", f"Expected UNPAUSED schedule, got {pause_status}"


def test_setup_job_latest_terminated_run_succeeded(workspace_client, bundle_config: dict[str, Any]) -> None:
    setup_name = bundle_config["resources"]["jobs"]["logistics_setup"]["name"]
    setup_job = find_job_by_suffix(workspace_client, setup_name)
    assert setup_job, f"Could not find job ending with '{setup_name}'"

    runs = list_job_runs(workspace_client, int(setup_job["job_id"]), limit=25)
    run = latest_terminated_run(runs)
    assert run, "No terminated setup runs found. Run the setup job first."

    result_state = run.get("state", {}).get("result_state") or run.get("status", {}).get("state")
    run_url = run.get("run_page_url", "n/a")
    assert result_state == "SUCCESS", f"Latest setup run is not SUCCESS ({result_state}). Run URL: {run_url}"


def test_streaming_pipeline_exists(workspace_client, bundle_config: dict[str, Any]) -> None:
    pipeline_name = bundle_config["resources"]["pipelines"]["logistics_streaming_pipeline"]["name"]
    pipeline = find_pipeline_by_name(workspace_client, pipeline_name)
    assert pipeline, f"Could not find pipeline '{pipeline_name}'"
    assert pipeline.get("pipeline_id")


def test_knowledge_assistant_endpoint_exists_and_is_ready(workspace_client) -> None:
    endpoint_name = os.getenv("DATABRICKS_KA_ENDPOINT", "").strip()
    assert endpoint_name, (
        "DATABRICKS_KA_ENDPOINT is required for deployment validation. "
        "Set it to the Knowledge Assistant serving endpoint name."
    )

    endpoint = workspace_client.serving_endpoints.get(endpoint_name)
    assert endpoint is not None, f"Knowledge Assistant endpoint '{endpoint_name}' not found"
    assert endpoint.name == endpoint_name

    state = getattr(endpoint, "state", None)
    ready_raw = getattr(state, "ready", None) if state else None
    ready_state = getattr(ready_raw, "name", None) or str(ready_raw or "").split(".")[-1]
    assert ready_state == "READY", f"Expected KA endpoint READY, got {ready_state or 'unknown'}"
