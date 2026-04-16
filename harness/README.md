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

### One-time setup: Install the skill

Genie Code discovers skills from `.assistant/skills/` in your workspace, not from Git folders directly. Run the install notebook once to copy the skill into place:

1. Clone this repo into your Databricks workspace (Workspace > Add > Git folder)
2. Open `harness/install_skill.py` as a notebook
3. Run all cells — this copies the skill to `/Users/{you}/.assistant/skills/logistics-demo/`

### Use the skill

Once installed, Genie Code auto-loads the skill in **Agent mode** when you ask about deploying or setting up the logistics demo. You can also invoke it explicitly:

```
@logistics-demo Deploy demo mode to catalog "my_catalog" with warehouse_id "my_warehouse_id"
```

Or describe what you want naturally:

```
Deploy the logistics control center demo using catalog "my_catalog" and warehouse "my_warehouse_id"
```

### Customer data adapt via Genie Code

```
@logistics-demo Adapt to customer data in source_catalog "customer_prod", source_schema "supply_chain".
Target catalog "my_catalog", warehouse_id "my_warehouse_id".
```

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
├── install_skill.py                # One-click installer for Genie Code
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
