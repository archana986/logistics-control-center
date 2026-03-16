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
    {"id": "BNA", "name": "Nashville SuperHub", "lat": 36.124, "lng": -86.678, "type": "air_hub", "region": "Southeast"},
    {"id": "STL", "name": "Saint Louis Hub", "lat": 38.747, "lng": -90.361, "type": "dc", "region": "Midwest"},
    {"id": "ORD", "name": "Chicago O'Hare Hub", "lat": 41.974, "lng": -87.907, "type": "air_hub", "region": "Midwest"},
    {"id": "ATL", "name": "Atlanta Hub", "lat": 33.640, "lng": -84.427, "type": "air_hub", "region": "Southeast"},
    {"id": "DFW", "name": "Dallas-Fort Worth SuperHub", "lat": 32.897, "lng": -97.038, "type": "air_hub", "region": "South"},
    {"id": "LAX", "name": "Los Angeles Hub", "lat": 33.942, "lng": -118.408, "type": "air_hub", "region": "West"},
    {"id": "EWR", "name": "Newark Gateway Hub", "lat": 40.692, "lng": -74.169, "type": "air_hub", "region": "Northeast"},
    {"id": "OAK", "name": "Oakland West Coast Hub", "lat": 37.721, "lng": -122.221, "type": "air_hub", "region": "West"},
    {"id": "PHX", "name": "Phoenix Distribution Hub", "lat": 33.435, "lng": -112.006, "type": "dc", "region": "Southwest"},
    {"id": "SEA", "name": "Seattle-Tacoma Hub", "lat": 47.449, "lng": -122.309, "type": "air_hub", "region": "Northwest"},
    {"id": "MIA", "name": "Miami International Hub", "lat": 25.796, "lng": -80.274, "type": "air_hub", "region": "Southeast"},
    {"id": "DEN", "name": "Denver Mountain Hub", "lat": 39.856, "lng": -104.673, "type": "air_hub", "region": "Mountain"},
    {"id": "PIT", "name": "Pittsburgh International Hub", "lat": 40.491, "lng": -80.233, "type": "air_hub", "region": "Northeast"},
    {"id": "ANC", "name": "Anchorage International Hub", "lat": 61.174, "lng": -149.996, "type": "air_hub", "region": "Alaska"},
    {"id": "BOS", "name": "Boston Regional Hub", "lat": 42.365, "lng": -71.010, "type": "dc", "region": "Northeast"},
    {"id": "PHL", "name": "Philadelphia Hub", "lat": 39.872, "lng": -75.241, "type": "dc", "region": "Northeast"},
    {"id": "MSP", "name": "Minneapolis-St. Paul Hub", "lat": 44.883, "lng": -93.222, "type": "dc", "region": "Midwest"},
    {"id": "SLC", "name": "Salt Lake City Hub", "lat": 40.789, "lng": -111.978, "type": "dc", "region": "Mountain"},
    {"id": "CLT", "name": "Charlotte Regional Hub", "lat": 35.214, "lng": -80.943, "type": "dc", "region": "Southeast"},
    {"id": "LAS", "name": "Las Vegas Distribution Center", "lat": 36.081, "lng": -115.152, "type": "dc", "region": "Southwest"},
]

customers = [
    {"id": "CUST-WMT", "name": "Walmart Supply Chain", "contact": "ops@wmt.com", "tier": "platinum", "preferredCommunication": "proactive"},
    {"id": "CUST-UPS", "name": "UPS Marketplace", "contact": "ops@ups.com", "tier": "gold", "preferredCommunication": "email"},
    {"id": "CUST-AMZ", "name": "Amazon Retail", "contact": "ops@amazon.com", "tier": "platinum", "preferredCommunication": "proactive"},
    {"id": "CUST-TGT", "name": "Target Fulfillment", "contact": "ops@target.com", "tier": "gold", "preferredCommunication": "email"},
]

lane_templates = [
    {"id": "BNA-PIT-AIR", "origin": "BNA", "dest": "PIT", "mode": "air", "avgDailyVolume": 425000, "onTimePct": 0.96, "delayMinutes": 18, "slaRiskPct": 0.04},
    {"id": "PIT-ORD-AIR", "origin": "PIT", "dest": "ORD", "mode": "air", "avgDailyVolume": 380000, "onTimePct": 0.95, "delayMinutes": 22, "slaRiskPct": 0.05},
    {"id": "BNA-STL-AIR", "origin": "BNA", "dest": "STL", "mode": "air", "avgDailyVolume": 285000, "onTimePct": 0.87, "delayMinutes": 140, "slaRiskPct": 0.13},
    {"id": "BNA-STL-GROUND", "origin": "BNA", "dest": "STL", "mode": "ground", "avgDailyVolume": 125000, "onTimePct": 0.78, "delayMinutes": 185, "slaRiskPct": 0.22},
    {"id": "BNA-ORD-AIR", "origin": "BNA", "dest": "ORD", "mode": "air", "avgDailyVolume": 340000, "onTimePct": 0.94, "delayMinutes": 35, "slaRiskPct": 0.06},
    {"id": "ORD-STL-GROUND", "origin": "ORD", "dest": "STL", "mode": "ground", "avgDailyVolume": 145000, "onTimePct": 0.96, "delayMinutes": 22, "slaRiskPct": 0.04},
    {"id": "BNA-ATL-AIR", "origin": "BNA", "dest": "ATL", "mode": "air", "avgDailyVolume": 295000, "onTimePct": 0.92, "delayMinutes": 48, "slaRiskPct": 0.08},
    {"id": "ATL-STL-AIR", "origin": "ATL", "dest": "STL", "mode": "air", "avgDailyVolume": 215000, "onTimePct": 0.95, "delayMinutes": 28, "slaRiskPct": 0.05},
    {"id": "BNA-DFW-GROUND", "origin": "BNA", "dest": "DFW", "mode": "ground", "avgDailyVolume": 310000, "onTimePct": 0.91, "delayMinutes": 52, "slaRiskPct": 0.09},
    {"id": "DFW-LAX-AIR", "origin": "DFW", "dest": "LAX", "mode": "air", "avgDailyVolume": 365000, "onTimePct": 0.93, "delayMinutes": 41, "slaRiskPct": 0.07},
    {"id": "BNA-EWR-AIR", "origin": "BNA", "dest": "EWR", "mode": "air", "avgDailyVolume": 405000, "onTimePct": 0.94, "delayMinutes": 32, "slaRiskPct": 0.06},
    {"id": "EWR-BOS-GROUND", "origin": "EWR", "dest": "BOS", "mode": "ground", "avgDailyVolume": 175000, "onTimePct": 0.97, "delayMinutes": 15, "slaRiskPct": 0.03},
    {"id": "LAX-OAK-GROUND", "origin": "LAX", "dest": "OAK", "mode": "ground", "avgDailyVolume": 235000, "onTimePct": 0.96, "delayMinutes": 20, "slaRiskPct": 0.04},
    {"id": "OAK-SEA-AIR", "origin": "OAK", "dest": "SEA", "mode": "air", "avgDailyVolume": 190000, "onTimePct": 0.95, "delayMinutes": 25, "slaRiskPct": 0.05},
    {"id": "SEA-ANC-AIR", "origin": "SEA", "dest": "ANC", "mode": "air", "avgDailyVolume": 85000, "onTimePct": 0.92, "delayMinutes": 45, "slaRiskPct": 0.08},
    {"id": "DFW-PHX-AIR", "origin": "DFW", "dest": "PHX", "mode": "air", "avgDailyVolume": 265000, "onTimePct": 0.94, "delayMinutes": 30, "slaRiskPct": 0.06},
    {"id": "PHX-LAS-GROUND", "origin": "PHX", "dest": "LAS", "mode": "ground", "avgDailyVolume": 145000, "onTimePct": 0.96, "delayMinutes": 18, "slaRiskPct": 0.04},
    {"id": "ATL-MIA-AIR", "origin": "ATL", "dest": "MIA", "mode": "air", "avgDailyVolume": 275000, "onTimePct": 0.93, "delayMinutes": 38, "slaRiskPct": 0.07},
    {"id": "ATL-CLT-GROUND", "origin": "ATL", "dest": "CLT", "mode": "ground", "avgDailyVolume": 185000, "onTimePct": 0.97, "delayMinutes": 12, "slaRiskPct": 0.03},
    {"id": "ORD-MSP-GROUND", "origin": "ORD", "dest": "MSP", "mode": "ground", "avgDailyVolume": 195000, "onTimePct": 0.96, "delayMinutes": 20, "slaRiskPct": 0.04},
    {"id": "DEN-SLC-AIR", "origin": "DEN", "dest": "SLC", "mode": "air", "avgDailyVolume": 155000, "onTimePct": 0.95, "delayMinutes": 24, "slaRiskPct": 0.05},
    {"id": "SLC-OAK-AIR", "origin": "SLC", "dest": "OAK", "mode": "air", "avgDailyVolume": 165000, "onTimePct": 0.94, "delayMinutes": 28, "slaRiskPct": 0.06},
    {"id": "EWR-PHL-GROUND", "origin": "EWR", "dest": "PHL", "mode": "ground", "avgDailyVolume": 210000, "onTimePct": 0.98, "delayMinutes": 8, "slaRiskPct": 0.02},
    {"id": "PIT-ATL-AIR", "origin": "PIT", "dest": "ATL", "mode": "air", "avgDailyVolume": 320000, "onTimePct": 0.96, "delayMinutes": 18, "slaRiskPct": 0.04},
    {"id": "PIT-STL-GROUND", "origin": "PIT", "dest": "STL", "mode": "ground", "avgDailyVolume": 295000, "onTimePct": 0.95, "delayMinutes": 22, "slaRiskPct": 0.05},
    {"id": "PIT-LAX-AIR", "origin": "PIT", "dest": "LAX", "mode": "air", "avgDailyVolume": 350000, "onTimePct": 0.94, "delayMinutes": 28, "slaRiskPct": 0.06},
    {"id": "ORD-DEN-AIR", "origin": "ORD", "dest": "DEN", "mode": "air", "avgDailyVolume": 245000, "onTimePct": 0.95, "delayMinutes": 23, "slaRiskPct": 0.05},
    {"id": "LAX-PHX-GROUND", "origin": "LAX", "dest": "PHX", "mode": "ground", "avgDailyVolume": 225000, "onTimePct": 0.95, "delayMinutes": 24, "slaRiskPct": 0.05},
    {"id": "DFW-ATL-AIR", "origin": "DFW", "dest": "ATL", "mode": "air", "avgDailyVolume": 305000, "onTimePct": 0.93, "delayMinutes": 35, "slaRiskPct": 0.07},
    {"id": "ATL-EWR-AIR", "origin": "ATL", "dest": "EWR", "mode": "air", "avgDailyVolume": 385000, "onTimePct": 0.94, "delayMinutes": 30, "slaRiskPct": 0.06},
    {"id": "MIA-ATL-AIR", "origin": "MIA", "dest": "ATL", "mode": "air", "avgDailyVolume": 265000, "onTimePct": 0.94, "delayMinutes": 32, "slaRiskPct": 0.06},
    {"id": "DEN-PHX-AIR", "origin": "DEN", "dest": "PHX", "mode": "air", "avgDailyVolume": 185000, "onTimePct": 0.96, "delayMinutes": 19, "slaRiskPct": 0.04},
    {"id": "ORD-EWR-AIR", "origin": "ORD", "dest": "EWR", "mode": "air", "avgDailyVolume": 395000, "onTimePct": 0.93, "delayMinutes": 38, "slaRiskPct": 0.07},
    {"id": "LAX-DEN-AIR", "origin": "LAX", "dest": "DEN", "mode": "air", "avgDailyVolume": 275000, "onTimePct": 0.94, "delayMinutes": 30, "slaRiskPct": 0.06},
    {"id": "SEA-ORD-AIR", "origin": "SEA", "dest": "ORD", "mode": "air", "avgDailyVolume": 285000, "onTimePct": 0.93, "delayMinutes": 36, "slaRiskPct": 0.07},
    {"id": "BOS-EWR-GROUND", "origin": "BOS", "dest": "EWR", "mode": "ground", "avgDailyVolume": 165000, "onTimePct": 0.97, "delayMinutes": 14, "slaRiskPct": 0.03},
]


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


lanes: list[dict] = []
capacity_lanes: list[dict] = []
for template in lane_templates:
    avg_daily = int(_clamp(random.gauss(template["avgDailyVolume"], template["avgDailyVolume"] * 0.08), 60000, 550000))
    on_time = round(_clamp(random.gauss(template["onTimePct"], 0.015), 0.72, 0.985), 4)
    delay = int(round(_clamp(random.gauss(template["delayMinutes"], max(3.0, template["delayMinutes"] * 0.18)), 5, 220)))
    sla_risk = round(_clamp(random.gauss(template["slaRiskPct"], 0.012), 0.02, 0.28), 4)

    baseline_util = _clamp(random.gauss(0.78, 0.08), 0.56, 0.94)
    max_capacity = int(max(avg_daily + 10000, avg_daily / baseline_util))
    utilization = round(_clamp(avg_daily / max_capacity, 0.45, 0.98), 4)
    available = max(0, max_capacity - avg_daily)

    lanes.append(
        {
            "id": template["id"],
            "origin": template["origin"],
            "dest": template["dest"],
            "mode": template["mode"],
            "avgDailyVolume": avg_daily,
            "onTimePct": on_time,
            "delayMinutes": delay,
            "slaRiskPct": sla_risk,
            "maxCapacity": max_capacity,
            "utilizationPct": utilization,
            "availableCapacity": available,
        }
    )
    capacity_lanes.append(
        {
            "id": template["id"],
            "origin": template["origin"],
            "dest": template["dest"],
            "mode": template["mode"],
            "avgDailyVolume": avg_daily,
            "onTimePct": on_time,
            "delayMinutes": delay,
            "slaRiskPct": sla_risk,
            "maxCapacity": max_capacity,
            "utilizationPct": utilization,
            "availableCapacity": available,
            "optimalUtilization": 0.82,
        }
    )

# Ensure BNA-STL narrative lanes have high delay (red on map) and elevated SLA risk for demo
for lane in lanes:
    if lane["id"] == "BNA-STL-AIR":
        lane["delayMinutes"] = random.randint(105, 150)
        lane["slaRiskPct"] = round(random.uniform(0.11, 0.16), 4)
        lane["onTimePct"] = round(random.uniform(0.82, 0.9), 4)
    if lane["id"] == "BNA-STL-GROUND":
        lane["delayMinutes"] = random.randint(160, 210)
        lane["slaRiskPct"] = round(random.uniform(0.17, 0.24), 4)
        lane["onTimePct"] = round(random.uniform(0.72, 0.82), 4)
for cap in capacity_lanes:
    if cap["id"] in {"BNA-STL-AIR", "BNA-STL-GROUND"}:
        cap["delayMinutes"] = next(l["delayMinutes"] for l in lanes if l["id"] == cap["id"])
        cap["slaRiskPct"] = next(l["slaRiskPct"] for l in lanes if l["id"] == cap["id"])
        cap["onTimePct"] = next(l["onTimePct"] for l in lanes if l["id"] == cap["id"])

now = datetime.utcnow()
shipments: list[dict] = []
shipment_events: list[dict] = []
incident_rows: list[dict] = []
incident_events: list[dict] = []
capacity_events: list[dict] = []
sensor_events: list[dict] = []
customer_interactions: list[dict] = []

shipment_seq = 100000
for lane in lanes:
    lane_id = lane["id"]
    lane_volume = int(lane.get("avgDailyVolume") or 0)
    mode = lane.get("mode", "ground")
    is_narrative_lane = lane_id in {"BNA-STL-AIR", "BNA-STL-GROUND"}

    # Scale shipment rows by lane volume so larger lanes naturally carry more records.
    avg_packages_per_shipment = 26 if mode == "ground" else 24
    baseline_shipments = max(2500, int(lane_volume / max(1, avg_packages_per_shipment)))
    if is_narrative_lane:
        baseline_shipments = max(9000, baseline_shipments)
    shipment_count = int(_clamp(random.gauss(baseline_shipments, baseline_shipments * 0.08), 1500, 14000))

    for _ in range(shipment_count):
        customer = random.choice(customers)
        tracking_id = f"PKG-{shipment_seq}"
        shipment_seq += 1

        promised = now + timedelta(minutes=random.randint(30, 360))
        delay_center = _clamp(lane["delayMinutes"] * 0.45 - 5, -10, 120)
        delay_spread = 12 if lane["delayMinutes"] < 50 else 22
        delay = int(round(_clamp(random.gauss(delay_center, delay_spread), -25, 220)))
        current = promised + timedelta(minutes=delay)

        delivered_prob = 0.22 if not is_narrative_lane else 0.14
        status = "delivered" if random.random() < delivered_prob else "in_transit"

        # Keep package counts realistic while matching lane-level daily volume on average.
        package_mean = max(8.0, lane_volume / max(1, shipment_count))
        package_count = int(_clamp(random.gauss(package_mean, package_mean * 0.35), 1, 90))

        if is_narrative_lane:
            priority = random.choices(["LOW", "MED", "HIGH"], weights=[0.15, 0.45, 0.40], k=1)[0]
        else:
            priority = random.choices(["LOW", "MED", "HIGH"], weights=[0.35, 0.45, 0.20], k=1)[0]

        shipments.append(
            {
                "trackingId": tracking_id,
                "customerId": customer["id"],
                "priority": priority,
                "laneId": lane_id,
                "promisedETA": promised,
                "currentETA": current if status == "in_transit" else now - timedelta(minutes=random.randint(5, 120)),
                "packageCount": package_count,
                "status": status,
            }
        )
        shipment_events.append(
            {
                "event_id": str(uuid.uuid4()),
                "trackingId": tracking_id,
                "laneId": lane_id,
                "event_time": now,
                "status": status,
                "eta_delta_minutes": delay,
                "event_date": date.today(),
            }
        )

# Narrative lanes (BNA-STL) must always have incidents for demo flows: reroute urgent packages, AI root cause analysis
NARRATIVE_LANE_IDS = {"BNA-STL-AIR", "BNA-STL-GROUND"}

for lane in lanes:
    is_narrative = lane["id"] in NARRATIVE_LANE_IDS
    if is_narrative or random.random() < 0.22:
        incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        impact = random.randint(20, 160) if not is_narrative else random.randint(90, 180)
        is_active = random.random() < 0.7 if not is_narrative else True
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
