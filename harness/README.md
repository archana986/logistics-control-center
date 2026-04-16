# Logistics Control Center — Deployment Harness

One-command deployment for the Logistics Control Center demo, from either **Claude Code** or **Databricks Genie Code**.

## Two Modes

| Mode | What it does | When to use |
|------|-------------|-------------|
| **Demo deploy** | Generates synthetic logistics data and deploys everything | Demos, testing, showcases |
| **Customer data adapt** | Maps customer's existing tables via adapter views | Showing the platform on real customer data |

## Using from Claude Code

```
/logistics-demo
```

The skill will ask which mode you want and collect the required inputs (catalog, warehouse ID). Everything else is automated.

### Quick demo deploy (inline)

```
/logistics-demo Deploy demo mode to catalog "my_catalog" with warehouse "abc123def456"
```

## Using from Databricks Genie Code

1. Clone this repo into your Databricks workspace (Workspace > Add > Git folder)
2. Open Genie Code in **Agent mode**
3. The skill auto-appears — Genie Code discovers the `SKILL.md` from the Git folder

### Demo deploy prompt

Copy and paste, replacing the two values:

```
@SKILL.md Deploy demo mode to catalog "MY_CATALOG" with warehouse_id "MY_WAREHOUSE_ID"
```

### Customer data adapt prompt

```
@SKILL.md Adapt to customer data. Target catalog "MY_CATALOG", warehouse_id "MY_WAREHOUSE_ID",
source_catalog "CUSTOMER_CATALOG", source_schema "CUSTOMER_SCHEMA".
```

### Important notes for Genie Code

- **No CLI:** The Databricks CLI is not available in Genie Code's notebook environment. The deploy guide includes Python SDK / REST API alternatives for every step. Genie Code will use these automatically.
- **Knowledge Assistant:** The KA creation API may not be available in all environments. If setup task 8 fails, this is expected — the app works without it. To enable the KA panel, create a Knowledge Assistant manually via the Databricks UI (Agents > Create Knowledge Assistant) and update the app's `DATABRICKS_KA_ENDPOINT` environment variable.

## What Gets Deployed

| Resource | Description |
|----------|------------|
| Unity Catalog schema | Tables, views, and volumes for logistics data |
| Streaming pipeline | Bronze/Silver/Gold medallion architecture (serverless) |
| Genie Space | Natural language analytics over logistics metrics |
| Knowledge Assistant | Document Q&A over logistics SOPs |
| Databricks App | React + FastAPI full-stack application |
| Scheduled job | 5-minute streaming refresh for live data updates |

## File Structure

```
harness/
├── SKILL.md                        # Skill router (entry point for both runtimes)
├── README.md                       # This file
└── resources/
    ├── DEMO_DEPLOY.md              # Demo deploy flow (synthetic data)
    ├── CUSTOMER_ADAPT_FLOW.md      # Customer data adapt flow (real data)
    ├── SCHEMA_CONTRACT.md          # Complete table/column definitions + alias map
    ├── CUSTOMER_ADAPT.md           # Mapping algorithm reference
    └── CONFIG_TEMPLATE.yaml        # Configuration template
```

## Configuration

Copy `resources/CONFIG_TEMPLATE.yaml` and fill in your values. The only required fields are:
- `catalog` — your Unity Catalog catalog name
- `warehouse_id` — your SQL Warehouse ID

Everything else has sensible defaults or is auto-populated during deployment.

## Requirements

- Databricks workspace with Unity Catalog enabled
- SQL Warehouse (serverless preferred)
- `CREATE SCHEMA` permission on the target catalog
- For customer adapt mode: `SELECT` permission on source tables
