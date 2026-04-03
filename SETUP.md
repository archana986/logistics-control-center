# Setup Guide - Logistics Control Center

Deploy the Logistics Control Center on your Databricks workspace in minutes.

**Everything happens in Databricks** - no local setup required.

---

## Prerequisites

| Requirement | How to Check |
|-------------|--------------|
| **Databricks Workspace** | With Unity Catalog enabled |
| **SQL Warehouse** | Serverless recommended; you need CAN_USE permission |
| **Catalog Access** | You need CREATE SCHEMA permission on your target catalog |

---

## Step 1: Clone Repository to Databricks Workspace

1. Open your Databricks workspace
2. Go to **Workspace** → **Repos** → **Add Repo**
3. Paste this URL:
   ```
   https://github.com/archana-krishnamurthy_data/logistics-control-center
   ```
4. Click **Create Repo**

The repo will be cloned to: `/Repos/<your-username>/logistics-control-center`

You should see this structure:
```
logistics-control-center/
├── README.md
├── SETUP.md              # You are here
├── CONFIG.md             # Config file reference
├── databricks.yml        # Edit this in Step 2
├── app.yaml              # Edit this in Step 2
├── backend/              # Python FastAPI
├── src/                  # React frontend
├── databricks/           # Notebooks and pipelines
└── public/               # Static assets
```

---

## Step 2: Configure Your Workspace Values

### Edit databricks.yml

1. In Databricks, open `databricks.yml` from the repo
2. Find the `targets.dev` section and update these values:

```yaml
targets:
  dev:
    workspace:
      profile: DEFAULT                    # Use DEFAULT for workspace execution
    variables:
      warehouse_id: "your-warehouse-id"   # Your SQL Warehouse ID
      catalog: "your-catalog"             # Your catalog name
      schema: "logistics_control_center"
      genie_space_id: ""                  # Leave empty for now
      ka_endpoint: ""                     # Leave empty for now
```

**Where to find values:**
| Value | Location in Databricks UI |
|-------|---------------------------|
| `warehouse_id` | SQL Warehouses → Select warehouse → Copy ID from URL |
| `catalog` | Data Explorer → Select a catalog you own |

3. Save the file

### Edit app.yaml

1. Open `app.yaml` from the repo
2. Update the environment variables to match:

```yaml
env:
  - name: DATABRICKS_SQL_WAREHOUSE_ID
    value: "your-warehouse-id"            # Same as above
  - name: DATABRICKS_CATALOG
    value: "your-catalog"                 # Same as above
  - name: DATABRICKS_GENIE_SPACE_ID
    value: ""                             # Leave empty for now
  - name: DATABRICKS_KA_ENDPOINT
    value: ""                             # Leave empty for now
```

3. Save the file

---

## Step 3: Deploy Infrastructure

Open a **Web Terminal** in Databricks or use the Databricks CLI:

```bash
# Navigate to the repo
cd /Workspace/Repos/<your-username>/logistics-control-center

# Validate configuration
databricks bundle validate -t dev

# Deploy infrastructure (pipeline, jobs, app)
databricks bundle deploy -t dev
```

---

## Step 4: Run Setup Job

```bash
databricks bundle run logistics_setup -t dev
```

This takes 5-10 minutes and creates:
- Unity Catalog schema and volumes
- Synthetic logistics data
- Bronze → Silver → Gold pipeline run
- Genie Space for analytics
- Knowledge Assistant for document Q&A

**Important:** When complete, note the output:

```
════════════════════════════════════════════════════════════════════════════
SAVE THESE VALUES:
  DATABRICKS_GENIE_SPACE_ID: 01f12abc123456789
  DATABRICKS_KA_ENDPOINT: ka-abc123-endpoint
════════════════════════════════════════════════════════════════════════════
```

---

## Step 5: Add Agent IDs and Complete Deployment

### Update databricks.yml

Add the IDs from Step 4:

```yaml
targets:
  dev:
    variables:
      warehouse_id: "your-warehouse-id"
      catalog: "your-catalog"
      schema: "logistics_control_center"
      genie_space_id: "01f12abc123456789"    # ← Add this
      ka_endpoint: "ka-abc123-endpoint"       # ← Add this
```

### Update app.yaml

```yaml
env:
  - name: DATABRICKS_GENIE_SPACE_ID
    value: "01f12abc123456789"               # ← Add this
  - name: DATABRICKS_KA_ENDPOINT
    value: "ka-abc123-endpoint"              # ← Add this
```

### Redeploy and Grant Permissions

```bash
# Redeploy with agent IDs
databricks bundle deploy -t dev

# Grant app permissions to Unity Catalog
databricks bundle run logistics_app_permissions -t dev
```

---

## Step 6: Access Your App

Your app URL is shown in the deployment output:

```
https://logistics-incident-response-<workspace-id>.azuredatabricksapps.com
```

Click the URL to open the Logistics Control Center!

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

---

## Complete Workflow Example

Here's the full deployment workflow from start to finish:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Clone to Databricks Workspace (UI)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Workspace → Repos → Add Repo                                               │
│  URL: https://github.com/archana-krishnamurthy_data/logistics-control-center│
│  Click: Create Repo                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: Edit Config Files (UI)                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Open databricks.yml → Update targets.dev section:                          │
│    profile: DEFAULT                                                         │
│    warehouse_id: "your-id"                                                  │
│    catalog: "your-catalog"                                                  │
│                                                                             │
│  Open app.yaml → Update env section with same values                        │
│  Save both files                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: Deploy Infrastructure (Terminal)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  cd /Workspace/Repos/<user>/logistics-control-center                        │
│  databricks bundle validate -t dev                                          │
│  databricks bundle deploy -t dev                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: Run Setup Job (Terminal, ~10 min)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  databricks bundle run logistics_setup -t dev                               │
│                                                                             │
│  Note output:                                                               │
│    DATABRICKS_GENIE_SPACE_ID: 01f12abc...                                   │
│    DATABRICKS_KA_ENDPOINT: ka-abc123-endpoint                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: Add Agent IDs (UI)                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  Edit databricks.yml → Add to targets.dev.variables:                        │
│    genie_space_id: "01f12abc..."                                            │
│    ka_endpoint: "ka-abc123-endpoint"                                        │
│                                                                             │
│  Edit app.yaml → Add same values to env section                             │
│  Save both files                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 6: Complete Deployment (Terminal)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  databricks bundle deploy -t dev                                            │
│  databricks bundle run logistics_app_permissions -t dev                     │
│                                                                             │
│  App URL: https://logistics-incident-response-<id>.azuredatabricksapps.com  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FAQ

**Q: Do I need to install Node.js locally?**
No. The app builds inside the Databricks App environment.

**Q: Can I use a shared catalog?**
Yes, as long as you have CREATE SCHEMA permission.

**Q: How do I update the app after changes?**
Run `databricks bundle deploy -t dev` to push updates.

**Q: Can I deploy to multiple workspaces?**
Yes. Add additional targets in `databricks.yml` (e.g., `prod`) with different profiles.
