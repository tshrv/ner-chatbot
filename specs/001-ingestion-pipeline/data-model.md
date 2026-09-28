# Data Model: Ingestion Pipeline

**Feature**: Ingestion Pipeline (`001-ingestion-pipeline`)  
**Date**: 2026-09-28  
**Status**: Completed  

---

## 1. Domain Entities & Schemas

### 1.1 IngestionJob
Represents an individual execution of the ingestion pipeline.

- **Collection**: `jobs`
- **Fields**:
  - `_id` / `job_id` (`str`): Unique UUID4 string identifier for the execution.
  - `file_path` (`str`): Absolute or relative filesystem path of the target document.
  - `document_id` (`str | None`): UUID4 string referencing the registered document.
  - `status` (`str`): Job state:
    - `"pending"`: Job registered, not yet started.
    - `"in_progress"`: Content extraction or NER actively executing.
    - `"completed"`: All pages extracted and NER completed successfully.
    - `"partially_completed"`: Pipeline finished, but one or more pages experienced extraction/NER failures.
    - `"failed"`: Pipeline aborted (fatal input error, unhandled exception, or SIGINT cancellation).
  - `total_pages` (`int`): Total pages discovered in the target document (0 if failed before inspection).
  - `pages_extracted` (`int`): Count of pages with successful OCR extraction.
  - `pages_ner_completed` (`int`): Count of pages with successful entity recognition.
  - `total_entities_found` (`int`): Total count of distinct document-scoped entities recognized.
  - `total_occurrences_found` (`int`): Total count of page-level mentions recorded.
  - `error_message` (`str | None`): Diagnostic message if status is `"failed"` or `"partially_completed"`.
  - `started_at` (`datetime`): Timestamp when execution began (UTC).
  - `completed_at` (`datetime | None`): Timestamp when execution finished (UTC).

---

### 1.2 Document
Represents the target PDF document registered for extraction.

- **Collection**: `documents`
- **Fields**:
  - `_id` / `document_id` (`str`): Unique UUID4 string identifier.
  - `job_id` (`str`): UUID4 reference to the initiating IngestionJob.
  - `name` (`str`): Filename of the target PDF (e.g., `"sample.pdf"`).
  - `file_path` (`str`): Resolved filesystem path to the file.
  - `file_size_bytes` (`int`): Size of the document in bytes.
  - `format` (`str`): File format identifier (default: `"application/pdf"`).
  - `total_pages` (`int`): Total number of pages reported by Xberg metadata.
  - `status` (`str`): Document lifecycle state (`"pending"`, `"in_progress"`, `"completed"`, `"failed"`).
  - `error_message` (`str | None`): Error description if document-level extraction failed.
  - `created_at` (`datetime`): Record creation timestamp (UTC).

---

### 1.3 DocumentPage
Represents an individual page within the document, storing the OCR-transcribed textual content and per-page lifecycle statuses.

- **Collection**: `pages`
- **Fields**:
  - `_id` / `page_id` (`str`): Unique UUID4 string identifier.
  - `document_id` (`str`): UUID4 reference to the parent Document.
  - `job_id` (`str`): UUID4 reference to the IngestionJob.
  - `page_number` (`int`): 1-based sequential page index.
  - `content` (`str`): OCR-extracted plain text content of the page.
  - `char_count` (`int`): Character length of `content`.
  - `extraction_status` (`str`): State of OCR extraction (`"pending"`, `"completed"`, `"failed"`).
  - `ner_status` (`str`): State of named entity recognition (`"pending"`, `"completed"`, `"failed"`).
  - `error_message` (`str | None`): Diagnostic error text if extraction or NER failed for this page.
  - `created_at` (`datetime`): Page record creation timestamp (UTC).

---

### 1.4 RecognizedEntity
Represents a distinct named entity discovered within the document (deduplicated per document).

- **Collection**: `entities`
- **Fields**:
  - `_id` / `entity_id` (`str`): Unique UUID4 string identifier.
  - `document_id` (`str`): UUID4 reference to the parent Document.
  - `name` (`str`): Normalized / canonical entity surface string (e.g., `"John Doe"`).
  - `entity_type` (`str`): Entity classification category (e.g., `"Person"`, `"Organization"`, `"Location"`, `"Date"`, `"Event"`).
  - `total_occurrences` (`int`): Aggregate count of occurrences across all pages of the document.
  - `created_at` (`datetime`): Record creation timestamp (UTC).

---

### 1.5 EntityOccurrence
Represents a specific mention of a recognized entity on a specific page, including character offsets and confidence.

- **Collection**: `occurrences`
- **Fields**:
  - `_id` / `occurrence_id` (`str`): Unique UUID4 string identifier.
  - `entity_id` (`str`): UUID4 reference to the parent RecognizedEntity.
  - `document_id` (`str`): UUID4 reference to the parent Document.
  - `page_number` (`int`): 1-based sequential page index where the mention occurs.
  - `start_offset` (`int`): 0-based character index where the entity starts in the page's `content`.
  - `end_offset` (`int`): 0-based character index where the entity ends in the page's `content`.
  - `surface_text` (`str`): Exact text span extracted from the page.
  - `confidence` (`float`): Model prediction confidence score between 0.0 and 1.0.
  - `created_at` (`datetime`): Record creation timestamp (UTC).

---

## 2. Relationships & Indexes

### Entity Relationship Diagram (ERD)

```text
[ IngestionJob ]
       │ 1
       │ has
       ▼ 1
[ Document ] ──────── 1:N ────────► [ DocumentPage ]
       │ 1                                 │ 1
       │ has                               │ has
       ▼ N                                 ▼ N
[ RecognizedEntity ] ── 1:N ──────► [ EntityOccurrence ]
```

### MongoDB Indexes

1. **`jobs`**:
   - `_id` (default primary index)
   - `status` (sparse / ascending for status filtering)
   - `started_at` (descending for execution history)

2. **`documents`**:
   - `_id` (primary index)
   - `job_id` (lookup by execution job)

3. **`pages`**:
   - Compound index: `{ document_id: 1, page_number: 1 }` (unique constraint)
   - `job_id` (lookup by execution job)

4. **`entities`**:
   - Compound index: `{ document_id: 1, name: 1, entity_type: 1 }` (unique constraint for document-scoped deduplication)

5. **`occurrences`**:
   - `entity_id` (lookup all occurrences of an entity)
   - Compound index: `{ document_id: 1, page_number: 1 }` (lookup occurrences per page)

---

## 3. Pydantic Models Hierarchy

All models inherit from `pydantic.BaseModel` configured with `model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)`.

```python
class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"

class ExtractionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class NerStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
```
