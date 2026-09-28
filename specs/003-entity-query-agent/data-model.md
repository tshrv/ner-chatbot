# Data & Tool Schema Models: Entity Query AI Agent

**Feature**: Entity Query AI Agent (`003-entity-query-agent`)  
**Date**: 2026-09-28  
**Status**: Completed  

---

## 1. Tool Return Schemas (Pydantic Models)

These structured schemas define the payloads returned by the database inspection tools to the Pydantic AI agent.

### 1.1 EntityTypeCountResult
```python
class EntityTypeCountResult(BaseModel):
    total_types_count: int = Field(description="Total count of entity type mentions across document records")
    unique_types_count: int = Field(description="Count of distinct entity types (e.g., Person, Organization)")
    types: List[str] = Field(description="Alphabetical list of unique entity type names")
```

### 1.2 EntityCountResult
```python
class EntityCountResult(BaseModel):
    total_entities_count: int = Field(description="Total entity records stored across documents")
    unique_entities_count: int = Field(description="Count of distinct entity names across documents")
```

### 1.3 EntityExistenceResult
```python
class EntityExistenceResult(BaseModel):
    exists: bool = Field(description="Whether the entity or entity type was found")
    query_term: str = Field(description="The input term searched")
    canonical_name: Optional[str] = Field(default=None, description="Matched canonical name with actual casing")
    entity_type: Optional[str] = Field(default=None, description="Classification type of the matched entity")
```

### 1.4 OccurrenceItem & OccurrenceQueryResult
```python
class OccurrenceDetail(BaseModel):
    document_name: str = Field(description="Source PDF filename where mention was found")
    page_number: int = Field(description="1-based page index")
    start_offset: int = Field(description="0-based character start position")
    end_offset: int = Field(description="0-based character end position")
    surface_text: str = Field(description="Exact text token from page")
    confidence: float = Field(description="Entity prediction confidence score")

class OccurrenceQueryResult(BaseModel):
    target: str = Field(description="Target entity name or entity type searched")
    search_type: str = Field(description="'entity' or 'entity_type'")
    total_occurrences: int = Field(description="Total occurrences found across all documents")
    document_breakdown: Dict[str, int] = Field(description="Count of occurrences grouped by document name")
    sample_occurrences: List[OccurrenceDetail] = Field(description="Detailed list of up to 10 occurrences")
    has_more: bool = Field(description="True if total occurrences exceed the returned sample limit")
```

---

## 2. Configuration Model Extension (`src/config.py`)

New settings fields in `Settings` class:

| Setting Name | Type | Default | Description |
|---|---|---|---|
| `gcp_vertex_ai_api_key` | `Optional[str]` | `None` (loaded from `.env`) | API key for Google Cloud Vertex AI access |
| `llm_model_name` | `str` | `"gemini-3.8-flash"` | Gemini model identifier |
| `agent_max_retries` | `int` | `3` | Maximum retry attempts for transient tool/model errors |

---

## 3. Database Collection Access Boundary

The AI agent tools are strictly bounded to read-only access on three collections:
- `entities`: Read-only queries for names and types.
- `occurrences`: Read-only queries for spans, offsets, and page numbers.
- `documents`: Read-only lookup to resolve `document_id` to human-readable `document.name`.
- **PROHIBITED**: `jobs` collection is never accessed or exposed to the agent tools.
