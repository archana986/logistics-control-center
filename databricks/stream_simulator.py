"""Real-time data streaming simulator for logistics demo.

This script runs continuously and simulates real-time data mutations:
- Shipment ETA updates
- New incident generation
- Lane metric drift
- Capacity updates
- Agent activities
- Customer interactions

Run this as a Databricks Job with a schedule (e.g., every 30 seconds) or as a
long-running notebook.
"""

import json
import os
import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from databricks import config


class StreamSimulator:
    """Simulates real-time data streaming for logistics operations."""
    
    def __init__(self, client: WorkspaceClient, warehouse_id: str):
        self.client = client
        self.warehouse_id = warehouse_id
        self.cycle_count = 0
        
    def execute_sql(self, sql: str) -> bool:
        """Execute SQL statement and return success status."""
        try:
            execution = self.client.statement_execution.execute_statement(
                warehouse_id=self.warehouse_id,
                statement=sql,
                wait_timeout="30s"
            )
            return execution.status.state == StatementState.SUCCEEDED
        except Exception as e:
            print(f"  ✗ SQL execution error: {e}")
            return False
    
    def update_shipment_etas(self):
        """Randomly adjust shipment ETAs and mark some as delivered."""
        print("  Updating shipment ETAs...")
        
        # Get in-transit shipments
        sql = f"""
        SELECT trackingId, currentETA, promisedETA
        FROM {config.TABLE_NAMES['shipments']}
        WHERE status = 'in_transit'
        LIMIT 20
        """
        
        try:
            execution = self.client.statement_execution.execute_statement(
                warehouse_id=self.warehouse_id,
                statement=sql,
                wait_timeout="30s"
            )
            
            if execution.status.state == StatementState.SUCCEEDED:
                results = execution.result.data_array
                updated = 0
                delivered = 0
                
                for row in results[:5]:  # Update up to 5 shipments per cycle
                    tracking_id = row[0]
                    current_eta_str = row[1]
                    
                    if not current_eta_str:
                        continue
                    
                    # Parse timestamp and adjust by +/- 5-15 minutes
                    try:
                        current_eta = datetime.fromisoformat(current_eta_str.replace('Z', '+00:00'))
                        delta_minutes = random.randint(-15, 15)
                        new_eta = current_eta + timedelta(minutes=delta_minutes)
                        
                        # Occasionally mark as delivered (10% chance)
                        if random.random() < 0.1:
                            update_sql = f"""
                            UPDATE {config.TABLE_NAMES['shipments']}
                            SET status = 'delivered', 
                                currentETA = current_timestamp(),
                                updated_at = current_timestamp()
                            WHERE trackingId = '{tracking_id}'
                            """
                            delivered += 1
                        else:
                            update_sql = f"""
                            UPDATE {config.TABLE_NAMES['shipments']}
                            SET currentETA = CAST('{new_eta.isoformat()}' AS TIMESTAMP),
                                updated_at = current_timestamp()
                            WHERE trackingId = '{tracking_id}'
                            """
                            updated += 1
                        
                        self.execute_sql(update_sql)
                    except Exception as e:
                        print(f"    Error updating shipment {tracking_id}: {e}")
                
                if updated > 0 or delivered > 0:
                    print(f"    ✓ Updated {updated} shipments, delivered {delivered}")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    def generate_new_incidents(self):
        """Randomly generate new incidents."""
        print("  Generating new incidents...")
        
        # Get active lanes
        sql = f"""
        SELECT DISTINCT id FROM {config.TABLE_NAMES['lanes']}
        ORDER BY RANDOM()
        LIMIT 5
        """
        
        try:
            execution = self.client.statement_execution.execute_statement(
                warehouse_id=self.warehouse_id,
                statement=sql,
                wait_timeout="30s"
            )
            
            if execution.status.state == StatementState.SUCCEEDED and random.random() < 0.3:  # 30% chance
                results = execution.result.data_array
                if results:
                    lane_id = results[0][0]
                    
                    incident_types = [
                        "weather", "traffic_congestion", "equipment_issue",
                        "highway_delay", "air_traffic_control"
                    ]
                    incident_type = random.choice(incident_types)
                    
                    causes = {
                        "weather": "Thunderstorms affecting route",
                        "traffic_congestion": "Heavy traffic on major highway",
                        "equipment_issue": "Vehicle maintenance required",
                        "highway_delay": "Construction delay on route",
                        "air_traffic_control": "ATC hold at destination airport"
                    }
                    
                    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
                    ref = f"FX{random.randint(100, 999)}" if incident_type.startswith("air") else f"TRK-{random.randint(1000, 9999)}"
                    
                    impact_minutes = random.randint(30, 120)
                    confidence = round(random.uniform(0.75, 0.95), 2)
                    
                    insert_sql = f"""
                    INSERT INTO {config.TABLE_NAMES['incidents']}
                    (id, laneId, timestamp, type, ref, cause, impactMinutes, confidence, active)
                    VALUES (
                        '{incident_id}',
                        '{lane_id}',
                        current_timestamp(),
                        '{incident_type}',
                        '{ref}',
                        '{causes[incident_type]}',
                        {impact_minutes},
                        {confidence},
                        true
                    )
                    """
                    
                    if self.execute_sql(insert_sql):
                        print(f"    ✓ Created incident {incident_id} on {lane_id}")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    def resolve_incidents(self):
        """Randomly resolve some active incidents."""
        print("  Resolving incidents...")
        
        sql = f"""
        SELECT id FROM {config.TABLE_NAMES['incidents']}
        WHERE active = true
        ORDER BY RANDOM()
        LIMIT 3
        """
        
        try:
            execution = self.client.statement_execution.execute_statement(
                warehouse_id=self.warehouse_id,
                statement=sql,
                wait_timeout="30s"
            )
            
            if execution.status.state == StatementState.SUCCEEDED:
                results = execution.result.data_array
                resolved = 0
                
                for row in results:
                    if random.random() < 0.2:  # 20% chance to resolve
                        incident_id = row[0]
                        update_sql = f"""
                        UPDATE {config.TABLE_NAMES['incidents']}
                        SET active = false, updated_at = current_timestamp()
                        WHERE id = '{incident_id}'
                        """
                        
                        if self.execute_sql(update_sql):
                            resolved += 1
                
                if resolved > 0:
                    print(f"    ✓ Resolved {resolved} incidents")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    def drift_lane_metrics(self):
        """Apply small random changes to lane metrics."""
        print("  Drifting lane metrics...")
        
        # Get lanes to update
        sql = f"""
        SELECT id, delayMinutes, onTimePct, slaRiskPct, avgDailyVolume
        FROM {config.TABLE_NAMES['lanes']}
        ORDER BY RANDOM()
        LIMIT 10
        """
        
        try:
            execution = self.client.statement_execution.execute_statement(
                warehouse_id=self.warehouse_id,
                statement=sql,
                wait_timeout="30s"
            )
            
            if execution.status.state == StatementState.SUCCEEDED:
                results = execution.result.data_array
                updated = 0
                
                for row in results[:5]:  # Update up to 5 lanes
                    lane_id = row[0]
                    current_delay = int(row[1]) if row[1] else 0
                    current_on_time = float(row[2]) if row[2] else 0.90
                    current_sla_risk = float(row[3]) if row[3] else 0.05
                    current_volume = int(row[4]) if row[4] else 100000
                    
                    # Small random adjustments
                    new_delay = max(0, min(200, current_delay + random.randint(-10, 10)))
                    new_on_time = max(0.70, min(0.99, current_on_time + random.uniform(-0.02, 0.02)))
                    new_sla_risk = max(0.0, min(0.25, current_sla_risk + random.uniform(-0.01, 0.01)))
                    new_volume = max(50000, int(current_volume * random.uniform(0.98, 1.02)))
                    
                    update_sql = f"""
                    UPDATE {config.TABLE_NAMES['lanes']}
                    SET delayMinutes = {new_delay},
                        onTimePct = {new_on_time:.3f},
                        slaRiskPct = {new_sla_risk:.3f},
                        avgDailyVolume = {new_volume},
                        updated_at = current_timestamp()
                    WHERE id = '{lane_id}'
                    """
                    
                    if self.execute_sql(update_sql):
                        updated += 1
                
                if updated > 0:
                    print(f"    ✓ Updated {updated} lanes")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    def update_capacity_metrics(self):
        """Update capacity lane metrics and generate actions."""
        print("  Updating capacity metrics...")
        
        sql = f"""
        SELECT id, utilizationPct, availableCapacity, maxCapacity
        FROM {config.TABLE_NAMES['capacity_lanes']}
        ORDER BY RANDOM()
        LIMIT 5
        """
        
        try:
            execution = self.client.statement_execution.execute_statement(
                warehouse_id=self.warehouse_id,
                statement=sql,
                wait_timeout="30s"
            )
            
            if execution.status.state == StatementState.SUCCEEDED:
                results = execution.result.data_array
                updated = 0
                
                for row in results:
                    lane_id = row[0]
                    current_util = float(row[1]) if row[1] else 0.75
                    current_avail = int(row[2]) if row[2] else 10000
                    max_cap = int(row[3]) if row[3] else 100000
                    
                    # Small adjustments
                    new_util = max(0.50, min(0.98, current_util + random.uniform(-0.03, 0.03)))
                    new_avail = max(0, int(max_cap * (1 - new_util)))
                    
                    update_sql = f"""
                    UPDATE {config.TABLE_NAMES['capacity_lanes']}
                    SET utilizationPct = {new_util:.3f},
                        availableCapacity = {new_avail},
                        updated_at = current_timestamp()
                    WHERE id = '{lane_id}'
                    """
                    
                    if self.execute_sql(update_sql):
                        updated += 1
                    
                    # Generate capacity action if utilization crosses threshold
                    if new_util > 0.90 and random.random() < 0.3:
                        action_id = str(uuid.uuid4())
                        action_type = "hold_back" if new_util > 0.95 else "pull_forward"
                        volume_change = random.randint(2000, 8000) * (-1 if action_type == "hold_back" else 1)
                        
                        action_sql = f"""
                        INSERT INTO {config.TABLE_NAMES['capacity_actions']}
                        (id, laneId, type, volumeChange, npsImpact, costImpact, efficiencyImpact, notes)
                        VALUES (
                            '{action_id}',
                            '{lane_id}',
                            '{action_type}',
                            {volume_change},
                            {random.randint(-3, 5)},
                            {random.uniform(-10000, 20000):.2f},
                            {random.uniform(-0.1, 0.1):.3f},
                            'Auto-generated capacity optimization action'
                        )
                        """
                        self.execute_sql(action_sql)
                
                if updated > 0:
                    print(f"    ✓ Updated {updated} capacity lanes")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    def generate_agent_activities(self):
        """Generate new agent activity records."""
        print("  Generating agent activities...")
        
        sql = f"""
        SELECT DISTINCT id FROM {config.TABLE_NAMES['lanes']}
        ORDER BY RANDOM()
        LIMIT 3
        """
        
        try:
            execution = self.client.statement_execution.execute_statement(
                warehouse_id=self.warehouse_id,
                statement=sql,
                wait_timeout="30s"
            )
            
            if execution.status.state == StatementState.SUCCEEDED and random.random() < 0.4:  # 40% chance
                results = execution.result.data_array
                if results:
                    lane_id = results[0][0]
                    agent_types = ["capacity", "pricing", "sales"]
                    agent_type = random.choice(agent_types)
                    
                    activity_id = str(uuid.uuid4())
                    situations = {
                        "capacity": f"Capacity constraint detected on {lane_id}",
                        "pricing": f"Pricing optimization opportunity on {lane_id}",
                        "sales": f"Sales opportunity identified on {lane_id}"
                    }
                    
                    actions = {
                        "capacity": "Recommended capacity adjustment",
                        "pricing": "Generated spot pricing quote",
                        "sales": "Identified target customers"
                    }
                    
                    insert_sql = f"""
                    INSERT INTO {config.TABLE_NAMES['agent_activities']}
                    (id, laneId, timestamp, agentType, situation, action, result, status, metadata)
                    VALUES (
                        '{activity_id}',
                        '{lane_id}',
                        current_timestamp(),
                        '{agent_type}',
                        '{situations[agent_type]}',
                        '{actions[agent_type]}',
                        'Action completed successfully',
                        'completed',
                        '{{}}'
                    )
                    """
                    
                    if self.execute_sql(insert_sql):
                        print(f"    ✓ Created {agent_type} activity on {lane_id}")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    def generate_customer_interactions(self):
        """Generate new customer interaction records."""
        print("  Generating customer interactions...")
        
        sql = f"""
        SELECT DISTINCT id FROM {config.TABLE_NAMES['customers']}
        ORDER BY RANDOM()
        LIMIT 2
        """
        
        try:
            execution = self.client.statement_execution.execute_statement(
                warehouse_id=self.warehouse_id,
                statement=sql,
                wait_timeout="30s"
            )
            
            if execution.status.state == StatementState.SUCCEEDED and random.random() < 0.3:  # 30% chance
                results = execution.result.data_array
                if results:
                    customer_id = results[0][0]
                    interaction_types = ["email", "call"]
                    interaction_type = random.choice(interaction_types)
                    
                    interaction_id = str(uuid.uuid4())
                    summaries = {
                        "email": "Proactive update sent regarding shipment status",
                        "call": "Follow-up call regarding service quality"
                    }
                    
                    insert_sql = f"""
                    INSERT INTO {config.TABLE_NAMES['customer_interactions']}
                    (id, customerId, date, type, summary, sentiment, tags)
                    VALUES (
                        '{interaction_id}',
                        '{customer_id}',
                        current_timestamp(),
                        '{interaction_type}',
                        '{summaries[interaction_type]}',
                        'positive',
                        ARRAY('proactive-communication')
                    )
                    """
                    
                    if self.execute_sql(insert_sql):
                        print(f"    ✓ Created {interaction_type} interaction for {customer_id}")
        except Exception as e:
            print(f"    ✗ Error: {e}")
    
    def run_cycle(self):
        """Run one simulation cycle."""
        self.cycle_count += 1
        print(f"\n--- Cycle {self.cycle_count} ---")
        print(f"Time: {datetime.now().isoformat()}")
        
        # Shipment updates (every cycle)
        self.update_shipment_etas()
        
        # Incident lifecycle (every 2 cycles)
        if self.cycle_count % 2 == 0:
            self.generate_new_incidents()
            self.resolve_incidents()
        
        # Lane metric drift (every cycle)
        self.drift_lane_metrics()
        
        # Capacity updates (every 2 cycles)
        if self.cycle_count % 2 == 0:
            self.update_capacity_metrics()
        
        # Agent activities (every 3 cycles)
        if self.cycle_count % 3 == 0:
            self.generate_agent_activities()
        
        # Customer interactions (every 4 cycles)
        if self.cycle_count % 4 == 0:
            self.generate_customer_interactions()
        
        print("--- Cycle complete ---\n")


def main():
    """Main simulation loop."""
    import signal
    
    client = WorkspaceClient()
    warehouse_id = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")
    
    if not warehouse_id:
        raise ValueError("DATABRICKS_SQL_WAREHOUSE_ID environment variable must be set")
    
    simulator = StreamSimulator(client, warehouse_id)
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\n\nShutting down stream simulator...")
        print(f"Completed {simulator.cycle_count} cycles")
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run simulation loop
    interval_seconds = int(os.getenv("SIMULATOR_INTERVAL_SECONDS", "30"))
    
    print(f"Starting stream simulator (interval: {interval_seconds}s)")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            simulator.run_cycle()
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
