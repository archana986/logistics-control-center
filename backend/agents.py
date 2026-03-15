"""Agent Bricks client for Genie, Knowledge Assistant, and Multi-Agent Supervisor.

Knowledge Assistant (KA) and other Agent Bricks endpoints use the
``input``/``output`` wire format rather than the standard ``messages``/``choices``
format used by foundation-model serving endpoints.  The helpers here call
the endpoint through the SDK's low-level HTTP API so the payload can be
customised.
"""

import json
import os
from typing import Optional, Dict, Any

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole
from databricks.sdk.service.sql import StatementState


def _extract_agent_text(response_json: dict) -> tuple[str, list]:
    """Extract answer text and citations from an Agent Bricks response.

    Agent Bricks responses have the shape::

        {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": "..."},
                        ...
                    ]
                }
            ]
        }
    """
    text_parts: list[str] = []
    citations: list[str] = []

    for output_item in response_json.get("output", []):
        for content_block in output_item.get("content", []):
            if isinstance(content_block, dict):
                text = content_block.get("text", "")
                if text:
                    text_parts.append(text)
                for ann in content_block.get("annotations", []):
                    if isinstance(ann, dict) and ann.get("url"):
                        citations.append(ann["url"])

    return "\n".join(text_parts), citations


class AgentsClient:
    """Interface to Agent Bricks services."""

    def __init__(self, client: WorkspaceClient, config: Dict[str, str]):
        self.client = client
        self.genie_space_id = config.get("genie_space_id")
        self.ka_endpoint = config.get("knowledge_assistant_endpoint")
        self.supervisor_endpoint = config.get("supervisor_endpoint")

    # ------------------------------------------------------------------
    # Low-level helper: call an Agent Bricks endpoint via raw HTTP
    # ------------------------------------------------------------------
    def _call_agent_endpoint(self, endpoint_name: str, prompt: str) -> dict:
        """Call an Agent Bricks serving endpoint that uses the ``input`` format.

        Returns the raw JSON response dict.
        """
        payload = {
            "input": [{"role": "user", "content": prompt}]
        }

        # Use the SDK's internal API client to make an authenticated POST
        api_client = self.client.api_client
        resp = api_client.do(
            "POST",
            f"/serving-endpoints/{endpoint_name}/invocations",
            body=payload,
        )
        # resp is already a dict parsed from JSON
        return resp

    # ------------------------------------------------------------------
    # Genie
    # ------------------------------------------------------------------
    def query_genie(self, question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query structured data via Genie space."""
        if not self.genie_space_id:
            return {"answer": "Genie space not configured", "sql": None, "data": [], "source": "error"}

        try:
            message = self.client.genie.start_conversation_and_wait(
                space_id=self.genie_space_id,
                content=question,
            )
            text_parts: list[str] = []
            query_text: Optional[str] = None
            rows: list[dict] = []

            for attachment in getattr(message, "attachments", []) or []:
                text_obj = getattr(attachment, "text", None)
                if text_obj and getattr(text_obj, "content", None):
                    text_parts.append(str(text_obj.content))

                query_obj = getattr(attachment, "query", None)
                if query_obj and not query_text:
                    query_text = getattr(query_obj, "query", None)
                    attachment_id = getattr(attachment, "attachment_id", None)
                    if attachment_id and getattr(message, "conversation_id", None) and getattr(message, "id", None):
                        try:
                            result = self.client.genie.get_message_attachment_query_result(
                                space_id=self.genie_space_id,
                                conversation_id=message.conversation_id,
                                message_id=message.id,
                                attachment_id=str(attachment_id),
                            )
                            statement_response = getattr(result, "statement_response", None)
                            if statement_response and statement_response.status and statement_response.status.state == StatementState.SUCCEEDED:
                                # Parse simple row output
                                if statement_response.result and statement_response.result.data_array:
                                    cols = [c.name for c in statement_response.manifest.schema.columns]
                                    for row in statement_response.result.data_array:
                                        rows.append({cols[i]: row[i] if i < len(row) else None for i in range(len(cols))})
                        except Exception:
                            pass

            answer = "\\n\\n".join(part.strip() for part in text_parts if part and part.strip())
            if not answer:
                answer = "Genie returned no text answer for this question."
            return {"answer": answer, "sql": query_text, "data": rows, "source": "genie"}
        except Exception as e:
            return {"answer": f"Error querying Genie: {str(e)}", "sql": None, "data": [], "source": "error"}

    # ------------------------------------------------------------------
    # Knowledge Assistant
    # ------------------------------------------------------------------
    def query_knowledge_assistant(self, question: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query unstructured docs via Knowledge Assistant endpoint.

        Uses the Agent Bricks ``input``/``output`` wire format.
        """
        if not self.ka_endpoint:
            return {"answer": "Knowledge Assistant endpoint not configured", "citations": [], "source": "error"}

        try:
            # Build prompt with context
            prompt = question
            if context:
                context_parts = []
                for k, v in context.items():
                    context_parts.append(f"{k}: {json.dumps(v) if isinstance(v, (dict, list)) else v}")
                prompt = f"Context:\n" + "\n".join(context_parts) + f"\n\nQuestion: {question}"

            resp = self._call_agent_endpoint(self.ka_endpoint, prompt)
            answer, citations = _extract_agent_text(resp)

            if answer:
                return {"answer": answer, "citations": citations, "source": "knowledge_assistant"}
            else:
                return {"answer": "No response from Knowledge Assistant", "citations": [], "source": "error"}
        except Exception as e:
            return {"answer": f"Error querying Knowledge Assistant: {str(e)}", "citations": [], "source": "error"}

    # ------------------------------------------------------------------
    # Multi-Agent Supervisor
    # ------------------------------------------------------------------
    def query_supervisor(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route complex queries through Multi-Agent Supervisor."""
        if not self.supervisor_endpoint:
            return {"message": "Multi-Agent Supervisor endpoint not configured", "source": "error"}

        try:
            prompt = message
            if context:
                context_parts = []
                if context.get("incident"):
                    inc = context["incident"]
                    context_parts.append(f"Incident: {inc.get('ref', 'N/A')} on lane {inc.get('laneId', 'N/A')}")
                    context_parts.append(f"Type: {inc.get('type', 'N/A')}")
                    context_parts.append(f"Cause: {inc.get('cause', 'N/A')}")
                if context.get("lane"):
                    context_parts.append(f"Lane: {context['lane'].get('id', 'N/A')}")
                if context_parts:
                    prompt = "Context:\n" + "\n".join(context_parts) + f"\n\nUser question: {message}"

            # Try Agent Bricks format first
            try:
                resp = self._call_agent_endpoint(self.supervisor_endpoint, prompt)
                answer, _ = _extract_agent_text(resp)
                if answer:
                    return {"message": answer, "source": "supervisor"}
            except Exception:
                pass

            # Fallback: standard chat completion format
            response = self.client.serving_endpoints.query(
                name=self.supervisor_endpoint,
                messages=[ChatMessage(role=ChatMessageRole.USER, content=prompt)],
                max_tokens=2000,
                temperature=0.5,
            )
            if response.choices and len(response.choices) > 0:
                mc = response.choices[0].message.content
                if isinstance(mc, list):
                    text_parts = [b.get("text", "") for b in mc if isinstance(b, dict) and b.get("text")]
                    return {"message": "\n".join(text_parts), "source": "supervisor"}
                return {"message": str(mc), "source": "supervisor"}

            return {"message": "No response from Multi-Agent Supervisor", "source": "error"}
        except Exception as e:
            return {"message": f"Error querying Multi-Agent Supervisor: {str(e)}", "source": "error"}


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
