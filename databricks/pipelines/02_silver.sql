CREATE OR REFRESH MATERIALIZED VIEW mv_latest_shipment_events
COMMENT "Latest known shipment event per tracking ID"
AS
WITH ranked AS (
  SELECT
    trackingId,
    laneId,
    status,
    eta_delta_minutes,
    event_time,
    ROW_NUMBER() OVER (PARTITION BY trackingId ORDER BY event_time DESC) AS rn
  FROM st_shipment_events
)
SELECT
  trackingId,
  laneId,
  status,
  eta_delta_minutes,
  event_time
FROM ranked
WHERE rn = 1;

CREATE OR REFRESH MATERIALIZED VIEW mv_latest_incident_events
COMMENT "Latest known incident status per incident ID"
AS
WITH ranked AS (
  SELECT
    incident_id,
    laneId,
    type,
    active,
    impact_minutes,
    event_time,
    ROW_NUMBER() OVER (PARTITION BY incident_id ORDER BY event_time DESC) AS rn
  FROM st_incident_events
)
SELECT
  incident_id,
  laneId,
  type,
  active,
  impact_minutes,
  event_time
FROM ranked
WHERE rn = 1;

CREATE OR REFRESH MATERIALIZED VIEW mv_latest_capacity_events
COMMENT "Latest known capacity status per lane"
AS
WITH ranked AS (
  SELECT
    laneId,
    availableCapacity,
    utilizationPct,
    event_time,
    ROW_NUMBER() OVER (PARTITION BY laneId ORDER BY event_time DESC) AS rn
  FROM st_capacity_events
)
SELECT
  laneId,
  availableCapacity,
  utilizationPct,
  event_time
FROM ranked
WHERE rn = 1;

CREATE OR REFRESH MATERIALIZED VIEW mv_sensor_hourly
COMMENT "Hourly sensor rollups by lane for monitoring and KPI views"
AS
SELECT
  lane_id AS laneId,
  date_trunc("hour", event_time) AS event_hour,
  AVG(vibration) AS avg_vibration,
  AVG(temp_c) AS avg_temp_c,
  AVG(gps_delay_minutes) AS avg_gps_delay_minutes,
  AVG(weather_risk) AS avg_weather_risk,
  COUNT(*) AS sample_count
FROM st_sensor_events
GROUP BY lane_id, date_trunc("hour", event_time);
