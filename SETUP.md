# Setup Guide - Logistics Control Center

This guide walks you through deploying the Logistics Control Center on your Databricks workspace.

## Prerequisites

| Requirement | How to Check/Get |
|-------------|------------------|
| **Databricks CLI** | `databricks --version` (install: `pip install databricks-cli`) |
| **CLI Authentication** | `databricks auth login --host <workspace-url>` |
| **Unity Catalog** | Workspace must have UC enabled |
| **SQL Warehouse** | Serverless recommended; you need CAN_USE permission |
| **Catalog Access** | You need CREATE SCHEMA permission on your target catalog |

## Deployment Overview

The deployment happens in **3 phases** due to dependencies:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: Deploy Infrastructure                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • Edit databricks.yml with your parameters                                 │
│  • Deploy pipeline and jobs (app commented out)                             │
│  └──▶ Creates: Pipeline, Setup Job, Refresh Job                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: Create Data & Agents                                              │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • Run the logistics_setup job                                              │
│  • Note the Genie Space ID and KA Endpoint from output                      │
│  └──▶ Creates: Tables, Data, Genie Space, Knowledge Assistant              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: Deploy App                                                         │
│  ─────────────────────────────────────────────────────────────────────────  │
│  • Update databricks.yml with Genie Space ID and KA Endpoint                │
│  • Uncomment the apps section                                               │
│  • Update app.yaml with the same values                                     │
│  • Deploy and grant permissions                                             │
│  └──▶ Creates: Databricks App (running)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Deploy Infrastructure

### Step 1.1: Find Your Parameters

Before editing config files, gather these values from your Databricks workspace:

| Parameter | Where to Find |
|-----------|---------------|
| **Profile Name** | Run `databricks auth profiles` to list profiles |
| **Warehouse ID** | SQL Warehouses → Select warehouse → Copy ID from URL or details |
| **Catalog Name** | Data Explorer → Select a catalog you own or can create schemas in |

### Step 1.2: Edit databricks.yml

Open `databricks.yml` and update the `targets.dev` section:

```yaml
targets:
  dev:
    mode: development
    default: true
    workspace:
      # ╔═══════════════════════════════════════════════════════════════════════╗
      # ║ CHANGE THIS: Your Databricks CLI profile name                         ║
      # ╚═══════════════════════════════════════════════════════════════════════╝
      profile: my-workspace-profile    # <-- Replace with your profile
    variables:
      # ╔═══════════════════════════════════════════════════════════════════════╗
      # ║ CHANGE THESE: Your workspace values                                    ║
      # ╚═══════════════════════════════════════════════════════════════════════╝
      warehouse_id: "abc123def456"     # <-- Your SQL Warehouse ID
      catalog: "my_catalog"            # <-- Your catalog name
      schema: "logistics_control_center"
      # Leave these empty for now (populated in Phase 2)
      genie_space_id: ""
      ka_endpoint: ""
```

### Step 1.3: Verify the Apps Section is Commented

Ensure the `resources.apps` section is **commented out** (it should be by default):

```yaml
resources:
  # apps:                              # <-- This line should be commented
  #   logistics_control_center_app:    # <-- All app lines should be commented
  #     name: logistics-incident-response
  #     ...
```

### Step 1.4: Validate and Deploy

```bash
# Validate your configuration
databricks bundle validate -t dev

# Deploy infrastructure (pipeline, jobs)
databricks bundle deploy -t dev
```

**Expected output:**
```
Uploading bundle files to /Workspace/Users/...
Deploying resources...
Deployment complete!
```

---

## Phase 2: Create Data & Agents

### Step 2.1: Run the Setup Job

```bash
databricks bundle run logistics_setup -t dev
```

This job takes 5-10 minutes and:
- Creates Unity Catalog schema and volumes
- Generates synthetic logistics data
- Runs the streaming pipeline (Bronze → Silver → Gold)
- Creates metric views for Genie Space
- Creates the Genie Space
- Creates the Knowledge Assistant

### Step 2.2: Get the Agent IDs

When the job completes, look at the output for these values:

```
════════════════════════════════════════════════════════════════════════════
DEPLOYMENT COMPLETE - Save these values for Phase 3:
════════════════════════════════════════════════════════════════════════════
DATABRICKS_GENIE_SPACE_ID: 01f12abc123456789
DATABRICKS_KA_ENDPOINT: ka-abc123-endpoint
════════════════════════════════════════════════════════════════════════════
```

**Alternative:** Find these in the Databricks UI:
- **Genie Space ID:** Workspace → Genie → Open your space → ID in URL
- **KA Endpoint:** Workspace → Serving → Model Serving → Your endpoint name

---

## Phase 3: Deploy App

### Step 3.1: Update databricks.yml with Agent IDs

Add the values from Phase 2 to `targets.dev.variables`:

```yaml
targets:
  dev:
    workspace:
      profile: my-workspace-profile
    variables:
      warehouse_id: "abc123def456"
      catalog: "my_catalog"
      schema: "logistics_control_center"
      # ╔═══════════════════════════════════════════════════════════════════════╗
      # ║ PHASE 2 VALUES: Add these from the setup job output                   ║
      # ╚═══════════════════════════════════════════════════════════════════════╝
      genie_space_id: "01f12abc123456789"      # <-- From Phase 2
      ka_endpoint: "ka-abc123-endpoint"         # <-- From Phase 2
```

### Step 3.2: Uncomment the Apps Section

Find the `resources.apps` section and uncomment it:

```yaml
resources:
  # Uncomment this entire section ↓
  apps:
    logistics_control_center_app:
      name: logistics-incident-response
      description: "Logistics Control Center - AI-powered incident response"
      source_code_path: .
      resources:
        - name: app-sql-warehouse
          sql_warehouse:
            id: ${var.warehouse_id}
            permission: CAN_USE
        - name: app-genie-space
          genie_space:
            name: "Logistics Control Center Metrics"
            space_id: ${var.genie_space_id}
            permission: CAN_RUN
        - name: app-ka-endpoint
          serving_endpoint:
            name: ${var.ka_endpoint}
            permission: CAN_QUERY
```

### Step 3.3: Update app.yaml

Open `app.yaml` and update the environment variables:

```yaml
env:
  # ─────────────────────────────────────────────────────────────────────────────
  # Unity Catalog Configuration
  # ─────────────────────────────────────────────────────────────────────────────
  - name: DATABRICKS_SQL_WAREHOUSE_ID
    value: "abc123def456"              # <-- Same as databricks.yml
  - name: DATABRICKS_CATALOG
    value: "my_catalog"                # <-- Same as databricks.yml
  - name: DATABRICKS_SCHEMA
    value: "logistics_control_center"

  # ─────────────────────────────────────────────────────────────────────────────
  # Agent Bricks Configuration (from Phase 2)
  # ─────────────────────────────────────────────────────────────────────────────
  - name: DATABRICKS_GENIE_SPACE_ID
    value: "01f12abc123456789"         # <-- From Phase 2
  - name: DATABRICKS_KA_ENDPOINT
    value: "ka-abc123-endpoint"        # <-- From Phase 2
```

### Step 3.4: Deploy the App

```bash
# Deploy with the app now included
databricks bundle deploy -t dev

# Grant the app's service principal access to Unity Catalog
databricks bundle run logistics_app_permissions -t dev
```

### Step 3.5: Access the App

The deployment output includes the app URL:

```
App URL: https://logistics-incident-response-<workspace-id>.azuredatabricksapps.com
```

Click the URL to open the Logistics Control Center.

---

## Configuration Reference

### databricks.yml Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `warehouse_id` | SQL Warehouse ID | `"106bb1811885f66e"` |
| `catalog` | Unity Catalog name | `"my_catalog"` |
| `schema` | Schema for logistics tables | `"logistics_control_center"` |
| `genie_space_id` | Genie Space ID (Phase 2 output) | `"01f12abc123456789"` |
| `ka_endpoint` | Knowledge Assistant endpoint (Phase 2 output) | `"ka-abc123-endpoint"` |

### app.yaml Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABRICKS_SQL_WAREHOUSE_ID` | Same as warehouse_id | `"106bb1811885f66e"` |
| `DATABRICKS_CATALOG` | Same as catalog | `"my_catalog"` |
| `DATABRICKS_SCHEMA` | Same as schema | `"logistics_control_center"` |
| `DATABRICKS_GENIE_SPACE_ID` | Same as genie_space_id | `"01f12abc123456789"` |
| `DATABRICKS_KA_ENDPOINT` | Same as ka_endpoint | `"ka-abc123-endpoint"` |
| `DATABRICKS_MODEL_ENDPOINT` | Foundation Model name | `"databricks-meta-llama-3-1-70b-instruct"` |

---

## Troubleshooting

### Authentication Issues

```bash
# Re-authenticate
databricks auth login --host https://<workspace>.azuredatabricks.net

# Verify profile works
databricks clusters list -p <your-profile>
```

### Catalog/Schema Errors

```sql
-- Check your catalog access (run in SQL Editor)
SHOW CATALOGS;
SHOW SCHEMAS IN <your_catalog>;

-- Create schema manually if needed
CREATE SCHEMA IF NOT EXISTS <your_catalog>.logistics_control_center;
```

### App Won't Start

1. Check app logs: `https://<app-url>/logz`
2. Verify all env vars are set correctly in `app.yaml`
3. Ensure the app service principal has UC permissions

### Job Failures

```bash
# Check job run details
databricks jobs list-runs --job-id <job-id> -p <your-profile>
```

---

## Cleanup

To remove all resources:

```bash
# Destroy bundle resources
databricks bundle destroy -t dev

# Manually delete (if needed):
# - Schema: DROP SCHEMA IF EXISTS <catalog>.logistics_control_center CASCADE;
# - Genie Space: Workspace → Genie → Delete
# - Serving Endpoint: Workspace → Serving → Delete
```
