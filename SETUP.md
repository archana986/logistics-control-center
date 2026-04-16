# Setup Guide - Logistics Control Center

Deploy the Logistics Control Center on your Databricks workspace.

**Everything runs from the CLI** — clone the repo locally, configure, and deploy.

## Prerequisites

| Requirement | How to Check |
|-------------|--------------|
| **Databricks Workspace** | With Unity Catalog enabled |
| **SQL Warehouse** | Serverless recommended; you need CAN_USE permission |
| **Catalog Access** | You need CREATE SCHEMA permission on your target catalog |
| **Databricks CLI** | [Install](https://docs.databricks.com/dev-tools/cli/install.html) and authenticate with `databricks auth login` |

## Step 1: Clone the Repository

```bash
git clone https://github.com/archana-krishnamurthy_data/logistics-control-center.git
cd logistics-control-center
```

## Step 2: Configure Your Workspace Values

You need two values from your workspace:

| Value | Where to Find It |
|-------|-------------------|
| `warehouse_id` | SQL Warehouses → Click your warehouse → Copy ID from URL or Overview |
| `catalog` | Data Explorer → Select a catalog you own or have CREATE SCHEMA on |

### Edit databricks.yml

Open `databricks.yml` and find the `targets.dev.variables` section (~line 77). Replace the placeholders:

```yaml
    variables:
      warehouse_id: "your-warehouse-id"        # ← Your SQL Warehouse ID
      catalog: "your-catalog"                  # ← Your catalog name
      schema: "logistics_control_center"
```

### Edit app.yaml

Open `app.yaml` and find the Unity Catalog Configuration section (~line 49). Set your catalog:

```yaml
  - name: DATABRICKS_CATALOG
    value: "your-catalog"                      # ← Same catalog as databricks.yml
```

**Save both files.** That's all for Step 2 — warehouse ID, Genie Space ID, and KA endpoint are auto-injected via `valueFrom` when the app deploys later.

## Step 3: Deploy Infrastructure

```bash
databricks bundle deploy -t dev
```

This creates:
- Streaming pipeline (Bronze/Silver/Gold)
- Setup job
- Streaming refresh job

**Note:** The app is NOT deployed yet — it requires IDs that the setup job will create.

Expected output:
```
Uploading bundle files...
Deploying resources...
Deployment complete!
```

## Step 4: Run the Setup Job

```bash
databricks bundle run logistics_setup -t dev
```

This takes **5-10 minutes** and creates:
- Unity Catalog schema and volumes
- Synthetic logistics data
- Bronze → Silver → Gold pipeline run
- Genie Space for analytics
- Knowledge Assistant for document Q&A

**Important:** When the job completes, note these two values from the output:

```
════════════════════════════════════════════════════════════════════════════
SAVE THESE VALUES FOR STEP 5:
  DATABRICKS_GENIE_SPACE_ID: 01f12abc123456789
  DATABRICKS_KA_ENDPOINT: ka-abc123-endpoint
════════════════════════════════════════════════════════════════════════════
```

## Step 5: Run the Streaming Refresh

```bash
databricks bundle run logistics_streaming_refresh -t dev
```

This takes **3-5 minutes** and:
- Appends incremental events to the raw data volumes
- Runs the Bronze → Silver → Gold pipeline update
- Refreshes serving tables for the app
- Updates reroute optimization data

## Step 6: Add Agent IDs and Deploy the App

### 6a. Add the include line to databricks.yml

Open `databricks.yml` and add this line near the top (after the `sync:` block, before `workspace:`):

```yaml
include:
  - resources/app.yml
```

### 6b. Add the agent IDs to databricks.yml

In the same `targets.dev.variables` section you edited in Step 2, add the IDs from Step 4:

```yaml
    variables:
      warehouse_id: "your-warehouse-id"                    # Already set
      catalog: "your-catalog"                              # Already set
      schema: "logistics_control_center"
      genie_space_id: "your-genie-space-id"                # ← From Step 4 output
      ka_endpoint: "your-ka-endpoint"                      # ← From Step 4 output
```

### 6c. Deploy and grant permissions

```bash
# Deploy the app
databricks bundle deploy -t dev

# Grant the app's service principal access to Unity Catalog
databricks bundle run logistics_app_permissions -t dev
```

## Step 7: Access Your App

Your app URL is shown in the deployment output:

```
App URL: https://logistics-incident-response-<workspace-id>.databricksapps.com
```

Click the URL to open the Logistics Control Center.

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Clone Repo                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  git clone <repo-url> && cd logistics-control-center                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: Configure (2 files, 3 values)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  databricks.yml → warehouse_id, catalog                                    │
│  app.yaml → catalog                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: Deploy Infrastructure                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  databricks bundle deploy -t dev                                           │
│  Creates: pipeline, setup job, refresh job (no app yet)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: Run Setup Job (~10 min)                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  databricks bundle run logistics_setup -t dev                              │
│  → Note: genie_space_id and ka_endpoint from output                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: Run Streaming Refresh (~5 min)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  databricks bundle run logistics_streaming_refresh -t dev                  │
│  Appends events → runs pipeline → refreshes serving tables                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 6: Add IDs + Deploy App (1 file)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  databricks.yml → Add include: resources/app.yml                           │
│  databricks.yml → Add genie_space_id + ka_endpoint                         │
│  databricks bundle deploy -t dev                                           │
│  databricks bundle run logistics_app_permissions -t dev                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 7: Access App                                                        │
├─────────────────────────────────────────────────────────────────────────────┘
│  https://logistics-incident-response-<workspace-id>.databricksapps.com     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Configuration Summary

| File | What to Change | When |
|------|----------------|------|
| `databricks.yml` | `warehouse_id`, `catalog` | Step 2 |
| `app.yaml` | `DATABRICKS_CATALOG` | Step 2 |
| `databricks.yml` | Add `include: - resources/app.yml` | Step 6 |
| `databricks.yml` | `genie_space_id`, `ka_endpoint` | Step 6 |

**Values you never need to edit:**
- `app.yaml` warehouse ID, Genie Space ID, KA endpoint — auto-injected via `valueFrom`
- `resources/app.yml` — no edits needed

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Catalog not found"** | Verify catalog access: `SHOW CATALOGS;` in SQL Editor |
| **"Warehouse not found"** | Check warehouse ID; verify CAN_USE permission |
| **Deploy fails with empty space_id** | Make sure you added `include: - resources/app.yml` only AFTER Step 4 (in Step 6) |
| **Validation fails** | Ensure all placeholders are replaced with real values |
| **App won't start** | Check logs at `https://<app-url>/logz` |
| **Setup job fails** | Check task-level logs in Jobs UI; likely permissions issue |

## Cleanup

To remove **everything** created by this demo (DAB resources, Genie Space, KA endpoint, UC schema):

```bash
./cleanup.sh
```

The script reads your `databricks.yml` for IDs, confirms before deleting, and handles each resource independently (if one is already gone, it continues).

## FAQ

**Q: Do I need to install anything locally?**
You need the Databricks CLI. Everything else runs in Databricks.

**Q: Can I deploy from the workspace terminal instead?**
Yes. Clone the repo as a Git Folder, set `profile: DEFAULT` in databricks.yml, and run the same commands from the workspace terminal.

**Q: Can I use a shared catalog?**
Yes, as long as you have CREATE SCHEMA permission.

**Q: How do I update the app after changes?**
Run `databricks bundle deploy -t dev` to push updates.

**Q: Where do I find the Genie Space ID after setup?**
In the setup job output, or: Workspace → Genie → Your space → ID in URL.

**Q: Why is the app in a separate file (resources/app.yml)?**
The app requires a Genie Space ID and KA endpoint that don't exist until the setup job creates them. By keeping the app in a separate include file, the first deploy succeeds without those IDs. You add the include after the setup job provides them.
