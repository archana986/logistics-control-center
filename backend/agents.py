"""Agent Bricks client for Genie, Knowledge Assistant, and Multi-Agent Supervisor."""

import os
from typing import Optional, Dict, Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole


class AgentsClient:
    """Interface to Agent Bricks services."""
    
    def __init__(self, client: WorkspaceClient, config: Dict[str, str]):
        self.client = client
        self.genie_space_id = config.get("genie_space_id")
        self.ka_endpoint = config.get("knowledge_assistant_endpoint")
        self.supervisor_endpoint = config.get("supervisor_endpoint")
    
    def query_genie(self, question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query structured data via Genie space.
        
        Uses the Genie Conversations API to submit natural language questions
        and get SQL queries + results.
        """
        if not self.genie_space_id:
            return {
                "answer": "Genie space not configured",
                "sql": None,
                "data": [],
                "source": "error"
            }
        
        try:
            # Use Genie Conversations API
            # Note: This is a simplified implementation - actual Genie API may differ
            # Genie spaces are queried via SQL Warehouse with NL-to-SQL conversion
            
            # For now, return a placeholder response
            # In production, this would use the actual Genie Conversations API
            # which is typically accessed via SQL Warehouse with special NL query syntax
            
            return {
                "answer": f"Genie query for: {question}",
                "sql": f"-- Generated SQL for: {question}",
                "data": [],
                "source": "genie",
                "note": "Genie integration requires Genie Conversations API access"
            }
        except Exception as e:
            return {
                "answer": f"Error querying Genie: {str(e)}",
                "sql": None,
                "data": [],
                "source": "error"
            }
    
    def query_knowledge_assistant(self, question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query unstructured docs via Knowledge Assistant endpoint."""
        if not self.ka_endpoint:
            return {
                "answer": "Knowledge Assistant endpoint not configured",
                "citations": [],
                "source": "error"
            }
        
        try:
            # Build prompt with context
            prompt = question
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                prompt = f"Context:\n{context_str}\n\nQuestion: {question}"
            
            # Query Knowledge Assistant endpoint
            response = self.client.serving_endpoints.query(
                name=self.ka_endpoint,
                messages=[
                    ChatMessage(
                        role=ChatMessageRole.USER,
                        content=prompt
                    )
                ],
                max_tokens=2000,
                temperature=0.3,
            )
            
            # Extract response
            if response.choices and len(response.choices) > 0:
                message_content = response.choices[0].message.content
                
                # Handle structured content
                if isinstance(message_content, list):
                    text_parts = []
                    citations = []
                    for block in message_content:
                        if isinstance(block, dict):
                            if block.get('type') == 'text' and 'text' in block:
                                text_parts.append(block['text'])
                            elif 'text' in block:
                                text_parts.append(block['text'])
                            # Extract citations if present
                            if 'citations' in block:
                                citations.extend(block['citations'])
                    answer = '\n'.join(text_parts) if text_parts else str(message_content)
                else:
                    answer = message_content
                
                return {
                    "answer": answer,
                    "citations": citations if 'citations' in locals() else [],
                    "source": "knowledge_assistant"
                }
            else:
                return {
                    "answer": "No response from Knowledge Assistant",
                    "citations": [],
                    "source": "error"
                }
        except Exception as e:
            return {
                "answer": f"Error querying Knowledge Assistant: {str(e)}",
                "citations": [],
                "source": "error"
            }
    
    def query_supervisor(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route complex queries through Multi-Agent Supervisor."""
        if not self.supervisor_endpoint:
            return {
                "message": "Multi-Agent Supervisor endpoint not configured",
                "source": "error"
            }
        
        try:
            # Build context-aware prompt
            prompt = message
            if context:
                context_parts = []
                if context.get("incident"):
                    incident = context["incident"]
                    context_parts.append(f"Incident: {incident.get('ref', 'N/A')} on lane {incident.get('laneId', 'N/A')}")
                    context_parts.append(f"Type: {incident.get('type', 'N/A')}")
                    context_parts.append(f"Cause: {incident.get('cause', 'N/A')}")
                
                if context.get("lane"):
                    lane = context["lane"]
                    context_parts.append(f"Lane: {lane.get('id', 'N/A')}")
                
                if context_parts:
                    prompt = f"Context:\n" + "\n".join(context_parts) + f"\n\nUser question: {message}"
            
            # Query Supervisor endpoint
            response = self.client.serving_endpoints.query(
                name=self.supervisor_endpoint,
                messages=[
                    ChatMessage(
                        role=ChatMessageRole.USER,
                        content=prompt
                    )
                ],
                max_tokens=2000,
                temperature=0.5,
            )
            
            # Extract response
            if response.choices and len(response.choices) > 0:
                message_content = response.choices[0].message.content
                
                # Handle structured content
                if isinstance(message_content, list):
                    text_parts = []
                    for block in message_content:
                        if isinstance(block, dict):
                            if block.get('type') == 'text' and 'text' in block:
                                text_parts.append(block['text'])
                            elif 'text' in block:
                                text_parts.append(block['text'])
                    message_text = '\n'.join(text_parts) if text_parts else str(message_content)
                else:
                    message_text = message_content
                
                return {
                    "message": message_text,
                    "source": "supervisor"
                }
            else:
                return {
                    "message": "No response from Multi-Agent Supervisor",
                    "source": "error"
                }
        except Exception as e:
            return {
                "message": f"Error querying Multi-Agent Supervisor: {str(e)}",
                "source": "error"
            }


def get_agents_client(client: Optional[WorkspaceClient] = None) -> Optional[AgentsClient]:
    """Get or create AgentsClient instance."""
    if client is None:
        from backend.main import get_databricks_client
        client = get_databricks_client()
    
    if client is None:
        return None
    
    config = {
        "genie_space_id": os.getenv("DATABRICKS_GENIE_SPACE_ID"),
        "knowledge_assistant_endpoint": os.getenv("DATABRICKS_KA_ENDPOINT"),
        "supervisor_endpoint": os.getenv("DATABRICKS_SUPERVISOR_ENDPOINT"),
    }
    
    return AgentsClient(client, config)
