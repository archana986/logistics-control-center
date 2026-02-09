"""Seed Delta tables with initial data from mock JSON files.

This script reads existing JSON files from public/mock/ and writes them to Delta tables.
For missing JSON files, it generates realistic sample data based on the TypeScript types.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from databricks import config


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSON file and return list of records."""
    if not file_path.exists():
        return []
    with open(file_path, 'r') as f:
        return json.load(f)


def generate_customers() -> List[Dict[str, Any]]:
    """Generate customer data based on shipments."""
    return [
        {
            "id": "walmart-supply",
            "name": "Walmart Supply Chain",
            "contact": "logistics@walmart.com",
            "tier": "platinum",
            "preferredCommunication": "email"
        },
        {
            "id": "techcorp-industries",
            "name": "TechCorp Industries",
            "contact": "shipping@techcorp.com",
            "tier": "gold",
            "preferredCommunication": "both"
        },
        {
            "id": "amazon-logistics",
            "name": "Amazon Logistics",
            "contact": "ops@amazon.com",
            "tier": "platinum",
            "preferredCommunication": "email"
        },
        {
            "id": "target-distribution",
            "name": "Target Distribution",
            "contact": "logistics@target.com",
            "tier": "gold",
            "preferredCommunication": "phone"
        },
        {
            "id": "bestbuy-logistics",
            "name": "Best Buy Logistics",
            "contact": "shipping@bestbuy.com",
            "tier": "silver",
            "preferredCommunication": "email"
        },
        {
            "id": "WALMART",
            "name": "Walmart",
            "contact": "logistics@walmart.com",
            "tier": "platinum",
            "preferredCommunication": "email"
        },
        {
            "id": "AMAZON",
            "name": "Amazon",
            "contact": "ops@amazon.com",
            "tier": "platinum",
            "preferredCommunication": "email"
        },
        {
            "id": "TARGET",
            "name": "Target",
            "contact": "logistics@target.com",
            "tier": "gold",
            "preferredCommunication": "phone"
        },
    ]


def generate_customer_interactions() -> List[Dict[str, Any]]:
    """Generate customer interaction history."""
    interactions = []
    customer_ids = ["walmart-supply", "techcorp-industries", "amazon-logistics", "target-distribution"]
    
    base_date = datetime.now() - timedelta(days=90)
    
    for customer_id in customer_ids:
        # Email interactions
        for i in range(3):
            interactions.append({
                "id": str(uuid.uuid4()),
                "customerId": customer_id,
                "date": (base_date + timedelta(days=i*10)).isoformat() + "Z",
                "type": "email",
                "summary": f"Proactive alert about lane disruption - customer acknowledged",
                "sentiment": "positive" if i % 2 == 0 else "neutral",
                "tags": ["proactive-communication"] if i == 0 else []
            })
        
        # Call interactions
        for i in range(2):
            interactions.append({
                "id": str(uuid.uuid4()),
                "customerId": customer_id,
                "date": (base_date + timedelta(days=i*15 + 5)).isoformat() + "Z",
                "type": "call",
                "summary": f"Follow-up call regarding service quality",
                "sentiment": "positive",
                "tags": ["phone-preferred"] if customer_id == "target-distribution" else []
            })
    
    return interactions


def generate_capacity_lanes(lanes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate capacity lane data from regular lanes."""
    capacity_lanes = []
    
    for lane in lanes:
        max_capacity = int(lane.get("avgDailyVolume", 100000) * 1.5)
        utilization = lane.get("onTimePct", 0.85)  # Use onTimePct as base for utilization
        available_capacity = int(max_capacity * (1 - utilization))
        
        capacity_lanes.append({
            **lane,
            "maxCapacity": max_capacity,
            "utilizationPct": utilization,
            "availableCapacity": max(0, available_capacity),
            "optimalUtilization": 0.85
        })
    
    return capacity_lanes


def generate_capacity_actions() -> Dict[str, List[Dict[str, Any]]]:
    """Generate capacity actions by lane."""
    actions = {
        "BNA-STL-AIR": [
            {
                "id": str(uuid.uuid4()),
                "laneId": "BNA-STL-AIR",
                "type": "pull_forward",
                "volumeChange": 5000,
                "npsImpact": 5,
                "costImpact": 15000.0,
                "efficiencyImpact": 0.08,
                "notes": "Pull forward urgent shipments to improve customer satisfaction"
            }
        ],
        "BNA-ORD-AIR": [
            {
                "id": str(uuid.uuid4()),
                "laneId": "BNA-ORD-AIR",
                "type": "hold_back",
                "volumeChange": -3000,
                "npsImpact": -2,
                "costImpact": -8000.0,
                "efficiencyImpact": -0.05,
                "notes": "Hold back non-urgent shipments to reduce congestion"
            }
        ]
    }
    return actions


def generate_agent_activities() -> List[Dict[str, Any]]:
    """Generate agent activity records."""
    activities = []
    base_time = datetime.now() - timedelta(hours=2)
    
    agent_types = ["capacity", "pricing", "sales"]
    lanes = ["BNA-STL-AIR", "BNA-ORD-AIR", "ORD-ATL-AIR"]
    
    for i, lane_id in enumerate(lanes):
        agent_type = agent_types[i % len(agent_types)]
        activities.append({
            "id": str(uuid.uuid4()),
            "laneId": lane_id,
            "timestamp": (base_time + timedelta(minutes=i*30)).isoformat() + "Z",
            "agentType": agent_type,
            "situation": f"Detected capacity constraint on {lane_id}",
            "action": f"{agent_type.title()} agent recommended optimization",
            "result": "Action approved and implemented",
            "status": "completed",
            "metadata": json.dumps({
                "customerId": "walmart-supply" if i == 0 else None,
                "volumeChange": 5000 if agent_type == "capacity" else None
            })
        })
    
    return activities


def generate_sales_opportunities() -> List[Dict[str, Any]]:
    """Generate sales opportunities."""
    opportunities = []
    base_date = datetime.now() + timedelta(days=7)
    
    opportunities.append({
        "laneId": "BNA-STL-AIR",
        "activityId": str(uuid.uuid4()),
        "availableCapacity": 15000,
        "forecastDate": base_date.date().isoformat(),
        "targetCustomers": [
            {"id": "walmart-supply", "name": "Walmart Supply Chain", "reason": "High volume customer with capacity needs"}
        ],
        "pricing": {
            "historical": 2.50,
            "recommended": 2.75,
            "discount": 0.10
        },
        "projectedImpact": {
            "revenue": 45000.0,
            "utilizationBefore": 0.75,
            "utilizationAfter": 0.88,
            "margin": 0.22
        }
    })
    
    return opportunities


def insert_data(client: WorkspaceClient, warehouse_id: str, table_name: str, data: List[Dict[str, Any]]):
    """Insert data into Delta table using SQL."""
    if not data:
        print(f"  ⚠ No data to insert for {table_name}")
        return
    
    # Convert data to JSON for SQL insertion
    data_json = json.dumps(data).replace("'", "''")  # Escape single quotes
    
    # Use MERGE or INSERT based on table structure
    if "PRIMARY KEY" in table_name or table_name.endswith("centers") or table_name.endswith("customers"):
        # Use MERGE for tables with primary keys
        columns = list(data[0].keys())
        columns_str = ", ".join(columns)
        
        # Build VALUES clause
        values_clauses = []
        for row in data:
            values = []
            for col in columns:
                val = row.get(col)
                if val is None:
                    values.append("NULL")
                elif isinstance(val, (dict, list)):
                    values.append(f"'{json.dumps(val).replace(chr(39), chr(39)+chr(39))}'")
                elif isinstance(val, str):
                    values.append(f"'{val.replace(chr(39), chr(39)+chr(39))}'")
                elif isinstance(val, bool):
                    values.append("TRUE" if val else "FALSE")
                else:
                    values.append(str(val))
            values_clauses.append(f"({', '.join(values)})")
        
        sql = f"""
        MERGE INTO {table_name} AS target
        USING (VALUES {', '.join(values_clauses)}) AS source ({columns_str})
        ON target.id = source.id
        WHEN MATCHED THEN UPDATE SET *
        WHEN NOT MATCHED THEN INSERT *
        """
    else:
        # Use INSERT OVERWRITE for append-only tables
        columns = list(data[0].keys())
        columns_str = ", ".join(columns)
        
        values_clauses = []
        for row in data:
            values = []
            for col in columns:
                val = row.get(col)
                if val is None:
                    values.append("NULL")
                elif isinstance(val, (dict, list)):
                    values.append(f"'{json.dumps(val).replace(chr(39), chr(39)+chr(39))}'")
                elif isinstance(val, str):
                    # Handle timestamp strings
                    if "T" in val and "Z" in val:
                        values.append(f"CAST('{val}' AS TIMESTAMP)")
                    else:
                        values.append(f"'{val.replace(chr(39), chr(39)+chr(39))}'")
                elif isinstance(val, bool):
                    values.append("TRUE" if val else "FALSE")
                else:
                    values.append(str(val))
            values_clauses.append(f"({', '.join(values)})")
        
        sql = f"""
        INSERT INTO {table_name} ({columns_str})
        VALUES {', '.join(values_clauses)}
        """
    
    try:
        execution = client.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            statement=sql,
            wait_timeout="60s"
        )
        
        if execution.status.state == StatementState.SUCCEEDED:
            print(f"  ✓ Inserted {len(data)} rows into {table_name}")
        else:
            print(f"  ⚠ Warning: Insert may have failed: {execution.status.state}")
            if execution.status.state == StatementState.FAILED:
                print(f"    Error: {execution.status.error}")
    except Exception as e:
        print(f"  ✗ Error inserting into {table_name}: {e}")
        # Try alternative approach: write as DataFrame
        print(f"    Attempting DataFrame write...")
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            # This would require Spark session - skip for now
            print(f"    DataFrame approach requires Spark session - skipping")
        except:
            pass


def seed_all_tables(client: WorkspaceClient, warehouse_id: str, project_root: Path):
    """Seed all tables with data."""
    mock_dir = project_root / "public" / "mock"
    
    print("Loading data from JSON files...")
    
    # Load existing JSON files
    centers = load_json_file(mock_dir / "centers.json")
    lanes = load_json_file(mock_dir / "lanes.json")
    incidents = load_json_file(mock_dir / "incidents.json")
    shipments = load_json_file(mock_dir / "shipments.json")
    reroute_solutions = load_json_file(mock_dir / "reroute_solutions.json")
    
    # Generate missing data
    print("Generating missing data...")
    customers = generate_customers()
    customer_interactions = generate_customer_interactions()
    capacity_lanes = generate_capacity_lanes(lanes)
    capacity_actions_dict = generate_capacity_actions()
    agent_activities = generate_agent_activities()
    sales_opportunities = generate_sales_opportunities()
    
    # Add IDs to incidents (they don't have IDs in JSON)
    for i, incident in enumerate(incidents):
        if "id" not in incident:
            incident["id"] = f"INC-{i+1:04d}"
    
    print("\nSeeding tables...")
    
    # Seed each table
    insert_data(client, warehouse_id, config.TABLE_NAMES["centers"], centers)
    insert_data(client, warehouse_id, config.TABLE_NAMES["lanes"], lanes)
    insert_data(client, warehouse_id, config.TABLE_NAMES["incidents"], incidents)
    insert_data(client, warehouse_id, config.TABLE_NAMES["shipments"], shipments)
    insert_data(client, warehouse_id, config.TABLE_NAMES["reroute_solutions"], reroute_solutions)
    insert_data(client, warehouse_id, config.TABLE_NAMES["customers"], customers)
    insert_data(client, warehouse_id, config.TABLE_NAMES["customer_interactions"], customer_interactions)
    insert_data(client, warehouse_id, config.TABLE_NAMES["capacity_lanes"], capacity_lanes)
    
    # Capacity actions need special handling (nested by laneId)
    all_capacity_actions = []
    for lane_id, actions in capacity_actions_dict.items():
        all_capacity_actions.extend(actions)
    insert_data(client, warehouse_id, config.TABLE_NAMES["capacity_actions"], all_capacity_actions)
    
    insert_data(client, warehouse_id, config.TABLE_NAMES["agent_activities"], agent_activities)
    insert_data(client, warehouse_id, config.TABLE_NAMES["sales_opportunities"], sales_opportunities)
    
    print("\n✓ Seeding complete!")


def main():
    """Main seed function."""
    import sys
    
    client = WorkspaceClient()
    warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")
    
    if not warehouse_id:
        raise ValueError("DATABRICKS_SQL_WAREHOUSE_ID environment variable must be set")
    
    # Determine project root (assume script is in databricks/ subdirectory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"Project root: {project_root}")
    print(f"Warehouse ID: {warehouse_id}")
    print(f"Catalog: {config.CATALOG}")
    print(f"Schema: {config.SCHEMA}\n")
    
    seed_all_tables(client, warehouse_id, project_root)


if __name__ == "__main__":
    main()
