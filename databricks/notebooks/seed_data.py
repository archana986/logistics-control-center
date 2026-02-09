# Databricks notebook source
# MAGIC %md
# MAGIC # Seed Delta Tables from Mock JSON Data
# MAGIC
# MAGIC Loads the curated demo data from `public/mock/*.json` into Delta tables.
# MAGIC This ensures the deployed app matches the demo narrative exactly.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import json
import os

CATALOG = "demos"
SCHEMA = "logistics_control_center"

TABLE_NAMES = {
    "centers": f"{CATALOG}.{SCHEMA}.centers",
    "lanes": f"{CATALOG}.{SCHEMA}.lanes",
    "incidents": f"{CATALOG}.{SCHEMA}.incidents",
    "shipments": f"{CATALOG}.{SCHEMA}.shipments",
    "reroute_solutions": f"{CATALOG}.{SCHEMA}.reroute_solutions",
}

# The bundle uploads the repo to workspace — find the mock data relative to this notebook
# Notebook path: {root}/databricks/notebooks/seed_data  (3 levels below root)
# Mock data at:  {root}/public/mock/*.json
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
# Go up 3 levels: seed_data -> notebooks -> databricks -> root
workspace_root = "/".join(notebook_path.split("/")[:-3])
mock_dir = f"{workspace_root}/public/mock"

print(f"Notebook: {notebook_path}")
print(f"Workspace root: {workspace_root}")
print(f"Mock data dir: {mock_dir}")

# Verify the mock dir exists
try:
    files = dbutils.fs.ls(f"file:/Workspace{mock_dir}")
    print(f"Files in mock dir: {[f.name for f in files]}")
except Exception as e:
    print(f"WARNING: Could not list mock dir: {e}")
    # Try to find files by listing workspace
    try:
        import subprocess
        result = subprocess.run(["find", f"/Workspace{workspace_root}", "-name", "*.json", "-path", "*/mock/*"], capture_output=True, text=True, timeout=10)
        print(f"Found JSON files: {result.stdout}")
    except Exception as e2:
        print(f"Also failed to search: {e2}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Helper: Load JSON from Workspace

# COMMAND ----------

def load_mock_json(filename):
    """Load a JSON file from the workspace mock directory."""
    # Try several path strategies
    paths_to_try = [
        f"/Workspace{mock_dir}/{filename}",
        f"/Workspace{notebook_path.rsplit('/', 3)[0]}/public/mock/{filename}",
    ]

    for path in paths_to_try:
        try:
            with open(path, "r") as f:
                data = json.load(f)
            print(f"  ✓ Loaded {len(data)} records from {filename} (path: {path})")
            return data
        except Exception as e:
            print(f"  ✗ {path}: {e}")

    # Fallback: try dbutils.fs
    for path in paths_to_try:
        try:
            ws_path = path.replace("/Workspace", "")
            content = dbutils.fs.head(f"file:{path}", 1024 * 1024)
            data = json.loads(content)
            print(f"  ✓ Loaded {len(data)} records from {filename} (dbutils: {path})")
            return data
        except Exception as e:
            print(f"  ✗ dbutils {path}: {e}")

    print(f"  ✗✗ FAILED to load {filename} from any path")
    return []


def write_to_table(data, table_name, schema_hint=None):
    """Write list-of-dicts to a Delta table using INSERT OVERWRITE."""
    if not data:
        print(f"  ⚠ No data for {table_name}, skipping")
        return

    df = spark.createDataFrame(data, schema=schema_hint)
    # Use overwriteSchema to handle any column mismatches
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(table_name)
    print(f"  ✓ Wrote {len(data)} rows to {table_name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Seed Centers

# COMMAND ----------

print("Loading centers...")
centers = load_mock_json("centers.json")
write_to_table(centers, TABLE_NAMES["centers"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Seed Lanes

# COMMAND ----------

print("Loading lanes...")
lanes = load_mock_json("lanes.json")
write_to_table(lanes, TABLE_NAMES["lanes"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Seed Incidents

# COMMAND ----------

print("Loading incidents...")
incidents_raw = load_mock_json("incidents.json")

# Add required fields that mock JSON doesn't have
for i, inc in enumerate(incidents_raw):
    if "id" not in inc:
        inc["id"] = f"INC-{str(i+1).zfill(6)}"
    if "active" not in inc:
        inc["active"] = True
    # Ensure numeric types
    if "impactMinutes" in inc and inc["impactMinutes"] is not None:
        inc["impactMinutes"] = int(inc["impactMinutes"])
    if "impactThroughputPct" in inc and inc["impactThroughputPct"] is not None:
        inc["impactThroughputPct"] = float(inc["impactThroughputPct"])
    if "confidence" in inc and inc["confidence"] is not None:
        inc["confidence"] = float(inc["confidence"])

write_to_table(incidents_raw, TABLE_NAMES["incidents"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Seed Shipments

# COMMAND ----------

print("Loading shipments...")
shipments_raw = load_mock_json("shipments.json")

# Add required fields
for s in shipments_raw:
    if "status" not in s:
        s["status"] = "in_transit"
    if "packageCount" in s and s["packageCount"] is not None:
        s["packageCount"] = int(s["packageCount"])

write_to_table(shipments_raw, TABLE_NAMES["shipments"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Seed Reroute Solutions

# COMMAND ----------

print("Loading reroute solutions...")
reroutes = load_mock_json("reroute_solutions.json")
write_to_table(reroutes, TABLE_NAMES["reroute_solutions"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verification

# COMMAND ----------

print("\n=== Table Row Counts ===")
for name, table in TABLE_NAMES.items():
    try:
        count = spark.sql(f"SELECT COUNT(*) FROM {table}").collect()[0][0]
        print(f"  {table}: {count} rows")
    except Exception as e:
        print(f"  {table}: ERROR - {e}")

# Verify the key narrative data
print("\n=== Narrative Verification ===")
bna_stl_air_incidents = spark.sql(f"""
    SELECT id, ref, type, cause, impactMinutes 
    FROM {TABLE_NAMES['incidents']} 
    WHERE laneId = 'BNA-STL-AIR'
    ORDER BY timestamp
""").collect()
print(f"BNA-STL-AIR incidents: {len(bna_stl_air_incidents)}")
for row in bna_stl_air_incidents:
    print(f"  {row.ref}: {row.type} - {row.cause} ({row.impactMinutes}m)")

bna_stl_air_shipments = spark.sql(f"""
    SELECT trackingId, customerId, priority, packageCount 
    FROM {TABLE_NAMES['shipments']} 
    WHERE laneId = 'BNA-STL-AIR'
""").collect()
print(f"BNA-STL-AIR shipments: {len(bna_stl_air_shipments)}")
for row in bna_stl_air_shipments:
    print(f"  {row.trackingId}: {row.customerId} ({row.priority}) - {row.packageCount} packages")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done
# MAGIC
# MAGIC All demo narrative data has been loaded into Delta tables.
# MAGIC The deployed app should now show the same data as the local mock JSON.

# COMMAND ----------

print("\n✓ Seed data complete — demo narrative is ready!")
