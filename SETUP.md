# Setup Guide - Logistics Control Center

Deploy the Logistics Control Center on your Databricks workspace in minutes.

## Prerequisites

| Requirement | How to Check/Get |
|-------------|------------------|
| **Databricks CLI** | `databricks --version` (install: `pip install databricks-cli`) |
| **CLI Authentication** | `databricks auth login --host <workspace-url>` |
| **Unity Catalog** | Workspace must have UC enabled |
| **SQL Warehouse** | Serverless recommended; you need CAN_USE permission |
| **Catalog Access** | You need CREATE SCHEMA permission on your target catalog |

---

## Quick Start (5 Steps)

### Step 1: Configure Your Workspace

Edit `databricks.yml` - update only the `targets.dev` section:

```yaml
targets:
  dev:
    mode: development
    default: true
    workspace:
      profile: my-workspace-profile      # Your CLI profile name
    variables:
      warehouse_id: "abc123def456"        # Your SQL Warehouse ID
      catalog: "my_catalog"               # Your catalog name
      schema: "logistics_control_center"
      genie_space_id: ""                  # Leave empty for now
      ka_endpoint: ""                     # Leave empty for now
```

**Where to find these values:**
- **Profile**: Run `databricks auth profiles`
- **Warehouse ID**: SQL Warehouses → Select warehouse → Copy ID from URL
- **Catalog**: Data Explorer → Select a catalog you own

### Step 2: Deploy Infrastructure

```bash
databricks bundle deploy -t dev
```

This creates the pipeline, jobs, and app (app won't fully work yet).

### Step 3: Run Setup Job

```bash
databricks bundle run logistics_setup -t dev
```

This takes 5-10 minutes and creates:
- Unity Catalog schema and volumes
- Synthetic logistics data
- Bronze → Silver → Gold pipeline run
- Genie Space for analytics
- Knowledge Assistant for document Q&A

**Important:** When complete, the job output shows:

```
════════════════════════════════════════════════════════════════════════════
SAVE THESE VALUES:
  DATABRICKS_GENIE_SPACE_ID: 01f12abc123456789
  DATABRICKS_KA_ENDPOINT: ka-abc123-endpoint
════════════════════════════════════════════════════════════════════════════
```

### Step 4: Add Agent IDs and Redeploy

Update `databricks.yml` with the IDs from Step 3:

```yaml
targets:
  dev:
    variables:
      warehouse_id: "abc123def456"
      catalog: "my_catalog"
      schema: "logistics_control_center"
      genie_space_id: "01f12abc123456789"    # ← Add this
      ka_endpoint: "ka-abc123-endpoint"       # ← Add this
```

Also update `app.yaml` with the same values:

```yaml
env:
  - name: DATABRICKS_SQL_WAREHOUSE_ID
    value: "abc123def456"
  - name: DATABRICKS_CATALOG
    value: "my_catalog"
  - name: DATABRICKS_GENIE_SPACE_ID
    value: "01f12abc123456789"               # ← Add this
  - name: DATABRICKS_KA_ENDPOINT
    value: "ka-abc123-endpoint"              # ← Add this
```

Then redeploy:

```bash
databricks bundle deploy -t dev
```

### Step 5: Grant Permissions and Access App

```bash
databricks bundle run logistics_app_permissions -t dev
```

Your app is now live! Find the URL in the deployment output:

```
App URL: https://logistics-incident-response-<workspace-id>.azuredatabricksapps.com
```

---

## Configuration Summary

### What You Edit (Once)

| File | What to Change |
|------|----------------|
| `databricks.yml` | `targets.dev.workspace.profile`, `targets.dev.variables.*` |
| `app.yaml` | Environment variables (same values as databricks.yml) |

### Values You Need

| Value | Where to Find | When to Add |
|-------|---------------|-------------|
| `profile` | `databricks auth profiles` | Step 1 |
| `warehouse_id` | SQL Warehouses UI | Step 1 |
| `catalog` | Data Explorer | Step 1 |
| `genie_space_id` | Setup job output | Step 4 |
| `ka_endpoint` | Setup job output | Step 4 |

---

## Troubleshooting

### "Catalog not found"
- Verify you have access: `SHOW CATALOGS;` in SQL Editor
- Use a catalog where you have CREATE SCHEMA permission

### "Warehouse not found"
- Check warehouse ID is correct (no quotes needed if numeric)
- Verify you have CAN_USE permission on the warehouse

### App won't start
- Check logs: `https://<app-url>/logz`
- Verify all env vars are set in `app.yaml`
- Run permissions job: `databricks bundle run logistics_app_permissions -t dev`

### Setup job fails
- Check task-level logs in the Jobs UI
- Most common: catalog/schema permissions

---

## Cleanup

```bash
# Remove all deployed resources
databricks bundle destroy -t dev

# Manually delete if needed:
# DROP SCHEMA IF EXISTS <catalog>.logistics_control_center CASCADE;
```
