# Customer Data Adaptation — Algorithm & Reference

This document describes how to adapt the Logistics Control Center to work with a customer's existing tables instead of synthetic data.

## Overview

The adapter layer creates **SQL views** in the target schema that map customer columns to the app's expected column names. The backend queries these views transparently — no app code changes needed.

```
Customer Tables                 Adapter Views                    App Backend
┌──────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│ shipping_routes   │────>│ lanes                │────>│ get_lanes()      │
│ warehouses        │────>│ centers              │────>│ get_centers()    │
│ delivery_orders   │────>│ shipments            │────>│ get_shipment_... │
│ issue_reports     │────>│ incidents            │────>│ get_incidents()  │
└──────────────────┘     └──────────────────────┘     └──────────────────┘
```

---

## Phase 1: Discovery

Get all tables and columns in a single query via `information_schema`:

```sql
SELECT table_name, column_name, full_data_type, is_nullable
FROM {source_catalog}.information_schema.columns
WHERE table_schema = '{source_schema}'
ORDER BY table_name, ordinal_position
```

Group results by `table_name` to build: `{table_name: [{column_name, data_type, is_nullable}]}`.

**Do NOT sample data yet** — sampling happens after matching (Phase 2) for matched tables only.

---

## Phase 2: Table Matching

Match each customer table to a contract table (see SCHEMA_CONTRACT.md) using:

1. **Name similarity**: Compare table names (e.g., `shipping_routes` ~ `lanes`)
2. **Column overlap**: Jaccard similarity on column name sets (case-insensitive)
3. **Semantic hints**: Use the alias map from SCHEMA_CONTRACT.md

**Scoring:**
```
score = (0.3 * name_similarity) + (0.7 * column_overlap)
```

Accept matches with score > 0.3. Present all proposed matches to the user for confirmation.

**No table is required.** The app degrades gracefully — any unmatched table gets an empty stub. Match what you can, stub the rest. After mapping, inform the user which features will be active vs empty:

| Table | Feature when populated | When empty |
|-------|----------------------|------------|
| `centers` | Map shows distribution centers/hubs | Map is empty (app still loads) |
| `lanes` | Network arcs and route metrics | Network view empty |
| `incidents` | Incident cards, reroute panel | No incidents shown |
| `shipments` | Shipment metrics, Genie analytics | Metric views return zeros |
| `customers` | Customer panel, comms generation | Customer panel empty |
| `capacity_lanes` | Capacity management view | Capacity tab empty |
| `capacity_actions` | Capacity action recommendations | No actions shown |
| `agent_activities` | Agent activity feed | Feed empty (populated at runtime) |
| `sales_opportunities` | Sales opportunity panel | Panel empty (populated at runtime) |
| `reroute_solutions` | Reroute suggestions | Empty (AI-generated at runtime) |
| `customer_interactions` | Customer interaction history | No history shown |

---

## Phase 3: Column Mapping

For each matched table pair, map columns using this priority order:

1. **Exact match** (case-insensitive): `lat` = `LAT` = `Lat`
2. **Semantic alias** (from SCHEMA_CONTRACT.md alias map): `latitude` → `lat`
3. **Type-compatible fuzzy match**: Levenshtein distance < 3 and compatible types
4. **User override**: From `column_overrides` in config

### Type Compatibility Matrix

| Contract Type | Compatible Customer Types |
|--------------|--------------------------|
| STRING | STRING, VARCHAR, CHAR, TEXT |
| INT | INT, INTEGER, BIGINT, SMALLINT, TINYINT, LONG |
| DOUBLE | DOUBLE, FLOAT, DECIMAL, NUMERIC |
| TIMESTAMP | TIMESTAMP, DATETIME, DATE (with CAST) |
| BOOLEAN | BOOLEAN, BIT, TINYINT (with CAST) |
| ARRAY/STRUCT | Skip — create with defaults |

### Handling Gaps

For each contract column that has no match:

| Situation | Action |
|-----------|--------|
| Column has a sensible default | Use default in view: `0 AS delayMinutes` |
| Column is not required (nullable) | Use NULL: `NULL AS sentiment` |
| Column is required, no default possible | Flag to user, ask for manual mapping |
| Complex type (ARRAY, STRUCT) | Create with empty/default: `ARRAY() AS targetCustomers` |

### Default Values by Column

| Column | Default | Rationale |
|--------|---------|-----------|
| region | NULL | Optional display field |
| delayMinutes | 0 | No delay assumed |
| slaRiskPct | 0.0 | No risk assumed |
| onTimePct | 100.0 | Optimistic default |
| avgDailyVolume | 0 | Unknown |
| maxCapacity | 1000 | Reasonable placeholder |
| utilizationPct | 50.0 | Neutral placeholder |
| availableCapacity | 500 | Half of default maxCapacity |
| optimalUtilization | 80.0 | Industry standard target |
| impactMinutes | 0 | No impact assumed |
| impactThroughputPct | 0.0 | No impact assumed |
| confidence | 1.0 | Full confidence |
| active | true | Assume active |
| packageCount | 1 | At least one package |
| status | 'in_transit' | Default state |
| sentiment | NULL | Unknown |
| metadata | '{}' | Empty JSON |
| notes | NULL | Optional |

---

## Phase 4: Generate Adapter Views

For each contract table with a customer match, generate SQL:

```sql
CREATE OR REPLACE VIEW {target_catalog}.{target_schema}.{contract_table} AS
SELECT
  {customer_col_1} AS {contract_col_1},
  {customer_col_2} AS {contract_col_2},
  -- For unmapped columns with defaults:
  0 AS delayMinutes,
  NULL AS notes
FROM {source_catalog}.{source_schema}.{customer_table}
```

**Example** — mapping a customer `warehouses` table to `centers`:
```sql
CREATE OR REPLACE VIEW demo.logistics_control_center.centers AS
SELECT
  warehouse_id AS id,
  warehouse_name AS name,
  latitude AS lat,
  longitude AS lng,
  facility_type AS type,
  NULL AS region
FROM customer_prod.supply_chain.warehouses
```

---

## Phase 5: Stub Missing Tables

For contract tables with **no** customer equivalent, create empty tables:

```sql
CREATE TABLE IF NOT EXISTS {target_catalog}.{target_schema}.{contract_table} (
  -- columns from SCHEMA_CONTRACT.md
)
USING DELTA
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true');
```

This ensures the backend doesn't error on missing tables — it just returns empty results.

---

## Phase 6: Create Helper & Metric Views

After adapter views are in place, run the metric view creation SQL. The views reference the adapter views by name, so they work transparently:

1. `api_shipment_lane_customer_metrics` — aggregates from `shipments`
2. `api_lane_health` — computed from `capacity_lanes`
3. `api_customer_rollup` — joins `customers` + `shipments`

Then create Genie metric views (`network_metrics`, `shipment_metrics`, `capacity_metrics`) pointing at the helper views.

---

## Phase 7: Create Genie Space

Create a Genie Space tailored to the customer's data:

- **Title**: "{Customer Name} Logistics Analytics" (or keep default)
- **Instructions**: Adapt sample questions to reflect actual data patterns
  - If customer has specific route names, use them in examples
  - If customer uses different terminology, reflect that
- **Metric views**: Point at the views created in Phase 6
- **Sample questions**: Generate 3-5 based on actual data patterns found during discovery

---

## Troubleshooting

| Issue | Resolution |
|-------|-----------|
| View creation fails: "table not found" | Check source_catalog.source_schema is accessible |
| Type mismatch in view | Add explicit CAST: `CAST(col AS INT) AS contract_col` |
| Null values breaking frontend | Add COALESCE: `COALESCE(col, default) AS contract_col` |
| Complex types can't be mapped | Use defaults: `ARRAY() AS targetCustomers` |
| Customer table has extra columns | Ignore — views only SELECT needed columns |
| Customer table has fewer rows | Fine — app works with any data volume |
| Genie returns wrong answers | Check metric view definitions, add more instructions |
