"""
Refresh serving Delta tables from pipeline gold materialized views.
"""

CATALOG = "demos"
SCHEMA = "logistics_control_center"

spark.sql(
    f"""
    INSERT OVERWRITE {CATALOG}.{SCHEMA}.shipments
    SELECT
      trackingId,
      customerId,
      priority,
      laneId,
      promisedETA,
      currentETA,
      packageCount,
      status,
      updated_at
    FROM logistics_shipments_gold
    """
)

spark.sql(
    f"""
    INSERT OVERWRITE {CATALOG}.{SCHEMA}.incidents
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
      active,
      current_timestamp() AS created_at
    FROM logistics_incidents_gold
    """
)

spark.sql(
    f"""
    INSERT OVERWRITE {CATALOG}.{SCHEMA}.capacity_lanes
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
      optimalUtilization,
      updated_at
    FROM logistics_capacity_gold
    """
)

print("Serving tables refreshed from pipeline gold views.")
