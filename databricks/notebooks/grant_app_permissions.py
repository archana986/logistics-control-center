"""Grant Unity Catalog access to the Databricks App service principal."""

from __future__ import annotations

import argparse

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-name", required=True)
    parser.add_argument("--warehouse-id", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    return parser.parse_args()


def _quote_principal(principal: str) -> str:
    return f"`{principal.replace('`', '``')}`"


def _run_sql(client: WorkspaceClient, warehouse_id: str, statement: str) -> None:
    execution = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="40s",
    )
    state = execution.status.state if execution.status else None
    if state != StatementState.SUCCEEDED:
        error = execution.status.error if execution.status else "unknown"
        raise RuntimeError(f"SQL failed with state={state}: {error}")


def main() -> None:
    args = _parse_args()
    client = WorkspaceClient()

    app = client.api_client.do("GET", f"/api/2.0/apps/{args.app_name}")
    principal = app.get("service_principal_client_id") or app.get("service_principal_name")
    if not principal:
        raise RuntimeError(
            f"App {args.app_name} does not expose a service principal identifier; cannot grant permissions."
        )

    fq_schema = f"{args.catalog}.{args.schema}"
    principal_sql = _quote_principal(principal)
    statements = [
        f"GRANT USE CATALOG ON CATALOG {args.catalog} TO {principal_sql}",
        f"GRANT USE SCHEMA ON SCHEMA {fq_schema} TO {principal_sql}",
        f"GRANT SELECT ON SCHEMA {fq_schema} TO {principal_sql}",
    ]

    for stmt in statements:
        print(f"Executing: {stmt}")
        _run_sql(client, args.warehouse_id, stmt)

    print(f"Granted app principal permissions on {fq_schema}: {principal}")


if __name__ == "__main__":
    main()
