---
name: logistics-demo
description: "Deploy the Logistics Control Center demo with synthetic data or adapt it to customer tables. Handles full end-to-end setup: data, pipeline, Genie Space, Knowledge Assistant, and Databricks App."
user-invocable: true
---

# Logistics Control Center — Deployment Skill

Deploy an AI-powered logistics incident response app on Databricks. React + FastAPI frontend, medallion pipeline, Genie Space, Knowledge Assistant.

**Repo:** https://github.com/archana986/logistics-control-center

## Prerequisites

1. `CREATE SCHEMA` permission on the target catalog
2. A SQL Warehouse available (serverless preferred)
3. Databricks CLI (for Claude Code / terminal) OR Python SDK access (for Genie Code / notebooks — CLI is not available in notebook environments)

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

## Deployment Architecture

**Two-phase deploy:** The app is in a separate file (`resources/app.yml`) and is NOT included in the first deploy. Phase 1 creates infrastructure (pipeline + jobs). Phase 2 adds `include: - resources/app.yml` and agent IDs after the setup job, then redeploys. This avoids first-deploy failures from empty Genie Space IDs.

**`valueFrom` auto-injection:** `app.yaml` uses `valueFrom` for warehouse ID, Genie Space ID, and KA endpoint — these are auto-injected from the app resource definition. Only `catalog` and `schema` need manual edit in `app.yaml`.

**Model:** Default foundation model is `databricks-llama-4-maverick`. Configurable in `app.yaml` under `DATABRICKS_MODEL_ENDPOINT`.

**Cleanup:** Run `./cleanup.sh` from repo root for full teardown (DAB resources, Genie Space, KA, schema).

## Known Limitations

- **Knowledge Assistant:** KA creation API is not available in all environments (notably Genie Code notebooks). If it fails during setup, skip it — the app works without it, the KA panel will be inactive. To enable KA, create it manually via the Databricks UI (Agents > Create Knowledge Assistant) and update the `ka_endpoint` variable in `databricks.yml`, then redeploy.
- **Genie Space permissions:** The setup job auto-grants `CAN_MANAGE` to the deploying user. If that fails, grant manually: Genie > Space > Share > Add your email > Can Manage.

## Error Recovery

| Error | Resolution |
|-------|-----------|
| Auth error on `bundle deploy` | Run `databricks auth login --profile {profile}` |
| `databricks` CLI not available | Use Python SDK / REST API path (see DEMO_DEPLOY.md Step 2) |
| First deploy fails on empty genie_space_id | Expected — don't add `include: - resources/app.yml` until Step 6 |
| Setup job task fails | Check task output — retry if transient |
| Notebooks "Unable to access" | Ensure notebooks imported without `.ipynb` extension in workspace path |
| Job params not reaching notebooks | Add `base_parameters` with `catalog` and `schema` to every notebook task |
| Genie Space creation fails | Fall back to REST API: `POST /api/2.0/genie/spaces` |
| Genie Space CAN_MANAGE denied | Grant manually: Genie > Space > Share > Can Manage |
| KA creation fails | Skip — see Known Limitations above |
| App creation SDK error | Use REST API `POST /api/2.0/apps` instead of SDK |
| `Could not find principal` on GRANT | Use the SP's `applicationId` (UUID), not display name |
| Warehouse permission error | Rely on app resource declarations — they auto-grant to the SP |
| App returns 500 | Check `databricks apps logs logistics-incident-response` |
| Hardcoded old values in YAML | Read both files — replace ALL warehouse/catalog values, not just placeholders |
| Bundle deploy timeout | Retry — first deploy builds node_modules |
