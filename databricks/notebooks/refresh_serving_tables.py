"""
Refresh serving Delta tables from pipeline gold materialized views.
"""

CATALOG = "demos"
SCHEMA = "logistics_control_center"
GOLD = f"{CATALOG}.{SCHEMA}"

spark.sql(
    f"""
    INSERT OVERWRITE {CATALOG}.{SCHEMA}.shipments (trackingId, customerId, priority, laneId, promisedETA, currentETA, packageCount, status)
    SELECT
      trackingId,
      customerId,
      priority,
      laneId,
      promisedETA,
      currentETA,
      packageCount,
      status
    FROM {GOLD}.logistics_shipments_gold
    """
)

spark.sql(
    f"""
    INSERT OVERWRITE {CATALOG}.{SCHEMA}.incidents (id, laneId, timestamp, type, ref, cause, impactMinutes, impactThroughputPct, confidence, active)
    SELECT
      id,
      laneId,
      timestamp,
      type,
      ref,
      cause,
      impactMinutes,
      impactThroughputPct,
      confidence,
      active
    FROM {GOLD}.logistics_incidents_gold
    """
)

spark.sql(
    f"""
    INSERT OVERWRITE {CATALOG}.{SCHEMA}.capacity_lanes (id, origin, dest, mode, avgDailyVolume, onTimePct, delayMinutes, slaRiskPct, maxCapacity, utilizationPct, availableCapacity, optimalUtilization)
    SELECT
      id,
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
      optimalUtilization
    FROM {GOLD}.logistics_capacity_gold
    """
)

print("Serving tables refreshed from pipeline gold views.")
