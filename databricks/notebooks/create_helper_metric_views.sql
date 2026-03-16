-- Helper serving views and UC metric views for Logistics Control Center

-- Use existing namespace only.
USE CATALOG demos;
USE SCHEMA logistics_control_center;

CREATE OR REPLACE VIEW demos.logistics_control_center.api_shipments AS
SELECT * FROM demos.logistics_control_center.shipments;

CREATE OR REPLACE VIEW demos.logistics_control_center.api_incidents AS
SELECT * FROM demos.logistics_control_center.incidents;

CREATE OR REPLACE VIEW demos.logistics_control_center.api_capacity_lanes AS
SELECT * FROM demos.logistics_control_center.capacity_lanes;

CREATE OR REPLACE VIEW demos.logistics_control_center.api_lane_health AS
SELECT
  id AS laneId,
  origin,
  dest,
  mode,
  avgDailyVolume,
  onTimePct,
  delayMinutes,
  slaRiskPct,
  maxCapacity,
  utilizationPct,
  availableCapacity,
  -- Deterministic health score used by dashboards and Genie.
  ROUND(
    LEAST(
      100.0,
      GREATEST(
        0.0,
        (COALESCE(delayMinutes, 0) * 0.6) + (COALESCE(slaRiskPct, 0) * 0.4)
      )
    ),
    2
  ) AS laneHealthScore
FROM demos.logistics_control_center.lanes;

CREATE OR REPLACE VIEW demos.logistics_control_center.api_customer_rollup AS
SELECT
  c.id AS customer_id,
  c.name AS customer_name,
  c.tier,
  COUNT(DISTINCT s.trackingId) AS shipment_count,
  SUM(CASE WHEN s.status = 'in_transit' THEN s.packageCount ELSE 0 END) AS in_transit_packages
FROM demos.logistics_control_center.customers c
LEFT JOIN demos.logistics_control_center.api_shipments s ON c.id = s.customerId
GROUP BY c.id, c.name, c.tier;

CREATE OR REPLACE VIEW demos.logistics_control_center.network_metrics
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Top-level network KPIs for control tower operations."
  source: demos.logistics_control_center.api_lane_health
  dimensions:
    - name: Lane ID
      expr: laneId
    - name: Origin
      expr: origin
    - name: Destination
      expr: dest
    - name: Mode
      expr: mode
  measures:
    - name: Avg Delay Minutes
      expr: AVG(delayMinutes)
    - name: Avg SLA Risk Pct
      expr: AVG(slaRiskPct)
    - name: Avg Lane Health Score
      expr: AVG(laneHealthScore)
    - name: Critical Lane Count
      expr: SUM(CASE WHEN laneHealthScore >= 70 THEN 1 ELSE 0 END)
$$;

CREATE OR REPLACE VIEW demos.logistics_control_center.shipment_metrics
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Shipment service-level metrics."
  source: demos.logistics_control_center.api_shipments
  dimensions:
    - name: Tracking ID
      expr: trackingId
    - name: Lane ID
      expr: laneId
    - name: Customer ID
      expr: customerId
    - name: Priority
      expr: priority
    - name: Status
      expr: status
  measures:
    - name: Total Packages
      expr: SUM(packageCount)
    - name: In Transit Packages
      expr: SUM(CASE WHEN status = 'in_transit' THEN packageCount ELSE 0 END)
    - name: Delayed Shipment Count
      expr: SUM(CASE WHEN currentETA > promisedETA THEN 1 ELSE 0 END)
$$;

CREATE OR REPLACE VIEW demos.logistics_control_center.incident_metrics
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Incident severity and disruption metrics."
  source: demos.logistics_control_center.api_incidents
  dimensions:
    - name: Incident ID
      expr: id
    - name: Lane ID
      expr: laneId
    - name: Type
      expr: type
    - name: Active
      expr: active
  measures:
    - name: Incident Count
      expr: COUNT(id)
    - name: Active Incident Count
      expr: SUM(CASE WHEN active THEN 1 ELSE 0 END)
    - name: Avg Impact Minutes
      expr: AVG(impactMinutes)
    - name: Avg Confidence
      expr: AVG(confidence)
$$;

CREATE OR REPLACE VIEW demos.logistics_control_center.capacity_metrics
WITH METRICS
LANGUAGE YAML
AS $$
  version: 1.1
  comment: "Lane capacity and utilization metrics."
  source: demos.logistics_control_center.api_capacity_lanes
  dimensions:
    - name: Lane ID
      expr: id
    - name: Origin
      expr: origin
    - name: Destination
      expr: dest
    - name: Mode
      expr: mode
  measures:
    - name: Avg Utilization Pct
      expr: AVG(utilizationPct)
    - name: Total Available Capacity
      expr: SUM(availableCapacity)
    - name: Avg Delay Minutes
      expr: AVG(delayMinutes)
$$;

SELECT "OK: helper and metric views created" AS status;
