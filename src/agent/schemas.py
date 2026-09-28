"""Pydantic schemas for AI agent tool returns."""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class EntityTypeCountResult(BaseModel):
    """Result schema for entity type counting."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    total_types_count: int = Field(
        description="Total count of entity type mentions across document records"
    )
    unique_types_count: int = Field(
        description="Count of distinct entity types (e.g., Person, Organization)"
    )
    types: List[str] = Field(description="Alphabetical list of unique entity type names")


class EntityCountResult(BaseModel):
    """Result schema for entity counting."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    total_entities_count: int = Field(description="Total entity records stored across documents")
    unique_entities_count: int = Field(
        description="Count of distinct entity names across documents"
    )


class EntityExistenceResult(BaseModel):
    """Result schema for existence checks on entities or types."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    exists: bool = Field(description="Whether the entity or entity type was found")
    query_term: str = Field(description="The input term searched")
    canonical_name: Optional[str] = Field(
        default=None, description="Matched canonical name with actual casing"
    )
    entity_type: Optional[str] = Field(
        default=None, description="Classification type of the matched entity"
    )


class EntityItem(BaseModel):
    """Summary record for a single entity in a list."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(description="Entity name")
    entity_type: str = Field(description="Classification category")
    total_occurrences: int = Field(description="Number of occurrences in the document")


class EntityListResult(BaseModel):
    """Result schema for listing entities."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    entities: List[EntityItem] = Field(description="List of entities matching the query")
    total_returned: int = Field(description="Number of entity items returned in this result")
    total_unique_entities: int = Field(description="Total unique entities present in database")


class OccurrenceDetail(BaseModel):
    """Specific page occurrence detail for an entity."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    document_name: str = Field(description="Source PDF filename where mention was found")
    page_number: int = Field(description="1-based page index")
    start_offset: int = Field(description="0-based character start position")
    end_offset: int = Field(description="0-based character end position")
    surface_text: str = Field(description="Exact text token from page")
    confidence: float = Field(description="Entity prediction confidence score")


class OccurrenceQueryResult(BaseModel):
    """Aggregated occurrence query result with top-N preview."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    target: str = Field(description="Target entity name or entity type searched")
    search_type: str = Field(description="'entity' or 'entity_type'")
    total_occurrences: int = Field(description="Total occurrences found across all documents")
    document_breakdown: Dict[str, int] = Field(
        description="Count of occurrences grouped by document name"
    )
    sample_occurrences: List[OccurrenceDetail] = Field(
        description="Detailed list of up to 10 occurrences"
    )
    has_more: bool = Field(description="True if total occurrences exceed the returned sample limit")
