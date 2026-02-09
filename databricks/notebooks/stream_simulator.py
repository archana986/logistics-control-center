# Databricks notebook source
# MAGIC %md
# MAGIC # Real-Time Data Streaming Simulator
# MAGIC 
# MAGIC This notebook simulates real-time data mutations:
# MAGIC - Shipment ETA updates
# MAGIC - New incident generation
# MAGIC - Lane metric drift
# MAGIC - Capacity updates
# MAGIC - Agent activities
# MAGIC - Customer interactions
# MAGIC 
# MAGIC Run this as a scheduled Databricks Job (e.g., every 30 seconds).

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import random
import uuid
from datetime import datetime, timedelta

CATALOG = "demos"
SCHEMA = "logistics_control_center"

TABLE_NAMES = {
    "centers": f"{CATALOG}.{SCHEMA}.centers",
    "lanes": f"{CATALOG}.{SCHEMA}.lanes",
    "incidents": f"{CATALOG}.{SCHEMA}.incidents",
    "shipments": f"{CATALOG}.{SCHEMA}.shipments",
    "reroute_solutions": f"{CATALOG}.{SCHEMA}.reroute_solutions",
    "customers": f"{CATALOG}.{SCHEMA}.customers",
    "customer_interactions": f"{CATALOG}.{SCHEMA}.customer_interactions",
    "capacity_lanes": f"{CATALOG}.{SCHEMA}.capacity_lanes",
    "capacity_actions": f"{CATALOG}.{SCHEMA}.capacity_actions",
    "agent_activities": f"{CATALOG}.{SCHEMA}.agent_activities",
    "sales_opportunities": f"{CATALOG}.{SCHEMA}.sales_opportunities",
}

print(f"Running stream simulator cycle at {datetime.now().isoformat()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Update Shipment ETAs

# COMMAND ----------

# Get in-transit shipments and update ETAs
shipments_df = spark.sql(f"""
    SELECT trackingId, currentETA, promisedETA
    FROM {TABLE_NAMES['shipments']}
    WHERE status = 'in_transit'
    LIMIT 20
""")

if shipments_df.count() > 0:
    updated = 0
    delivered = 0
    
    for row in shipments_df.take(5):  # Update up to 5 shipments per cycle
        tracking_id = row.trackingId
        current_eta = row.currentETA
        
        if current_eta:
            # Adjust ETA by +/- 5-15 minutes
            delta_minutes = random.randint(-15, 15)
            new_eta = current_eta + timedelta(minutes=delta_minutes)
            
            # Occasionally mark as delivered (10% chance)
            if random.random() < 0.1:
                spark.sql(f"""
                    UPDATE {TABLE_NAMES['shipments']}
                    SET status = 'delivered', 
                        currentETA = current_timestamp()
                    WHERE trackingId = '{tracking_id}'
                """)
                delivered += 1
            else:
                spark.sql(f"""
                    UPDATE {TABLE_NAMES['shipments']}
                    SET currentETA = CAST('{new_eta.isoformat()}' AS TIMESTAMP)
                    WHERE trackingId = '{tracking_id}'
                """)
                updated += 1
    
    if updated > 0 or delivered > 0:
        print(f"✓ Updated {updated} shipments, delivered {delivered}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate New Incidents
# MAGIC
# MAGIC Note: We exclude key narrative lanes (BNA-STL-AIR, BNA-STL-GROUND) from new incident generation
# MAGIC to preserve the curated demo story. New incidents can be created on other lanes for realism.

# COMMAND ----------

# 30% chance to generate a new incident (but not on narrative lanes)
if random.random() < 0.3:
    # Exclude narrative lanes to preserve demo story
    narrative_lanes = ["BNA-STL-AIR", "BNA-STL-GROUND"]
    narrative_lanes_str = "', '".join(narrative_lanes)
    
    lanes_df = spark.sql(f"""
        SELECT DISTINCT id FROM {TABLE_NAMES['lanes']}
        WHERE id NOT IN ('{narrative_lanes_str}')
        ORDER BY RANDOM()
        LIMIT 5
    """)
    
    if lanes_df.count() > 0:
        lane_id = lanes_df.first().id
        
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
        
        spark.sql(f"""
            INSERT INTO {TABLE_NAMES['incidents']}
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
        """)
        print(f"✓ Created incident {incident_id} on {lane_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Resolve Incidents

# COMMAND ----------

# Resolve some active incidents (20% chance per incident)
incidents_df = spark.sql(f"""
    SELECT id FROM {TABLE_NAMES['incidents']}
    WHERE active = true
    ORDER BY RANDOM()
    LIMIT 3
""")

resolved = 0
for row in incidents_df.collect():
    if random.random() < 0.2:  # 20% chance to resolve
        incident_id = row.id
        spark.sql(f"""
            UPDATE {TABLE_NAMES['incidents']}
            SET active = false
            WHERE id = '{incident_id}'
        """)
        resolved += 1

if resolved > 0:
    print(f"✓ Resolved {resolved} incidents")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Drift Lane Metrics
# MAGIC
# MAGIC Note: Narrative lanes (BNA-STL-AIR, BNA-STL-GROUND) are excluded from metric drift
# MAGIC to preserve the curated demo story. Other lanes can drift for realism.

# COMMAND ----------

# Apply small random changes to lane metrics (excluding narrative lanes)
narrative_lanes = ["BNA-STL-AIR", "BNA-STL-GROUND"]
narrative_lanes_str = "', '".join(narrative_lanes)

lanes_df = spark.sql(f"""
    SELECT id, delayMinutes, onTimePct, slaRiskPct, avgDailyVolume
    FROM {TABLE_NAMES['lanes']}
    WHERE id NOT IN ('{narrative_lanes_str}')
    ORDER BY RANDOM()
    LIMIT 10
""")

updated = 0
for row in lanes_df.take(5):  # Update up to 5 lanes
    lane_id = row.id
    current_delay = int(row.delayMinutes) if row.delayMinutes else 0
    current_on_time = float(row.onTimePct) if row.onTimePct else 0.90
    current_sla_risk = float(row.slaRiskPct) if row.slaRiskPct else 0.05
    current_volume = int(row.avgDailyVolume) if row.avgDailyVolume else 100000
    
    # Small random adjustments
    new_delay = max(0, min(200, current_delay + random.randint(-10, 10)))
    new_on_time = max(0.70, min(0.99, current_on_time + random.uniform(-0.02, 0.02)))
    new_sla_risk = max(0.0, min(0.25, current_sla_risk + random.uniform(-0.01, 0.01)))
    new_volume = max(50000, int(current_volume * random.uniform(0.98, 1.02)))
    
    spark.sql(f"""
        UPDATE {TABLE_NAMES['lanes']}
        SET delayMinutes = {new_delay},
            onTimePct = {new_on_time:.3f},
            slaRiskPct = {new_sla_risk:.3f},
            avgDailyVolume = {new_volume}
        WHERE id = '{lane_id}'
    """)
    updated += 1

if updated > 0:
    print(f"✓ Updated {updated} lanes")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Update Capacity Metrics

# COMMAND ----------

# Update capacity lane metrics and generate actions
capacity_df = spark.sql(f"""
    SELECT id, utilizationPct, availableCapacity, maxCapacity
    FROM {TABLE_NAMES['capacity_lanes']}
    ORDER BY RANDOM()
    LIMIT 5
""")

updated = 0
for row in capacity_df.collect():
    lane_id = row.id
    current_util = float(row.utilizationPct) if row.utilizationPct else 0.75
    current_avail = int(row.availableCapacity) if row.availableCapacity else 10000
    max_cap = int(row.maxCapacity) if row.maxCapacity else 100000
    
    # Small adjustments
    new_util = max(0.50, min(0.98, current_util + random.uniform(-0.03, 0.03)))
    new_avail = max(0, int(max_cap * (1 - new_util)))
    
    spark.sql(f"""
        UPDATE {TABLE_NAMES['capacity_lanes']}
        SET utilizationPct = {new_util:.3f},
            availableCapacity = {new_avail}
        WHERE id = '{lane_id}'
    """)
    updated += 1
    
    # Generate capacity action if utilization crosses threshold
    if new_util > 0.90 and random.random() < 0.3:
        action_id = str(uuid.uuid4())
        action_type = "hold_back" if new_util > 0.95 else "pull_forward"
        volume_change = random.randint(2000, 8000) * (-1 if action_type == "hold_back" else 1)
        
        spark.sql(f"""
            INSERT INTO {TABLE_NAMES['capacity_actions']}
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
        """)

if updated > 0:
    print(f"✓ Updated {updated} capacity lanes")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Agent Activities

# COMMAND ----------

# 40% chance to generate agent activity
if random.random() < 0.4:
    lanes_df = spark.sql(f"""
        SELECT DISTINCT id FROM {TABLE_NAMES['lanes']}
        ORDER BY RANDOM()
        LIMIT 3
    """)
    
    if lanes_df.count() > 0:
        lane_id = lanes_df.first().id
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
        
        spark.sql(f"""
            INSERT INTO {TABLE_NAMES['agent_activities']}
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
        """)
        print(f"✓ Created {agent_type} activity on {lane_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Customer Interactions

# COMMAND ----------

# 30% chance to generate customer interaction
if random.random() < 0.3:
    customers_df = spark.sql(f"""
        SELECT DISTINCT id FROM {TABLE_NAMES['customers']}
        ORDER BY RANDOM()
        LIMIT 2
    """)
    
    if customers_df.count() > 0:
        customer_id = customers_df.first().id
        interaction_types = ["email", "call"]
        interaction_type = random.choice(interaction_types)
        
        interaction_id = str(uuid.uuid4())
        summaries = {
            "email": "Proactive update sent regarding shipment status",
            "call": "Follow-up call regarding service quality"
        }
        
        spark.sql(f"""
            INSERT INTO {TABLE_NAMES['customer_interactions']}
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
        """)
        print(f"✓ Created {interaction_type} interaction for {customer_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cycle Complete

# COMMAND ----------

print(f"\n✓ Stream simulator cycle complete at {datetime.now().isoformat()}")
