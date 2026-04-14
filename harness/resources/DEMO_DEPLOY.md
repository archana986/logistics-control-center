# Demo Deploy Flow

Deploy the Logistics Control Center with synthetic data. No customer data needed.

## Step 1 — Clone and configure

```bash
git clone https://github.com/archana986/logistics-control-center.git
cd logistics-control-center
```

Patch config placeholders in both files at once. The YAML files use `<YOUR_WAREHOUSE_ID>` and `<YOUR_CATALOG>` as markers:

```bash
# Replace placeholders in databricks.yml and app.yaml
sed -i '' 's/<YOUR_WAREHOUSE_ID>/{warehouse_id}/g' databricks.yml app.yaml
sed -i '' 's/<YOUR_CATALOG>/{catalog}/g' databricks.yml app.yaml
```

If the schema is not the default `logistics_control_center`, also replace:
```bash
sed -i '' 's/logistics_control_center/{schema}/g' databricks.yml app.yaml
```

## Step 2 — Deploy infrastructure

```bash
databricks bundle deploy -t dev
```

Creates the app shell, pipeline, and job definitions. The app won't be fully functional until agent IDs are configured.

## Step 3 — Run setup job

```bash
databricks bundle run logistics_setup -t dev
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

## Step 4 — Extract agent IDs and activate app

After the setup job completes, extract two values:
- `genie_space_id` — from the `create_genie_space` task output
- `ka_endpoint` — from the `create_knowledge_assistant` task output

Programmatically:
```bash
# Get the job ID
JOB_ID=$(databricks jobs list --name "logistics-control-center-setup" --output json | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['job_id'])")

# Get the latest run
RUN_ID=$(databricks runs list --job-id $JOB_ID --output json | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['run_id'])")

# Extract from task outputs
databricks runs get-output --run-id $RUN_ID --output json
# Parse genie_space_id and ka_endpoint from the notebook outputs
```

Or via MCP tools:
```
mcp__databricks__manage_job_runs (action: list, filter by job name)
→ parse notebook output cells for genie_space_id and ka_endpoint
```

### Activate immediately (no second bundle deploy)

Update the running app's env vars directly via the Apps API:

```bash
databricks apps update logistics-incident-response --json '{
  "resources": [
    {"name": "app-genie-space", "genie_space": {"space_id": "{genie_space_id}", "permission": "CAN_RUN"}},
    {"name": "app-ka-endpoint", "serving_endpoint": {"name": "{ka_endpoint}", "permission": "CAN_QUERY"}}
  ]
}'
```

Or via REST API:
```bash
curl -X PATCH "https://{workspace_host}/api/2.0/apps/logistics-incident-response" \
  -H "Authorization: Bearer $(databricks auth token)" \
  -d '{"env": [
    {"name": "DATABRICKS_GENIE_SPACE_ID", "value": "{genie_space_id}"},
    {"name": "DATABRICKS_KA_ENDPOINT", "value": "{ka_endpoint}"}
  ]}'
```

### Also patch YAML for future deploys

Update `databricks.yml` so subsequent `bundle deploy` commands retain the IDs:
```bash
sed -i '' 's/genie_space_id: ""/genie_space_id: "{genie_space_id}"/' databricks.yml
sed -i '' 's/ka_endpoint: ""/ka_endpoint: "{ka_endpoint}"/' databricks.yml
```

And `app.yaml`:
```bash
sed -i '' '/DATABRICKS_GENIE_SPACE_ID/{n;s/value: ""/value: "{genie_space_id}"/;}' app.yaml
sed -i '' '/DATABRICKS_KA_ENDPOINT/{n;s/value: ""/value: "{ka_endpoint}"/;}' app.yaml
```

## Step 5 — Grant permissions

```bash
databricks bundle run logistics_app_permissions -t dev
```

Grants the app's service principal access to UC tables, warehouse, Genie Space, and KA endpoint.

## Step 6 — Verify

1. **Tables populated:** `SELECT count(*) FROM {catalog}.{schema}.centers` — should return rows
2. **App running:** `databricks apps get logistics-incident-response` — get URL, confirm it loads
3. **Genie works:** Ask "How many active incidents?" in the Genie panel
4. **KA works:** Ask "What is the reroute SOP?" in the KA panel

Print the app URL for the user.

## Step 7 — Save config (optional)

If the user didn't start with a config file, offer to save one:
```bash
cp harness/resources/CONFIG_TEMPLATE.yaml harness/config.yaml
# Fill in the collected values + extracted agent IDs
```

This allows future redeployments to skip the interactive prompts.
