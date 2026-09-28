# Research & Technical Decisions: Entity Query AI Agent

**Feature**: Entity Query AI Agent (`003-entity-query-agent`)  
**Date**: 2026-09-28  
**Status**: Completed  

---

## 1. Agent Framework & Architecture

### Decision
Use `pydantic-ai` (`pydantic-ai-slim[google]`) to build the AI agent, with the Google Gemini model accessed via GCP Vertex AI / Google Cloud Provider with the configured API key (`GCP_VERTEX_AI_API_KEY`).

### Rationale
- The user explicitly requested `pydantic-ai` and `GCP Vertex AI via api key (Agent Platform API)` with model `gemini-3.8-flash`.
- Pydantic AI natively integrates with Google Cloud Provider via `GoogleModel` and `GoogleCloudProvider(api_key=...)`.
- Type-safe tool definitions using Python type hints and Pydantic schemas ensure strict parameter validation.
- Single-turn execution is naturally enforced by invoking `agent.run(prompt)` per turn without passing message history.

### Alternatives Considered
- LangChain / CrewAI: Heavier abstractions, more boilerplate, less native alignment with Pydantic domain models.
- Custom OpenAI client wrapper: Requires manual tool call parsing and schema conversion.

---

## 2. Model & Authentication Configuration

### Decision
Load `GCP_VERTEX_AI_API_KEY` from `.env` via `src/config.py` using `pydantic-settings`. Configure the provider:
```python
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google_cloud import GoogleCloudProvider

provider = GoogleCloudProvider(api_key=settings.gcp_vertex_ai_api_key)
model = GoogleModel(settings.llm_model_name, provider=provider)
```
Default model identifier: `"gemini-3.8-flash"`.

### Rationale
- Securely pulls credentials from `.env` without exposing or hardcoding keys.
- Directly supports Vertex AI express mode / API key access.

---

## 3. Database Inspection Tools Design

### Decision
Implement an asynchronous entity querying toolset in `src/services/agent_tools.py` directly querying MongoDB via `motor`:
1. `count_entity_types()`: Aggregate total and unique entity type counts.
2. `list_entity_types()`: Distinct list of all entity types in database.
3. `check_entity_type_exists(type_name: str)`: Case-insensitive regex check for type existence.
4. `count_entities()`: Aggregate total entity records and unique entity names.
5. `list_entities(type_name: Optional[str] = None, limit: int = 50)`: List entity names and types.
6. `check_entity_exists(entity_name: str)`: Case-insensitive check for entity presence.
7. `get_entity_occurrences(entity_name: str)`: Look up occurrences with document name resolution, page number, and character offsets.
8. `get_entity_type_occurrences(type_name: str)`: Look up occurrences for all entities of a given type.

### Rationale
- Fulfills 100% of the query types requested by the user.
- Strictly queries `entities`, `occurrences`, and `documents` collections; never accesses `jobs` collection.
- Case-insensitive regex matching (`{"$regex": f"^{re.escape(name)}$", "$options": "i"}`) ensures robust entity lookup.

---

## 4. Single-Turn Chat Loop & Guardrails

### Decision
Implement the CLI chat loop under Typer command `chat` in `src/main.py`:
- Welcome banner: Displays usage and exit instructions.
- Stdin loop: Prompts with `You: `, receives query, invokes agent with query only.
- Strict system prompt:
  - Answers ONLY about entities, types, and occurrences.
  - Denies out-of-scope queries (general facts, chit-chat, pipeline execution details).
  - Explicitly states when data is missing rather than hallucinating.
  - Formats occurrence lists with document breakdown and top 10 previews.
- Retries: Wraps `agent.run()` in a 3-attempt retry loop on transient model or network errors.

### Rationale
- Conforms to User Stories 1, 2, and 3.
- Completely prevents conversational state leakage across turns.
