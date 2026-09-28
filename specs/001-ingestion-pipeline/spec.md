# Feature Specification: Ingestion Pipeline

**Feature Branch**: `001-ingestion-pipeline`

**Created**: 2026-09-28

**Status**: Draft

**Input**: User description: "Build a content extraction and named entitiy recognition pipeline. Let's call it "Ingestion Pipeline", available as cli command. Consider each trigger as a fresh execution and associate a unique job id with it. A PDF file will be available in the local file system, for which we run the context extraction process. Assign a unique id to the document. We need OCR enabled extraction. We expect the extracted content to retain the associated page number, document id, name, path, status, etc. Store it in a database. After extraction is completed, we start the named entity recognition process. For each page's content, we run enitity recognition. Recognition should most likely result in entities, their type, their occurences in text, etc. Save all of this information in database."

## Clarifications

### Session 2026-09-28

- Q: How should the extraction pipeline determine when to perform optical character recognition (OCR) on PDF pages? → A: Option B: Unconditional OCR on every page regardless of existing digital text layers.
- Q: At what scope should recognized entities be deduplicated and linked to occurrences? → A: Option A: Document-scoped deduplication (entities are unique per document, with occurrences across pages linked to the document's entity registry).
- Q: How should entity occurrences in page text be positioned and referenced in the database? → A: Option A: Character offsets (store 0-based start and end character offsets within the page text along with occurrence frequency).
- Q: If the named entity recognition process encounters an unrecoverable error on a specific page's text, how should the pipeline handle that page and the overall job? → A: Option A: Graceful page degradation (record the failure on that specific page, continue processing subsequent pages, and mark the job as Partially Completed).
- Q: How should the CLI command behave when execution is interrupted by a user cancellation signal (e.g., SIGINT / Ctrl+C)? → A: Option A: Graceful cancellation (catch signal, roll back in-flight transactions, update Job status to Failed (Interrupted) in the database, and exit cleanly).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Standard End-to-End PDF Ingestion and Entity Recognition via CLI (Priority: P1)

An operator executes the ingestion pipeline CLI command providing the path to a local PDF document. The system creates a fresh execution with a unique job identifier, registers the document with a unique document identifier, extracts the text content page-by-page, and stores all page content and document metadata in the database. Following successful extraction, the system automatically analyzes each page's content for named entities, identifies the entities, their categories, and their occurrences in the text, and stores all recognition data in the database, outputting a clear execution summary upon completion.

**Why this priority**: This represents the core end-to-end functionality of the Ingestion Pipeline. It delivers immediate, self-contained business value by transforming raw PDF documents into structured, queryable page content and recognized entities linked to their source records.

**Independent Test**: Can be tested independently by running the CLI command against a sample multi-page PDF document and verifying that a unique job record is created, document metadata and page text are stored in the database, entities and occurrences are extracted per page, and a success summary is output to the console.

**Acceptance Scenarios**:

1. **Given** a valid PDF file residing on the local filesystem, **When** the operator invokes the CLI ingestion command specifying the file path, **Then** the system registers a fresh execution with a unique job ID, assigns a unique document ID, and marks the job status as in progress.
2. **Given** an active ingestion job, **When** the content extraction process executes, **Then** each page's text is extracted and stored in the database along with its page number, document ID, document name, source path, and extraction status.
3. **Given** stored page content from a successful extraction, **When** the named entity recognition process executes for each page, **Then** identified entities, their entity types, and their occurrences (including position references and page links) are stored in the database.
4. **Given** completion of both extraction and entity recognition stages, **When** the pipeline finishes processing, **Then** the job status is updated to completed, and the system displays an execution summary on the console with job ID, document ID, total pages processed, and total entities discovered.

---

### User Story 2 - Uniform OCR-Driven Extraction Across All Document Types (Priority: P2)

An operator provides a PDF document (whether digitally generated, scanned physical paper, or image-centric without text streams). The pipeline uses its OCR capability to detect, recognize, and transcribe text from the visual content of every page unconditionally, preserving page numbering and metadata uniformly, allowing the subsequent entity recognition stage to analyze the transcribed text.

**Why this priority**: Documents ingested from diverse sources often have corrupted or incomplete embedded digital text layers. Unconditional OCR guarantees a consistent visual-fidelity extraction across all document formats without relying on fragile digital streams.

**Independent Test**: Can be tested independently by submitting both scanned image-only PDFs and digitally generated PDFs to the CLI command and verifying that text is successfully recognized via OCR, stored with correct page numbers and status, and processed for entities.

**Acceptance Scenarios**:

1. **Given** a PDF document containing scanned or rasterized image pages, **When** the extraction process processes each page, **Then** the OCR engine transcribes visual text into extracted content and records the page status as completed.
2. **Given** a document containing existing digital text layers, **When** extraction runs, **Then** all pages have their content extracted via the OCR engine and retained with correct sequential page numbers.

---

### User Story 3 - Execution Tracking and Resilient Failure Handling (Priority: P3)

An operator invokes the ingestion pipeline with an invalid input (such as a missing file path, a non-PDF file, or a corrupted document). The system generates a unique job ID, logs the failure with clear diagnostic details, updates the job status to failed in the database, and provides an actionable error message on the command line without unhandled exceptions or crashes.

**Why this priority**: Operational reliability requires that erroneous or corrupted inputs are safely isolated, cleanly audited, and clearly communicated to the operator without corrupting database state or hanging CLI executions.

**Independent Test**: Can be tested independently by providing non-existent paths, unreadable files, or corrupted PDFs to the CLI command and confirming that a unique job ID is recorded, database status reflects the failure, and the CLI exits cleanly with an error message and non-zero exit code.

**Acceptance Scenarios**:

1. **Given** a non-existent or inaccessible file path passed to the CLI, **When** the command is executed, **Then** the system records an execution job with a unique job ID, marks the status as failed with an appropriate error reason, outputs a descriptive error message to the console, and exits with a non-zero code.
2. **Given** a corrupted PDF where specific pages cannot be rendered or extracted, **When** extraction is attempted, **Then** the unreadable pages are marked with a failed status and error details, while any readable pages proceed, and the overall job completes with an audit log of page errors.

---

### Edge Cases

- **Empty PDF**: When a PDF file contains zero pages or is zero bytes in size, the system records the job, assigns a document ID, marks the document and job status as failed with an explanatory message, and halts further processing.
- **No Entities Found**: When a page contains valid extracted text but no named entities match the recognition models, the pipeline completes successfully, records the page content, and logs zero entity occurrences without failing.
- **Large Page Counts**: When processing high-page-count documents, the pipeline processes and commits page content and entity records iteratively to ensure system stability and progress visibility.
- **Duplicate Ingestion Invocations**: When the CLI command is executed multiple times against the exact same local file path, each execution is treated as an isolated run with a distinct job ID and fresh document assignment, ensuring complete lineage tracking.
- **Special Characters and Multi-Column Formats**: When a PDF page contains complex layouts, multi-column text, or special characters, the extraction preserves the textual flow accurately enough for entity recognition models to parse contextual mentions.
- **Page-Level Entity Recognition Failure**: When entity recognition fails on an individual page due to unparseable or corrupted text, the system marks that page's entity recognition status as failed with error details, continues processing all remaining pages, and marks the overall job as Partially Completed with an audit summary of page errors.
- **Process Interruption (SIGINT / Ctrl+C)**: When the operator interrupts the CLI execution, the pipeline catches the interrupt signal gracefully, rolls back any active uncommitted page transaction, updates the Job status in the database to Failed with an interruption reason, displays an interruption notice, and exits cleanly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a CLI command to trigger the document ingestion pipeline.
- **FR-002**: The system MUST accept a local filesystem path to a target PDF document as an input parameter for the CLI command.
- **FR-003**: The system MUST create a fresh execution record with a unique Job ID upon every invocation of the CLI command.
- **FR-004**: The system MUST validate that the target file exists, is accessible, and adheres to the PDF format prior to processing.
- **FR-005**: The system MUST assign a unique Document ID to the document being ingested.
- **FR-006**: The system MUST extract textual content from each page of the PDF document by executing optical character recognition (OCR) across every page unconditionally, ensuring consistent text extraction regardless of whether an underlying digital text stream exists.
- **FR-007**: The system MUST associate and retain with each extracted page record: the Document ID, document name, source file path, 1-based page number, extracted text, and extraction status.
- **FR-008**: The system MUST persist all extracted document metadata and page records into a persistent database.
- **FR-009**: The system MUST initiate the named entity recognition process across the extracted content of each page after content extraction for the page is completed.
- **FR-010**: The system MUST identify named entities from each page's extracted content, classifying each recognized entity by type (e.g., person, organization, location, date, or other designated categories), and deduplicating unique entities at the document level.
- **FR-011**: The system MUST capture and record the occurrences of each recognized entity within the page text, storing 0-based start and end character offsets within the page text alongside occurrence frequency.
- **FR-012**: The system MUST persist unique document-scoped entities and their page-level occurrences into the database, explicitly linking occurrences to both the parent Document ID and the specific Page Number.
- **FR-013**: The system MUST track and update the status of each job through its lifecycle stages (Pending, In Progress, Completed, Failed, or Partially Completed), marking the job as Partially Completed if extraction or entity recognition fails on individual pages while other pages succeed, and recording Failed (Interrupted) upon graceful termination from user interruption.
- **FR-014**: The system MUST display execution progress and a final completion summary to the CLI user, including the Job ID, Document ID, total pages processed, and total entities recognized.
- **FR-015**: The system MUST record descriptive error details in the database and present actionable error messages via the CLI when processing fails.

### Key Entities

- **Ingestion Job**: Represents an individual execution run of the pipeline. Key attributes include: unique Job ID, start timestamp, completion timestamp, execution status (Pending, In Progress, Completed, Failed, Partially Completed), and error summary.
- **Document**: Represents the target file being ingested. Key attributes include: unique Document ID, associated Job ID, original document name, local filesystem path, format type, total page count, and document status.
- **Document Page**: Represents an individual page within a document. Key attributes include: unique Page ID, Document ID reference, sequential page number, extracted textual content, extraction status (Pending, Completed, Failed), entity recognition status (Pending, Completed, Failed), and error description.
- **Recognized Entity**: Represents a distinct named entity discovered within a document (deduplicated per document). Key attributes include: unique Entity ID, Document ID reference, canonical name/text, and entity classification/type.
- **Entity Occurrence**: Represents a specific mention of an entity on a particular page. Key attributes include: unique Occurrence ID, Entity ID reference, Page ID reference, Document ID reference, start_offset (0-based start character index), end_offset (0-based end character index), exact surface text, and mention frequency.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can execute the pipeline via a single CLI command with feedback provided within 5 seconds of invocation confirming job start and Job ID assignment.
- **SC-002**: 100% of pipeline executions generate a globally unique Job ID and Document ID, maintaining complete execution isolation.
- **SC-003**: 100% of successfully extracted pages retain accurate page numbers, Document ID linkage, file path, and extraction status in the database.
- **SC-004**: OCR extraction successfully transcribes clear scanned or image-based PDF pages with at least 85% character recognition accuracy.
- **SC-005**: 100% of recognized entities on any page are persisted with their respective entity types, occurrence positions, and page linkages.
- **SC-006**: The end-to-end pipeline (extraction through entity persistence) processes a standard 10-page text document in under 60 seconds.
- **SC-007**: 100% of fatal errors (e.g., invalid file path, unreadable file, corrupted format) result in an audited Failed status in the database, a non-zero CLI exit code, and a descriptive error message displayed to the operator.

## Assumptions

- Target PDF documents are stored on the local filesystem and accessible by the user running the CLI command.
- The pipeline processes a single document per CLI invocation; batch ingestion of directory trees can be handled via repeated invocations or a subsequent batch orchestration feature.
- OCR text extraction is optimized for English-language documents by default; multi-language OCR models can be configured as future extensions.
- Database services are provisioned and accessible prior to running the ingestion pipeline command.
- Standard general entity classifications (e.g., PERSON, ORGANIZATION, LOCATION, DATE, MISCELLANEOUS) are supported as standard entity recognition types.
- If a document page contains zero extractable text (e.g., a completely blank page), the page is marked as completed with empty content, and entity recognition is cleanly bypassed for that page.
