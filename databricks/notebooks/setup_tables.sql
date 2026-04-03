-- Logistics Control Center data foundation
-- Parameters: catalog, schema (passed from databricks.yml as named parameters)
--
-- This script creates:
-- 1) schema if not exists
-- 2) managed volumes for raw files + documents
-- 3) canonical serving tables consumed by API/UI
-- 4) Delta options for efficient writes

-- Use catalog from parameter
USE CATALOG IDENTIFIER(:catalog);

-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS IDENTIFIER(:schema);
USE SCHEMA IDENTIFIER(:schema);

-- Volumes use string concatenation with IDENTIFIER
CREATE VOLUME IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.raw_data');
CREATE VOLUME IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.documents');

-- ---------------------------
-- Serving dimensions/facts
-- ---------------------------
CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.centers') (
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

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.customers') (
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

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.lanes') (
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

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.shipments') (
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

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.incidents') (
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

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.customer_interactions') (
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

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.capacity_lanes') (
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

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.capacity_actions') (
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

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.agent_activities') (
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

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.sales_opportunities') (
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

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.reroute_solutions') (
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
CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.raw_sensor_events') (
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

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.raw_shipment_events') (
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

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.raw_incident_events') (
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

CREATE TABLE IF NOT EXISTS IDENTIFIER(:catalog || '.' || :schema || '.raw_capacity_events') (
  event_id STRING,
  laneId STRING,
  event_time TIMESTAMP,
  availableCapacity INT,
  utilizationPct DOUBLE,
  event_date DATE
)
USING DELTA
PARTITIONED BY (event_date);

SELECT CONCAT('OK: ', :schema, ' foundation ready (tables + volumes).') AS status;
