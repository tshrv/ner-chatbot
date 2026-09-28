# Research & Technical Decisions: Ingestion Pipeline

**Feature**: Ingestion Pipeline (`001-ingestion-pipeline`)  
**Date**: 2026-09-28  
**Status**: Completed  

---

## 1. CLI Framework & Application Entrypoint

### Decision
Use `typer` to provide the command-line interface as the single entrypoint for the ingestion pipeline, organized under an `app` group or direct CLI command with typed arguments and options.

### Rationale
- Strictly aligns with Constitution Principle II (CLI Interface via Typer).
- Enforces static type hints for parameters (`Path`, `Optional[List[str]]`, `float`, etc.).
- Built-in parameter validation, auto-generated help docs, and standard I/O separation (diagnostic logs to stderr, clean user summary to stdout).

### Alternatives Considered
- `argparse` / `click`: Click is the underlying foundation for Typer, but Typer uses modern Python type annotations directly, avoiding boilerplate parameter decorators.

---

## 2. Document & Page Content Extraction Service

### Decision
Integrate with `xberg` running as a containerized service (`ghcr.io/xberg-io/xberg:1.2.9`) exposed on `http://localhost:8000`. Content extraction is executed via HTTP REST API (`POST /extract`) using `httpx.AsyncClient` with multipart file upload (`files={"files": file_bytes}`) and unconditional OCR configuration (`{"ocr": {"backend": "tesseract", "language": ["eng"]}, "force_ocr": true}`).

### Rationale
- The user requested Xberg version 1.2.9 via Docker Compose and API client calls.
- Per Constitution Principle IV, running external extraction tools in Docker ensures reproducibility and clean host environments.
- Per Constitution Principle III, `httpx.AsyncClient` ensures extraction network I/O does not block the async event loop.
- Xberg `/extract` endpoint provides a structured response containing:
  - `content`: full concatenated document text.
  - `pages`: list of page objects containing `page_number` (1-indexed) and `content` (extracted page text).
  - `metadata`: page count and format metadata.

### Alternatives Considered
- Direct Python binding (`pip install xberg`): Requires native C/Rust binaries and local OCR dependencies on the host machine, violating the container-first principle.
- Unstructured / PyMuPDF: User explicitly specified Xberg with Docker Compose.

---

## 3. Named Entity Recognition (NER) Framework

### Decision
Use `gliner` Python package with the pretrained multitask model `"knowledgator/gliner-multitask-large-v0.5"`. Run model inference within worker threads using `asyncio.to_thread` to prevent CPU-bound PyTorch/ONNX matrix operations from stalling the async event loop.

### Rationale
- High zero-shot and open-vocabulary entity recognition accuracy without requiring heavy fine-tuning.
- Returns explicit character offsets (`start`, `end`), recognized surface text, labels, and confidence scores (`score`).
- CPU-heavy inference is isolated via `asyncio.to_thread(model.predict_entities, page_text, labels, threshold=threshold)`, complying with Constitution Principle III.
- Configurable entity labels are loaded from `.env` via Pydantic settings with sane defaults (`["Person", "Organization", "Location", "Date", "Event"]`).

### Alternatives Considered
- `spaCy`: Fast, but requires separate pipelines for custom or diverse entity types; GLiNER multitask supports flexible, arbitrary label schemas out of the box.
- Cloud NER APIs (AWS Comprehend, Google NLP): Adds recurring network latency, costs, and external credential dependencies.

---

## 4. Persistent Storage & Database Layer

### Decision
Use MongoDB as the primary database running via Docker Compose (`image: mongo:7.0` or `mongo:8.0`), accessed asynchronously through `motor` (`motor.motor_asyncio.AsyncIOMotorClient`).

### Rationale
- MongoDB provides a document-oriented data model that maps cleanly to hierarchical and nested document structures (jobs, documents, pages, entities, and occurrences).
- `motor` is the standard asynchronous driver for MongoDB in Python, aligning with Constitution Principle III.
- Containerized via Docker Compose with explicit volume mounts and health checks, satisfying Constitution Principle IV.

### Alternatives Considered
- PostgreSQL with JSONB: Robust, but document collections in MongoDB offer native schema flexibility for varying OCR and NER metadata fields.
- SQLite: Lacks native async driver (must use aiosqlite wrapper) and doesn't support concurrent multi-service operations or containerized deployment patterns standard in this stack.

---

## 5. Configuration & Data Modeling

### Decision
Use `pydantic` (v2) for domain entities, request/response models, and validation, paired with `pydantic-settings` (`BaseSettings`) for reading configuration from `.env` files and environment variables.

### Rationale
- Pydantic provides runtime validation, clean serialization/deserialization with MongoDB BSON/JSON, and strict typing.
- `pydantic-settings` provides structured environment parsing with defaults for `MONGODB_URI`, `DATABASE_NAME`, `XBERG_API_URL`, `GLINER_MODEL_NAME`, and `NER_LABELS`.

### Alternatives Considered
- `dataclasses`: Does not offer runtime input validation, environment variable parsing, or JSON schema generation.

---

## 6. Observability & Structured Logging

### Decision
Use `loguru.logger` across all modules. Workflow executions are traced using `logger.bind(job_id=..., document_id=..., page_number=...)` at key lifecycle milestones (job start, file validation, Xberg API dispatch, page OCR completion, GLiNER inference, DB persistence, and job summary/error exit).

### Rationale
- Directly implements Constitution Principle VII.
- Contextual attributes enable filtering logs by `job_id` or `document_id` across asynchronous executions.

---

## 7. Lifecycle & Error Handling Strategy

### Decision
- **Job ID & Document ID**: Generated using UUID4 string identifiers (`str(uuid.uuid4())`) on each trigger.
- **Graceful Page Degradation**: If entity recognition fails for a specific page, that page is recorded with `ner_status="failed"` and the error details. Processing continues for subsequent pages, and the overall job finishes with status `"partially_completed"`.
- **Signal Handling**: Catch `SIGINT` (Ctrl+C) in the CLI orchestration layer, mark the active job in MongoDB as `failed` with reason `"Execution interrupted by user"`, and exit with code 130.
