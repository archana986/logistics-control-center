---
name: logistics-demo
description: "Deploy the Logistics Control Center demo with synthetic data or adapt it to customer tables. Handles full end-to-end setup: data, pipeline, Genie Space, Knowledge Assistant, and Databricks App."
user-invocable: true
---

# Logistics Control Center — Deployment Skill

Deploy an AI-powered logistics incident response app on Databricks. React + FastAPI frontend, medallion pipeline, Genie Space, Knowledge Assistant.

**Repo:** https://github.com/archana986/logistics-control-center

## Prerequisites

1. Databricks CLI installed and authenticated (`/databricks-authentication` or `databricks auth login`)
2. `CREATE SCHEMA` permission on the target catalog
3. A SQL Warehouse available (serverless preferred)

## Configuration

Check for `harness/config.yaml` in the repo. If it exists, read deployment values from it. If not, collect interactively and offer to save for repeat deployments:

- `catalog` — Unity Catalog catalog name (required)
- `warehouse_id` — SQL Warehouse ID (or auto-detect via `databricks warehouses list`)
- `schema` — Schema name (default: `logistics_control_center`)
- `profile` — Databricks CLI profile (default: `DEFAULT`)

## Mode Selection

Ask the user:

| Mode | Description | When to use |
|------|-------------|-------------|
| **Demo deploy** | Generates synthetic logistics data, deploys everything | Demos, testing, showcases |
| **Customer data adapt** | Maps existing customer tables via adapter views | Showing the platform on real customer data |

Then read and follow the appropriate resource:

- **Demo deploy** → read `resources/DEMO_DEPLOY.md`
- **Customer data adapt** → read `resources/CUSTOMER_ADAPT_FLOW.md`

## Reference Resources

- `resources/SCHEMA_CONTRACT.md` — complete table/column definitions and semantic alias map
- `resources/CUSTOMER_ADAPT.md` — discovery + mapping algorithm details
- `resources/CONFIG_TEMPLATE.yaml` — config file template

## Delegated Skills

- `/databricks-authentication` — CLI auth setup
- `/databricks-warehouse-selector` — auto-select best warehouse
- `/databricks-genie` — Genie Space creation
- `/agent-bricks` — Knowledge Assistant creation

## Error Recovery

| Error | Resolution |
|-------|-----------|
| Auth error on `bundle deploy` | Run `databricks auth login --profile {profile}` |
| Setup job task fails | `databricks runs get-output --run-id {id}` — retry if transient |
| Genie Space creation fails | Fall back to REST API: `POST /api/2.0/genie/spaces` |
| KA creation fails | Skip — app works without it |
| App returns 500 | Check `databricks apps logs logistics-incident-response` |
| Permission denied on customer tables | `GRANT SELECT` on source tables to deploying principal |
| Bundle deploy timeout | Retry — first deploy builds node_modules |
