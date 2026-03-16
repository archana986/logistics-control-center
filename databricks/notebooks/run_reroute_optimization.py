"""
Simple lane reroute optimizer.

Produces ranked reroute options based on:
- estimated ETA delta
- capacity fit
- added cost
"""

from __future__ import annotations

CATALOG = "demos"
SCHEMA = "logistics_control_center"

lanes_df = spark.table(f"{CATALOG}.{SCHEMA}.capacity_lanes")
incidents_df = spark.table(f"{CATALOG}.{SCHEMA}.incidents").where("active = true")

lanes = [r.asDict() for r in lanes_df.collect()]
incident_lanes = {r["laneId"] for r in incidents_df.select("laneId").distinct().collect()}

results: list[dict] = []

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
        utilization = float(candidate.get("utilizationPct") or 0.8)

        # Keep values in a realistic demo range (close to public mock data shape).
        if coverage_ratio >= 0.35:
            delta_eta = -int(600 + coverage_ratio * 900)  # usually faster than waiting on disrupted lane
        else:
            delta_eta = int(90 + (0.35 - coverage_ratio) * 600)  # constrained options add delay

        raw_cost = 1800 + (1.0 - coverage_ratio) * 2600 + utilization * 1000
        added_cost = round(min(5500.0, max(1500.0, raw_cost)), 2)
        capacity_used_pct = round(min(95.0, max(10.0, (demand / max(1, available)) * 100)), 2)

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
          tgt.notes = src.notes
        WHEN NOT MATCHED THEN INSERT (
          laneId, strategy, deltaETAminutes, addedCostUSD, capacityUsedPct, notes
        ) VALUES (
          src.laneId, src.strategy, src.deltaETAminutes, src.addedCostUSD, src.capacityUsedPct, src.notes
        )
        """
    )
    print(f"Upserted {len(results)} reroute candidates.")
