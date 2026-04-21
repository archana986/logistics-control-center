# Demo Deploy Flow

Deploy the Logistics Control Center with synthetic data. No customer data needed.

**Two runtime paths:** This guide provides both CLI commands (for Claude Code / local terminal) and Python SDK/REST API equivalents (for Genie Code / notebook environments where the Databricks CLI is not available). Use whichever matches your environment.

**Two-phase deployment:** The app is deployed separately from infrastructure. Phase 1 (Steps 1-5) creates the pipeline, jobs, and data. Phase 2 (Steps 6-7) adds the app after agent IDs are known. This avoids first-deploy failures from empty Genie Space IDs.

## Step 1 — Configure YAML files

### `databricks.yml`

In the `targets.dev.variables` section, set `warehouse_id` and `catalog`:
```yaml
variables:
  warehouse_id: "{warehouse_id}"
  catalog: "{catalog}"
  schema: "{schema}"                    # default: logistics_control_center
  genie_space_id: ""                    # leave empty — populated in Step 6
  ka_endpoint: ""                       # leave empty — populated in Step 6
```

**Do NOT add `include: - resources/app.yml` yet** — the app is added in Step 6 after agent IDs exist.

### `app.yaml`

Only `catalog` and `schema` need to be set. Warehouse ID, Genie Space ID, and KA endpoint are auto-injected via `valueFrom` from the app resource:
```yaml
- name: DATABRICKS_CATALOG
  value: "{catalog}"
- name: DATABRICKS_SCHEMA
  value: "{schema}"
```

Do NOT edit the `valueFrom` entries — they are auto-injected from `resources/app.yml`.

### Placeholder format

The YAML files use placeholder values like `"your-warehouse-id"` and `"<YOUR_CATALOG>"`. Replace ALL occurrences — search both files for any warehouse, catalog, or schema values and update them.

## Step 2 — Deploy infrastructure (Phase 1 — no app yet)

### CLI path
```bash
databricks bundle deploy -t dev
```

This creates the pipeline and jobs only. The app is NOT deployed yet (it's in `resources/app.yml` which is not included).

### SDK/REST API path (Genie Code / notebooks)

The Databricks CLI is not available in notebook execution environments. Use the Python SDK:

1. **Upload files** to the workspace bundle path
2. **Create the streaming pipeline** via `w.pipelines.create()`
3. **Create the setup job** via `w.jobs.create()`
   - IMPORTANT: Pass `base_parameters` with `catalog` and `schema` on EVERY notebook task
   - Job-level parameters do NOT auto-propagate to notebook widgets

**SDK gotchas:**
- `JobEnvironmentSpec` may not exist — omit `environments`; serverless works without it
- Import notebooks **without** `.ipynb` extension in workspace paths

## Step 3 — Run setup job

### CLI path
```bash
databricks bundle run logistics_setup -t dev
```

### SDK path
```python
run = w.jobs.run_now(job_id=job_id)
# Poll until TERMINATED
```

Takes ~10 minutes. Runs 8 sequential tasks:
1. Creates schema, volumes, and serving tables
2. Generates synthetic data
3. Runs the Bronze/Silver/Gold pipeline
4. Refreshes serving tables
5. Creates helper and metric views
6. Generates synthetic KA documents
7. Creates a Genie Space — note the `genie_space_id` from output
8. Creates a Knowledge Assistant — note the `ka_endpoint` from output

**Task 7 (Genie Space):** The setup job auto-grants `CAN_MANAGE` to the deploying user. If that fails, grant manually: Genie > Space > Share > Add your email > Can Manage.

**Task 8 (Knowledge Assistant) may fail.** KA creation API is not available in all environments. If it fails, skip it — the app works without it. See Known Limitations in SKILL.md.

## Step 4 — Run streaming refresh

### CLI path
```bash
databricks bundle run logistics_streaming_refresh -t dev
```

### SDK path
```python
refresh_run = w.jobs.run_now(job_id=streaming_refresh_job_id)
# Poll until TERMINATED
```

Takes ~5 minutes. Populates live streaming data for the dashboard.

## Step 5 — Extract agent IDs

From the setup job output (Step 3), extract:
- `genie_space_id` — from the `create_genie_space` task output
- `ka_endpoint` — from the `create_knowledge_assistant` task output (if it succeeded)

### CLI path
```bash
# Find in the job run output, or:
# Workspace UI → Genie → Logistics Control Center Metrics → ID in URL
# Workspace UI → Serving → KA endpoint name
```

### SDK path
```python
run_output = w.jobs.get_run(run_id=run.run_id)
for task in run_output.tasks:
    if task.task_key == "create_genie_space":
        # Parse genie_space_id from notebook output
        pass
    if task.task_key == "create_knowledge_assistant":
        # Parse ka_endpoint from notebook output (may be missing)
        pass
```

## Step 6 — Add app include + agent IDs, redeploy (Phase 2)

### 6a. Add the include line to `databricks.yml`

Near the top of the file, add:
```yaml
include:
  - resources/app.yml
```

### 6b. Add the agent IDs to `databricks.yml`

In the `targets.dev.variables` section:
```yaml
genie_space_id: "{extracted_genie_space_id}"
ka_endpoint: "{extracted_ka_endpoint}"
```

### 6c. Deploy and grant permissions

#### CLI path
```bash
databricks bundle deploy -t dev
databricks bundle run logistics_app_permissions -t dev
```

#### SDK/REST API path

Create the app via REST API:
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
            {"name": "app-genie-space", "genie_space": {"space_id": "{genie_space_id}", "permission": "CAN_RUN"}},
            {"name": "app-ka-endpoint", "serving_endpoint": {"name": "{ka_endpoint}", "permission": "CAN_QUERY"}}
        ]
    }
)
```

Grant UC permissions using the SP's `applicationId` (UUID), not display name:
```python
app_info = requests.get(f"{w.config.host}/api/2.0/apps/logistics-incident-response", ...).json()
sp_app_id = app_info["service_principal"]["application_id"]

w.statement_execution.execute_statement(
    warehouse_id="{warehouse_id}",
    statement=f"GRANT USE SCHEMA ON {catalog}.{schema} TO `{sp_app_id}`"
)
w.statement_execution.execute_statement(
    warehouse_id="{warehouse_id}",
    statement=f"GRANT SELECT ON SCHEMA {catalog}.{schema} TO `{sp_app_id}`"
)
```

Warehouse and Genie Space permissions are auto-granted via app resource declarations.

## Step 7 — Verify

1. **Tables populated:** `SELECT count(*) FROM {catalog}.{schema}.centers` — should return rows
2. **App running:** Get URL from deploy output, confirm it loads
3. **Genie works:** Ask "How many active incidents?" in the Genie panel
4. **KA panel:** Will be inactive if KA creation was skipped (expected)

Print the app URL for the user.

**Cleanup:** To tear down all resources, run `./cleanup.sh` from the repo root.
