CREATE OR REFRESH STREAMING TABLE st_shipment_events
COMMENT "Bronze shipment events from UC Volume landing zone"
AS SELECT *
FROM STREAM READ_FILES(
  "/Volumes/demos/logistics_control_center/raw_data/shipment_events",
  format => "json",
  inferColumnTypes => true
);

CREATE OR REFRESH STREAMING TABLE st_incident_events
COMMENT "Bronze incident events from UC Volume landing zone"
AS SELECT *
FROM STREAM READ_FILES(
  "/Volumes/demos/logistics_control_center/raw_data/incident_events",
  format => "json",
  inferColumnTypes => true
);

CREATE OR REFRESH STREAMING TABLE st_capacity_events
COMMENT "Bronze capacity events from UC Volume landing zone"
AS SELECT *
FROM STREAM READ_FILES(
  "/Volumes/demos/logistics_control_center/raw_data/capacity_events",
  format => "json",
  inferColumnTypes => true
);

CREATE OR REFRESH STREAMING TABLE st_sensor_events
COMMENT "Bronze sensor events from UC Volume landing zone"
AS SELECT *
FROM STREAM READ_FILES(
  "/Volumes/demos/logistics_control_center/raw_data/sensor_events",
  format => "parquet",
  inferColumnTypes => true
);
