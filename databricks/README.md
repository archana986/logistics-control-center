# Databricks Setup Scripts

This directory contains scripts for setting up and populating the Databricks data layer for the Logistics Control Center demo.

## Prerequisites

- Databricks workspace with Unity Catalog enabled
- SQL Warehouse (Pro or Serverless) available
- Databricks CLI configured or service principal authentication
- Python environment with `databricks-sdk` installed

## Setup Order

1. **Setup Catalog and Tables** (`setup_catalog.py`)
2. **Seed Initial Data** (`seed_data.py`)
3. **Generate Documents** (`generate_documents.py`)
4. **Set Up Agent Bricks** (see `setup_agents.md`)
5. **Start Stream Simulator** (`stream_simulator.py`)

## Scripts

### `setup_catalog.py`

Creates the Unity Catalog structure:
- Catalog: `logistics_demo`
- Schema: `network_ops`
- Volume: `documents` (for unstructured docs)
- 11 Delta tables for logistics data

**Usage:**
```bash
export DATABRICKS_SQL_WAREHOUSE_ID=<your-warehouse-id>
python databricks/setup_catalog.py
```

Or run in a Databricks notebook.

### `seed_data.py`

Loads initial data from `public/mock/*.json` files into Delta tables.

**Usage:**
```bash
export DATABRICKS_SQL_WAREHOUSE_ID=<your-warehouse-id>
python databricks/seed_data.py
```

Or run in a Databricks notebook.

### `generate_documents.py`

Generates unstructured markdown documents for Knowledge Assistant:
- Incident analysis reports
- Maintenance bulletins
- Operational procedures
- Customer SLA documents
- Route planning guides
- Root cause analysis reports

Documents are written to `logistics_demo.network_ops.documents` UC Volume.

**Usage:**
```bash
python databricks/generate_documents.py
```

Or run in a Databricks notebook.

### `stream_simulator.py`

Simulates real-time data streaming by continuously mutating Delta tables:
- Updates shipment ETAs
- Generates new incidents
- Drifts lane metrics
- Updates capacity data
- Creates agent activities
- Logs customer interactions

**Usage:**

As a Databricks Job (recommended):
1. Create a new Databricks Job
2. Add a Python task
3. Set the script path to `databricks/stream_simulator.py`
4. Set environment variable: `DATABRICKS_SQL_WAREHOUSE_ID=<warehouse-id>`
5. Set schedule to run every 30 seconds (or desired interval)
6. Or run continuously with a long timeout

As a standalone script:
```bash
export DATABRICKS_SQL_WAREHOUSE_ID=<your-warehouse-id>
export SIMULATOR_INTERVAL_SECONDS=30
python databricks/stream_simulator.py
```

Press Ctrl+C to stop.

## Configuration

All scripts use `config.py` for shared configuration:
- Catalog name: `logistics_demo`
- Schema name: `network_ops`
- Volume name: `documents`

Modify `config.py` if you need different names.

## Troubleshooting

### "Warehouse ID not set"
Set `DATABRICKS_SQL_WAREHOUSE_ID` environment variable.

### "Catalog already exists"
This is normal - the script will skip creation if it exists.

### "Permission denied"
Ensure your Databricks user/service principal has:
- `CREATE CATALOG` permission (for catalog creation)
- `USE CATALOG` and `CREATE SCHEMA` (for schema creation)
- `USE SCHEMA` and `CREATE TABLE` (for table creation)
- `USE VOLUME` and `WRITE VOLUME` (for document generation)

### "Table creation failed"
Check SQL Warehouse logs for detailed error messages. Common issues:
- Column type mismatches
- Reserved keyword usage
- Missing permissions

## Next Steps

After running these scripts:
1. Verify data in Delta tables using SQL queries
2. Set up Agent Bricks (Genie, Knowledge Assistant, Supervisor) - see `setup_agents.md`
3. Configure backend environment variables
4. Test the application
