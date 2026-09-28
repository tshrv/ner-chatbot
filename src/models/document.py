"""Document and DocumentPage domain models and extraction lifecycle enums."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentStatus(str, Enum):
    """Lifecycle status of a document."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionStatus(str, Enum):
    """Content extraction status for an individual page."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class NerStatus(str, Enum):
    """Named entity recognition status for an individual page."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(BaseModel):
    """Document metadata and registration record."""

    model_config = ConfigDict(
        populate_by_name=True, arbitrary_types_allowed=True, use_enum_values=True
    )

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        alias="_id",
        description="Unique UUID4 string identifier for the document",
    )
    job_id: str = Field(
        ...,
        description="Reference UUID4 of the initiating execution job",
    )
    name: str = Field(
        ...,
        description="Original filename of the document",
    )
    file_path: str = Field(
        ...,
        description="Resolved filesystem path of the source document",
    )
    file_size_bytes: int = Field(
        default=0,
        ge=0,
        description="Size of the document in bytes",
    )
    format: str = Field(
        default="application/pdf",
        description="File MIME or format identifier",
    )
    total_pages: int = Field(
        default=0,
        ge=0,
        description="Total page count of the document",
    )
    status: DocumentStatus = Field(
        default=DocumentStatus.PENDING,
        description="Document-level extraction and processing status",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if document processing fails",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Record creation timestamp (UTC)",
    )

    @property
    def document_id(self) -> str:
        """Alias returning the unique document identifier."""
        return self.id


class DocumentPage(BaseModel):
    """Individual page textual content and extraction/NER state."""

    model_config = ConfigDict(
        populate_by_name=True, arbitrary_types_allowed=True, use_enum_values=True
    )

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        alias="_id",
        description="Unique UUID4 string identifier for the page",
    )
    document_id: str = Field(
        ...,
        description="Reference UUID4 to the parent Document",
    )
    job_id: str = Field(
        ...,
        description="Reference UUID4 to the associated IngestionJob",
    )
    page_number: int = Field(
        ...,
        ge=1,
        description="1-based sequential page index within the document",
    )
    content: str = Field(
        default="",
        description="OCR-transcribed plain text content of the page",
    )
    char_count: int = Field(
        default=0,
        ge=0,
        description="Total character count of page content",
    )
    extraction_status: ExtractionStatus = Field(
        default=ExtractionStatus.PENDING,
        description="Status of the OCR extraction stage for this page",
    )
    ner_status: NerStatus = Field(
        default=NerStatus.PENDING,
        description="Status of the named entity recognition stage for this page",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Diagnostic error description if extraction or NER fails",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Page record creation timestamp (UTC)",
    )

    @property
    def page_id(self) -> str:
        """Alias returning the unique page identifier."""
        return self.id
