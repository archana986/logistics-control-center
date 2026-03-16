CREATE OR REFRESH MATERIALIZED VIEW logistics_shipments_gold
COMMENT "Serving shipment status with latest event deltas applied"
AS
SELECT
  s.trackingId,
  s.customerId,
  s.priority,
  s.laneId,
  s.promisedETA,
  CASE
    WHEN e.event_time IS NOT NULL THEN s.promisedETA + e.eta_delta_minutes * INTERVAL '1' MINUTE
    ELSE s.currentETA
  END AS currentETA,
  s.packageCount,
  COALESCE(e.status, s.status) AS status,
  current_timestamp() AS updated_at
FROM demos.logistics_control_center.shipments s
LEFT JOIN mv_latest_shipment_events e ON s.trackingId = e.trackingId;

CREATE OR REFRESH MATERIALIZED VIEW logistics_incidents_gold
COMMENT "Serving incident status merged with latest incident event stream"
AS
SELECT
  i.id,
  i.laneId,
  COALESCE(e.event_time, i.timestamp) AS timestamp,
  COALESCE(e.type, i.type) AS type,
  i.ref,
  i.cause,
  CAST(COALESCE(e.impact_minutes, i.impactMinutes) AS INT) AS impactMinutes,
  i.impactThroughputPct,
  i.confidence,
  COALESCE(e.active, i.active) AS active
FROM demos.logistics_control_center.incidents i
LEFT JOIN mv_latest_incident_events e ON i.id = e.incident_id;

CREATE OR REFRESH MATERIALIZED VIEW logistics_capacity_gold
COMMENT "Serving lane capacity merged with latest capacity stream"
AS
SELECT
  c.id,
  c.origin,
  c.dest,
  c.mode,
  c.avgDailyVolume,
  c.onTimePct,
  c.delayMinutes,
  c.slaRiskPct,
  c.maxCapacity,
  CAST(COALESCE(e.utilizationPct, c.utilizationPct) AS DOUBLE) AS utilizationPct,
  CAST(COALESCE(e.availableCapacity, c.availableCapacity) AS INT) AS availableCapacity,
  c.optimalUtilization,
  current_timestamp() AS updated_at
FROM demos.logistics_control_center.capacity_lanes c
LEFT JOIN mv_latest_capacity_events e ON c.id = e.laneId;

CREATE OR REFRESH MATERIALIZED VIEW logistics_lane_health_gold
COMMENT "Lane-level health index derived from latency, SLA risk, and sensor volatility"
AS
WITH latest_sensor AS (
  SELECT
    laneId,
    avg_vibration,
    avg_temp_c,
    avg_gps_delay_minutes,
    avg_weather_risk,
    ROW_NUMBER() OVER (PARTITION BY laneId ORDER BY event_hour DESC) AS rn
  FROM mv_sensor_hourly
)
SELECT
  l.id AS laneId,
  l.origin,
  l.dest,
  l.mode,
  l.delayMinutes,
  l.slaRiskPct,
  CAST(
    LEAST(
      100.0,
      (COALESCE(ls.avg_gps_delay_minutes, l.delayMinutes) * 0.6)
      + (l.slaRiskPct * 120.0)
      + (COALESCE(ls.avg_weather_risk, 0.0) * 35.0)
      + (COALESCE(ls.avg_vibration, 0.0) * 3.0)
    ) AS DOUBLE
  ) AS laneHealthScore,
  current_timestamp() AS updated_at
FROM demos.logistics_control_center.lanes l
LEFT JOIN latest_sensor ls ON l.id = ls.laneId AND ls.rn = 1;
