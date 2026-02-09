# Databricks notebook source
# MAGIC %md
# MAGIC # Seed Delta Tables with Synthetic Data
# MAGIC
# MAGIC Uses [dbldatagen](https://github.com/databrickslabs/dbldatagen) to generate
# MAGIC realistic logistics data natively in Spark (no RDD APIs, serverless-compatible).
# MAGIC
# MAGIC - **Reference tables** (centers, lanes, customers, reroute_solutions): inserted via SQL VALUES
# MAGIC - **Transactional tables** (shipments, incidents, etc.): generated with dbldatagen at scale

# COMMAND ----------

# MAGIC %pip install dbldatagen
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

CATALOG = "demos"
SCHEMA = "logistics_control_center"
ROW_SCALE = 1  # Multiply for larger datasets

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Reference Data — Centers (SQL VALUES)

# COMMAND ----------

spark.sql(f"INSERT OVERWRITE {CATALOG}.{SCHEMA}.centers (id, name, lat, lng, type) VALUES " + ",".join([
    "('BNA','Nashville SuperHub',36.124,-86.678,'air_hub')",
    "('STL','Saint Louis Hub',38.747,-90.361,'dc')",
    "('ORD','Chicago O''Hare Hub',41.974,-87.907,'air_hub')",
    "('ATL','Atlanta Hub',33.640,-84.427,'air_hub')",
    "('DFW','Dallas-Fort Worth SuperHub',32.897,-97.038,'air_hub')",
    "('LAX','Los Angeles Hub',33.942,-118.408,'air_hub')",
    "('EWR','Newark Gateway Hub',40.692,-74.169,'air_hub')",
    "('OAK','Oakland West Coast Hub',37.721,-122.221,'air_hub')",
    "('PHX','Phoenix Distribution Hub',33.435,-112.006,'dc')",
    "('SEA','Seattle-Tacoma Hub',47.449,-122.309,'air_hub')",
    "('MIA','Miami International Hub',25.796,-80.274,'air_hub')",
    "('DEN','Denver Mountain Hub',39.856,-104.673,'air_hub')",
    "('PIT','Pittsburgh International Hub',40.491,-80.233,'air_hub')",
    "('ANC','Anchorage International Hub',61.174,-149.996,'air_hub')",
    "('BOS','Boston Regional Hub',42.365,-71.010,'dc')",
    "('PHL','Philadelphia Hub',39.872,-75.241,'dc')",
    "('MSP','Minneapolis-St. Paul Hub',44.883,-93.222,'dc')",
    "('SLC','Salt Lake City Hub',40.789,-111.978,'dc')",
    "('CLT','Charlotte Regional Hub',35.214,-80.943,'dc')",
    "('LAS','Las Vegas Distribution Center',36.081,-115.152,'dc')",
]))
print("✓ Wrote 20 rows to centers")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Reference Data — Lanes (SQL VALUES)

# COMMAND ----------

lane_rows = [
    "('BNA-PIT-AIR','BNA','PIT','air',425000,0.96,18,0.04)",
    "('PIT-ORD-AIR','PIT','ORD','air',380000,0.95,22,0.05)",
    "('BNA-STL-AIR','BNA','STL','air',285000,0.87,140,0.13)",
    "('BNA-STL-GROUND','BNA','STL','ground',125000,0.78,185,0.22)",
    "('BNA-ORD-AIR','BNA','ORD','air',340000,0.94,35,0.06)",
    "('ORD-STL-GROUND','ORD','STL','ground',145000,0.96,22,0.04)",
    "('BNA-ATL-AIR','BNA','ATL','air',295000,0.92,48,0.08)",
    "('ATL-STL-AIR','ATL','STL','air',215000,0.95,28,0.05)",
    "('BNA-DFW-GROUND','BNA','DFW','ground',310000,0.91,52,0.09)",
    "('DFW-LAX-AIR','DFW','LAX','air',365000,0.93,41,0.07)",
    "('BNA-EWR-AIR','BNA','EWR','air',405000,0.94,32,0.06)",
    "('EWR-BOS-GROUND','EWR','BOS','ground',175000,0.97,15,0.03)",
    "('LAX-OAK-GROUND','LAX','OAK','ground',235000,0.96,20,0.04)",
    "('OAK-SEA-AIR','OAK','SEA','air',190000,0.95,25,0.05)",
    "('SEA-ANC-AIR','SEA','ANC','air',85000,0.92,45,0.08)",
    "('DFW-PHX-AIR','DFW','PHX','air',265000,0.94,30,0.06)",
    "('PHX-LAS-GROUND','PHX','LAS','ground',145000,0.96,18,0.04)",
    "('ATL-MIA-AIR','ATL','MIA','air',275000,0.93,38,0.07)",
    "('ATL-CLT-GROUND','ATL','CLT','ground',185000,0.97,12,0.03)",
    "('ORD-MSP-GROUND','ORD','MSP','ground',195000,0.96,20,0.04)",
    "('DEN-SLC-AIR','DEN','SLC','air',155000,0.95,24,0.05)",
    "('SLC-OAK-AIR','SLC','OAK','air',165000,0.94,28,0.06)",
    "('EWR-PHL-GROUND','EWR','PHL','ground',210000,0.98,8,0.02)",
    "('PIT-ATL-AIR','PIT','ATL','air',320000,0.96,18,0.04)",
    "('PIT-STL-GROUND','PIT','STL','ground',295000,0.95,22,0.05)",
    "('PIT-LAX-AIR','PIT','LAX','air',350000,0.94,28,0.06)",
    "('ORD-DEN-AIR','ORD','DEN','air',245000,0.95,23,0.05)",
    "('LAX-PHX-GROUND','LAX','PHX','ground',225000,0.95,24,0.05)",
    "('DFW-ATL-AIR','DFW','ATL','air',305000,0.93,35,0.07)",
    "('ATL-EWR-AIR','ATL','EWR','air',385000,0.94,30,0.06)",
    "('MIA-ATL-AIR','MIA','ATL','air',265000,0.94,32,0.06)",
    "('DEN-PHX-AIR','DEN','PHX','air',185000,0.96,19,0.04)",
    "('ORD-EWR-AIR','ORD','EWR','air',395000,0.93,38,0.07)",
    "('LAX-DEN-AIR','LAX','DEN','air',275000,0.94,30,0.06)",
    "('SEA-ORD-AIR','SEA','ORD','air',285000,0.93,36,0.07)",
    "('BOS-EWR-GROUND','BOS','EWR','ground',165000,0.97,14,0.03)",
]
spark.sql(f"INSERT OVERWRITE {CATALOG}.{SCHEMA}.lanes (id, origin, dest, mode, avgDailyVolume, onTimePct, delayMinutes, slaRiskPct) VALUES " + ",".join(lane_rows))
print(f"✓ Wrote {len(lane_rows)} rows to lanes")

# Collect lane IDs for use in generated tables
lane_ids = [r.split("'")[1] for r in lane_rows]

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Reference Data — Customers (SQL VALUES)

# COMMAND ----------

spark.sql(f"""
INSERT OVERWRITE {CATALOG}.{SCHEMA}.customers (id, name, contact, tier, preferredCommunication) VALUES
('walmart-supply', 'Walmart Supply Chain', 'logistics@walmart.com', 'platinum', 'email'),
('techcorp-industries', 'TechCorp Industries', 'shipping@techcorp.com', 'gold', 'both'),
('amazon-logistics', 'Amazon Logistics', 'ops@amazon.com', 'platinum', 'email'),
('target-distribution', 'Target Distribution', 'logistics@target.com', 'gold', 'phone'),
('bestbuy-logistics', 'Best Buy Logistics', 'shipping@bestbuy.com', 'silver', 'email'),
('nike-supply', 'Nike Supply Chain', 'logistics@nike.com', 'gold', 'email'),
('costco-freight', 'Costco Freight Services', 'freight@costco.com', 'platinum', 'both'),
('homedepot-logistics', 'Home Depot Logistics', 'transport@homedepot.com', 'silver', 'phone'),
('WALMART', 'Walmart', 'logistics@walmart.com', 'platinum', 'email'),
('AMAZON', 'Amazon', 'ops@amazon.com', 'platinum', 'email'),
('TARGET', 'Target', 'logistics@target.com', 'gold', 'phone')
""")
customer_ids = ['walmart-supply','techcorp-industries','amazon-logistics','target-distribution',
                'bestbuy-logistics','nike-supply','costco-freight','homedepot-logistics']
print("✓ Wrote 11 rows to customers")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Reference Data — Reroute Solutions (SQL VALUES)

# COMMAND ----------

spark.sql(f"""
INSERT OVERWRITE {CATALOG}.{SCHEMA}.reroute_solutions (laneId, strategy, deltaETAminutes, addedCostUSD, capacityUsedPct, notes) VALUES
('BNA-STL-AIR','TRUCK-VIA-ORD',-1140,3100,42,'Consolidate on two night trucks BNA→ORD→STL; priority dock slot in STL.'),
('BNA-STL-AIR','AIR-VIA-ATL',-960,4800,28,'Reroute through Atlanta hub with FX connections.'),
('BNA-STL-AIR','AIR-VIA-PIT',-1320,2800,35,'Route through Pittsburgh with automated sort. Best cost/speed balance.'),
('SEA-ANC-AIR','DELAY-24HR',1440,0,0,'Wait for winter storm to pass. Weather expected to clear within 24 hours.'),
('ATL-MIA-AIR','GROUND-EXPEDITED',-780,2200,55,'Dedicated expedited ground service via I-95.'),
('ORD-EWR-AIR','AIR-VIA-ATL',-900,3900,31,'Connect through Atlanta to bypass Newark ground stop.'),
('ORD-EWR-AIR','AIR-VIA-BNA',-720,4200,26,'Route through Nashville SuperHub with guaranteed capacity.'),
('DFW-LAX-AIR','GROUND-VIA-PHX',-660,1800,48,'Overnight ground via Phoenix hub. Reliable alternative.'),
('SEA-ORD-AIR','AIR-VIA-DEN',-840,3400,33,'Connect through Denver Mountain Hub.'),
('DFW-ATL-AIR','GROUND-EXPEDITED',-1020,2900,52,'Direct expedited ground service.'),
('BNA-STL-GROUND','AIR-DIRECT',-1560,5200,38,'Switch to air freight. Bypasses I-65 highway closure.'),
('BNA-STL-GROUND','GROUND-VIA-PIT',-1200,2400,45,'Reroute through Pittsburgh via alternate highways.'),
('BNA-STL-GROUND','GROUND-VIA-STL',-1380,2800,51,'Northern route through St. Louis using I-64 and I-70.'),
('BNA-ATL-AIR','AIR-VIA-BHM',-900,3200,29,'Connect through Birmingham with regional carrier partner.'),
('BNA-ATL-AIR','GROUND-EXPEDITED',-720,1900,58,'Priority ground service via I-55 and I-20.'),
('BNA-ATL-AIR','AIR-VIA-PIT',-1080,3600,32,'Route through Pittsburgh International with automated sort.'),
('BNA-DFW-GROUND','GROUND-VIA-LIT',-720,1800,45,'Reroute through Little Rock via alternate highways.'),
('BNA-DFW-GROUND','AIR-EXPEDITED',-1020,4100,35,'Switch to expedited air freight.'),
('BNA-DFW-GROUND','GROUND-VIA-OKC',-840,2200,48,'Route via Oklahoma City with team driver relay.')
""")
print("✓ Wrote 19 rows to reroute_solutions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Generated Data — Incidents (dbldatagen)

# COMMAND ----------

import dbldatagen as dg
from pyspark.sql.types import StringType, IntegerType, DoubleType, BooleanType, TimestampType
from pyspark.sql.functions import expr

incident_count = int(50 * ROW_SCALE)

# Build base columns first
incident_base = (
    dg.DataGenerator(spark, name="incidents_base", rows=incident_count, partitions=4, randomSeedMethod="hash_fieldname", seedColumnName="_seed_id")
    .withColumn("id", StringType(), expr="concat('INC-', lpad(cast(_seed_id as string), 6, '0'))")
    .withColumn("laneId", StringType(), values=lane_ids, random=True)
    .withColumn("timestamp", TimestampType(), begin="2025-09-01 00:00:00", end="2025-10-22 23:59:00", interval="1 minute", random=True)
    .withColumn("type", StringType(), values=["flight_delay", "highway_closure", "equipment_issue", "weather", "traffic_congestion", "air_traffic_control", "customs_delay"], random=True, weights=[25, 15, 20, 15, 10, 10, 5])
    .withColumn("impactMinutes", IntegerType(), minValue=15, maxValue=240, random=True)
    .withColumn("impactThroughputPct", DoubleType(), expr="round(-rand() * 50, 1)")
    .withColumn("confidence", DoubleType(), minValue=0.70, maxValue=0.99, random=True)
    .withColumn("active", BooleanType(), expr="rand() > 0.3")
)
incident_df = incident_base.build()

# Add dependent columns using SQL via temporary view
incident_df.createOrReplaceTempView("incidents_temp")
incident_df = spark.sql("""
SELECT 
  id, laneId, timestamp, `type`, impactMinutes, impactThroughputPct, confidence, active,
  CASE WHEN `type` IN ('flight_delay','air_traffic_control') THEN concat('FX', cast(floor(rand()*900+100) as string)) ELSE concat('TRK-', cast(floor(rand()*9000+1000) as string)) END as ref,
  CASE `type` 
    WHEN 'flight_delay' THEN element_at(array('Ice storm affecting route','Mechanical issue detected','Crew scheduling delay','Late inbound connection'), cast(floor(rand()*4)+1 as int))
    WHEN 'highway_closure' THEN element_at(array('Multi-vehicle accident','Construction zone closure','Bridge inspection','Hazmat spill on highway'), cast(floor(rand()*4)+1 as int))
    WHEN 'equipment_issue' THEN element_at(array('Landing gear hydraulic actuator failure','Engine maintenance required','Tire replacement needed','Brake system inspection'), cast(floor(rand()*4)+1 as int))
    WHEN 'weather' THEN element_at(array('Thunderstorms affecting route','Heavy fog reducing visibility','Winter storm warning','High winds exceeding limits'), cast(floor(rand()*4)+1 as int))
    WHEN 'traffic_congestion' THEN 'Heavy traffic on major highway'
    WHEN 'air_traffic_control' THEN 'ATC hold at destination airport'
    ELSE 'Customs processing delay'
  END as cause
FROM incidents_temp
""")

incident_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{CATALOG}.{SCHEMA}.incidents")
print(f"✓ Wrote {incident_count} rows to incidents")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Generated Data — Shipments (dbldatagen)

# COMMAND ----------

shipment_count = int(200 * ROW_SCALE)

shipment_base = (
    dg.DataGenerator(spark, name="shipments_base", rows=shipment_count, partitions=4, randomSeedMethod="hash_fieldname", seedColumnName="_seed_id")
    .withColumn("trackingId", StringType(), expr="concat(element_at(array('WMT','TECH','AMZ','TGT','BBY','NKE','CST','HD'), cast(floor(rand()*8)+1 as int)), '-', lpad(cast(_seed_id as string), 4, '0'))")
    .withColumn("customerId", StringType(), values=customer_ids, random=True)
    .withColumn("priority", StringType(), values=["HIGH", "MED", "LOW"], random=True, weights=[3, 5, 2])
    .withColumn("laneId", StringType(), values=lane_ids, random=True)
    .withColumn("promisedETA", TimestampType(), begin="2025-10-21 08:00:00", end="2025-10-25 23:59:00", interval="1 minute", random=True)
    .withColumn("packageCount", IntegerType(), minValue=50, maxValue=5000, random=True)
    .withColumn("status", StringType(), values=["in_transit", "delivered", "delayed", "at_hub"], random=True, weights=[50, 25, 15, 10])
)
shipment_df = shipment_base.build()

# Add dependent column using SQL via temporary view
shipment_df.createOrReplaceTempView("shipments_temp")
shipment_df = spark.sql("""
SELECT 
  trackingId, customerId, priority, laneId, promisedETA, packageCount, status,
  (promisedETA + make_interval(0,0,0,0, cast(floor(rand()*6 - 2) as int), cast(floor(rand()*60) as int), 0)) as currentETA
FROM shipments_temp
""")

shipment_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{CATALOG}.{SCHEMA}.shipments")
print(f"✓ Wrote {shipment_count} rows to shipments")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Generated Data — Customer Interactions (dbldatagen)

# COMMAND ----------

interaction_count = int(100 * ROW_SCALE)

interaction_base = (
    dg.DataGenerator(spark, name="customer_interactions_base", rows=interaction_count, partitions=4, randomSeedMethod="hash_fieldname", seedColumnName="_seed_id")
    .withColumn("id", StringType(), expr="uuid()")
    .withColumn("customerId", StringType(), values=customer_ids, random=True)
    .withColumn("date", TimestampType(), begin="2025-07-01 08:00:00", end="2025-10-22 18:00:00", interval="1 minute", random=True)
    .withColumn("type", StringType(), values=["email", "call", "chat", "in_person"], random=True, weights=[40, 30, 20, 10])
    .withColumn("sentiment", StringType(), values=["positive", "neutral", "negative"], random=True, weights=[55, 35, 10])
    .withColumn("tags", "array<string>", expr="CASE WHEN rand() < 0.3 THEN array('proactive-communication') WHEN rand() < 0.5 THEN array('escalation') WHEN rand() < 0.7 THEN array('follow-up') ELSE array() END")
)
interaction_df = interaction_base.build()

# Add dependent column using SQL via temporary view
interaction_df.createOrReplaceTempView("interactions_temp")
interaction_df = spark.sql("""
SELECT 
  id, customerId, date, `type`, sentiment, tags,
  CASE `type` 
    WHEN 'email' THEN element_at(array('Proactive alert about lane disruption - customer acknowledged','Shipment tracking update sent - delivery on schedule','SLA performance report shared - metrics improving','Capacity planning update - seasonal adjustments communicated'), cast(floor(rand()*4)+1 as int))
    WHEN 'call' THEN element_at(array('Follow-up call regarding service quality','Discussed upcoming peak season capacity needs','Resolved billing discrepancy for last month','Reviewed quarterly business performance metrics'), cast(floor(rand()*4)+1 as int))
    WHEN 'chat' THEN element_at(array('Quick check on delayed shipment status','Confirmed delivery window for priority packages','Updated preferred communication preferences','Requested expedited handling for urgent order'), cast(floor(rand()*4)+1 as int))
    ELSE 'On-site review of distribution center operations'
  END as summary
FROM interactions_temp
""")

interaction_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{CATALOG}.{SCHEMA}.customer_interactions")
print(f"✓ Wrote {interaction_count} rows to customer_interactions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Generated Data — Capacity Lanes (derived from lanes)

# COMMAND ----------

# Capacity lanes extend regular lanes with capacity metrics
spark.sql(f"""
INSERT OVERWRITE {CATALOG}.{SCHEMA}.capacity_lanes
  (id, origin, dest, mode, avgDailyVolume, onTimePct, delayMinutes, slaRiskPct,
   maxCapacity, utilizationPct, availableCapacity, optimalUtilization)
SELECT
  id, origin, dest, mode, avgDailyVolume, onTimePct, delayMinutes, slaRiskPct,
  cast(avgDailyVolume * 1.5 as int) AS maxCapacity,
  round(0.65 + rand() * 0.30, 3) AS utilizationPct,
  cast(avgDailyVolume * 1.5 * (1 - (0.65 + rand() * 0.30)) as int) AS availableCapacity,
  0.85 AS optimalUtilization
FROM {CATALOG}.{SCHEMA}.lanes
""")
capacity_lane_count = spark.table(f"{CATALOG}.{SCHEMA}.capacity_lanes").count()
print(f"✓ Wrote {capacity_lane_count} rows to capacity_lanes")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Generated Data — Capacity Actions (dbldatagen)

# COMMAND ----------

action_count = int(30 * ROW_SCALE)

action_base = (
    dg.DataGenerator(spark, name="capacity_actions_base", rows=action_count, partitions=4, randomSeedMethod="hash_fieldname", seedColumnName="_seed_id")
    .withColumn("id", StringType(), expr="uuid()")
    .withColumn("laneId", StringType(), values=lane_ids, random=True)
    .withColumn("type", StringType(), values=["pull_forward", "hold_back", "redistribute", "expedite"], random=True, weights=[30, 25, 25, 20])
    .withColumn("npsImpact", IntegerType(), minValue=-5, maxValue=8, random=True)
    .withColumn("costImpact", DoubleType(), expr="round(-10000 + rand() * 30000, 2)")
    .withColumn("efficiencyImpact", DoubleType(), expr="round(-0.10 + rand() * 0.20, 3)")
)
action_df = action_base.build()

# Add dependent columns using SQL via temporary view
action_df.createOrReplaceTempView("actions_temp")
action_df = spark.sql("""
SELECT 
  id, laneId, `type`, npsImpact, costImpact, efficiencyImpact,
  CASE `type` 
    WHEN 'pull_forward' THEN cast(2000 + floor(rand()*8000) as int)
    WHEN 'hold_back' THEN cast(-(2000 + floor(rand()*6000)) as int)
    WHEN 'redistribute' THEN cast(-1000 + floor(rand()*2000) as int)
    ELSE cast(1000 + floor(rand()*5000) as int)
  END as volumeChange,
  CASE `type` 
    WHEN 'pull_forward' THEN 'Pull forward urgent shipments to improve customer satisfaction'
    WHEN 'hold_back' THEN 'Hold back non-urgent shipments to reduce congestion'
    WHEN 'redistribute' THEN 'Redistribute volume across parallel lanes for balance'
    ELSE 'Expedite processing to clear backlog'
  END as notes
FROM actions_temp
""")

action_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{CATALOG}.{SCHEMA}.capacity_actions")
print(f"✓ Wrote {action_count} rows to capacity_actions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Generated Data — Agent Activities (dbldatagen)

# COMMAND ----------

activity_count = int(80 * ROW_SCALE)

activity_base = (
    dg.DataGenerator(spark, name="agent_activities_base", rows=activity_count, partitions=4, randomSeedMethod="hash_fieldname", seedColumnName="_seed_id")
    .withColumn("id", StringType(), expr="uuid()")
    .withColumn("laneId", StringType(), values=lane_ids, random=True)
    .withColumn("timestamp", TimestampType(), begin="2025-10-20 00:00:00", end="2025-10-22 23:59:00", interval="1 minute", random=True)
    .withColumn("agentType", StringType(), values=["capacity", "pricing", "sales", "routing", "maintenance"], random=True, weights=[25, 25, 20, 20, 10])
    .withColumn("result", StringType(), values=["Action approved and implemented", "Action pending review", "Action completed successfully", "Recommendation deferred", "Escalated to operations team"], random=True, weights=[35, 20, 25, 10, 10])
    .withColumn("status", StringType(), values=["completed", "pending", "in_progress", "failed"], random=True, weights=[60, 20, 15, 5])
    .withColumn("metadata", StringType(), expr="concat('{\"confidence\":', cast(round(0.7 + rand()*0.3, 2) as string), ',\"processingTimeMs\":', cast(floor(rand()*5000) as string), '}')")
)
activity_df = activity_base.build()

# Add dependent columns using SQL via temporary view
activity_df.createOrReplaceTempView("activities_temp")
activity_df = spark.sql("""
SELECT 
  id, laneId, timestamp, agentType, result, status, metadata,
  CASE agentType 
    WHEN 'capacity' THEN concat('Capacity constraint detected on ', laneId)
    WHEN 'pricing' THEN concat('Pricing optimization opportunity on ', laneId)
    WHEN 'sales' THEN concat('Sales opportunity identified on ', laneId)
    WHEN 'routing' THEN concat('Route optimization available for ', laneId)
    ELSE concat('Maintenance pattern detected on ', laneId)
  END as situation,
  CASE agentType 
    WHEN 'capacity' THEN 'Recommended capacity adjustment'
    WHEN 'pricing' THEN 'Generated spot pricing quote'
    WHEN 'sales' THEN 'Identified target customers for available capacity'
    WHEN 'routing' THEN 'Proposed alternative routing strategy'
    ELSE 'Flagged equipment for preventive maintenance'
  END as action
FROM activities_temp
""")

activity_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{CATALOG}.{SCHEMA}.agent_activities")
print(f"✓ Wrote {activity_count} rows to agent_activities")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Generated Data — Sales Opportunities (SQL with complex structs)

# COMMAND ----------

# Sales opportunities have complex STRUCT/ARRAY types - create row by row using UNION ALL
sales_sql = f"""
INSERT OVERWRITE {CATALOG}.{SCHEMA}.sales_opportunities
  (laneId, activityId, availableCapacity, forecastDate, targetCustomers, pricing, projectedImpact)
SELECT * FROM (
  SELECT
    'BNA-STL-AIR' as laneId,
    uuid() as activityId,
    cast(5000 + floor(rand() * 20000) as int) as availableCapacity,
    date_add(current_date(), cast(floor(rand() * 30) as int)) as forecastDate,
    array(named_struct('id', cast('walmart-supply' as string), 'name', cast('Walmart Supply Chain' as string), 'reason', cast('High volume customer with capacity needs on BNA-STL-AIR' as string))) as targetCustomers,
    named_struct('historical', cast(round(1.50 + rand() * 2.0, 2) as double), 'recommended', cast(round(2.00 + rand() * 2.5, 2) as double), 'discount', cast(round(rand() * 0.15, 2) as double)) as pricing,
    named_struct('revenue', cast(round(10000 + rand() * 80000, 2) as double), 'utilizationBefore', cast(round(0.60 + rand() * 0.25, 2) as double), 'utilizationAfter', cast(round(0.80 + rand() * 0.18, 2) as double), 'margin', cast(round(0.10 + rand() * 0.20, 2) as double)) as projectedImpact
  UNION ALL
  SELECT
    'BNA-ORD-AIR' as laneId,
    uuid() as activityId,
    cast(5000 + floor(rand() * 20000) as int) as availableCapacity,
    date_add(current_date(), cast(floor(rand() * 30) as int)) as forecastDate,
    array(named_struct('id', cast('amazon-logistics' as string), 'name', cast('Amazon Logistics' as string), 'reason', cast('High volume customer with capacity needs on BNA-ORD-AIR' as string))) as targetCustomers,
    named_struct('historical', cast(round(1.50 + rand() * 2.0, 2) as double), 'recommended', cast(round(2.00 + rand() * 2.5, 2) as double), 'discount', cast(round(rand() * 0.15, 2) as double)) as pricing,
    named_struct('revenue', cast(round(10000 + rand() * 80000, 2) as double), 'utilizationBefore', cast(round(0.60 + rand() * 0.25, 2) as double), 'utilizationAfter', cast(round(0.80 + rand() * 0.18, 2) as double), 'margin', cast(round(0.10 + rand() * 0.20, 2) as double)) as projectedImpact
  UNION ALL
  SELECT
    'DFW-LAX-AIR' as laneId,
    uuid() as activityId,
    cast(5000 + floor(rand() * 20000) as int) as availableCapacity,
    date_add(current_date(), cast(floor(rand() * 30) as int)) as forecastDate,
    array(named_struct('id', cast('target-distribution' as string), 'name', cast('Target Distribution' as string), 'reason', cast('High volume customer with capacity needs on DFW-LAX-AIR' as string))) as targetCustomers,
    named_struct('historical', cast(round(1.50 + rand() * 2.0, 2) as double), 'recommended', cast(round(2.00 + rand() * 2.5, 2) as double), 'discount', cast(round(rand() * 0.15, 2) as double)) as pricing,
    named_struct('revenue', cast(round(10000 + rand() * 80000, 2) as double), 'utilizationBefore', cast(round(0.60 + rand() * 0.25, 2) as double), 'utilizationAfter', cast(round(0.80 + rand() * 0.18, 2) as double), 'margin', cast(round(0.10 + rand() * 0.20, 2) as double)) as projectedImpact
  UNION ALL
  SELECT
    'BNA-EWR-AIR' as laneId,
    uuid() as activityId,
    cast(5000 + floor(rand() * 20000) as int) as availableCapacity,
    date_add(current_date(), cast(floor(rand() * 30) as int)) as forecastDate,
    array(named_struct('id', cast('techcorp-industries' as string), 'name', cast('TechCorp Industries' as string), 'reason', cast('High volume customer with capacity needs on BNA-EWR-AIR' as string))) as targetCustomers,
    named_struct('historical', cast(round(1.50 + rand() * 2.0, 2) as double), 'recommended', cast(round(2.00 + rand() * 2.5, 2) as double), 'discount', cast(round(rand() * 0.15, 2) as double)) as pricing,
    named_struct('revenue', cast(round(10000 + rand() * 80000, 2) as double), 'utilizationBefore', cast(round(0.60 + rand() * 0.25, 2) as double), 'utilizationAfter', cast(round(0.80 + rand() * 0.18, 2) as double), 'margin', cast(round(0.10 + rand() * 0.20, 2) as double)) as projectedImpact
  UNION ALL
  SELECT
    'ATL-MIA-AIR' as laneId,
    uuid() as activityId,
    cast(5000 + floor(rand() * 20000) as int) as availableCapacity,
    date_add(current_date(), cast(floor(rand() * 30) as int)) as forecastDate,
    array(named_struct('id', cast('nike-supply' as string), 'name', cast('Nike Supply Chain' as string), 'reason', cast('High volume customer with capacity needs on ATL-MIA-AIR' as string))) as targetCustomers,
    named_struct('historical', cast(round(1.50 + rand() * 2.0, 2) as double), 'recommended', cast(round(2.00 + rand() * 2.5, 2) as double), 'discount', cast(round(rand() * 0.15, 2) as double)) as pricing,
    named_struct('revenue', cast(round(10000 + rand() * 80000, 2) as double), 'utilizationBefore', cast(round(0.60 + rand() * 0.25, 2) as double), 'utilizationAfter', cast(round(0.80 + rand() * 0.18, 2) as double), 'margin', cast(round(0.10 + rand() * 0.20, 2) as double)) as projectedImpact
  UNION ALL
  SELECT
    'ORD-EWR-AIR' as laneId,
    uuid() as activityId,
    cast(5000 + floor(rand() * 20000) as int) as availableCapacity,
    date_add(current_date(), cast(floor(rand() * 30) as int)) as forecastDate,
    array(named_struct('id', cast('costco-freight' as string), 'name', cast('Costco Freight Services' as string), 'reason', cast('High volume customer with capacity needs on ORD-EWR-AIR' as string))) as targetCustomers,
    named_struct('historical', cast(round(1.50 + rand() * 2.0, 2) as double), 'recommended', cast(round(2.00 + rand() * 2.5, 2) as double), 'discount', cast(round(rand() * 0.15, 2) as double)) as pricing,
    named_struct('revenue', cast(round(10000 + rand() * 80000, 2) as double), 'utilizationBefore', cast(round(0.60 + rand() * 0.25, 2) as double), 'utilizationAfter', cast(round(0.80 + rand() * 0.18, 2) as double), 'margin', cast(round(0.10 + rand() * 0.20, 2) as double)) as projectedImpact
  UNION ALL
  SELECT
    'PIT-LAX-AIR' as laneId,
    uuid() as activityId,
    cast(5000 + floor(rand() * 20000) as int) as availableCapacity,
    date_add(current_date(), cast(floor(rand() * 30) as int)) as forecastDate,
    array(named_struct('id', cast('bestbuy-logistics' as string), 'name', cast('Best Buy Logistics' as string), 'reason', cast('High volume customer with capacity needs on PIT-LAX-AIR' as string))) as targetCustomers,
    named_struct('historical', cast(round(1.50 + rand() * 2.0, 2) as double), 'recommended', cast(round(2.00 + rand() * 2.5, 2) as double), 'discount', cast(round(rand() * 0.15, 2) as double)) as pricing,
    named_struct('revenue', cast(round(10000 + rand() * 80000, 2) as double), 'utilizationBefore', cast(round(0.60 + rand() * 0.25, 2) as double), 'utilizationAfter', cast(round(0.80 + rand() * 0.18, 2) as double), 'margin', cast(round(0.10 + rand() * 0.20, 2) as double)) as projectedImpact
  UNION ALL
  SELECT
    'SEA-ORD-AIR' as laneId,
    uuid() as activityId,
    cast(5000 + floor(rand() * 20000) as int) as availableCapacity,
    date_add(current_date(), cast(floor(rand() * 30) as int)) as forecastDate,
    array(named_struct('id', cast('homedepot-logistics' as string), 'name', cast('Home Depot Logistics' as string), 'reason', cast('High volume customer with capacity needs on SEA-ORD-AIR' as string))) as targetCustomers,
    named_struct('historical', cast(round(1.50 + rand() * 2.0, 2) as double), 'recommended', cast(round(2.00 + rand() * 2.5, 2) as double), 'discount', cast(round(rand() * 0.15, 2) as double)) as pricing,
    named_struct('revenue', cast(round(10000 + rand() * 80000, 2) as double), 'utilizationBefore', cast(round(0.60 + rand() * 0.25, 2) as double), 'utilizationAfter', cast(round(0.80 + rand() * 0.18, 2) as double), 'margin', cast(round(0.10 + rand() * 0.20, 2) as double)) as projectedImpact
) t
"""
spark.sql(sales_sql)
print("✓ Wrote 8 rows to sales_opportunities")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("\n✓ Seeding complete!\n")
for name, table in sorted({
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
}.items()):
    count = spark.table(table).count()
    print(f"  {name:30s} {count:>8,} rows")
