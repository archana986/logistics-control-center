# Databricks notebook source
# MAGIC %md
# MAGIC # Setup Lakebase Autoscaling Postgres
# MAGIC 
# MAGIC Creates a Lakebase Autoscaling Postgres database project using the Databricks Python SDK.
# MAGIC 
# MAGIC Reference: [Databricks SDK Postgres API](https://databricks-sdk-py.readthedocs.io/en/latest/workspace/postgres/postgres.html)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

PROJECT_ID = "logistics-demo"
BRANCH_ID = "main"
ENDPOINT_ID = "primary"

PROJECT_DESCRIPTION = "Logistics Control Center Demo - Lakebase Postgres Database"
BRANCH_DESCRIPTION = "Main branch for logistics demo"
ENDPOINT_DESCRIPTION = "Primary compute endpoint for logistics demo"

# Autoscaling configuration
MIN_CU = 0.5  # Scale to zero
MAX_CU = 2.0

# COMMAND ----------

# MAGIC %md
# MAGIC ## Initialize Databricks Client

# COMMAND ----------

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.postgres import Project, Branch, Endpoint, AutoscalingLimit

w = WorkspaceClient()

print("✓ Databricks client initialized")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Project

# COMMAND ----------

import time

def wait_for_operation(operation_name: str, timeout_seconds: int = 300):
    """Wait for a long-running operation to complete."""
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        op = w.postgres.get_operation(operation_name)
        if op.done:
            if op.error:
                raise Exception(f"Operation failed: {op.error}")
            return op
        time.sleep(2)
    raise TimeoutError(f"Operation {operation_name} timed out after {timeout_seconds} seconds")

# Check if project already exists
project_name = f"projects/{PROJECT_ID}"
try:
    existing_project = w.postgres.get_project(project_name)
    print(f"✓ Project '{PROJECT_ID}' already exists: {existing_project.display_name}")
except Exception as e:
    # Project doesn't exist, create it
    print(f"Creating project '{PROJECT_ID}'...")
    project = Project(
        display_name=PROJECT_DESCRIPTION
    )
    
    create_op = w.postgres.create_project(project, PROJECT_ID)
    print(f"  Operation started: {create_op.name}")
    
    # Wait for operation to complete
    completed_op = wait_for_operation(create_op.name)
    print(f"✓ Project '{PROJECT_ID}' created successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Branch

# COMMAND ----------

branch_name = f"{project_name}/branches/{BRANCH_ID}"

try:
    existing_branch = w.postgres.get_branch(branch_name)
    print(f"✓ Branch '{BRANCH_ID}' already exists")
except Exception as e:
    # Branch doesn't exist, create it
    print(f"Creating branch '{BRANCH_ID}'...")
    branch = Branch(
        display_name=BRANCH_DESCRIPTION,
        # No expiry means permanent branch
    )
    
    create_op = w.postgres.create_branch(project_name, branch, BRANCH_ID)
    print(f"  Operation started: {create_op.name}")
    
    # Wait for operation to complete
    completed_op = wait_for_operation(create_op.name)
    print(f"✓ Branch '{BRANCH_ID}' created successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Compute Endpoint

# COMMAND ----------

endpoint_name = f"{branch_name}/endpoints/{ENDPOINT_ID}"

try:
    existing_endpoint = w.postgres.get_endpoint(endpoint_name)
    print(f"✓ Endpoint '{ENDPOINT_ID}' already exists")
    print(f"  Connection: {existing_endpoint.connection_string}")
except Exception as e:
    # Endpoint doesn't exist, create it
    print(f"Creating endpoint '{ENDPOINT_ID}'...")
    endpoint = Endpoint(
        display_name=ENDPOINT_DESCRIPTION,
        endpoint_type="ENDPOINT_TYPE_READ_WRITE",
        autoscaling_limit=AutoscalingLimit(
            min_cu=MIN_CU,
            max_cu=MAX_CU
        )
    )
    
    create_op = w.postgres.create_endpoint(branch_name, endpoint, ENDPOINT_ID)
    print(f"  Operation started: {create_op.name}")
    
    # Wait for operation to complete
    completed_op = wait_for_operation(create_op.name)
    print(f"✓ Endpoint '{ENDPOINT_ID}' created successfully")
    
    # Get the endpoint details to show connection info
    endpoint_details = w.postgres.get_endpoint(endpoint_name)
    print(f"\nConnection details:")
    print(f"  Connection string: {endpoint_details.connection_string}")
    if hasattr(endpoint_details, 'host') and endpoint_details.host:
        print(f"  Host: {endpoint_details.host}")
    if hasattr(endpoint_details, 'port') and endpoint_details.port:
        print(f"  Port: {endpoint_details.port}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Setup

# COMMAND ----------

# Get final endpoint details
endpoint_details = w.postgres.get_endpoint(endpoint_name)

print("✓ Lakebase setup complete!")
print(f"\nConfiguration:")
print(f"  Project: {PROJECT_ID}")
print(f"  Branch: {BRANCH_ID}")
print(f"  Endpoint: {ENDPOINT_ID}")
print(f"  Type: Read-Write")
print(f"  Autoscaling: {MIN_CU} - {MAX_CU} CU")
print(f"\nConnection:")
print(f"  {endpoint_details.connection_string}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Next Steps
# MAGIC 
# MAGIC The Lakebase Postgres database is now ready. You can:
# MAGIC 
# MAGIC 1. **Connect to the database** using the connection string shown above
# MAGIC 2. **Create tables** using standard PostgreSQL DDL
# MAGIC 3. **Query data** using SQL or your application's database driver
# MAGIC 
# MAGIC The endpoint will automatically scale based on workload (0.5 - 2.0 CU).
