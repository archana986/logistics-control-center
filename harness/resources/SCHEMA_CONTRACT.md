# Schema Contract — Logistics Control Center

This document defines every table and view the application requires. It is the canonical reference for both **demo deploy** (synthetic data generation) and **customer data adapt** (column mapping).

## Serving Tables

These are the tables the FastAPI backend (`backend/db.py`) queries directly.

### `centers`
Distribution centers / logistics hubs shown on the map.

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| id | STRING | Yes | Primary key |
| name | STRING | Yes | Display name |
| lat | DOUBLE | Yes | Latitude |
| lng | DOUBLE | Yes | Longitude |
| type | STRING | Yes | e.g. "hub", "warehouse", "port" |
| region | STRING | No | Optional grouping |

**Used by:** `get_centers()` → map layer

### `lanes`
Shipping lanes connecting centers.

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| id | STRING | Yes | Primary key |
| origin | STRING | Yes | Origin center name |
| dest | STRING | Yes | Destination center name |
| mode | STRING | Yes | "air", "ground", "ocean" |
| avgDailyVolume | INT | Yes | Average daily package volume |
| onTimePct | DOUBLE | Yes | On-time delivery percentage (0-100) |
| delayMinutes | INT | Yes | Average delay in minutes |
| slaRiskPct | DOUBLE | Yes | SLA risk percentage (0-100) |
| maxCapacity | INT | No | Used by capacity_lanes |
| utilizationPct | DOUBLE | No | Used by capacity_lanes |
| availableCapacity | INT | No | Used by capacity_lanes |

**Used by:** `get_lanes()` → network view, arc layer

### `incidents`
Active and historical incidents on lanes.

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| id | STRING | Yes | Primary key |
| laneId | STRING | Yes | FK to lanes.id |
| timestamp | TIMESTAMP | Yes | When incident occurred |
| type | STRING | Yes | e.g. "weather", "mechanical", "congestion" |
| ref | STRING | No | Reference identifier |
| cause | STRING | No | Root cause description |
| impactMinutes | INT | No | Estimated delay impact |
| impactThroughputPct | DOUBLE | No | Throughput reduction percentage |
| confidence | DOUBLE | No | Detection confidence score |
| active | BOOLEAN | No | Whether incident is ongoing |

**Used by:** `get_incidents()` → incident drawer, incident cards

### `shipments`
Individual shipment tracking records.

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| trackingId | STRING | Yes | Primary key |
| customerId | STRING | Yes | FK to customers.id |
| priority | STRING | Yes | "standard", "express", "urgent" |
| laneId | STRING | Yes | FK to lanes.id |
| promisedETA | TIMESTAMP | No | Original promised ETA |
| currentETA | TIMESTAMP | No | Current estimated ETA |
| packageCount | INT | No | Number of packages |
| status | STRING | No | "in_transit", "delivered", "delayed" |

**Used by:** `api_shipment_lane_customer_metrics` view → `get_shipment_lane_metrics()`

### `customers`
Customer records.

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| id | STRING | Yes | Primary key |
| name | STRING | Yes | Customer name |
| contact | STRING | No | Contact info |
| tier | STRING | No | "gold", "silver", "bronze" |
| preferredCommunication | STRING | No | "email", "sms", "phone" |

**Used by:** `get_customers()` → customer panel

### `customer_interactions`
History of interactions with customers.

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| id | STRING | Yes | Primary key |
| customerId | STRING | Yes | FK to customers.id |
| date | TIMESTAMP | Yes | Interaction date |
| type | STRING | Yes | e.g. "call", "email", "chat" |
| summary | STRING | No | Interaction summary |
| sentiment | STRING | No | "positive", "neutral", "negative" |
| tags | STRING | No | Comma-separated tags |

**Used by:** `get_customer_interactions()` → customer detail view

### `capacity_lanes`
Lane capacity data for the capacity management view.

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| id | STRING | Yes | Primary key (same as lanes.id) |
| origin | STRING | Yes | Origin center |
| dest | STRING | Yes | Destination center |
| mode | STRING | Yes | Transport mode |
| avgDailyVolume | INT | No | Average daily volume |
| onTimePct | DOUBLE | No | On-time percentage |
| delayMinutes | INT | No | Average delay |
| slaRiskPct | DOUBLE | No | SLA risk percentage |
| maxCapacity | INT | Yes | Maximum lane capacity |
| utilizationPct | DOUBLE | Yes | Current utilization (0-100) |
| availableCapacity | INT | Yes | Remaining capacity |
| optimalUtilization | DOUBLE | No | Target utilization |

**Used by:** `get_capacity_lanes()` → capacity management view

### `capacity_actions`
Recommended or taken actions on capacity.

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| id | STRING | Yes | Primary key |
| laneId | STRING | Yes | FK to lanes.id |
| type | STRING | Yes | Action type |
| volumeChange | INT | Yes | Volume delta |
| npsImpact | INT | Yes | NPS score impact |
| costImpact | DOUBLE | Yes | Cost impact USD |
| efficiencyImpact | DOUBLE | Yes | Efficiency change |
| notes | STRING | No | Description |

**Used by:** `get_capacity_actions()` → capacity action panel

### `agent_activities`
Log of AI agent actions.

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| id | STRING | Yes | Primary key |
| laneId | STRING | Yes | FK to lanes.id |
| timestamp | TIMESTAMP | Yes | When action occurred |
| agentType | STRING | Yes | "reroute", "capacity", "customer" |
| situation | STRING | No | What triggered the agent |
| action | STRING | No | What the agent did |
| result | STRING | No | Outcome description |
| status | STRING | Yes | "completed", "pending", "failed" |
| metadata | STRING | No | JSON string with extra data |

**Used by:** `get_agent_activities()` → agent activity feed

### `sales_opportunities`
AI-generated sales opportunities from capacity analysis.

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| laneId | STRING | Yes | FK to lanes.id |
| activityId | STRING | Yes | FK to agent_activities.id |
| availableCapacity | INT | Yes | Capacity available to sell |
| forecastDate | DATE | Yes | Target date |
| targetCustomers | ARRAY<STRUCT> | No | Complex type: id, name, reason |
| pricing | STRUCT | No | Complex type: historical, recommended, discount |
| projectedImpact | STRUCT | No | Complex type: revenue, utilizationBefore/After, margin |

**Used by:** `get_sales_opportunities()` → sales opportunity panel

### `reroute_solutions`
AI-generated reroute suggestions for incidents.

| Column | Type | Required | Notes |
|--------|------|----------|-------|
| laneId | STRING | Yes | FK to lanes.id |
| strategy | STRING | Yes | Reroute strategy description |
| deltaETAminutes | INT | Yes | Additional ETA in minutes |
| addedCostUSD | DOUBLE | Yes | Additional cost |
| capacityUsedPct | DOUBLE | Yes | Capacity usage of alternative |
| notes | STRING | No | Details |

**Used by:** `get_reroute_suggestions()` → reroute panel in incident drawer

---

## Helper Views

Created by `create_helper_metric_views.sql`. These are SQL views over the serving tables.

### `api_shipment_lane_customer_metrics`
Aggregated shipment metrics per lane per customer.

| Column | Source Expression |
|--------|------------------|
| laneId | shipments.laneId |
| customerId | shipments.customerId |
| shipmentCount | COUNT(*) |
| urgentShipmentCount | SUM(CASE priority = 'urgent') |
| totalPackages | SUM(packageCount) |
| inTransitPackages | SUM(CASE status = 'in_transit') |
| delayedShipmentCount | SUM(CASE status = 'delayed') |

### `api_lane_health`
Lane health score combining on-time, delay, and SLA metrics.

| Column | Source |
|--------|--------|
| laneId, origin, dest, mode, avgDailyVolume, onTimePct, delayMinutes, slaRiskPct, maxCapacity, utilizationPct, availableCapacity | capacity_lanes |
| laneHealthScore | Computed: weighted combination of onTimePct, delayMinutes, slaRiskPct |

### `api_customer_rollup`
Customer-level rollup of shipment data.

| Column | Source |
|--------|--------|
| customer_id, customer_name, tier | customers |
| shipment_count | COUNT DISTINCT trackingId |
| in_transit_packages | SUM packageCount WHERE status = 'in_transit' |

---

## Genie Metric Views

These are YAML-defined metric views used by the Genie Space for natural language analytics.

### `network_metrics` (source: `api_lane_health`)
- **Dimensions:** Lane ID, Origin, Destination, Mode
- **Measures:** Avg Utilization Pct, Total Available Capacity, Avg Delay Minutes, Avg SLA Risk Pct, Avg Lane Health Score, Critical Lane Count

### `shipment_metrics` (source: `api_shipments` / `shipments`)
- **Dimensions:** Tracking ID, Lane ID, Customer ID, Priority, Status
- **Measures:** Shipment counts, status aggregations

### `capacity_metrics` (source: `api_capacity_lanes` / `capacity_lanes`)
- **Dimensions:** Lane ID, Origin, Destination, Mode
- **Measures:** Avg Utilization Pct, Total Available Capacity, Avg Delay Minutes

---

## Semantic Alias Map

When mapping customer data, these aliases should be considered equivalent:

| Contract Column | Common Aliases |
|----------------|----------------|
| id | identifier, key, code, _id |
| name | facility_name, center_name, customer_name, label |
| lat | latitude, y, lat_coord |
| lng | longitude, lon, x, lng_coord, long |
| laneId | lane_id, lane_code, route_id |
| customerId | customer_id, cust_id, client_id |
| trackingId | tracking_id, tracking_number, shipment_id, tracking_code |
| origin | source, from, from_city, origin_city, src |
| dest | destination, to, to_city, dest_city, dst |
| mode | transport_mode, shipping_mode, carrier_type |
| avgDailyVolume | avg_daily_volume, daily_volume, volume |
| onTimePct | on_time_pct, on_time_rate, otd_rate |
| delayMinutes | delay_minutes, avg_delay, delay_mins |
| slaRiskPct | sla_risk_pct, sla_risk, risk_pct |
| maxCapacity | max_capacity, capacity, total_capacity |
| utilizationPct | utilization_pct, utilization, util_pct |
| availableCapacity | available_capacity, free_capacity, remaining_capacity |
| impactMinutes | impact_minutes, delay_impact, impact_mins |
| deltaETAminutes | delta_eta_minutes, eta_delta, additional_eta |
| addedCostUSD | added_cost_usd, extra_cost, cost_delta |
| preferredCommunication | preferred_communication, contact_method, comm_preference |
