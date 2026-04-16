# Demo Deploy Flow

Deploy the Logistics Control Center with synthetic data. No customer data needed.

**Two runtime paths:** This guide provides both CLI commands (for Claude Code / local terminal) and Python SDK/REST API equivalents (for Genie Code / notebook environments where the Databricks CLI is not available). Use whichever matches your environment.

## Step 1 — Configure YAML files

The YAML config files may contain either placeholder markers (`<YOUR_WAREHOUSE_ID>`, `<YOUR_CATALOG>`) or hardcoded values from a previous deployment. Replace **all** occurrences of warehouse_id, catalog, and schema values in both `databricks.yml` and `app.yaml`.

### What to replace in `databricks.yml`

In the `targets.dev.variables` section, set:
```yaml
warehouse_id: "{warehouse_id}"
catalog: "{catalog}"
schema: "{schema}"
genie_space_id: ""
ka_endpoint: ""
```

Clear any pre-existing `genie_space_id` or `ka_endpoint` values — they'll be populated after the setup job.

### What to replace in `app.yaml`

In the `env` section, set:
```yaml
- name: DATABRICKS_SQL_WAREHOUSE_ID
  value: "{warehouse_id}"
- name: DATABRICKS_CATALOG
  value: "{catalog}"
- name: DATABRICKS_SCHEMA
  value: "{schema}"
- name: DATABRICKS_GENIE_SPACE_ID
  value: ""
- name: DATABRICKS_KA_ENDPOINT
  value: ""
```

### Important: handle hardcoded author values

The dev target may already have the original author's values baked in (not placeholders). Common stale values to look for and replace:
- `94565ba1e601c81a` (old warehouse ID)
- `akrishn_fe_dsa` (old catalog)

**Do not assume only placeholders need replacing.** Read both files, find ALL occurrences of warehouse_id, catalog, and schema values, and replace them with the user's values.

## Step 2 — Deploy infrastructure

### CLI path
```bash
databricks bundle deploy -t dev
```

### SDK/REST API path (Genie Code / notebooks)

The Databricks CLI is not available in notebook execution environments. Instead, use the Databricks Python SDK and REST API to replicate bundle deploy:

1. **Upload files** to the workspace using the Workspace API:
   ```python
   from databricks.sdk import WorkspaceClient
   w = WorkspaceClient()
   # Upload all repo files to the bundle workspace path
   # Target: /Workspace/Users/{username}/.bundle/logistics-control-center/dev/
   ```

2. **Create the streaming pipeline** via SDK:
   ```python
   pipeline = w.pipelines.create(
       name="logistics-control-center-streaming",
       catalog="{catalog}",
       target="{schema}",
       serverless=True,
       channel="CURRENT",
       continuous=False,
       libraries=[...],  # References to 01_bronze.sql, 02_silver.sql, 03_gold.sql
       configuration={"catalog": "{catalog}", "schema": "{schema}"}
   )
   pipeline_id = pipeline.pipeline_id
   ```

3. **Create the setup job** via SDK:
   ```python
   job = w.jobs.create(
       name="logistics-control-center-setup",
       tasks=[...],  # 8 tasks from databricks.yml
       # IMPORTANT: Pass base_parameters on EVERY notebook task:
       #   {"catalog": "{catalog}", "schema": "{schema}"}
       # Job-level parameters do NOT auto-propagate to notebook widgets
   )
   ```

4. **Create the app** via REST API (SDK may lack some App resource types):
   ```python
   import requests
   resp = requests.post(
       f"{w.config.host}/api/2.0/apps",
       headers={"Authorization": f"Bearer {w.config.token}"},
       json={
           "name": "logistics-incident-response",
           "description": "Logistics Control Center",
           "resources": [
               {"name": "app-sql-warehouse", "sql_warehouse": {"id": "{warehouse_id}", "permission": "CAN_USE"}},
               {"name": "app-genie-space", "genie_space": {"space_id": "", "permission": "CAN_RUN"}},
           ]
       }
   )
   ```

**SDK version gotchas:**
- `JobEnvironmentSpec` may not exist in older SDK versions — omit the `environments` parameter; serverless compute works without it
- `AppResourceGenieSpace` may not exist — use the REST API for app creation
- When uploading notebooks, import them **without** the `.ipynb` extension in the workspace path, or job task notebook references won't resolve

## Step 3 — Run setup job

### CLI path
```bash
databricks bundle run logistics_setup -t dev
```

### SDK path
```python
run = w.jobs.run_now(job_id=job_id)
# Poll for completion
import time
while True:
    status = w.jobs.get_run(run.run_id)
    if status.state.life_cycle_state.value in ("TERMINATED", "SKIPPED", "INTERNAL_ERROR"):
        break
    time.sleep(30)
```

Takes ~10 minutes. Runs 8 sequential tasks:
1. Creates schema, volumes, and serving tables
2. Generates synthetic data (shipments, incidents, centers, lanes, customers)
3. Runs the Bronze/Silver/Gold pipeline
4. Refreshes serving tables from gold outputs
5. Creates helper and metric views
6. Generates synthetic KA documents
7. Creates a Genie Space from metric views
8. Creates a Knowledge Assistant from generated docs

**Task 8 (Knowledge Assistant) may fail.** The KA creation API is not available in all environments. If it fails, **skip it** — the app works without it, the KA panel will just be inactive. This is a known limitation.

## Step 4 — Extract agent IDs and activate app

After the setup job completes, extract:
- `genie_space_id` — from the `create_genie_space` task output
- `ka_endpoint` — from the `create_knowledge_assistant` task output (if task succeeded)

### CLI path
```bash
JOB_ID=$(databricks jobs list --name "logistics-control-center-setup" --output json | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['job_id'])")
RUN_ID=$(databricks runs list --job-id $JOB_ID --output json | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['run_id'])")
databricks runs get-output --run-id $RUN_ID --output json
```

### SDK path
```python
run_output = w.jobs.get_run(run_id=run.run_id)
for task in run_output.tasks:
    if task.task_key == "create_genie_space":
        # Parse genie_space_id from notebook output
        pass
    if task.task_key == "create_knowledge_assistant":
        # Parse ka_endpoint from notebook output (may be missing if task failed)
        pass
```

### Update the app with agent IDs

Via REST API:
```python
import requests
resp = requests.patch(
    f"{w.config.host}/api/2.0/apps/logistics-incident-response",
    headers={"Authorization": f"Bearer {w.config.token}"},
    json={
        "resources": [
            {"name": "app-sql-warehouse", "sql_warehouse": {"id": "{warehouse_id}", "permission": "CAN_USE"}},
            {"name": "app-genie-space", "genie_space": {"space_id": "{genie_space_id}", "permission": "CAN_RUN"}}
        ]
    }
)
```

If KA endpoint was created, also add:
```python
{"name": "app-ka-endpoint", "serving_endpoint": {"name": "{ka_endpoint}", "permission": "CAN_QUERY"}}
```

## Step 5 — Grant permissions

The app's service principal needs access to UC tables and the warehouse.

### CLI path
```bash
databricks bundle run logistics_app_permissions -t dev
```

### SDK/SQL path

**Important:** Use the service principal's `applicationId` (UUID), not the display name. The display name may contain spaces that UC cannot resolve.

```python
# Get the app's service principal
app_info = requests.get(
    f"{w.config.host}/api/2.0/apps/logistics-incident-response",
    headers={"Authorization": f"Bearer {w.config.token}"}
).json()
sp_id = app_info["service_principal"]["id"]
sp_app_id = app_info["service_principal"]["application_id"]  # UUID

# Grant UC permissions using the applicationId
w.statement_execution.execute_statement(
    warehouse_id="{warehouse_id}",
    statement=f"GRANT USE SCHEMA ON {catalog}.{schema} TO `{sp_app_id}`"
)
w.statement_execution.execute_statement(
    warehouse_id="{warehouse_id}",
    statement=f"GRANT SELECT ON SCHEMA {catalog}.{schema} TO `{sp_app_id}`"
)
```

**Note:** Warehouse and Genie Space permissions are auto-granted via the app's resource declarations (`app-sql-warehouse`, `app-genie-space`). You do NOT need to separately grant these.

## Step 6 — Verify

1. **Tables populated:** `SELECT count(*) FROM {catalog}.{schema}.centers` — should return rows
2. **App running:** Check the app URL — confirm it loads
3. **Genie works:** Ask "How many active incidents?" in the Genie panel
4. **KA panel:** Will be inactive if KA creation was skipped (expected)

Print the app URL for the user.

## Step 7 — Save config (optional)

If the user didn't start with a config file, offer to save one for future redeployments.
