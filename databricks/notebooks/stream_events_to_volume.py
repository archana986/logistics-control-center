"""
Append synthetic incremental logistics events to UC volume landing zones.
Designed to be scheduled as a frequent job to feed the declarative pipeline.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, date

CATALOG = "demos"
SCHEMA = "logistics_control_center"
RAW_BASE = f"/Volumes/{CATALOG}/{SCHEMA}/raw_data"
now = datetime.utcnow()

lanes = [r.asDict() for r in spark.table(f"{CATALOG}.{SCHEMA}.lanes").select("id", "origin", "dest", "mode", "delayMinutes").collect()]
shipments = [r.asDict() for r in spark.table(f"{CATALOG}.{SCHEMA}.shipments").select("trackingId", "laneId", "status").orderBy("updated_at DESC").limit(40).collect()]
incidents = [r.asDict() for r in spark.table(f"{CATALOG}.{SCHEMA}.incidents").select("id", "laneId", "type", "active").limit(20).collect()]
capacity = [r.asDict() for r in spark.table(f"{CATALOG}.{SCHEMA}.capacity_lanes").select("id", "availableCapacity", "utilizationPct").collect()]

shipment_events: list[dict] = []
for s in shipments[: min(10, len(shipments))]:
    shipment_events.append(
        {
            "event_id": str(uuid.uuid4()),
            "trackingId": s["trackingId"],
            "laneId": s["laneId"],
            "event_time": now,
            "status": "delivered" if random.random() < 0.08 else "in_transit",
            "eta_delta_minutes": random.randint(-20, 45),
            "event_date": date.today(),
        }
    )

incident_events: list[dict] = []
for i in incidents[: min(4, len(incidents))]:
    incident_events.append(
        {
            "event_id": str(uuid.uuid4()),
            "incident_id": i["id"],
            "laneId": i["laneId"],
            "event_time": now,
            "type": i["type"],
            "active": random.random() >= 0.2,
            "impact_minutes": random.randint(20, 180),
            "event_date": date.today(),
        }
    )

if random.random() < 0.35 and lanes:
    lane = random.choice(lanes)
    incident_events.append(
        {
            "event_id": str(uuid.uuid4()),
            "incident_id": f"INC-{uuid.uuid4().hex[:8].upper()}",
            "laneId": lane["id"],
            "event_time": now,
            "type": random.choice(["weather", "equipment_issue", "air_traffic_control", "highway_delay"]),
            "active": True,
            "impact_minutes": random.randint(25, 160),
            "event_date": date.today(),
        }
    )

capacity_events: list[dict] = []
for c in capacity[: min(8, len(capacity))]:
    jitter = random.uniform(-0.06, 0.06)
    new_util = max(0.4, min(0.99, float(c["utilizationPct"]) + jitter))
    new_avail = max(0, int(float(c["availableCapacity"]) * random.uniform(0.9, 1.1)))
    capacity_events.append(
        {
            "event_id": str(uuid.uuid4()),
            "laneId": c["id"],
            "event_time": now,
            "availableCapacity": new_avail,
            "utilizationPct": round(new_util, 4),
            "event_date": date.today(),
        }
    )

sensor_events: list[dict] = []
for lane in lanes[: min(8, len(lanes))]:
    sensor_events.append(
        {
            "event_id": str(uuid.uuid4()),
            "lane_id": lane["id"],
            "center_id": lane["origin"],
            "event_time": now,
            "vibration": round(random.uniform(0.8, 4.1), 4),
            "temp_c": round(random.uniform(6.0, 35.0), 2),
            "gps_delay_minutes": max(0, int(lane.get("delayMinutes") or 0) + random.randint(-15, 20)),
            "weather_risk": round(random.uniform(0.01, 0.95), 4),
            "event_date": date.today(),
        }
    )

if shipment_events:
    spark.createDataFrame(shipment_events).coalesce(1).write.mode("append").json(f"{RAW_BASE}/shipment_events")
if incident_events:
    spark.createDataFrame(incident_events).coalesce(1).write.mode("append").json(f"{RAW_BASE}/incident_events")
if capacity_events:
    spark.createDataFrame(capacity_events).coalesce(1).write.mode("append").json(f"{RAW_BASE}/capacity_events")
if sensor_events:
    spark.createDataFrame(sensor_events).coalesce(1).write.mode("append").parquet(f"{RAW_BASE}/sensor_events")

print(
    "stream_events_to_volume wrote "
    f"{len(shipment_events)} shipment, {len(incident_events)} incident, "
    f"{len(capacity_events)} capacity, {len(sensor_events)} sensor events"
)
