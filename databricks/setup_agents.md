# Agent Bricks Setup Guide

This guide walks you through setting up Genie, Knowledge Assistant, and Multi-Agent Supervisor for the Logistics Control Center demo.

## Prerequisites

- Databricks workspace with Unity Catalog enabled
- SQL Warehouse (Pro or Serverless) available
- Access to Mosaic AI Model Serving
- Access to foundation models in Unity Catalog (`system.ai` schema)
- Serverless compute enabled
- Production monitoring for MLflow (Beta) enabled (for tracing)

## Step 1: Set Up Genie Space

### 1.1 Create Genie Space

1. Navigate to **SQL** → **Genie** in your Databricks workspace
2. Click **Create Space**
3. Name: `Logistics Network Operations`
4. Description: `Structured data queries for logistics network operations`

### 1.2 Add Data Sources

Add all Delta tables from `demos.logistics_control_center` schema:

1. Click **Add Data**
2. Select each table:
   - `demos.logistics_control_center.centers`
   - `demos.logistics_control_center.lanes`
   - `demos.logistics_control_center.incidents`
   - `demos.logistics_control_center.shipments`
   - `demos.logistics_control_center.reroute_solutions`
   - `demos.logistics_control_center.customers`
   - `demos.logistics_control_center.capacity_lanes`
   - `demos.logistics_control_center.capacity_actions`
   - `demos.logistics_control_center.agent_activities`
   - `demos.logistics_control_center.sales_opportunities`

### 1.3 Configure General Instructions

In the **General Instructions** field, add:

```
This Genie space provides logistics network operations data for a package
shipping carrier. Users query shipment status, lane performance, incident
details, customer information, and capacity metrics. All data is about
CARGO/PACKAGE logistics, not passenger travel.

Key terminology:
- Lane: A shipping route between two distribution centers (e.g., BNA-STL-AIR)
- Center/Hub: A distribution center or air hub
- Incident: A disruption affecting a lane (weather, traffic, equipment)
- SLA Risk: Probability of missing service level agreement
- On-time %: Percentage of packages arriving within promised window
```

### 1.4 Add Example SQL Queries (Trusted Assets)

Add these example queries to help Genie understand common questions:

**Query 1: "Which lanes are at risk?"**
```sql
SELECT * FROM demos.logistics_control_center.lanes 
WHERE slaRiskPct > 0.10 
ORDER BY delayMinutes DESC
```

**Query 2: "Show me Walmart shipments"**
```sql
SELECT * FROM demos.logistics_control_center.shipments 
WHERE customerId LIKE '%walmart%'
```

**Query 3: "What incidents are active on BNA-STL-AIR?"**
```sql
SELECT * FROM demos.logistics_control_center.incidents 
WHERE laneId = 'BNA-STL-AIR' AND active = true
```

**Query 4: "Network utilization summary"**
```sql
SELECT 
  AVG(utilizationPct) as avg_utilization,
  SUM(availableCapacity) as total_buffer,
  COUNT(*) FILTER (WHERE utilizationPct > 0.95) as overcapacity_count
FROM demos.logistics_control_center.capacity_lanes
```

### 1.5 Add Column Descriptions

For each table, add helpful column descriptions in the Genie knowledge store:

- **lanes.delayMinutes**: "Current delay in minutes for this lane"
- **lanes.slaRiskPct**: "Probability (0-1) of missing service level agreement"
- **incidents.confidence**: "AI detection confidence score (0-1)"
- **shipments.priority**: "Shipment priority: LOW, MED, or HIGH"
- **capacity_lanes.utilizationPct**: "Current capacity utilization (0-1)"

### 1.6 Save and Note Space ID

1. Click **Save**
2. Note the Genie Space ID from the URL (e.g., `spaces/1234567890abcdef`)
3. Set environment variable: `DATABRICKS_GENIE_SPACE_ID=1234567890abcdef`

## Step 2: Set Up Knowledge Assistant

### 2.1 Generate Documents

First, ensure documents are generated in the UC Volume:

```bash
# Run the document generator script in a Databricks notebook
python databricks/generate_documents.py
```

This creates documents in `demos.logistics_control_center.documents` volume.

### 2.2 Create Knowledge Assistant Agent

1. Navigate to **Agents** → **Knowledge Assistant** in your Databricks workspace
2. Click **Build**
3. Name: `Logistics Operations Knowledge Base`
4. Description: `Answers questions about logistics operations, maintenance procedures, incident history, root cause analysis, customer SLA terms, and operational best practices for a cargo package shipping carrier.`

### 2.3 Configure Knowledge Source

1. Under **Knowledge source**, select **UC Files**
2. **Source**: Select `demos.logistics_control_center.documents` volume
3. **Name**: `Logistics Operations Documents`
4. **Describe the content**: `Incident analysis reports, maintenance bulletins, operational procedures, customer SLA documents, route planning guides, and root cause analysis reports for cargo logistics operations.`

### 2.4 Add Instructions

In the **Instructions** field:

```
You are an operations knowledge assistant for a cargo logistics carrier.
Answer questions about maintenance bulletins, incident analysis reports,
operational procedures, customer SLA terms, and route planning.
Always cite the source document. Focus on actionable insights.
Remember: we transport packages and freight, not passengers.
```

### 2.5 Create Agent

1. Click **Create Agent**
2. Wait for the agent to finish building (may take a few minutes to hours)
3. Once ready, note the agent endpoint name
4. Set environment variable: `DATABRICKS_KA_ENDPOINT=<endpoint-name>`

### 2.6 Test Knowledge Assistant

1. In the **Build** tab, test with questions like:
   - "What maintenance history exists for 757-200 landing gear?"
   - "What does the incident analysis report say about FX423?"
   - "What are the SLA terms for Walmart?"

2. Verify responses include citations to source documents

## Step 3: Set Up Multi-Agent Supervisor

### 3.1 Prerequisites

Ensure you have:
- Genie Space created (Step 1)
- Knowledge Assistant agent created (Step 2)
- Permissions: `CAN_QUERY` on Knowledge Assistant endpoint, access to Genie space

### 3.2 Create Multi-Agent Supervisor

1. Navigate to **Agents** → **Multi-Agent Supervisor** in your Databricks workspace
2. Click **Build**
3. Name: `Logistics Operations Supervisor`
4. Description: `Coordinates structured data queries and knowledge base lookups to answer complex logistics operations questions.`

### 3.3 Configure Subagents

Add two subagents:

**Subagent 1: Genie Space**
1. **Type**: Genie Space
2. **Genie space**: Select `Logistics Network Operations`
3. **Agent name**: `Structured Data Query Agent`
4. **Describe the content**: `Provides access to structured logistics data including shipments, lanes, incidents, capacity metrics, and customer information. Use this for data/metrics questions, counts, aggregations, and performance queries.`

**Subagent 2: Knowledge Assistant**
1. **Type**: Agent Endpoint
2. **Agent Endpoint**: Select `Logistics Operations Knowledge Base` endpoint
3. **Agent name**: `Knowledge Base Agent`
4. **Describe the content**: `Provides access to unstructured knowledge including maintenance bulletins, incident analysis reports, operational procedures, customer SLA terms, and route planning guides. Use this for knowledge questions, historical analysis, procedures, and best practices.`

### 3.4 Add Instructions

In the **Instructions** field:

```
Route data/metrics questions (shipment counts, lane performance, delays,
capacity utilization, customer information) to the Genie space.
Route knowledge questions (maintenance history, procedures, incident analysis,
SLA terms, operational best practices) to the Knowledge Assistant.
For complex questions requiring both structured data and knowledge, query both
subagents and synthesize the response.
Always remember: we transport packages and freight, not passengers.
```

### 3.5 Create Supervisor

1. Click **Create Agent**
2. Wait for the supervisor to finish building
3. Once ready, note the supervisor endpoint name
4. Set environment variable: `DATABRICKS_SUPERVISOR_ENDPOINT=<endpoint-name>`

### 3.6 Test Multi-Agent Supervisor

1. In the **Build** tab, test with questions like:
   - "How many shipments are at risk on BNA-STL-AIR?" (should route to Genie)
   - "What does the maintenance bulletin say about 757-200 landing gear?" (should route to Knowledge Assistant)
   - "Analyze the BNA-STL-AIR incident and tell me how many shipments are affected" (should use both)

2. Verify the supervisor correctly routes to appropriate subagents

## Step 4: Configure Backend

### 4.1 Set Environment Variables

Add to your `app.yaml` or environment:

```yaml
env:
  - name: DATABRICKS_SQL_WAREHOUSE_ID
    value: "<your-warehouse-id>"
  - name: DATABRICKS_GENIE_SPACE_ID
    value: "<genie-space-id>"
  - name: DATABRICKS_KA_ENDPOINT
    value: "<knowledge-assistant-endpoint-name>"
  - name: DATABRICKS_SUPERVISOR_ENDPOINT
    value: "<supervisor-endpoint-name>"
```

### 4.2 Verify Configuration

1. Start the backend server
2. Check `/api/health` endpoint
3. Verify `database_connected: true` and `agents_configured: true`

## Step 5: Grant Permissions

### 5.1 Genie Space Permissions

1. Open Genie Space settings
2. Click **Share** or **Permissions**
3. Grant appropriate users/groups access to the space
4. Ensure users have `SELECT` privileges on underlying Unity Catalog tables

### 5.2 Knowledge Assistant Permissions

1. Open Knowledge Assistant agent page
2. Click kebab menu → **Manage permissions**
3. Grant `CAN_QUERY` permission to users who need to query the agent
4. Grant `CAN_MANAGE` permission to admins

### 5.3 Multi-Agent Supervisor Permissions

1. Open Supervisor agent page
2. Click kebab menu → **Manage permissions**
3. Grant `CAN_QUERY` permission to end users
4. Grant `CAN_MANAGE` permission to admins
5. Ensure end users have access to both subagents (Genie space + Knowledge Assistant)

## Troubleshooting

### Genie Not Generating SQL

- Check that example SQL queries are added as trusted assets
- Verify column descriptions are added in knowledge store
- Ensure table metadata is complete in Unity Catalog

### Knowledge Assistant Not Finding Documents

- Verify documents exist in UC Volume: `demos.logistics_control_center.documents`
- Check that volume is accessible
- Click **Sync** on the Knowledge Assistant agent to re-index documents

### Supervisor Not Routing Correctly

- Review subagent descriptions - they should clearly indicate when to use each
- Add more examples in the Instructions field
- Test individual subagents to ensure they work independently

### Permission Errors

- Verify users have `SELECT` privileges on Unity Catalog tables (for Genie)
- Verify users have `CAN_QUERY` permission on agent endpoints
- Check that Genie space is shared with appropriate users

## Next Steps

1. Test the integration by querying `/api/genie/query`, `/api/knowledge/query`, and `/api/supervisor/query`
2. Update frontend to use new agent endpoints
3. Monitor agent performance and add more examples/guidelines as needed
