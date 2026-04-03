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

---

## Step 2: Configure Your Workspace Values

### Edit databricks.yml

1. In Databricks, open `databricks.yml` from the repo
2. Find the `targets.dev` section (~line 68) and update these values:

```yaml
targets:
  dev:
    mode: development
    default: true
    workspace:
      profile: DEFAULT                        # Keep as DEFAULT for workspace execution
    variables:
      warehouse_id: "your-warehouse-id"       # ← Replace with your SQL Warehouse ID
      catalog: "your-catalog"                 # ← Replace with your catalog name
      schema: "logistics_control_center"
      genie_space_id: ""                      # Leave empty for now
      ka_endpoint: ""                         # Leave empty for now
```

**Where to find values:**

| Value | Location in Databricks UI |
|-------|---------------------------|
| `warehouse_id` | SQL Warehouses → Click warehouse → Copy ID from URL or Overview |
| `catalog` | Data Explorer → Select a catalog you own or have CREATE SCHEMA on |

3. **Save the file** (Ctrl+S or Cmd+S)

### Edit app.yaml

1. Open `app.yaml` from the repo
2. Find the Unity Catalog Configuration section (~line 48) and update:

```yaml
  - name: DATABRICKS_SQL_WAREHOUSE_ID
    value: "your-warehouse-id"                # ← Same as databricks.yml
  - name: DATABRICKS_CATALOG
    value: "your-catalog"                     # ← Same as databricks.yml
```

3. **Save the file**

---

## Step 3: Deploy Infrastructure

Open the Databricks **Web Terminal** or run from your local CLI:

```bash
# Navigate to the repo (in Web Terminal, you're already there)
cd /Workspace/Repos/<your-username>/logistics-control-center

# Validate configuration
databricks bundle validate -t dev

# Deploy infrastructure (pipeline, jobs, app)
databricks bundle deploy -t dev
```

Expected output:
```
Uploading bundle files...
Deploying resources...
Deployment complete!
```

---

## Step 4: Run Setup Job

```bash
databricks bundle run logistics_setup -t dev
```

This takes **5-10 minutes** and creates:
- Unity Catalog schema and volumes
- Synthetic logistics data
- Bronze → Silver → Gold pipeline run
- Genie Space for analytics
- Knowledge Assistant for document Q&A

**Important:** When the job completes, look at the final task output for these values:

```
════════════════════════════════════════════════════════════════════════════
SAVE THESE VALUES FOR STEP 5:
  DATABRICKS_GENIE_SPACE_ID: 01f12abc123456789
  DATABRICKS_KA_ENDPOINT: ka-abc123-endpoint
════════════════════════════════════════════════════════════════════════════
```

---

## Step 5: Add Agent IDs and Complete Deployment

### Update databricks.yml

1. Open `databricks.yml` again
2. Add the IDs from Step 4 to the `targets.dev.variables` section:

```yaml
    variables:
      warehouse_id: "your-warehouse-id"
      catalog: "your-catalog"
      schema: "logistics_control_center"
      genie_space_id: "01f12abc123456789"     # ← Add your ID here
      ka_endpoint: "ka-abc123-endpoint"        # ← Add your endpoint here
```

3. **Save the file**

### Update app.yaml

1. Open `app.yaml` again
2. Add the same IDs to the Agent Bricks section (~line 65):

```yaml
  - name: DATABRICKS_GENIE_SPACE_ID
    value: "01f12abc123456789"                 # ← Add your ID here
  - name: DATABRICKS_KA_ENDPOINT
    value: "ka-abc123-endpoint"                # ← Add your endpoint here
```

3. **Save the file**

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
App URL: https://logistics-incident-response-<workspace-id>.azuredatabricksapps.com
```

Click the URL to open the Logistics Control Center!

---

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Clone to Databricks (UI)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Workspace → Repos → Add Repo                                               │
│  URL: https://github.com/archana-krishnamurthy_data/logistics-control-center│
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: Edit Config Files (UI)                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  databricks.yml → targets.dev.variables: warehouse_id, catalog             │
│  app.yaml → env: DATABRICKS_SQL_WAREHOUSE_ID, DATABRICKS_CATALOG           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: Deploy Infrastructure (Terminal)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  databricks bundle validate -t dev                                          │
│  databricks bundle deploy -t dev                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: Run Setup Job (Terminal, ~10 min)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  databricks bundle run logistics_setup -t dev                               │
│  → Note: GENIE_SPACE_ID and KA_ENDPOINT from output                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: Add Agent IDs & Redeploy (UI + Terminal)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  databricks.yml → Add genie_space_id, ka_endpoint                          │
│  app.yaml → Add DATABRICKS_GENIE_SPACE_ID, DATABRICKS_KA_ENDPOINT          │
│  databricks bundle deploy -t dev                                            │
│  databricks bundle run logistics_app_permissions -t dev                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 6: Access App                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  https://logistics-incident-response-<workspace-id>.azuredatabricksapps.com │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration Summary

| File | What to Change | When |
|------|----------------|------|
| `databricks.yml` | `warehouse_id`, `catalog` | Step 2 |
| `databricks.yml` | `genie_space_id`, `ka_endpoint` | Step 5 |
| `app.yaml` | `DATABRICKS_SQL_WAREHOUSE_ID`, `DATABRICKS_CATALOG` | Step 2 |
| `app.yaml` | `DATABRICKS_GENIE_SPACE_ID`, `DATABRICKS_KA_ENDPOINT` | Step 5 |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Catalog not found"** | Verify catalog access: `SHOW CATALOGS;` in SQL Editor |
| **"Warehouse not found"** | Check warehouse ID; verify CAN_USE permission |
| **Validation fails** | Ensure all placeholders are replaced with real values |
| **App won't start** | Check logs at `https://<app-url>/logz` |
| **Setup job fails** | Check task-level logs in Jobs UI; likely permissions issue |

---

## Cleanup

```bash
# Remove all deployed resources
databricks bundle destroy -t dev

# Manually delete schema if needed:
# DROP SCHEMA IF EXISTS <catalog>.logistics_control_center CASCADE;
```

---

## FAQ

**Q: Do I need to install anything locally?**  
No. Everything runs in Databricks.

**Q: Can I use a shared catalog?**  
Yes, as long as you have CREATE SCHEMA permission.

**Q: How do I update the app after changes?**  
Run `databricks bundle deploy -t dev` to push updates.

**Q: Where do I find the Genie Space ID after setup?**  
In the setup job output, or: Workspace → Genie → Your space → ID in URL.
