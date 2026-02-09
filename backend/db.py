"""Database layer for querying Delta tables via SQL Warehouse."""

import json
import os
from pathlib import Path
from typing import Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState


class LogisticsDB:
    """Query Delta tables via SQL Warehouse."""
    
    def __init__(self, client: WorkspaceClient, warehouse_id: str):
        self.client = client
        self.warehouse_id = warehouse_id
        self._fallback_enabled = True
        self._project_root = Path(__file__).parent.parent
    
    @staticmethod
    def _parse_value(val: str, type_name: str):
        """Parse a string value from SQL warehouse into the correct Python type."""
        if val is None:
            return None
        type_upper = (type_name or "").upper()
        if type_upper in ("INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT", "LONG"):
            try:
                return int(val)
            except (ValueError, TypeError):
                return val
        elif type_upper in ("DOUBLE", "FLOAT", "DECIMAL"):
            try:
                return float(val)
            except (ValueError, TypeError):
                return val
        elif type_upper == "BOOLEAN":
            return str(val).lower() in ("true", "1", "yes")
        # STRING, TIMESTAMP, DATE, ARRAY, STRUCT, MAP — return as-is
        return val

    def _execute_query(self, sql: str) -> Optional[list]:
        """Execute SQL query and return results as list of dicts."""
        try:
            execution = self.client.statement_execution.execute_statement(
                warehouse_id=self.warehouse_id,
                statement=sql,
                wait_timeout="30s"
            )
            
            if execution.status.state == StatementState.SUCCEEDED:
                if execution.result and execution.result.data_array:
                    # Convert result to list of dicts with proper type parsing
                    columns = execution.result.manifest.schema.columns
                    col_names = [col.name for col in columns]
                    col_types = [getattr(col, 'type_name', 'STRING') or 'STRING' for col in columns]
                    results = []
                    for row in execution.result.data_array:
                        result_dict = {}
                        for i, col_name in enumerate(col_names):
                            val = row[i] if i < len(row) else None
                            result_dict[col_name] = self._parse_value(val, col_types[i])
                        results.append(result_dict)
                    return results
                return []
            else:
                print(f"Query failed: {execution.status.state}")
                if execution.status.error:
                    print(f"Error: {execution.status.error}")
                return None
        except Exception as e:
            print(f"Database query error: {e}")
            return None
    
    def _load_fallback_json(self, filename: str) -> list:
        """Load fallback JSON file."""
        if not self._fallback_enabled:
            return []
        
        json_path = self._project_root / "public" / "mock" / filename
        if json_path.exists():
            with open(json_path, 'r') as f:
                return json.load(f)
        return []
    
    def get_centers(self) -> list[dict]:
        """Get all distribution centers."""
        sql = "SELECT id, name, lat, lng, type FROM demos.logistics_control_center.centers ORDER BY id"
        result = self._execute_query(sql)
        if result is not None:
            return result
        return self._load_fallback_json("centers.json")
    
    def get_lanes(self) -> list[dict]:
        """Get all lanes."""
        sql = """
        SELECT id, origin, dest, mode, avgDailyVolume, onTimePct, delayMinutes, slaRiskPct
        FROM demos.logistics_control_center.lanes
        ORDER BY id
        """
        result = self._execute_query(sql)
        if result is not None:
            return result
        return self._load_fallback_json("lanes.json")
    
    def get_incidents(self, lane_id: Optional[str] = None) -> list[dict]:
        """Get incidents, optionally filtered by lane."""
        if lane_id:
            sql = f"""
            SELECT id, laneId, timestamp, type, ref, cause, impactMinutes, impactThroughputPct, confidence, active
            FROM demos.logistics_control_center.incidents
            WHERE laneId = '{lane_id}'
            ORDER BY timestamp DESC
            """
        else:
            sql = """
            SELECT id, laneId, timestamp, type, ref, cause, impactMinutes, impactThroughputPct, confidence, active
            FROM demos.logistics_control_center.incidents
            ORDER BY timestamp DESC
            """
        result = self._execute_query(sql)
        if result is not None:
            return result
        # Fallback with filtering
        fallback = self._load_fallback_json("incidents.json")
        if lane_id:
            return [i for i in fallback if i.get("laneId") == lane_id]
        return fallback
    
    def get_shipments(self, lane_id: Optional[str] = None, priority: Optional[str] = None) -> list[dict]:
        """Get shipments, optionally filtered by lane and/or priority."""
        conditions = []
        if lane_id:
            conditions.append(f"laneId = '{lane_id}'")
        if priority:
            conditions.append(f"priority = '{priority}'")
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        sql = f"""
        SELECT trackingId, customerId, priority, laneId, promisedETA, currentETA, packageCount, status
        FROM demos.logistics_control_center.shipments
        {where_clause}
        ORDER BY promisedETA
        """
        result = self._execute_query(sql)
        if result is not None:
            return result
        # Fallback with filtering
        fallback = self._load_fallback_json("shipments.json")
        if lane_id:
            fallback = [s for s in fallback if s.get("laneId") == lane_id]
        if priority:
            fallback = [s for s in fallback if s.get("priority") == priority]
        return fallback
    
    def get_reroute_suggestions(self, lane_id: str) -> list[dict]:
        """Get reroute suggestions for a lane."""
        sql = f"""
        SELECT laneId, strategy, deltaETAminutes, addedCostUSD, capacityUsedPct, notes
        FROM demos.logistics_control_center.reroute_solutions
        WHERE laneId = '{lane_id}'
        ORDER BY deltaETAminutes ASC
        """
        result = self._execute_query(sql)
        if result is not None:
            return result
        # Fallback
        all_suggestions = self._load_fallback_json("reroute_solutions.json")
        return [s for s in all_suggestions if s.get("laneId") == lane_id]
    
    def get_customers(self, ids: Optional[list[str]] = None) -> list[dict]:
        """Get customers, optionally filtered by IDs."""
        if ids:
            ids_str = "', '".join(ids)
            sql = f"""
            SELECT id, name, contact, tier, preferredCommunication
            FROM demos.logistics_control_center.customers
            WHERE id IN ('{ids_str}')
            ORDER BY id
            """
        else:
            sql = """
            SELECT id, name, contact, tier, preferredCommunication
            FROM demos.logistics_control_center.customers
            ORDER BY id
            """
        result = self._execute_query(sql)
        if result is not None:
            # Enrich with interactions
            for customer in result:
                customer_id = customer["id"]
                interactions = self.get_customer_interactions(customer_id)
                customer["recentInteractions"] = interactions[:5]  # Last 5 interactions
            return result
        # Fallback with filtering
        fallback = self._load_fallback_json("customers.json")
        if ids:
            return [c for c in fallback if c.get("id") in ids]
        return fallback
    
    def get_customer_interactions(self, customer_id: str) -> list[dict]:
        """Get customer interactions for a customer."""
        sql = f"""
        SELECT id, customerId, date, type, summary, sentiment, tags
        FROM demos.logistics_control_center.customer_interactions
        WHERE customerId = '{customer_id}'
        ORDER BY date DESC
        LIMIT 10
        """
        result = self._execute_query(sql)
        if result is not None:
            return result
        return []
    
    def get_capacity_lanes(self) -> list[dict]:
        """Get capacity lane data."""
        sql = """
        SELECT id, origin, dest, mode, avgDailyVolume, onTimePct, delayMinutes, slaRiskPct,
               maxCapacity, utilizationPct, availableCapacity, optimalUtilization
        FROM demos.logistics_control_center.capacity_lanes
        ORDER BY id
        """
        result = self._execute_query(sql)
        if result is not None:
            return result
        return self._load_fallback_json("capacity_lanes.json")
    
    def get_capacity_actions(self, lane_id: str) -> list[dict]:
        """Get capacity actions for a lane."""
        sql = f"""
        SELECT id, laneId, type, volumeChange, npsImpact, costImpact, efficiencyImpact, notes
        FROM demos.logistics_control_center.capacity_actions
        WHERE laneId = '{lane_id}'
        ORDER BY created_at DESC
        """
        result = self._execute_query(sql)
        if result is not None:
            return result
        # Fallback
        all_actions = self._load_fallback_json("capacity_actions.json")
        if isinstance(all_actions, dict):
            return all_actions.get(lane_id, [])
        return []
    
    def get_agent_activities(self, lane_id: Optional[str] = None) -> list[dict]:
        """Get agent activities, optionally filtered by lane."""
        if lane_id:
            sql = f"""
            SELECT id, laneId, timestamp, agentType, situation, action, result, status, metadata
            FROM demos.logistics_control_center.agent_activities
            WHERE laneId = '{lane_id}'
            ORDER BY timestamp DESC
            """
        else:
            sql = """
            SELECT id, laneId, timestamp, agentType, situation, action, result, status, metadata
            FROM demos.logistics_control_center.agent_activities
            ORDER BY timestamp DESC
            LIMIT 50
            """
        result = self._execute_query(sql)
        if result is not None:
            # Parse metadata JSON strings
            for activity in result:
                if activity.get("metadata") and isinstance(activity["metadata"], str):
                    try:
                        activity["metadata"] = json.loads(activity["metadata"])
                    except:
                        activity["metadata"] = {}
            return result
        # Fallback with filtering
        fallback = self._load_fallback_json("agent_activities.json")
        if lane_id:
            return [a for a in fallback if a.get("laneId") == lane_id]
        return fallback
    
    def get_sales_opportunities(self, lane_id: str, activity_id: str) -> Optional[dict]:
        """Get sales opportunity for a lane and activity."""
        sql = f"""
        SELECT laneId, activityId, availableCapacity, forecastDate, targetCustomers, pricing, projectedImpact
        FROM demos.logistics_control_center.sales_opportunities
        WHERE laneId = '{lane_id}' AND activityId = '{activity_id}'
        LIMIT 1
        """
        result = self._execute_query(sql)
        if result and len(result) > 0:
            return result[0]
        # Fallback
        all_opportunities = self._load_fallback_json("sales_opportunities.json")
        for opp in all_opportunities:
            if opp.get("laneId") == lane_id and opp.get("activityId") == activity_id:
                return opp
        return None
