# Databricks notebook source
# MAGIC %md
# MAGIC # Setup Lakebase Autoscaling Postgres
# MAGIC 
# MAGIC **Note:** The Databricks Python SDK does not currently expose the Lakebase Postgres API (`w.postgres`).
# MAGIC 
# MAGIC Please set up Lakebase Autoscaling Postgres manually using one of these methods:
# MAGIC 
# MAGIC ## Option 1: Using Databricks CLI
# MAGIC 
# MAGIC ```bash
# MAGIC # Create project
# MAGIC databricks postgres create-project logistics-demo \
# MAGIC   --description "Logistics Control Center Demo - Lakebase Postgres Database"
# MAGIC 
# MAGIC # Create branch (replace PROJECT_ID with actual project ID from above)
# MAGIC databricks postgres create-branch projects/PROJECT_ID main \
# MAGIC   --description "Main branch for logistics demo" \
# MAGIC   --no-expiry
# MAGIC 
# MAGIC # Create endpoint (replace PROJECT_ID with actual project ID)
# MAGIC databricks postgres create-endpoint projects/PROJECT_ID/branches/main primary \
# MAGIC   --endpoint-type ENDPOINT_TYPE_READ_WRITE \
# MAGIC   --autoscaling-limit-min-cu 0.5 \
# MAGIC   --autoscaling-limit-max-cu 2.0 \
# MAGIC   --description "Primary compute endpoint for logistics demo"
# MAGIC ```
# MAGIC 
# MAGIC ## Option 2: Using Databricks UI
# MAGIC 
# MAGIC 1. Navigate to **SQL** → **Lakebase** in the Databricks workspace
# MAGIC 2. Click **Create Project**
# MAGIC 3. Name: `logistics-demo`
# MAGIC 4. Create a branch named `main` (permanent, no expiry)
# MAGIC 5. Create a compute endpoint named `primary` with:
# MAGIC    - Type: Read-Write
# MAGIC    - Min CU: 0.5 (scale to zero)
# MAGIC    - Max CU: 2.0
# MAGIC 
# MAGIC ## Configuration Values
# MAGIC 
# MAGIC - **Project Name:** `logistics-demo`
# MAGIC - **Branch Name:** `main`
# MAGIC - **Endpoint Name:** `primary`
# MAGIC - **Endpoint Type:** Read-Write
# MAGIC - **Autoscaling:** Min 0.5 CU, Max 2.0 CU

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Setup
# MAGIC 
# MAGIC After creating the Lakebase instance manually, verify it exists:

# COMMAND ----------

# This cell will check if Lakebase is accessible (once SDK support is available)
# For now, manually verify in the UI or via CLI

print("Please verify Lakebase setup manually:")
print("  - Project: logistics-demo")
print("  - Branch: main")
print("  - Endpoint: primary")
print("\nOnce created, note the connection details (host, port) for your application configuration.")
