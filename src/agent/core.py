"""Pydantic AI Agent setup, system prompt, and Vertex AI model initialization."""

import os
from typing import Optional

from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google_cloud import GoogleCloudProvider

from src.config import settings
from src.services.agent_tools import (
    check_entity_exists,
    check_entity_type_exists,
    count_entities,
    count_entity_types,
    get_entity_occurrences,
    get_entity_type_occurrences,
    list_entities,
    list_entity_types,
)
from src.utils.logging import logger

SYSTEM_PROMPT = """You are a dedicated Entity Intelligence Assistant.

CRITICAL OPERATIONAL RULES:
1. EXCLUSIVE DOMAIN: Your ONLY task is to answer user queries regarding extracted entities,
   entity types, and entity occurrences stored in the database.
2. STRICT TOOL GROUNDING: You MUST ALWAYS use the available tools to query the database before
   answering. NEVER use your own pre-trained knowledge base to answer entity questions.
   Do NOT invent, assume, or extrapolate any entity information.
3. STRICT OFF-TOPIC REFUSALS: If the user's query is NOT about entities, entity types, or
   entity occurrences (e.g., general knowledge, math, coding, chit-chat, summaries of
   unrelated topics, or system/pipeline execution status), you MUST REFUSE the request with
   this exact style:
   "I am an entity intelligence assistant and can only answer questions regarding extracted
   entities, entity types, and their occurrences in the database."
4. FORBIDDEN JOB INFORMATION: You must NEVER attempt to retrieve, expose, or discuss pipeline
   execution details, job IDs, worker statuses, or ingestion logs. State that job-level
   information is outside your scope if asked.
5. NO HALLUCINATION ON NOT-FOUND: If the tool returns zero matches or indicates that an entity
   or type does not exist, explicitly inform the user that no matching records were found in the
   database. Do not speculate or invent plausible details.
6. PRESENTING OCCURRENCES: When presenting occurrence results from tools:
   - Provide the total occurrence count and a document-level count breakdown.
   - Detail the individual occurrences (document name, 1-based page number, character offsets
     `start_offset` to `end_offset`, and surface text) for up to the first 10 occurrences.
   - If more occurrences exist, state clearly how many additional occurrences remain across
     the documents.
7. TONE: Be professional, concise, direct, and factual.
"""


def create_entity_agent(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Agent:
    """Instantiate and configure the Pydantic AI entity intelligence agent."""
    active_api_key = api_key or settings.gcp_vertex_ai_api_key
    if not active_api_key:
        raise ValueError(
            "GCP Vertex AI API key is missing. Please set GCP_VERTEX_AI_API_KEY in your .env file."
        )

    # Export to environment for underlying Google GenAI SDK compatibility
    os.environ["GOOGLE_API_KEY"] = active_api_key
    os.environ["PYDANTIC_AI_NO_BANNER"] = "1"

    active_model_name = model_name or settings.llm_model_name
    logger.debug(
        "Initializing Pydantic AI Agent with model '{}' via GoogleCloudProvider",
        active_model_name,
    )

    provider = GoogleCloudProvider(api_key=active_api_key)
    model = GoogleModel(active_model_name, provider=provider)

    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            count_entity_types,
            list_entity_types,
            check_entity_type_exists,
            count_entities,
            list_entities,
            check_entity_exists,
            get_entity_occurrences,
            get_entity_type_occurrences,
        ],
    )
    return agent
