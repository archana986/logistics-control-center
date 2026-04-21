# Customer Data Adapt Flow

Map existing customer tables to the Logistics Control Center schema using adapter views. No synthetic data generation — the app runs on real customer data.

## Step 1 — Collect inputs

In addition to standard inputs (catalog, warehouse_id, schema, profile), collect:
- `source_catalog` — catalog containing customer's existing tables
- `source_schema` — schema containing customer's existing tables
- `column_overrides` (optional) — manual column mappings if known
- `dry_run` (optional) — if true, generate SQL but don't execute

## Step 2 — Discover customer schema (single query)

Get all tables and columns in one query via `information_schema`:

```sql
SELECT table_name, column_name, full_data_type, is_nullable
FROM {source_catalog}.information_schema.columns
WHERE table_schema = '{source_schema}'
ORDER BY table_name, ordinal_position
```

This returns the complete schema in one round-trip. Group results by `table_name` to build a map of `{table_name: [{column_name, data_type}]}`.

## Step 3 — Match tables to schema contract

> Reference: `resources/SCHEMA_CONTRACT.md` for the full contract and alias map.
> Reference: `resources/CUSTOMER_ADAPT.md` for the matching algorithm.

Compare discovered tables against the 11 contract tables using:
1. **Name similarity** between table names
2. **Column overlap** — Jaccard similarity on column name sets (case-insensitive)

Score: `(0.3 * name_similarity) + (0.7 * column_overlap)`. Accept matches > 0.3.

## Step 4 — Map columns for matched tables

For each matched table pair:

1. Apply `column_overrides` first (user always wins)
2. Exact match (case-insensitive): `lat` = `LAT`
3. Semantic aliases from SCHEMA_CONTRACT.md: `latitude` → `lat`, `longitude` → `lng`
4. Type-compatible fuzzy match (Levenshtein < 3)

**Now** sample data from matched tables only (skip unmatched tables):
```sql
SELECT * FROM {source_catalog}.{source_schema}.{matched_table} LIMIT 5
```

Use samples to validate mapping makes sense (e.g., `lat` column actually contains latitude values, not IDs).

## Step 5 — Present mapping for review

Show the proposed mapping and which features will be active:

```
Proposed Mapping:
  customer.warehouses → centers
    warehouse_id → id, warehouse_name → name, latitude → lat, longitude → lng
    facility_type → type, (default NULL) → region

  customer.shipping_routes → lanes
    route_id → id, from_city → origin, to_city → dest, transport → mode
    daily_vol → avgDailyVolume, otd_rate → onTimePct
    (default 0) → delayMinutes, (default 0.0) → slaRiskPct

  No match: agent_activities, sales_opportunities, reroute_solutions
    → Will create empty stubs (populated at runtime by AI agents)

Features:
  [active]  Map visualization (centers matched)
  [active]  Network view (lanes matched)
  [active]  Shipment metrics (shipments matched)
  [empty]   Reroute suggestions (no match — AI-generated at runtime)
  [empty]   Agent activity feed (no match — populated at runtime)

Proceed? (y/n)
```

Wait for user confirmation before executing.

## Step 6 — Generate adapter SQL

For each matched table, generate a `CREATE OR REPLACE VIEW`:

```sql
CREATE OR REPLACE VIEW {catalog}.{schema}.{contract_table} AS
SELECT
  {customer_col} AS {contract_col},
  -- unmapped columns with defaults:
  0 AS delayMinutes,
  NULL AS region
FROM {source_catalog}.{source_schema}.{customer_table}
```

For unmatched tables, generate `CREATE TABLE IF NOT EXISTS` with the full schema from SCHEMA_CONTRACT.md (empty stubs).

### Dry-run mode

If `dry_run` is set, **print all generated SQL** and stop. Do not execute. The user can review, edit, and run manually. This is useful for:
- Customer approval workflows
- Compliance review
- Manual tweaks before execution

```
--- DRY RUN: The following SQL would be executed ---

-- Adapter view: centers
CREATE OR REPLACE VIEW demo.logistics.centers AS ...

-- Adapter view: lanes
CREATE OR REPLACE VIEW demo.logistics.lanes AS ...

-- Stub table: agent_activities
CREATE TABLE IF NOT EXISTS demo.logistics.agent_activities (...)

--- End of dry run (12 statements). Run again without --dry-run to execute. ---
```

## Step 7 — Execute adapter SQL

If not dry-run, execute all statements via SQL warehouse:
```sql
-- Execute each CREATE VIEW and CREATE TABLE statement
-- Use mcp__databricks__execute_sql or databricks CLI
```

Verify each view returns data:
```sql
SELECT count(*) FROM {catalog}.{schema}.{contract_table}
```

## Step 8 — Create helper and metric views

The metric view SQL from `databricks/notebooks/create_helper_metric_views.sql` works as-is because adapter views use the same table names as the contract.

Execute with parameter substitution:
```bash
# Replace {catalog} and {schema} placeholders, then execute
```

## Step 9 — Create Genie Space

Create a Genie Space pointing at the metric views:
- Use `mcp__databricks__create_or_update_genie` or Databricks SDK
- Title: reflect customer context (e.g., "{Customer} Logistics Analytics")
- Sample questions: generate 3-5 based on actual data patterns from Step 4 samples
- Metric views: `network_metrics`, `shipment_metrics`, `capacity_metrics`

Extract `genie_space_id` from the response.

## Step 10 — Create Knowledge Assistant (optional)

If the customer has documents in a UC volume, create a KA pointing at them. Otherwise skip — the app handles missing KA gracefully.

Extract `ka_endpoint` if created.

## Step 11 — Deploy app (two-phase)

Clone the repo and configure:
```bash
git clone https://github.com/archana986/logistics-control-center.git
cd logistics-control-center
```

### Phase 1: Set warehouse_id and catalog in `databricks.yml` and `app.yaml`

In `databricks.yml` `targets.dev.variables`: set `warehouse_id`, `catalog`, `genie_space_id`, `ka_endpoint`.

In `app.yaml`: only set `DATABRICKS_CATALOG` and `DATABRICKS_SCHEMA` (warehouse/genie/KA are auto-injected via `valueFrom`).

### Phase 2: Add app include and deploy

Add to `databricks.yml`:
```yaml
include:
  - resources/app.yml
```

Deploy and grant permissions:
```bash
databricks bundle deploy -t dev
databricks bundle run logistics_app_permissions -t dev
```

**Note:** Skip the setup job and streaming refresh — adapter views replace synthetic data entirely.

## Step 12 — Verify

1. Query each adapter view: `SELECT count(*) FROM {catalog}.{schema}.{table}` — should return customer row counts
2. App loads with real data on the map
3. Genie answers a question about the customer's actual data
4. Empty stub features show "No data" gracefully (no errors)

Print the app URL.

## Step 13 — Save config (optional)

Offer to save `harness/config.yaml` with all collected values, mappings, and extracted IDs for repeat deployments.
