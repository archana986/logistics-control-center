-- Logistics Control Center data foundation
-- Catalog/schema are fixed to the existing target:
--   demos.logistics_control_center
--
-- This script creates:
-- 1) managed volumes for raw files + documents
-- 2) canonical serving tables consumed by API/UI
-- 3) Delta options for efficient writes

-- Do not create catalog/schema here; this deployment expects the namespace
-- to already exist.
USE CATALOG demos;
USE SCHEMA logistics_control_center;

CREATE VOLUME IF NOT EXISTS demos.logistics_control_center.raw_data;
CREATE VOLUME IF NOT EXISTS demos.logistics_control_center.documents;

-- ---------------------------
-- Serving dimensions/facts
-- ---------------------------
CREATE TABLE IF NOT EXISTS demos.logistics_control_center.centers (
  id STRING NOT NULL,
  name STRING NOT NULL,
  lat DOUBLE NOT NULL,
  lng DOUBLE NOT NULL,
  type STRING NOT NULL,
  region STRING,
  updated_at TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.feature.allowColumnDefaults' = 'supported'
);

CREATE TABLE IF NOT EXISTS demos.logistics_control_center.customers (
  id STRING NOT NULL,
  name STRING NOT NULL,
  contact STRING,
  tier STRING,
  preferredCommunication STRING,
  updated_at TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.feature.allowColumnDefaults' = 'supported'
);

CREATE TABLE IF NOT EXISTS demos.logistics_control_center.lanes (
  id STRING NOT NULL,
  origin STRING NOT NULL,
  dest STRING NOT NULL,
  mode STRING NOT NULL,
  avgDailyVolume INT,
  onTimePct DOUBLE,
  delayMinutes INT,
  slaRiskPct DOUBLE,
  maxCapacity INT,
  utilizationPct DOUBLE,
  availableCapacity INT,
  updated_at TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.feature.allowColumnDefaults' = 'supported'
);

CREATE TABLE IF NOT EXISTS demos.logistics_control_center.shipments (
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
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.feature.allowColumnDefaults' = 'supported'
);

CREATE TABLE IF NOT EXISTS demos.logistics_control_center.incidents (
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
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.feature.allowColumnDefaults' = 'supported'
);

CREATE TABLE IF NOT EXISTS demos.logistics_control_center.customer_interactions (
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
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.feature.allowColumnDefaults' = 'supported'
);

CREATE TABLE IF NOT EXISTS demos.logistics_control_center.capacity_lanes (
  id STRING NOT NULL,
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
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.feature.allowColumnDefaults' = 'supported'
);

CREATE TABLE IF NOT EXISTS demos.logistics_control_center.capacity_actions (
  id STRING NOT NULL,
  laneId STRING NOT NULL,
  type STRING NOT NULL,
  volumeChange INT NOT NULL,
  npsImpact INT NOT NULL,
  costImpact DOUBLE NOT NULL,
  efficiencyImpact DOUBLE NOT NULL,
  notes STRING,
  created_at TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA
PARTITIONED BY (laneId)
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.feature.allowColumnDefaults' = 'supported'
);

CREATE TABLE IF NOT EXISTS demos.logistics_control_center.agent_activities (
  id STRING NOT NULL,
  laneId STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  agentType STRING NOT NULL,
  situation STRING,
  action STRING,
  result STRING,
  status STRING NOT NULL,
  metadata STRING,
  created_at TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA
PARTITIONED BY (agentType)
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.feature.allowColumnDefaults' = 'supported'
);

CREATE TABLE IF NOT EXISTS demos.logistics_control_center.sales_opportunities (
  laneId STRING NOT NULL,
  activityId STRING NOT NULL,
  availableCapacity INT NOT NULL,
  forecastDate DATE NOT NULL,
  targetCustomers ARRAY<STRUCT<id: STRING, name: STRING, reason: STRING>>,
  pricing STRUCT<historical: DOUBLE, recommended: DOUBLE, discount: DOUBLE>,
  projectedImpact STRUCT<revenue: DOUBLE, utilizationBefore: DOUBLE, utilizationAfter: DOUBLE, margin: DOUBLE>,
  created_at TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.feature.allowColumnDefaults' = 'supported'
);

CREATE TABLE IF NOT EXISTS demos.logistics_control_center.reroute_solutions (
  laneId STRING NOT NULL,
  strategy STRING NOT NULL,
  deltaETAminutes INT NOT NULL,
  addedCostUSD DOUBLE NOT NULL,
  capacityUsedPct DOUBLE NOT NULL,
  notes STRING,
  created_at TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.feature.allowColumnDefaults' = 'supported'
);

-- ---------------------------
-- Raw event tables for pipeline outputs and QA
-- ---------------------------
CREATE TABLE IF NOT EXISTS demos.logistics_control_center.raw_sensor_events (
  event_id STRING,
  lane_id STRING,
  center_id STRING,
  event_time TIMESTAMP,
  vibration DOUBLE,
  temp_c DOUBLE,
  gps_delay_minutes INT,
  weather_risk DOUBLE,
  event_date DATE
)
USING DELTA
PARTITIONED BY (event_date);

CREATE TABLE IF NOT EXISTS demos.logistics_control_center.raw_shipment_events (
  event_id STRING,
  trackingId STRING,
  laneId STRING,
  event_time TIMESTAMP,
  status STRING,
  eta_delta_minutes INT,
  event_date DATE
)
USING DELTA
PARTITIONED BY (event_date);

CREATE TABLE IF NOT EXISTS demos.logistics_control_center.raw_incident_events (
  event_id STRING,
  incident_id STRING,
  laneId STRING,
  event_time TIMESTAMP,
  type STRING,
  active BOOLEAN,
  impact_minutes INT,
  event_date DATE
)
USING DELTA
PARTITIONED BY (event_date);

CREATE TABLE IF NOT EXISTS demos.logistics_control_center.raw_capacity_events (
  event_id STRING,
  laneId STRING,
  event_time TIMESTAMP,
  availableCapacity INT,
  utilizationPct DOUBLE,
  event_date DATE
)
USING DELTA
PARTITIONED BY (event_date);

SELECT 'OK: logistics_control_center foundation ready (tables + volumes).' AS status;
