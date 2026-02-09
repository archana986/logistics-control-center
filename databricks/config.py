"""Shared configuration for Databricks logistics demo."""

CATALOG = "demos"
SCHEMA = "logistics_control_center"
VOLUME = "documents"  # UC Volume for unstructured docs

TABLE_NAMES = {
    "centers": f"{CATALOG}.{SCHEMA}.centers",
    "lanes": f"{CATALOG}.{SCHEMA}.lanes",
    "incidents": f"{CATALOG}.{SCHEMA}.incidents",
    "shipments": f"{CATALOG}.{SCHEMA}.shipments",
    "reroute_solutions": f"{CATALOG}.{SCHEMA}.reroute_solutions",
    "customers": f"{CATALOG}.{SCHEMA}.customers",
    "customer_interactions": f"{CATALOG}.{SCHEMA}.customer_interactions",
    "capacity_lanes": f"{CATALOG}.{SCHEMA}.capacity_lanes",
    "capacity_actions": f"{CATALOG}.{SCHEMA}.capacity_actions",
    "agent_activities": f"{CATALOG}.{SCHEMA}.agent_activities",
    "sales_opportunities": f"{CATALOG}.{SCHEMA}.sales_opportunities",
}

VOLUME_PATH = f"{CATALOG}.{SCHEMA}.{VOLUME}"
