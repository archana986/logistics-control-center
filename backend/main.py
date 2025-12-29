import os
import json
from typing import Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

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

# Initialize Databricks client
# This works both locally (with CLI OAuth) and in Databricks Apps (with automatic auth)
workspace_client = None

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
    return {
        "status": "ok",
        "service": "Logistics AI Backend",
        "model_endpoint": MODEL_ENDPOINT,
        "databricks_connected": client is not None,
        "auth_mode": "databricks_app" if os.getenv('DATABRICKS_APP_NAME') else "cli"
    }


@api_app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Chat with the Databricks AI about incidents and root cause analysis."""
    
    try:
        # Get Databricks client (CLI for local dev, service principal for Databricks Apps)
        client = get_databricks_client()
        
        # Try to call the Databricks model
        if client:
            # Build context-aware prompt
            context_prompt = ""
            if request.context:
                incident = request.context.get("incident", {})
                lane = request.context.get("lane", {})
                
                if incident:
                    context_prompt = f"""You are an AI assistant helping with cargo logistics operations root cause analysis for a package shipping carrier (like Databricks Logistics). This is NOT about passenger airline operations - we transport packages and freight, not people. Our aircraft carry cargo packages between distribution centers.

Current Incident Context:
- Lane: {lane.get('id', 'N/A')}
- Type: {incident.get('type', '').replace('_', ' ').title()}
- Reference: {incident.get('ref', 'N/A')}
- Cause: {incident.get('cause', 'N/A')}
- Impact: {incident.get('impactMinutes', 'N/A')} minutes
- Confidence: {incident.get('confidence', 0) * 100:.0f}%

Provide helpful, concise, and factual responses about this incident, potential solutions, or related operational questions. Be professional and focus on cargo logistics operations management - remember we're dealing with package shipments, not passenger travel.

User question: {request.message}"""
                else:
                    context_prompt = f"""You are an AI assistant helping with cargo logistics operations and root cause analysis for a package shipping carrier (like Databricks Logistics). This is NOT about passenger airline operations - we transport packages and freight, not people.

User question: {request.message}"""
            else:
                context_prompt = request.message
            
            # Call the model
            response = client.serving_endpoints.query(
                name=MODEL_ENDPOINT,
                messages=[
                    ChatMessage(
                        role=ChatMessageRole.USER,
                        content=context_prompt
                    )
                ],
                max_tokens=2000,
                temperature=0.5,
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
                    message_text = '\n'.join(text_parts) if text_parts else str(message_content)
                else:
                    # Simple string content
                    message_text = message_content
                
                return ChatResponse(
                    message=message_text,
                    source="databricks"
                )
            else:
                raise Exception("No response from model")
                
        else:
            # Fallback response
            return ChatResponse(
                message="I'm currently unable to access the AI model. However, I can tell you that for most operational issues, it's important to review historical data, check for patterns, and consider both immediate fixes and long-term preventive measures.",
                source="fallback"
            )
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return ChatResponse(
            message="I'm having trouble processing your request right now. Please try rephrasing your question or check back shortly.",
            source="fallback"
        )


@api_app.get("/centers")
async def get_centers():
    """Get all distribution centers"""
    try:
        centers_file = Path(__file__).parent.parent / "public" / "mock" / "centers.json"
        with open(centers_file) as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load centers: {str(e)}")


@api_app.get("/shipments")
async def get_shipments():
    """Get all shipments"""
    try:
        shipments_file = Path(__file__).parent.parent / "public" / "mock" / "shipments.json"
        with open(shipments_file) as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load shipments: {str(e)}")


def generate_fallback_message(payload: CustomerUpdateRequest) -> str:
    """Generate a fallback spot quote using template logic."""
    
    action_type = request.action.get("type", "pull_forward")
    volume_change = abs(request.volumeChange)
    nps_impact = request.action.get("npsImpact", 0)
    cost_impact = request.action.get("costImpact", 0)
    efficiency_impact = request.action.get("efficiencyImpact", 0) * 100
    
    lane_id = request.laneId
    current_volume = request.lane.get("avgDailyVolume", 0)
    utilization = request.lane.get("utilizationPct", 0) * 100
    available_capacity = request.lane.get("availableCapacity", 0)
    
    # Calculate new utilization
    new_volume = current_volume + (volume_change if action_type == "pull_forward" else -volume_change)
    max_capacity = request.lane.get("maxCapacity", current_volume / (utilization / 100))
    new_utilization = (new_volume / max_capacity) * 100
    
    # Calculate price per package
    price_per_pkg = abs(cost_impact) / volume_change if volume_change > 0 else 0
    
    action_verb = "Pull Forward" if action_type == "pull_forward" else "Hold Back"
    delivery_commit = "Next-Day Delivery" if action_type == "pull_forward" else "2-Day Standard Service"
    
    quote = f"""SPOT CAPACITY QUOTE
Lane: {lane_id}
Quote ID: SQ-{lane_id.replace('-', '')}-{action_type.upper()[:4]}-001

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAPACITY OPTIMIZATION OPPORTUNITY

Action: {action_verb} {volume_change:,} Packages
Current Lane Utilization: {utilization:.0f}%
Projected Utilization: {new_utilization:.0f}%
Available Buffer: {available_capacity:,} packages

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRICING

Volume: {volume_change:,} packages
Rate: ${price_per_pkg:.2f} per package
Total: ${abs(cost_impact):,.2f}

Service Level: {delivery_commit}
{"Premium handling included" if action_type == "pull_forward" else "Standard processing"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BUSINESS IMPACT ANALYSIS

Customer Satisfaction (NPS): {nps_impact:+d} points
Operational Efficiency: {efficiency_impact:+.1f}%
Network Optimization: {"Reduced congestion" if action_type == "hold_back" else "Maximized throughput"}

{'✓ Recommended: Improves customer experience' if nps_impact > 0 else '⚠ Note: May impact customer satisfaction'}
{'✓ Improves operational efficiency' if efficiency_impact > 0 else '⚠ Reduces operational efficiency'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TERMS & CONDITIONS

• Quote valid for: 24 hours
• Subject to: Real-time capacity availability
• Commitment required: 4 hours advance notice
• Cancellation policy: Up to 2 hours before scheduled pickup
• Payment terms: Net 30 days

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

For approval or questions, contact:
Network Capacity Planning Team
Email: capacity@databricks.com | Phone: 1-800-DATABRICKS

This quote represents an optimal balance between customer satisfaction
and operational efficiency based on current network conditions."""
    
    return quote


@api_app.post("/generate-customer-update", response_model=CustomerUpdateResponse)
async def generate_customer_update(request: CustomerUpdateRequest):
    """Generate a customer update message using Databricks model with fallback."""
    
    try:
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

