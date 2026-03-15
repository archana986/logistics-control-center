"""
Create or update a Knowledge Assistant and attach volume-based knowledge source.
"""

from __future__ import annotations

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.knowledgeassistants import KnowledgeAssistant, KnowledgeSource

CATALOG = "demos"
SCHEMA = "logistics_control_center"
KA_DISPLAY_NAME = "Logistics Operations Knowledge Assistant"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/documents"

client = WorkspaceClient()

existing = None
for ka in client.knowledge_assistants.list_knowledge_assistants():
    if getattr(ka, "display_name", None) == KA_DISPLAY_NAME:
        existing = ka
        break

if existing:
    ka_obj = client.knowledge_assistants.update_knowledge_assistant(
        name=existing.name,
        knowledge_assistant=KnowledgeAssistant(
            display_name=KA_DISPLAY_NAME,
            description="Answers logistics SOP, incident, and reroute process questions from UC volume docs.",
            instructions=(
                "Use only the uploaded logistics documents. "
                "Quote process steps and include concise operational guidance."
            ),
        ),
        update_mask="display_name,description,instructions",
    )
    print(f"Updated knowledge assistant: {ka_obj.name}")
else:
    ka_obj = client.knowledge_assistants.create_knowledge_assistant(
        knowledge_assistant=KnowledgeAssistant(
            display_name=KA_DISPLAY_NAME,
            description="Answers logistics SOP, incident, and reroute process questions from UC volume docs.",
            instructions=(
                "Use only the uploaded logistics documents. "
                "Quote process steps and include concise operational guidance."
            ),
        )
    )
    print(f"Created knowledge assistant: {ka_obj.name}")

parent = ka_obj.name
source_name = "logistics-documents-volume"
sources = list(client.knowledge_assistants.list_knowledge_sources(parent=parent))
source_exists = any(getattr(s, "display_name", None) == source_name for s in sources)

if not source_exists:
    source = client.knowledge_assistants.create_knowledge_source(
        parent=parent,
        knowledge_source=KnowledgeSource(
            display_name=source_name,
            description=f"Knowledge files from {VOLUME_PATH}",
            volume_path=VOLUME_PATH,
        ),
    )
    print(f"Added knowledge source: {source.name}")
else:
    print("Knowledge source already exists; skipping create.")

client.knowledge_assistants.sync_knowledge_sources(name=parent)
print("Triggered knowledge source sync.")
