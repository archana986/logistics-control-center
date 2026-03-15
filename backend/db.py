"""Database layer for querying Delta tables via SQL Warehouse."""

from __future__ import annotations

import json
import os
from typing import Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState


class LogisticsDB:
    """Query logistics tables and views via SQL Warehouse."""

    def __init__(self, client: WorkspaceClient, warehouse_id: str):
        self.client = client
        self.warehouse_id = warehouse_id
        self.catalog = os.getenv("DATABRICKS_CATALOG", "demos")
        self.schema = os.getenv("DATABRICKS_SCHEMA", "logistics_control_center")

    @staticmethod
    def _parse_value(val: str, type_name: str):
        if val is None:
            return None
        type_upper = (type_name or "").upper()
        if type_upper in ("INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT", "LONG"):
            try:
                return int(val)
            except (ValueError, TypeError):
                return val
        if type_upper in ("DOUBLE", "FLOAT", "DECIMAL"):
            try:
                return float(val)
            except (ValueError, TypeError):
                return val
        if type_upper == "BOOLEAN":
            return str(val).lower() in ("true", "1", "yes")
        return val

    def _tbl(self, name: str) -> str:
        return f"{self.catalog}.{self.schema}.{name}"

    @staticmethod
    def _esc(value: str) -> str:
        return value.replace("'", "''")

    def _execute_query(self, sql: str) -> list[dict]:
        execution = self.client.statement_execution.execute_statement(
            warehouse_id=self.warehouse_id,
            statement=sql,
            wait_timeout="30s",
        )

        state = execution.status.state if execution.status else None
        if state != StatementState.SUCCEEDED:
            err = execution.status.error if execution.status else "unknown"
            raise RuntimeError(f"SQL failed: {state}; {err}")

        if not execution.result or not execution.result.data_array:
            return []

        columns = execution.result.manifest.schema.columns
        col_names = [col.name for col in columns]
        col_types = [getattr(col, "type_name", "STRING") or "STRING" for col in columns]
        output: list[dict] = []
        for row in execution.result.data_array:
            parsed = {}
            for i, col_name in enumerate(col_names):
                val = row[i] if i < len(row) else None
                parsed[col_name] = self._parse_value(val, col_types[i])
            output.append(parsed)
        return output

    def get_centers(self) -> list[dict]:
        return self._execute_query(f"SELECT id, name, lat, lng, type FROM {self._tbl('centers')} ORDER BY id")

    def get_lanes(self) -> list[dict]:
        return self._execute_query(
            f"""
            SELECT id, origin, dest, mode, avgDailyVolume, onTimePct, delayMinutes, slaRiskPct
            FROM {self._tbl('lanes')}
            ORDER BY id
            """
        )

    def get_incidents(self, lane_id: Optional[str] = None) -> list[dict]:
        where_clause = ""
        if lane_id:
            where_clause = f"WHERE laneId = '{self._esc(lane_id)}'"
        return self._execute_query(
            f"""
            SELECT id, laneId, timestamp, type, ref, cause, impactMinutes, impactThroughputPct, confidence, active
            FROM {self._tbl('incidents')}
            {where_clause}
            ORDER BY timestamp DESC
            """
        )

    def get_shipments(self, lane_id: Optional[str] = None, priority: Optional[str] = None) -> list[dict]:
        conditions: list[str] = []
        if lane_id:
            conditions.append(f"laneId = '{self._esc(lane_id)}'")
        if priority:
            conditions.append(f"priority = '{self._esc(priority)}'")
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        return self._execute_query(
            f"""
            SELECT trackingId, customerId, priority, laneId, promisedETA, currentETA, packageCount, status
            FROM {self._tbl('shipments')}
            {where_clause}
            ORDER BY promisedETA
            """
        )

    def get_reroute_suggestions(self, lane_id: str) -> list[dict]:
        return self._execute_query(
            f"""
            SELECT laneId, strategy, deltaETAminutes, addedCostUSD, capacityUsedPct, notes
            FROM {self._tbl('reroute_solutions')}
            WHERE laneId = '{self._esc(lane_id)}'
            ORDER BY deltaETAminutes ASC
            """
        )

    def get_customers(self, ids: Optional[list[str]] = None) -> list[dict]:
        if ids:
            ids_expr = "', '".join(self._esc(v) for v in ids)
            sql = (
                f"SELECT id, name, contact, tier, preferredCommunication FROM {self._tbl('customers')} "
                f"WHERE id IN ('{ids_expr}') ORDER BY id"
            )
        else:
            sql = f"SELECT id, name, contact, tier, preferredCommunication FROM {self._tbl('customers')} ORDER BY id"

        customers = self._execute_query(sql)
        for customer in customers:
            customer_id = customer["id"]
            customer["recentInteractions"] = self.get_customer_interactions(customer_id)[:5]
        return customers

    def get_customer_interactions(self, customer_id: str) -> list[dict]:
        return self._execute_query(
            f"""
            SELECT id, customerId, date, type, summary, sentiment, tags
            FROM {self._tbl('customer_interactions')}
            WHERE customerId = '{self._esc(customer_id)}'
            ORDER BY date DESC
            LIMIT 10
            """
        )

    def get_capacity_lanes(self) -> list[dict]:
        return self._execute_query(
            f"""
            SELECT id, origin, dest, mode, avgDailyVolume, onTimePct, delayMinutes, slaRiskPct,
                   maxCapacity, utilizationPct, availableCapacity, optimalUtilization
            FROM {self._tbl('capacity_lanes')}
            ORDER BY id
            """
        )

    def get_capacity_actions(self, lane_id: str) -> list[dict]:
        return self._execute_query(
            f"""
            SELECT id, laneId, type, volumeChange, npsImpact, costImpact, efficiencyImpact, notes
            FROM {self._tbl('capacity_actions')}
            WHERE laneId = '{self._esc(lane_id)}'
            ORDER BY created_at DESC
            """
        )

    def get_agent_activities(self, lane_id: Optional[str] = None) -> list[dict]:
        where_clause = ""
        if lane_id:
            where_clause = f"WHERE laneId = '{self._esc(lane_id)}'"
        rows = self._execute_query(
            f"""
            SELECT id, laneId, timestamp, agentType, situation, action, result, status, metadata
            FROM {self._tbl('agent_activities')}
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT 50
            """
        )
        for activity in rows:
            meta = activity.get("metadata")
            if isinstance(meta, str) and meta:
                try:
                    activity["metadata"] = json.loads(meta)
                except json.JSONDecodeError:
                    activity["metadata"] = {}
        return rows

    def get_sales_opportunities(self, lane_id: str, activity_id: str) -> Optional[dict]:
        rows = self._execute_query(
            f"""
            SELECT laneId, activityId, availableCapacity, forecastDate, targetCustomers, pricing, projectedImpact
            FROM {self._tbl('sales_opportunities')}
            WHERE laneId = '{self._esc(lane_id)}' AND activityId = '{self._esc(activity_id)}'
            LIMIT 1
            """
        )
        return rows[0] if rows else None
