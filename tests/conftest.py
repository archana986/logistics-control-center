from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
import yaml
from databricks.sdk import WorkspaceClient


REPO_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_FILE = REPO_ROOT / "databricks.yml"


def _load_bundle_config() -> dict[str, Any]:
    with BUNDLE_FILE.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="session")
def bundle_config() -> dict[str, Any]:
    return _load_bundle_config()


@pytest.fixture(scope="session")
def workspace_client() -> WorkspaceClient:
    profile = os.getenv("DATABRICKS_CLI_PROFILE", "DEFAULT")
    return WorkspaceClient(profile=profile)


@pytest.fixture(scope="session")
def warehouse_id(bundle_config: dict[str, Any]) -> str:
    env_warehouse = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")
    if env_warehouse:
        return env_warehouse
    return str(bundle_config["variables"]["warehouse_id"]["default"])


@pytest.fixture(scope="session")
def catalog(bundle_config: dict[str, Any]) -> str:
    return os.getenv("DATABRICKS_CATALOG", str(bundle_config["variables"]["catalog"]["default"]))


@pytest.fixture(scope="session")
def schema(bundle_config: dict[str, Any]) -> str:
    return os.getenv("DATABRICKS_SCHEMA", str(bundle_config["variables"]["schema"]["default"]))


@pytest.fixture(scope="session")
def api_base_url() -> str:
    return os.getenv("APP_BASE_URL", "http://localhost:8001/api").rstrip("/")
