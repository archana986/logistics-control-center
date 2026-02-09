"""Create Unity Catalog catalog, schema, and tables for logistics demo.

Run this script in a Databricks notebook or as a job to set up the data layer.
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import CreateCatalog, CreateSchema, CreateVolume
from databricks import config

def setup_catalog_and_schema(client: WorkspaceClient):
    """Create catalog and schema if they don't exist."""
    try:
        # Create catalog
        client.catalogs.create(
            CreateCatalog(
                name=config.CATALOG,
                comment="Logistics Network Operations Demo Catalog"
            )
        )
        print(f"✓ Created catalog: {config.CATALOG}")
    except Exception as e:
        if "already exists" in str(e).lower() or "ALREADY_EXISTS" in str(e):
            print(f"✓ Catalog {config.CATALOG} already exists")
        else:
            raise
    
    try:
        # Create schema
        client.schemas.create(
            CreateSchema(
                name=config.SCHEMA,
                catalog_name=config.CATALOG,
                comment="Network operations data schema"
            )
        )
        print(f"✓ Created schema: {config.CATALOG}.{config.SCHEMA}")
    except Exception as e:
        if "already exists" in str(e).lower() or "ALREADY_EXISTS" in str(e):
            print(f"✓ Schema {config.CATALOG}.{config.SCHEMA} already exists")
        else:
            raise

def setup_volume(client: WorkspaceClient):
    """Create UC Volume for unstructured documents."""
    try:
        client.volumes.create(
            CreateVolume(
                name=config.VOLUME,
                catalog_name=config.CATALOG,
                schema_name=config.SCHEMA,
                volume_type="MANAGED",
                comment="Unstructured documents for Knowledge Assistant"
            )
        )
        print(f"✓ Created volume: {config.VOLUME_PATH}")
    except Exception as e:
        if "already exists" in str(e).lower() or "ALREADY_EXISTS" in str(e):
            print(f"✓ Volume {config.VOLUME_PATH} already exists")
        else:
            raise

def setup_tables(client: WorkspaceClient, warehouse_id: str):
    """Create all Delta tables."""
    from databricks.sdk.service.sql import StatementState
    
    # DDL statements for all tables
    ddl_statements = [
        # Centers table
        f"""
        CREATE TABLE IF NOT EXISTS {config.TABLE_NAMES['centers']} (
            id STRING NOT NULL,
            name STRING NOT NULL,
            lat DOUBLE NOT NULL,
            lng DOUBLE NOT NULL,
            type STRING NOT NULL,
            updated_at TIMESTAMP DEFAULT current_timestamp()
        )
        USING DELTA
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        """,
        
        # Lanes table
        f"""
        CREATE TABLE IF NOT EXISTS {config.TABLE_NAMES['lanes']} (
            id STRING NOT NULL,
            origin STRING NOT NULL,
            dest STRING NOT NULL,
            mode STRING NOT NULL,
            avgDailyVolume INT,
            onTimePct DOUBLE,
            delayMinutes INT,
            slaRiskPct DOUBLE,
            updated_at TIMESTAMP DEFAULT current_timestamp()
        )
        USING DELTA
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        """,
        
        # Incidents table
        f"""
        CREATE TABLE IF NOT EXISTS {config.TABLE_NAMES['incidents']} (
            id STRING NOT NULL,
            laneId STRING NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            type STRING NOT NULL,
            ref STRING,
            cause STRING,
            impactMinutes INT,
            impactThroughputPct DOUBLE,
            confidence DOUBLE,
            active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT current_timestamp()
        )
        USING DELTA
        PARTITIONED BY (active)
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        """,
        
        # Shipments table
        f"""
        CREATE TABLE IF NOT EXISTS {config.TABLE_NAMES['shipments']} (
            trackingId STRING NOT NULL,
            customerId STRING NOT NULL,
            priority STRING NOT NULL,
            laneId STRING NOT NULL,
            promisedETA TIMESTAMP,
            currentETA TIMESTAMP,
            packageCount INT,
            status STRING DEFAULT 'in_transit',
            updated_at TIMESTAMP DEFAULT current_timestamp()
        )
        USING DELTA
        PARTITIONED BY (status)
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        """,
        
        # Reroute solutions table
        f"""
        CREATE TABLE IF NOT EXISTS {config.TABLE_NAMES['reroute_solutions']} (
            laneId STRING NOT NULL,
            strategy STRING NOT NULL,
            deltaETAminutes INT NOT NULL,
            addedCostUSD DOUBLE NOT NULL,
            capacityUsedPct DOUBLE NOT NULL,
            notes STRING,
            created_at TIMESTAMP DEFAULT current_timestamp(),
            PRIMARY KEY (laneId, strategy)
        )
        USING DELTA
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        """,
        
        # Customers table
        f"""
        CREATE TABLE IF NOT EXISTS {config.TABLE_NAMES['customers']} (
            id STRING NOT NULL PRIMARY KEY,
            name STRING NOT NULL,
            contact STRING,
            tier STRING,
            preferredCommunication STRING,
            updated_at TIMESTAMP DEFAULT current_timestamp()
        )
        USING DELTA
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        """,
        
        # Customer interactions table
        f"""
        CREATE TABLE IF NOT EXISTS {config.TABLE_NAMES['customer_interactions']} (
            id STRING NOT NULL,
            customerId STRING NOT NULL,
            date TIMESTAMP NOT NULL,
            type STRING NOT NULL,
            summary STRING,
            sentiment STRING,
            tags ARRAY<STRING>,
            created_at TIMESTAMP DEFAULT current_timestamp()
        )
        USING DELTA
        PARTITIONED BY (customerId)
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        """,
        
        # Capacity lanes table
        f"""
        CREATE TABLE IF NOT EXISTS {config.TABLE_NAMES['capacity_lanes']} (
            id STRING NOT NULL PRIMARY KEY,
            origin STRING NOT NULL,
            dest STRING NOT NULL,
            mode STRING NOT NULL,
            avgDailyVolume INT,
            onTimePct DOUBLE,
            delayMinutes INT,
            slaRiskPct DOUBLE,
            maxCapacity INT NOT NULL,
            utilizationPct DOUBLE NOT NULL,
            availableCapacity INT NOT NULL,
            optimalUtilization DOUBLE,
            updated_at TIMESTAMP DEFAULT current_timestamp()
        )
        USING DELTA
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        """,
        
        # Capacity actions table
        f"""
        CREATE TABLE IF NOT EXISTS {config.TABLE_NAMES['capacity_actions']} (
            id STRING NOT NULL,
            laneId STRING NOT NULL,
            type STRING NOT NULL,
            volumeChange INT NOT NULL,
            npsImpact INT NOT NULL,
            costImpact DOUBLE NOT NULL,
            efficiencyImpact DOUBLE NOT NULL,
            notes STRING,
            created_at TIMESTAMP DEFAULT current_timestamp(),
            PRIMARY KEY (id)
        )
        USING DELTA
        PARTITIONED BY (laneId)
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        """,
        
        # Agent activities table
        f"""
        CREATE TABLE IF NOT EXISTS {config.TABLE_NAMES['agent_activities']} (
            id STRING NOT NULL PRIMARY KEY,
            laneId STRING NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            agentType STRING NOT NULL,
            situation STRING,
            action STRING,
            result STRING,
            status STRING NOT NULL,
            metadata STRING,  -- JSON string
            created_at TIMESTAMP DEFAULT current_timestamp()
        )
        USING DELTA
        PARTITIONED BY (agentType)
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        """,
        
        # Sales opportunities table
        f"""
        CREATE TABLE IF NOT EXISTS {config.TABLE_NAMES['sales_opportunities']} (
            laneId STRING NOT NULL,
            activityId STRING NOT NULL,
            availableCapacity INT NOT NULL,
            forecastDate DATE NOT NULL,
            targetCustomers ARRAY<STRUCT<id: STRING, name: STRING, reason: STRING>>,
            pricing STRUCT<historical: DOUBLE, recommended: DOUBLE, discount: DOUBLE>,
            projectedImpact STRUCT<revenue: DOUBLE, utilizationBefore: DOUBLE, utilizationAfter: DOUBLE, margin: DOUBLE>,
            created_at TIMESTAMP DEFAULT current_timestamp(),
            PRIMARY KEY (laneId, activityId)
        )
        USING DELTA
        TBLPROPERTIES (
            'delta.autoOptimize.optimizeWrite' = 'true',
            'delta.autoOptimize.autoCompact' = 'true'
        )
        """,
    ]
    
    # Execute DDL statements
    for i, ddl in enumerate(ddl_statements, 1):
        try:
            execution = client.statement_execution.execute_statement(
                warehouse_id=warehouse_id,
                statement=ddl.strip(),
                wait_timeout="30s"
            )
            
            if execution.status.state == StatementState.SUCCEEDED:
                table_name = list(config.TABLE_NAMES.values())[i-1]
                print(f"✓ Created table: {table_name}")
            else:
                print(f"⚠ Warning: Table creation may have failed: {execution.status.state}")
        except Exception as e:
            print(f"⚠ Error creating table {i}: {e}")
            # Continue with next table

def main():
    """Main setup function."""
    import os
    
    client = WorkspaceClient()
    warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")
    
    if not warehouse_id:
        raise ValueError("DATABRICKS_SQL_WAREHOUSE_ID environment variable must be set")
    
    print("Setting up Unity Catalog structure...")
    setup_catalog_and_schema(client)
    setup_volume(client)
    setup_tables(client, warehouse_id)
    print("\n✓ Setup complete!")

if __name__ == "__main__":
    main()
