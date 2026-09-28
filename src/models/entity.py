"""RecognizedEntity and EntityOccurrence domain models."""

import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field


class RecognizedEntity(BaseModel):
    """Document-scoped unique named entity record."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, use_enum_values=True)

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        alias="_id",
        description="Unique UUID4 string identifier for the entity",
    )
    document_id: str = Field(
        ...,
        description="Reference UUID4 to the associated Document",
    )
    name: str = Field(
        ...,
        description="Normalized or canonical surface name of the entity",
    )
    entity_type: str = Field(
        ...,
        description="Entity classification label (e.g., Person, Organization, Location)",
    )
    total_occurrences: int = Field(
        default=1,
        ge=1,
        description="Cumulative count of occurrences across all pages of this document",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Record creation timestamp (UTC)",
    )

    @property
    def entity_id(self) -> str:
        """Alias returning the unique entity identifier."""
        return self.id


class EntityOccurrence(BaseModel):
    """Specific page-level mention of an entity with text character offsets."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, use_enum_values=True)

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        alias="_id",
        description="Unique UUID4 string identifier for the occurrence mention",
    )
    entity_id: str = Field(
        ...,
        description="Reference UUID4 to the parent RecognizedEntity",
    )
    document_id: str = Field(
        ...,
        description="Reference UUID4 to the parent Document",
    )
    page_number: int = Field(
        ...,
        ge=1,
        description="1-based sequential page index where the mention occurs",
    )
    start_offset: int = Field(
        ...,
        ge=0,
        description="0-based start character index within the page text",
    )
    end_offset: int = Field(
        ...,
        ge=0,
        description="0-based end character index within the page text",
    )
    surface_text: str = Field(
        ...,
        description="Exact surface text token as found in the page text",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Prediction confidence score from the recognition model",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Occurrence record creation timestamp (UTC)",
    )

    @property
    def occurrence_id(self) -> str:
        """Alias returning the unique occurrence identifier."""
        return self.id
