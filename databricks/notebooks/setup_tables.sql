-- Create all Delta tables for logistics control center
-- Catalog: demos
-- Schema: logistics_control_center

-- Note: Column defaults require the delta.feature.allowColumnDefaults feature flag
-- This is enabled per-table via TBLPROPERTIES

-- Centers table
CREATE TABLE IF NOT EXISTS demos.logistics_control_center.centers (
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
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.feature.allowColumnDefaults' = 'supported'
);

-- Lanes table
CREATE TABLE IF NOT EXISTS demos.logistics_control_center.lanes (
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
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.feature.allowColumnDefaults' = 'supported'
);

-- Incidents table
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

-- Shipments table
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

-- Reroute solutions table
CREATE TABLE IF NOT EXISTS demos.logistics_control_center.reroute_solutions (
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
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.feature.allowColumnDefaults' = 'supported'
);

-- Customers table
CREATE TABLE IF NOT EXISTS demos.logistics_control_center.customers (
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
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.feature.allowColumnDefaults' = 'supported'
);

-- Customer interactions table
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

-- Capacity lanes table
CREATE TABLE IF NOT EXISTS demos.logistics_control_center.capacity_lanes (
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
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.feature.allowColumnDefaults' = 'supported'
);

-- Capacity actions table
CREATE TABLE IF NOT EXISTS demos.logistics_control_center.capacity_actions (
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
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.feature.allowColumnDefaults' = 'supported'
);

-- Agent activities table
CREATE TABLE IF NOT EXISTS demos.logistics_control_center.agent_activities (
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
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.feature.allowColumnDefaults' = 'supported'
);

-- Sales opportunities table
CREATE TABLE IF NOT EXISTS demos.logistics_control_center.sales_opportunities (
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
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.feature.allowColumnDefaults' = 'supported'
);
