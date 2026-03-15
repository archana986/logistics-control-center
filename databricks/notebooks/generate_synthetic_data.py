"""Generates logistics synthetic master/event data and lands event files in UC Volumes."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, date

CATALOG = "demos"
SCHEMA = "logistics_control_center"
RAW_BASE = f"/Volumes/{CATALOG}/{SCHEMA}/raw_data"

random.seed(42)

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.raw_data")


def _write_overwrite(rows: list[dict], table_name: str) -> None:
    if not rows:
        return
    spark.createDataFrame(rows).write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(table_name)


def _append_files(rows: list[dict], path: str, fmt: str = "json") -> None:
    if not rows:
        return
    df = spark.createDataFrame(rows)
    if fmt == "json":
        df.coalesce(1).write.mode("append").json(path)
    else:
        df.coalesce(1).write.mode("append").parquet(path)


centers = [
    {"id": "HUB-ATL", "name": "Atlanta Hub", "lat": 33.64, "lng": -84.42, "type": "hub", "region": "Southeast"},
    {"id": "HUB-BNA", "name": "Nashville Hub", "lat": 36.13, "lng": -86.67, "type": "hub", "region": "Southeast"},
    {"id": "HUB-ORD", "name": "Chicago Hub", "lat": 41.97, "lng": -87.91, "type": "hub", "region": "Midwest"},
    {"id": "HUB-DFW", "name": "Dallas Hub", "lat": 32.90, "lng": -97.04, "type": "hub", "region": "South"},
    {"id": "HUB-STL", "name": "St Louis Hub", "lat": 38.75, "lng": -90.37, "type": "hub", "region": "Midwest"},
]

customers = [
    {"id": "CUST-WMT", "name": "Walmart Supply Chain", "contact": "ops@wmt.com", "tier": "platinum", "preferredCommunication": "proactive"},
    {"id": "CUST-UPS", "name": "UPS Marketplace", "contact": "ops@ups.com", "tier": "gold", "preferredCommunication": "email"},
    {"id": "CUST-AMZ", "name": "Amazon Retail", "contact": "ops@amazon.com", "tier": "platinum", "preferredCommunication": "proactive"},
    {"id": "CUST-TGT", "name": "Target Fulfillment", "contact": "ops@target.com", "tier": "gold", "preferredCommunication": "email"},
]

lane_pairs = [
    ("HUB-BNA", "HUB-STL", "air"),
    ("HUB-BNA", "HUB-ORD", "ground"),
    ("HUB-ATL", "HUB-ORD", "air"),
    ("HUB-DFW", "HUB-ORD", "ground"),
    ("HUB-ATL", "HUB-DFW", "ground"),
]

lanes: list[dict] = []
capacity_lanes: list[dict] = []
for idx, (origin, dest, mode) in enumerate(lane_pairs, start=1):
    lane_id = f"{origin}-{dest}-{mode.upper()}"
    max_capacity = random.randint(120000, 240000)
    avg_daily = int(max_capacity * random.uniform(0.55, 0.9))
    util = round(avg_daily / max_capacity, 4)
    lanes.append(
        {
            "id": lane_id,
            "origin": origin,
            "dest": dest,
            "mode": mode,
            "avgDailyVolume": avg_daily,
            "onTimePct": round(random.uniform(0.81, 0.97), 4),
            "delayMinutes": random.randint(15, 120),
            "slaRiskPct": round(random.uniform(0.03, 0.19), 4),
            "maxCapacity": max_capacity,
            "utilizationPct": util,
            "availableCapacity": max(0, max_capacity - avg_daily),
        }
    )
    capacity_lanes.append(
        {
            "id": lane_id,
            "origin": origin,
            "dest": dest,
            "mode": mode,
            "avgDailyVolume": avg_daily,
            "onTimePct": lanes[-1]["onTimePct"],
            "delayMinutes": lanes[-1]["delayMinutes"],
            "slaRiskPct": lanes[-1]["slaRiskPct"],
            "maxCapacity": max_capacity,
            "utilizationPct": util,
            "availableCapacity": max(0, max_capacity - avg_daily),
            "optimalUtilization": 0.82,
        }
    )

now = datetime.utcnow()
shipments: list[dict] = []
shipment_events: list[dict] = []
incident_rows: list[dict] = []
incident_events: list[dict] = []
capacity_events: list[dict] = []
sensor_events: list[dict] = []
customer_interactions: list[dict] = []

for i in range(180):
    lane = random.choice(lanes)
    customer = random.choice(customers)
    tracking_id = f"PKG-{100000+i}"
    promised = now + timedelta(minutes=random.randint(30, 240))
    delay = random.randint(-10, 70)
    current = promised + timedelta(minutes=delay)
    status = "delivered" if random.random() < 0.12 else "in_transit"
    shipments.append(
        {
            "trackingId": tracking_id,
            "customerId": customer["id"],
            "priority": random.choice(["LOW", "MED", "HIGH"]),
            "laneId": lane["id"],
            "promisedETA": promised,
            "currentETA": current if status == "in_transit" else now - timedelta(minutes=random.randint(5, 60)),
            "packageCount": random.randint(15, 450),
            "status": status,
        }
    )
    shipment_events.append(
        {
            "event_id": str(uuid.uuid4()),
            "trackingId": tracking_id,
            "laneId": lane["id"],
            "event_time": now,
            "status": status,
            "eta_delta_minutes": delay,
            "event_date": date.today(),
        }
    )

for lane in lanes:
    if random.random() < 0.65:
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        impact = random.randint(20, 160)
        is_active = random.random() < 0.7
        incident_rows.append(
            {
                "id": incident_id,
                "laneId": lane["id"],
                "timestamp": now - timedelta(minutes=random.randint(5, 360)),
                "type": random.choice(["weather", "air_traffic_control", "highway_delay", "equipment_issue"]),
                "ref": f"EVT-{random.randint(1000,9999)}",
                "cause": random.choice(
                    [
                        "Weather front impacted route reliability",
                        "Equipment maintenance hold",
                        "Highway congestion and lane closure",
                        "Airport departure queue delays",
                    ]
                ),
                "impactMinutes": impact,
                "impactThroughputPct": round(random.uniform(0.04, 0.35), 4),
                "confidence": round(random.uniform(0.78, 0.96), 4),
                "active": is_active,
            }
        )
        incident_events.append(
            {
                "event_id": str(uuid.uuid4()),
                "incident_id": incident_id,
                "laneId": lane["id"],
                "event_time": now,
                "type": incident_rows[-1]["type"],
                "active": is_active,
                "impact_minutes": impact,
                "event_date": date.today(),
            }
        )

for lane in capacity_lanes:
    utilization = max(0.45, min(0.99, lane["utilizationPct"] + random.uniform(-0.08, 0.08)))
    available = max(0, int(lane["maxCapacity"] * (1 - utilization)))
    capacity_events.append(
        {
            "event_id": str(uuid.uuid4()),
            "laneId": lane["id"],
            "event_time": now,
            "availableCapacity": available,
            "utilizationPct": round(utilization, 4),
            "event_date": date.today(),
        }
    )

for lane in lanes:
    for t in range(24):
        evt_time = now - timedelta(hours=t)
        sensor_events.append(
            {
                "event_id": str(uuid.uuid4()),
                "lane_id": lane["id"],
                "center_id": lane["origin"],
                "event_time": evt_time,
                "vibration": round(random.uniform(0.8, 3.6), 4),
                "temp_c": round(random.uniform(6.0, 34.0), 2),
                "gps_delay_minutes": random.randint(0, 80),
                "weather_risk": round(random.uniform(0.01, 0.9), 4),
                "event_date": evt_time.date(),
            }
        )

for customer in customers:
    for j in range(3):
        customer_interactions.append(
            {
                "id": str(uuid.uuid4()),
                "customerId": customer["id"],
                "date": now - timedelta(days=j, hours=random.randint(0, 8)),
                "type": random.choice(["email", "call", "ticket"]),
                "summary": random.choice(
                    [
                        "Reviewed SLA performance and proactive mitigation.",
                        "Provided ETA updates for delayed shipments.",
                        "Aligned on reroute strategy for critical lane.",
                    ]
                ),
                "sentiment": random.choice(["positive", "neutral"]),
                "tags": ["operations", "logistics"],
            }
        )

_write_overwrite(centers, f"{CATALOG}.{SCHEMA}.centers")
_write_overwrite(customers, f"{CATALOG}.{SCHEMA}.customers")
_write_overwrite(lanes, f"{CATALOG}.{SCHEMA}.lanes")
_write_overwrite(capacity_lanes, f"{CATALOG}.{SCHEMA}.capacity_lanes")
_write_overwrite(shipments, f"{CATALOG}.{SCHEMA}.shipments")
_write_overwrite(incident_rows, f"{CATALOG}.{SCHEMA}.incidents")
_write_overwrite(customer_interactions, f"{CATALOG}.{SCHEMA}.customer_interactions")

_append_files(shipment_events, f"{RAW_BASE}/shipment_events", "json")
_append_files(incident_events, f"{RAW_BASE}/incident_events", "json")
_append_files(capacity_events, f"{RAW_BASE}/capacity_events", "json")
_append_files(sensor_events, f"{RAW_BASE}/sensor_events", "parquet")

print("Synthetic logistics data generated successfully.")
print(f"Centers: {len(centers)} | Lanes: {len(lanes)} | Shipments: {len(shipments)} | Incidents: {len(incident_rows)}")
