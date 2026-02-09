import os
import json
from typing import Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

# Import database and agents layers
from backend.db import LogisticsDB
from backend.agents import AgentsClient, get_agents_client

# Create separate FastAPI apps for API and UI
api_app = FastAPI(title="Logistics AI Backend API")
app = FastAPI(title="Logistics Demo App")

# CORS configuration for local development and Databricks Apps
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get model endpoint from environment variable
MODEL_ENDPOINT = os.getenv("DATABRICKS_MODEL_ENDPOINT", "databricks-gpt-oss-20b")

# Get CLI profile name from environment variable (defaults to DEFAULT if not set)
CLI_PROFILE = os.getenv("DATABRICKS_CLI_PROFILE", "DEFAULT")

# Get SQL Warehouse ID
SQL_WAREHOUSE_ID = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID")

# Initialize Databricks client
# This works both locally (with CLI OAuth) and in Databricks Apps (with automatic auth)
workspace_client = None
logistics_db = None
agents_client = None

def get_databricks_client() -> Optional[WorkspaceClient]:
    """Get or create a Databricks client with proper authentication handling"""
    global workspace_client
    
    # Check if we're in a Databricks Apps environment
    is_databricks_app = os.getenv('DATABRICKS_APP_NAME') is not None
    
    if is_databricks_app:
        # In Databricks Apps - use app service principal
        if workspace_client is None:
            try:
                workspace_client = WorkspaceClient()
                current_user = workspace_client.current_user.me()
                print(f"✓ Connected to Databricks as: {current_user.user_name}")
            except Exception as e:
                print(f"⚠ Warning: Could not initialize Databricks client: {e}")
                return None
        return workspace_client
    else:
        # Local development - use CLI authentication with specific profile
        # Clear app-specific environment variables that might interfere with CLI auth
        original_host = os.environ.get('DATABRICKS_HOST')
        original_client_id = os.environ.get('DATABRICKS_CLIENT_ID')
        original_client_secret = os.environ.get('DATABRICKS_CLIENT_SECRET')
        
        try:
            # Temporarily remove these to force CLI auth
            if 'DATABRICKS_HOST' in os.environ:
                del os.environ['DATABRICKS_HOST']
            if 'DATABRICKS_CLIENT_ID' in os.environ:
                del os.environ['DATABRICKS_CLIENT_ID']
            if 'DATABRICKS_CLIENT_SECRET' in os.environ:
                del os.environ['DATABRICKS_CLIENT_SECRET']
            
            # Use specific profile if set, otherwise use default CLI config
            cli_client = WorkspaceClient(profile=CLI_PROFILE)
            
            # Test the connection and get workspace info
            try:
                current_user = cli_client.current_user.me()
                print(f"✓ Using CLI authentication with profile: {CLI_PROFILE}")
                print(f"✓ Connected as: {current_user.user_name}")
                print(f"✓ Using model endpoint: {MODEL_ENDPOINT}")
            except Exception as test_error:
                print(f"⚠ Warning: CLI profile '{CLI_PROFILE}' may be invalid: {test_error}")
                print(f"⚠ Available profiles: Run 'databricks auth profiles' to see valid profiles")
                return None
            
            return cli_client
            
        except Exception as e:
            print(f"⚠ Warning: Could not initialize CLI client with profile '{CLI_PROFILE}': {e}")
            print(f"⚠ Please run 'databricks auth login' if you haven't already")
            print(f"⚠ Or set DATABRICKS_CLI_PROFILE environment variable to a valid profile name")
            return None
        finally:
            # Restore original environment variables
            if original_host:
                os.environ['DATABRICKS_HOST'] = original_host
            if original_client_id:
                os.environ['DATABRICKS_CLIENT_ID'] = original_client_id
            if original_client_secret:
                os.environ['DATABRICKS_CLIENT_SECRET'] = original_client_secret


class CustomerUpdateRequest(BaseModel):
    customerName: str
    laneId: str
    strategy: dict
    incidentSummary: str
    customer: Optional[dict] = None
    incident: Optional[dict] = None


class CustomerUpdateResponse(BaseModel):
    message: str
    source: str  # "databricks" or "fallback"


class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None  # Context about the incident/lane
    history: Optional[list] = None  # Previous messages in the conversation


class ChatResponse(BaseModel):
    message: str
    source: str


class GenieQueryRequest(BaseModel):
    question: str


class GenieQueryResponse(BaseModel):
    answer: str
    sql: Optional[str] = None
    data: Optional[list] = None
    source: str


class KnowledgeQueryRequest(BaseModel):
    question: str
    context: Optional[dict] = None


class KnowledgeQueryResponse(BaseModel):
    answer: str
    citations: Optional[list] = None
    source: str


class SupervisorQueryRequest(BaseModel):
    message: str
    context: Optional[dict] = None


class SupervisorQueryResponse(BaseModel):
    message: str
    source: str


def get_logistics_db() -> Optional[LogisticsDB]:
    """Get or create LogisticsDB instance."""
    global logistics_db
    
    if logistics_db is None:
        client = get_databricks_client()
        if client and SQL_WAREHOUSE_ID:
            try:
                logistics_db = LogisticsDB(client, SQL_WAREHOUSE_ID)
                print(f"✓ Initialized LogisticsDB with warehouse: {SQL_WAREHOUSE_ID}")
            except Exception as e:
                print(f"⚠ Warning: Could not initialize LogisticsDB: {e}")
                return None
        else:
            print("⚠ Warning: Databricks client or SQL Warehouse ID not available")
            return None
    
    return logistics_db


def get_agents_client_instance() -> Optional[AgentsClient]:
    """Get or create AgentsClient instance."""
    global agents_client
    
    if agents_client is None:
        agents_client = get_agents_client()
        if agents_client:
            print("✓ Initialized AgentsClient")
        else:
            print("⚠ Warning: Could not initialize AgentsClient")
    
    return agents_client


def build_prompt(payload: CustomerUpdateRequest) -> str:
    """Build a detailed prompt for the model to generate a customer update message."""
    
    # Extract key information
    strategy_name = payload.strategy.get("strategy", "alternative route")
    delta_eta = payload.strategy.get("deltaETAminutes", 0)
    improved = delta_eta < 0
    impact_text = f"improved ETA by {abs(delta_eta)} minutes" if improved else f"+{delta_eta} minutes"
    
    # Build incident context
    incident_context = ""
    if payload.incident:
        incident_type = payload.incident.get("type", "").replace("_", " ").title()
        incident_ref = payload.incident.get("ref", "")
        incident_cause = payload.incident.get("cause", "")
        incident_impact = payload.incident.get("impactMinutes", 0)
        confidence = payload.incident.get("confidence", 0)
        
        incident_context = f"""
Incident Details:
- Type: {incident_type}
- Reference: {incident_ref}
- Root Cause: {incident_cause}
- Original Impact: {incident_impact} minutes
- Detection Confidence: {int(confidence * 100)}%
"""
    
    # Build customer context
    customer_context = ""
    if payload.customer and payload.customer.get("recentInteractions"):
        interactions = payload.customer.get("recentInteractions", [])[:2]
        if interactions:
            customer_context = "\n\nRecent Customer Interactions:\n"
            for i, interaction in enumerate(interactions, 1):
                customer_context += f"[{i}] {interaction.get('type', '').title()} on {interaction.get('date', '')}: {interaction.get('summary', '')}\n"
    
    prompt = f"""You are a professional logistics operations assistant for a cargo package shipping carrier (like Databricks Logistics). We transport packages and freight via aircraft and ground transportation - we do NOT transport passengers. Generate a clear, factual customer update email about a shipment disruption and rerouting action.

Context:
- Customer: {payload.customerName}
- Lane: {payload.laneId}
- Incident: {payload.incidentSummary}
- Reroute Strategy: {strategy_name}
- Impact: {impact_text}
{incident_context}
{customer_context}

Requirements:
1. Write a professional email with subject line and body
2. Be proactive and reassuring
3. Include specific details from the incident and reroute solution
4. If customer history shows preference for proactive communication, acknowledge that
5. Offer continued monitoring and support
6. Use a factual, professional tone - no chatbot-like language
7. Include the incident details section
8. If there are recent interactions, reference them appropriately and include citations at the end
9. Format exactly like a real operations team email
10. Remember: we're dealing with PACKAGE SHIPMENTS, not passenger travel

Generate ONLY the email content. Do not include any preambles, explanations, or chatbot-like responses. Start directly with the subject line."""

    return prompt


def call_databricks_model(prompt: str) -> str:
    """Call the Databricks foundation model serving endpoint."""
    
    client = get_databricks_client()
    if not client:
        raise Exception("Databricks client not initialized")
    
    try:
        # Call the model using the Databricks SDK
        response = client.serving_endpoints.query(
            name=MODEL_ENDPOINT,
            messages=[
                ChatMessage(
                    role=ChatMessageRole.USER,
                    content=prompt
                )
            ],
            max_tokens=1000,
            temperature=0.3,  # Lower temperature for more factual output
        )
        
        # Extract the response text
        if response.choices and len(response.choices) > 0:
            message_content = response.choices[0].message.content
            
            # Handle structured content (list of content blocks)
            if isinstance(message_content, list):
                # Extract text from content blocks
                text_parts = []
                for block in message_content:
                    if isinstance(block, dict):
                        if block.get('type') == 'text' and 'text' in block:
                            text_parts.append(block['text'])
                        elif 'text' in block:
                            text_parts.append(block['text'])
                return '\n'.join(text_parts) if text_parts else str(message_content)
            else:
                # Simple string content
                return message_content
        else:
            raise Exception("No response from model")
            
    except Exception as e:
        print(f"Error calling Databricks model: {e}")
        raise


def call_databricks_model_with_structured_output(prompt: str, response_format: dict) -> dict:
    """Call the Databricks foundation model with structured output (JSON schema)."""
    
    client = get_databricks_client()
    if not client:
        raise Exception("Databricks client not initialized")
    
    try:
        # Call the model using the Databricks SDK with response_format for structured output
        response = client.serving_endpoints.query(
            name=MODEL_ENDPOINT,
            messages=[
                ChatMessage(
                    role=ChatMessageRole.USER,
                    content=prompt
                )
            ],
            max_tokens=1500,
            temperature=0.3,
            extra_params={
                "response_format": response_format
            }
        )
        
        # Extract the response text
        if response.choices and len(response.choices) > 0:
            message_content = response.choices[0].message.content
            
            # Parse JSON response
            if isinstance(message_content, str):
                return json.loads(message_content)
            elif isinstance(message_content, dict):
                return message_content
            else:
                raise Exception(f"Unexpected response format: {type(message_content)}")
        else:
            raise Exception("No response from model")
            
    except Exception as e:
        print(f"Error calling Databricks model with structured output: {e}")
        raise


def generate_fallback_message(payload: CustomerUpdateRequest) -> str:
    """Generate a fallback message using the original logic."""
    
    strategy_name = payload.strategy.get("strategy", "alternative route")
    delta_eta = payload.strategy.get("deltaETAminutes", 0)
    improved = delta_eta < 0
    impact_text = f"improved ETA by {abs(delta_eta)} minutes" if improved else f"+{delta_eta} minutes"
    
    # Build personalized context
    personalized_context = ""
    if payload.customer and payload.customer.get("recentInteractions"):
        interactions = payload.customer.get("recentInteractions", [])[:2]
        has_proactive = any(
            "proactive" in interaction.get("tags", [])
            for interaction in interactions
        )
        needs_phone = any(
            "phone-preferred" in interaction.get("tags", []) or "critical-issues" in interaction.get("tags", [])
            for interaction in interactions
        )
        
        if has_proactive:
            personalized_context = "\nConsistent with your preference for proactive alerts, we're reaching out immediately to keep you informed."
        
        if needs_phone and not improved:
            personalized_context += "\nGiven the time-sensitive nature, our team is standing by for a call if you need one."
    
    # Build incident context
    incident_context = ""
    if payload.incident:
        incident_type = payload.incident.get("type", "").replace("_", " ").title()
        incident_ref = payload.incident.get("ref", "")
        incident_cause = payload.incident.get("cause", "")
        incident_impact = payload.incident.get("impactMinutes", 0)
        confidence = payload.incident.get("confidence", 0)
        
        incident_context = f"""

Incident Details:
• Type: {incident_type}
• Reference: {incident_ref}
• Root Cause: {incident_cause}
• Original Impact: {incident_impact} minutes
• Detection Confidence: {int(confidence * 100)}%"""
    
    # Build citations
    citations_section = ""
    if payload.customer and payload.customer.get("recentInteractions"):
        interactions = payload.customer.get("recentInteractions", [])[:2]
        if interactions:
            citations = []
            for i, interaction in enumerate(interactions, 1):
                citations.append(
                    f"[{i}] {interaction.get('type', '').title()} on {interaction.get('date', '')}: {interaction.get('summary', '')}"
                )
            
            citations_section = "\n\n---\n\nContext from Recent Interactions:\n" + "\n".join(citations)
    
    message = f"""Subject: Proactive update on your priority shipments ({payload.laneId})

Hi {payload.customerName},

We detected a disruption on {payload.laneId} ({payload.incidentSummary}). To protect your urgent deliveries,
we've proactively re-routed via {strategy_name}.{personalized_context}

• Estimated impact: {impact_text}
• Your shipments remain prioritized end-to-end
• Reroute automatically triggered by our network AI
{incident_context}

We'll continue to monitor until delivery is complete. If you'd like a live view or a call,
reply here and we'll set it up immediately.
{citations_section}

Thank you for your partnership,
Network Operations Center"""
    
    return message


@api_app.get("/health")
async def health():
    """Health check endpoint for the API"""
    client = get_databricks_client()
    db = get_logistics_db()
    agents = get_agents_client_instance()
    
    ka_ep = os.getenv("DATABRICKS_KA_ENDPOINT", "")
    
    return {
        "status": "ok",
        "service": "Logistics AI Backend",
        "model_endpoint": MODEL_ENDPOINT,
        "databricks_connected": client is not None,
        "database_connected": db is not None,
        "agents_configured": agents is not None,
        "agents_ka_endpoint": agents.ka_endpoint if agents else None,
        "ka_env_var": ka_ep if ka_ep else None,
        "sql_warehouse_id": SQL_WAREHOUSE_ID if SQL_WAREHOUSE_ID else None,
        "auth_mode": "databricks_app" if os.getenv('DATABRICKS_APP_NAME') else "cli"
    }


@api_app.get("/debug/ka-test")
async def debug_ka_test():
    """Debug endpoint to test the Knowledge Assistant connection."""
    ka_ep = os.getenv("DATABRICKS_KA_ENDPOINT", "")
    result = {"ka_endpoint_env": ka_ep}
    
    try:
        client = get_databricks_client()
        if not client:
            result["error"] = "No Databricks client"
            return result
        
        result["client_ok"] = True
        
        # Test via agents client
        agents = get_agents_client_instance()
        if agents:
            result["agents_ka_endpoint"] = agents.ka_endpoint
            try:
                ka_result = agents.query_knowledge_assistant("Hello, what information do you have?")
                result["agents_result_source"] = ka_result.get("source")
                result["agents_result_preview"] = ka_result.get("answer", "")[:200]
            except Exception as e:
                result["agents_error"] = str(e)
        else:
            result["agents_error"] = "agents client is None"
        
        # Test direct raw HTTP call
        if ka_ep and not ka_ep.startswith("<"):
            try:
                payload = {"input": [{"role": "user", "content": "Hello"}]}
                resp = client.api_client.do(
                    "POST",
                    f"/serving-endpoints/{ka_ep}/invocations",
                    body=payload,
                )
                result["direct_response_type"] = type(resp).__name__
                result["direct_has_output"] = "output" in resp if isinstance(resp, dict) else False
                if isinstance(resp, dict) and resp.get("output"):
                    from backend.agents import _extract_agent_text
                    answer, _ = _extract_agent_text(resp)
                    result["direct_answer_preview"] = answer[:200]
            except Exception as e:
                result["direct_error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    
    return result


@api_app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Chat about incidents and root cause analysis, using KA endpoint or model serving."""
    
    KA_SERVING_ENDPOINT = os.getenv("DATABRICKS_KA_ENDPOINT", "")
    
    try:
        client = get_databricks_client()
        
        # Build context-aware prompt
        context_prompt = ""
        if request.context:
            incident = request.context.get("incident", {})
            lane = request.context.get("lane", {})
            
            if incident:
                # Safely format confidence
                raw_conf = incident.get('confidence', 0)
                try:
                    conf_str = f"{float(raw_conf) * 100:.0f}%"
                except (ValueError, TypeError):
                    conf_str = "N/A"
                
                context_prompt = f"""You are an AI assistant helping with cargo logistics operations root cause analysis for a package shipping carrier. We transport packages and freight via aircraft and ground transportation between distribution centers - NOT passengers.

Current Incident Context:
- Lane: {lane.get('id', 'N/A')}
- Type: {incident.get('type', '').replace('_', ' ').title()}
- Reference: {incident.get('ref', 'N/A')}
- Cause: {incident.get('cause', 'N/A')}
- Impact: {incident.get('impactMinutes', 'N/A')} minutes
- Confidence: {conf_str}

Provide helpful, concise, and factual responses about this incident, potential solutions, or related operational questions. Be professional and focus on cargo logistics operations management.

User question: {request.message}"""
            else:
                context_prompt = f"""You are an AI assistant helping with cargo logistics operations and root cause analysis for a package shipping carrier. We transport packages and freight, not people.

User question: {request.message}"""
        else:
            context_prompt = request.message
        
        # Try Knowledge Assistant endpoint first (preferred for RCA)
        # KA uses Agent Bricks input/output format, not standard messages/choices
        if client and KA_SERVING_ENDPOINT and not KA_SERVING_ENDPOINT.startswith("<"):
            try:
                payload = {"input": [{"role": "user", "content": context_prompt}]}
                resp = client.api_client.do(
                    "POST",
                    f"/serving-endpoints/{KA_SERVING_ENDPOINT}/invocations",
                    body=payload,
                )
                from backend.agents import _extract_agent_text
                answer, _ = _extract_agent_text(resp)
                if answer:
                    return ChatResponse(message=answer, source="knowledge_assistant")
            except Exception as e:
                print(f"KA endpoint query failed, falling back to model: {e}")
        
        # Fallback to general model serving endpoint
        if client:
            response = client.serving_endpoints.query(
                name=MODEL_ENDPOINT,
                messages=[
                    ChatMessage(role=ChatMessageRole.USER, content=context_prompt)
                ],
                max_tokens=2000,
                temperature=0.5,
            )
            
            if response.choices and len(response.choices) > 0:
                message_content = response.choices[0].message.content
                message_text = _extract_text_from_response(message_content)
                return ChatResponse(message=message_text, source="databricks")
            else:
                raise Exception("No response from model")
        else:
            return ChatResponse(
                message="I'm currently unable to access the AI model. However, for most operational issues, review historical data, check for patterns, and consider both immediate fixes and long-term preventive measures.",
                source="fallback"
            )
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return ChatResponse(
            message="I'm having trouble processing your request right now. Please try rephrasing your question or check back shortly.",
            source="fallback"
        )


def _extract_text_from_response(message_content) -> str:
    """Extract text from model response content (handles string and list-of-blocks formats)."""
    if isinstance(message_content, list):
        text_parts = []
        for block in message_content:
            if isinstance(block, dict):
                if block.get('type') == 'text' and 'text' in block:
                    text_parts.append(block['text'])
                elif 'text' in block:
                    text_parts.append(block['text'])
        return '\n'.join(text_parts) if text_parts else str(message_content)
    return str(message_content)


@api_app.get("/centers")
async def get_centers():
    """Get all distribution centers"""
    db = get_logistics_db()
    if db:
        try:
            return db.get_centers()
        except Exception as e:
            print(f"Error querying centers: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON file
    try:
        centers_file = Path(__file__).parent.parent / "public" / "mock" / "centers.json"
        with open(centers_file) as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load centers: {str(e)}")


@api_app.get("/shipments")
async def get_shipments(laneId: Optional[str] = Query(None), priority: Optional[str] = Query(None)):
    """Get all shipments, optionally filtered by lane and/or priority"""
    db = get_logistics_db()
    if db:
        try:
            return db.get_shipments(lane_id=laneId, priority=priority)
        except Exception as e:
            print(f"Error querying shipments: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON file
    try:
        shipments_file = Path(__file__).parent.parent / "public" / "mock" / "shipments.json"
        with open(shipments_file) as f:
            all_shipments = json.load(f)
            # Apply filters if provided
            if laneId:
                all_shipments = [s for s in all_shipments if s.get("laneId") == laneId]
            if priority:
                all_shipments = [s for s in all_shipments if s.get("priority") == priority]
            return all_shipments
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load shipments: {str(e)}")


@api_app.get("/lanes")
async def get_lanes():
    """Get all lanes"""
    db = get_logistics_db()
    if db:
        try:
            return db.get_lanes()
        except Exception as e:
            print(f"Error querying lanes: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON file
    try:
        lanes_file = Path(__file__).parent.parent / "public" / "mock" / "lanes.json"
        with open(lanes_file) as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load lanes: {str(e)}")


@api_app.get("/incidents")
async def get_incidents(laneId: Optional[str] = Query(None)):
    """Get incidents, optionally filtered by lane"""
    db = get_logistics_db()
    if db:
        try:
            return db.get_incidents(lane_id=laneId)
        except Exception as e:
            print(f"Error querying incidents: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON file
    try:
        incidents_file = Path(__file__).parent.parent / "public" / "mock" / "incidents.json"
        with open(incidents_file) as f:
            all_incidents = json.load(f)
            if laneId:
                all_incidents = [i for i in all_incidents if i.get("laneId") == laneId]
            return all_incidents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load incidents: {str(e)}")


@api_app.get("/reroute-suggestions")
async def get_reroute_suggestions(laneId: str = Query(..., description="Lane ID")):
    """Get reroute suggestions for a lane"""
    db = get_logistics_db()
    if db:
        try:
            return db.get_reroute_suggestions(laneId)
        except Exception as e:
            print(f"Error querying reroute suggestions: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON file
    try:
        reroute_file = Path(__file__).parent.parent / "public" / "mock" / "reroute_solutions.json"
        with open(reroute_file) as f:
            all_suggestions = json.load(f)
            return [s for s in all_suggestions if s.get("laneId") == laneId]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load reroute suggestions: {str(e)}")


@api_app.get("/customers")
async def get_customers(ids: Optional[str] = Query(None, description="Comma-separated customer IDs")):
    """Get customers, optionally filtered by IDs"""
    customer_ids = ids.split(",") if ids else None
    
    db = get_logistics_db()
    if db:
        try:
            return db.get_customers(ids=customer_ids)
        except Exception as e:
            print(f"Error querying customers: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON file (if it exists)
    try:
        customers_file = Path(__file__).parent.parent / "public" / "mock" / "customers.json"
        if customers_file.exists():
            with open(customers_file) as f:
                all_customers = json.load(f)
                if customer_ids:
                    all_customers = [c for c in all_customers if c.get("id") in customer_ids]
                return all_customers
    except Exception as e:
        print(f"Error loading customers fallback: {e}")
    
    return []


@api_app.get("/capacity/lanes")
async def get_capacity_lanes():
    """Get capacity lane data"""
    db = get_logistics_db()
    if db:
        try:
            return db.get_capacity_lanes()
        except Exception as e:
            print(f"Error querying capacity lanes: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON file (if it exists)
    try:
        capacity_file = Path(__file__).parent.parent / "public" / "mock" / "capacity_lanes.json"
        if capacity_file.exists():
            with open(capacity_file) as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading capacity lanes fallback: {e}")
    
    return []


@api_app.get("/capacity/actions/{laneId}")
async def get_capacity_actions(laneId: str):
    """Get capacity actions for a lane"""
    db = get_logistics_db()
    if db:
        try:
            return db.get_capacity_actions(laneId)
        except Exception as e:
            print(f"Error querying capacity actions: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON file (if it exists)
    try:
        actions_file = Path(__file__).parent.parent / "public" / "mock" / "capacity_actions.json"
        if actions_file.exists():
            with open(actions_file) as f:
                all_actions = json.load(f)
                if isinstance(all_actions, dict):
                    return all_actions.get(laneId, [])
                return []
    except Exception as e:
        print(f"Error loading capacity actions fallback: {e}")
    
    return []


@api_app.get("/agent-activities")
async def get_agent_activities(laneId: Optional[str] = Query(None)):
    """Get agent activities, optionally filtered by lane"""
    db = get_logistics_db()
    if db:
        try:
            return db.get_agent_activities(lane_id=laneId)
        except Exception as e:
            print(f"Error querying agent activities: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON file (if it exists)
    try:
        activities_file = Path(__file__).parent.parent / "public" / "mock" / "agent_activities.json"
        if activities_file.exists():
            with open(activities_file) as f:
                all_activities = json.load(f)
                if laneId:
                    all_activities = [a for a in all_activities if a.get("laneId") == laneId]
                return all_activities
    except Exception as e:
        print(f"Error loading agent activities fallback: {e}")
    
    return []


@api_app.get("/sales-opportunities")
async def get_sales_opportunities(laneId: str = Query(..., description="Lane ID"), 
                                  activityId: str = Query(..., description="Activity ID")):
    """Get sales opportunity for a lane and activity"""
    db = get_logistics_db()
    if db:
        try:
            opportunity = db.get_sales_opportunities(laneId, activityId)
            return opportunity if opportunity else {}
        except Exception as e:
            print(f"Error querying sales opportunities: {e}")
            # Fallback to JSON
            pass
    
    # Fallback to JSON file (if it exists)
    try:
        opportunities_file = Path(__file__).parent.parent / "public" / "mock" / "sales_opportunities.json"
        if opportunities_file.exists():
            with open(opportunities_file) as f:
                all_opportunities = json.load(f)
                for opp in all_opportunities:
                    if opp.get("laneId") == laneId and opp.get("activityId") == activityId:
                        return opp
    except Exception as e:
        print(f"Error loading sales opportunities fallback: {e}")
    
    return {}


@api_app.post("/genie/query", response_model=GenieQueryResponse)
async def query_genie(request: GenieQueryRequest):
    """Query structured data via Genie space"""
    agents = get_agents_client_instance()
    if agents:
        try:
            result = agents.query_genie(request.question)
            return GenieQueryResponse(**result)
        except Exception as e:
            print(f"Error querying Genie: {e}")
            return GenieQueryResponse(
                answer=f"Error querying Genie: {str(e)}",
                source="error"
            )
    
    return GenieQueryResponse(
        answer="Genie space not configured",
        source="error"
    )


@api_app.post("/knowledge/query", response_model=KnowledgeQueryResponse)
async def query_knowledge(request: KnowledgeQueryRequest):
    """Query unstructured docs via Knowledge Assistant endpoint."""
    
    KA_SERVING_ENDPOINT = os.getenv("DATABRICKS_KA_ENDPOINT", "")
    
    # Try the agents client first (if configured)
    agents = get_agents_client_instance()
    if agents and agents.ka_endpoint:
        try:
            result = agents.query_knowledge_assistant(request.question, request.context)
            if result.get("source") != "error":
                return KnowledgeQueryResponse(**result)
        except Exception as e:
            print(f"Error querying via agents client: {e}")
    
    # Direct fallback: call the KA serving endpoint via raw HTTP (Agent Bricks input format)
    if KA_SERVING_ENDPOINT and not KA_SERVING_ENDPOINT.startswith("<"):
        client = get_databricks_client()
        if client:
            try:
                prompt = request.question
                if request.context:
                    context_str = "\n".join([
                        f"{k}: {json.dumps(v) if isinstance(v, (dict, list)) else v}"
                        for k, v in request.context.items()
                    ])
                    prompt = f"Context:\n{context_str}\n\nQuestion: {request.question}"

                payload = {"input": [{"role": "user", "content": prompt}]}
                resp = client.api_client.do(
                    "POST",
                    f"/serving-endpoints/{KA_SERVING_ENDPOINT}/invocations",
                    body=payload,
                )

                from backend.agents import _extract_agent_text
                answer, citations = _extract_agent_text(resp)
                if answer:
                    return KnowledgeQueryResponse(
                        answer=answer,
                        citations=citations,
                        source="knowledge_assistant"
                    )
            except Exception as e:
                print(f"Error calling KA endpoint directly: {e}")
    
    return KnowledgeQueryResponse(
        answer="Knowledge Assistant not configured",
        source="error"
    )


@api_app.post("/supervisor/query", response_model=SupervisorQueryResponse)
async def query_supervisor(request: SupervisorQueryRequest):
    """Route complex queries through Multi-Agent Supervisor"""
    agents = get_agents_client_instance()
    if agents:
        try:
            result = agents.query_supervisor(request.message, request.context)
            return SupervisorQueryResponse(**result)
        except Exception as e:
            print(f"Error querying Supervisor: {e}")
            return SupervisorQueryResponse(
                message=f"Error querying Supervisor: {str(e)}",
                source="error"
            )
    
    return SupervisorQueryResponse(
        message="Multi-Agent Supervisor not configured",
        source="error"
    )




@api_app.post("/generate-customer-update", response_model=CustomerUpdateResponse)
async def generate_customer_update(request: CustomerUpdateRequest):
    """Generate a customer update message using Databricks model with fallback."""
    
    try:
        # Enrich request with real data from database if available
        db = get_logistics_db()
        if db and request.customer is None:
            # Fetch customer data from database
            customers = db.get_customers(ids=[request.customerName] if request.customerName else None)
            if customers:
                request.customer = customers[0]
        
        # Get Databricks client (CLI for local dev, service principal for Databricks Apps)
        client = get_databricks_client()
        
        # Try to call the Databricks model
        if client:
            prompt = build_prompt(request)
            message = call_databricks_model(prompt)
            return CustomerUpdateResponse(
                message=message,
                source="databricks"
            )
        else:
            # Fallback to local generation
            message = generate_fallback_message(request)
            return CustomerUpdateResponse(
                message=message,
                source="fallback"
            )
    
    except Exception as e:
        print(f"Error generating with Databricks model: {e}")
        print("Falling back to local generation")
        
        # Fallback to local generation
        try:
            message = generate_fallback_message(request)
            return CustomerUpdateResponse(
                message=message,
                source="fallback"
            )
        except Exception as fallback_error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate message: {str(fallback_error)}"
            )


# Mount the API app at /api prefix
app.mount("/api", api_app)

# Mount static files for the React frontend
# Check if dist directory exists (for production/Databricks deployment)
dist_path = Path(__file__).parent.parent / "dist"
if dist_path.exists():
    print(f"📦 Serving static files from: {dist_path}")
    
    # Mount static files but NOT with catch-all, so we can handle SPA routing separately
    app.mount("/assets", StaticFiles(directory=str(dist_path / "assets")), name="assets")
    
    # Serve mock data
    mock_path = dist_path / "mock"
    if mock_path.exists():
        app.mount("/mock", StaticFiles(directory=str(mock_path)), name="mock")
    
    # Serve other static files (favicon, etc)
    @app.get("/vite.svg")
    @app.get("/tab_logo.png")
    async def serve_static_file(request):
        from fastapi.responses import FileResponse
        file_path = dist_path / request.url.path.lstrip('/')
        if file_path.exists():
            return FileResponse(file_path)
        raise HTTPException(status_code=404, detail="File not found")
    
    # Catch-all route for SPA - serve index.html for all non-API routes
    # This must come last so it doesn't override other routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        from fastapi.responses import FileResponse
        # If it's a file request (has extension), try to serve it
        if "." in full_path.split("/")[-1]:
            file_path = dist_path / full_path
            if file_path.exists():
                return FileResponse(file_path)
        # Otherwise serve index.html for SPA routing
        index_path = dist_path / "index.html"
        return FileResponse(index_path)
else:
    print(f"⚠️  No dist directory found at {dist_path}")
    print("   Run 'npm run build' to create production build")
    
    @app.get("/")
    async def dev_root():
        return {
            "message": "Development mode - frontend should be running on http://localhost:5173",
            "api_health": "http://localhost:8001/api/health",
            "api_docs": "http://localhost:8001/docs"
        }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)

