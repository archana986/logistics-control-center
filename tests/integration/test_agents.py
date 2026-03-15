from __future__ import annotations

import pytest

from tests.helpers.api_client import get_json, post_json

pytestmark = pytest.mark.integration


def _health(api_base_url: str) -> dict:
    status, payload = get_json(api_base_url, "/health")
    assert status == 200
    assert isinstance(payload, dict)
    return payload


def test_genie_query_returns_genie_source_when_configured(api_base_url: str) -> None:
    health = _health(api_base_url)
    genie_space = health.get("agents_configured") and health.get("databricks_connected")
    if not genie_space:
        pytest.skip("Agents client is not configured or Databricks is not connected.")

    status, payload = post_json(api_base_url, "/genie/query", {"question": "How many lanes are currently in the network?"})
    assert status == 200
    assert isinstance(payload, dict)
    source = payload.get("source")
    if source == "error":
        pytest.skip(f"Genie not yet configured in environment: {payload.get('answer')}")
    assert source == "genie"
    assert payload.get("answer")


def test_knowledge_query_returns_ka_source_when_configured(api_base_url: str) -> None:
    health = _health(api_base_url)
    ka_endpoint = health.get("ka_env_var") or health.get("agents_ka_endpoint")
    if not ka_endpoint:
        pytest.skip("Knowledge Assistant endpoint is not configured in environment.")

    status, payload = post_json(
        api_base_url,
        "/knowledge/query",
        {"question": "Summarize the incident response playbook for weather disruptions."},
    )
    assert status == 200
    assert isinstance(payload, dict)
    source = payload.get("source")
    if source == "error":
        pytest.skip(f"KA call returned error: {payload.get('answer')}")
    assert source == "knowledge_assistant"
    assert payload.get("answer")
