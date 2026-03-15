"""
Simple lane reroute optimizer.

Produces ranked reroute options based on:
- estimated ETA delta
- capacity fit
- added cost
"""

from __future__ import annotations

from datetime import datetime

CATALOG = "demos"
SCHEMA = "logistics_control_center"

lanes_df = spark.table(f"{CATALOG}.{SCHEMA}.capacity_lanes")
incidents_df = spark.table(f"{CATALOG}.{SCHEMA}.incidents").where("active = true")

lanes = [r.asDict() for r in lanes_df.collect()]
incident_lanes = {r["laneId"] for r in incidents_df.select("laneId").distinct().collect()}

results: list[dict] = []
now = datetime.utcnow()

for lane in lanes:
    lane_id = lane["id"]
    if lane_id not in incident_lanes:
        continue

    demand = int(lane.get("avgDailyVolume") or 0)
    for candidate in lanes:
        if candidate["id"] == lane_id:
            continue
        if candidate.get("mode") != lane.get("mode"):
            continue

        available = int(candidate.get("availableCapacity") or 0)
        if available <= 0:
            continue

        coverage_ratio = min(1.0, available / max(1, demand))
        delta_eta = int(15 + (1.0 - coverage_ratio) * 90)
        added_cost = round((1.0 - coverage_ratio) * 2200 + (candidate.get("utilizationPct") or 0.8) * 1400, 2)
        capacity_used_pct = round(min(1.0, demand / max(1, available)) * 100, 2)

        strategy = f"Reroute via {candidate['origin']}->{candidate['dest']}"
        notes = (
            f"Candidate lane {candidate['id']} covers {coverage_ratio:.0%} of disrupted volume. "
            f"Mode matched on {candidate.get('mode')}."
        )
        results.append(
            {
                "laneId": lane_id,
                "strategy": strategy,
                "deltaETAminutes": delta_eta,
                "addedCostUSD": added_cost,
                "capacityUsedPct": capacity_used_pct,
                "notes": notes,
                "created_at": now,
            }
        )

if not results:
    print("No active incident lanes found. Nothing to optimize.")
else:
    out_df = spark.createDataFrame(results)
    out_df.createOrReplaceTempView("reroute_updates")
    spark.sql(
        f"""
        MERGE INTO {CATALOG}.{SCHEMA}.reroute_solutions AS tgt
        USING reroute_updates AS src
        ON tgt.laneId = src.laneId AND tgt.strategy = src.strategy
        WHEN MATCHED THEN UPDATE SET
          tgt.deltaETAminutes = src.deltaETAminutes,
          tgt.addedCostUSD = src.addedCostUSD,
          tgt.capacityUsedPct = src.capacityUsedPct,
          tgt.notes = src.notes,
          tgt.created_at = src.created_at
        WHEN NOT MATCHED THEN INSERT *
        """
    )
    print(f"Upserted {len(results)} reroute candidates.")
