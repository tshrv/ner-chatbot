"""IngestionJob model and lifecycle status enumeration."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class JobStatus(str, Enum):
    """Lifecycle status of an execution job."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"


class IngestionJob(BaseModel):
    """Execution record for an individual ingestion pipeline run."""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, use_enum_values=True)

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        alias="_id",
        description="Unique UUID4 string identifier for the execution job",
    )
    file_path: str = Field(
        ...,
        description="Filesystem path of the target document provided at invocation",
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Reference UUID4 to the associated registered Document",
    )
    status: JobStatus = Field(
        default=JobStatus.PENDING,
        description="Current operational lifecycle stage of the job",
    )
    total_pages: int = Field(
        default=0,
        ge=0,
        description="Total pages discovered in the target document",
    )
    pages_extracted: int = Field(
        default=0,
        ge=0,
        description="Count of pages with successfully completed OCR extraction",
    )
    pages_ner_completed: int = Field(
        default=0,
        ge=0,
        description="Count of pages with successfully completed entity recognition",
    )
    total_entities_found: int = Field(
        default=0,
        ge=0,
        description="Total distinct document-scoped entities discovered",
    )
    total_occurrences_found: int = Field(
        default=0,
        ge=0,
        description="Total entity mentions recorded across all pages",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Explanatory diagnostic text if execution fails or partially degrades",
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when execution began (UTC)",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when execution terminated (UTC)",
    )

    @property
    def job_id(self) -> str:
        """Alias returning the unique job identifier."""
        return self.id
