# Tasks: Ingestion Pipeline

**Input**: Design documents from `/specs/001-ingestion-pipeline/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/cli-contract.md`, `quickstart.md`)  
**Prerequisites**: `plan.md`, `spec.md`, `data-model.md`, `contracts/cli-contract.md`  
**Tests**: Excluded per Constitution Principle VI (Human-Authored Testing Policy - AI test authoring is prohibited)  
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.  

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Every task includes exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency management, and containerized service setup.

- [X] T001 Configure project dependencies in `pyproject.toml` using `uv add` for `typer>=0.12.0`, `pydantic>=2.7.0`, `pydantic-settings>=2.2.0`, `motor>=3.5.0`, `gliner`, `httpx>=0.28.1`, `loguru>=0.7.3`, and `aiofiles>=25.1.0`
- [X] T002 [P] Update `docker-compose.yaml` to define containerized `mongodb` service (`image: mongo:7.0`, port `27017:27017`, environment `MONGO_INITDB_ROOT_USERNAME=root`, `MONGO_INITDB_ROOT_PASSWORD=example`, healthcheck, volume `mongo-data`) alongside `xberg-api` (`image: ghcr.io/xberg-io/xberg:1.2.9`)
- [X] T003 [P] Initialize directory scaffolding for `src/models/`, `src/services/`, and `src/utils/` with `__init__.py` files per `plan.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and base connectivity that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Create application configuration in `src/config.py` using `pydantic_settings.BaseSettings` loading `MONGODB_URI` (default: `"mongodb://root:example@localhost:27017"`), `DATABASE_NAME` (default: `"ner_chatbot"`), `XBERG_API_URL` (default: `"http://localhost:8000"`), `XBERG_OCR_LANGUAGE` (default: `"eng"`), `GLINER_MODEL_NAME` (default: `"knowledgator/gliner-multitask-large-v0.5"`), `NER_LABELS` (default: `["Person", "Organization", "Location", "Date", "Event"]`), and `NER_THRESHOLD` (default: `0.5`)
- [X] T005 [P] Configure structured logging in `src/utils/logging.py` using `loguru.logger` formatting diagnostic messages to `sys.stderr` with support for bound contextual keys (`job_id`, `document_id`, `page_number`)
- [X] T006 Implement async MongoDB client and database connection lifecycle in `src/database.py` using `motor.motor_asyncio.AsyncIOMotorClient`, exposing collections (`jobs`, `documents`, `pages`, `entities`, `occurrences`) and index initialization functions per `specs/001-ingestion-pipeline/data-model.md`
- [X] T007 [P] Create sample environment configuration template in `.env.example` defining default connection strings and model settings

**Checkpoint**: Foundation ready - user story implementation can now begin.

---

## Phase 3: User Story 1 - Standard End-to-End PDF Ingestion and Entity Recognition via CLI (Priority: P1) 🎯 MVP

**Goal**: An operator triggers ingestion on a PDF file via Typer CLI. The system assigns unique Job ID and Document ID, extracts page content via Xberg API, stores metadata and pages in MongoDB, runs GLiNER entity recognition on each page, stores document-scoped entities and occurrences, and prints an execution summary to stdout.

**Independent Test**: Execute `uv run python -m src.main ingest data/assessment-of-the-threat-from-russia.pdf` and verify that MongoDB contains linked job, document, pages, entities, and occurrences, and stdout displays the completion summary table.

### Implementation for User Story 1

- [X] T008 [P] [US1] Create IngestionJob models and enums in `src/models/job.py` with `JobStatus` enum verbatim values: `"pending"`, `"in_progress"`, `"completed"`, `"partially_completed"`, `"failed"`, UUID4 `job_id`, `file_path`, optional `document_id`, integer counters (`total_pages`, `pages_extracted`, `pages_ner_completed`, `total_entities_found`, `total_occurrences_found`), optional `error_message`, and `started_at`/`completed_at` datetime fields
- [X] T009 [P] [US1] Create Document and DocumentPage models in `src/models/document.py` with `DocumentStatus` (`"pending"`, `"in_progress"`, `"completed"`, `"failed"`), `ExtractionStatus` (`"pending"`, `"completed"`, `"failed"`), `NerStatus` (`"pending"`, `"completed"`, `"failed"`), 1-based integer `page_number`, string `content`, integer `char_count`, and UUID string references `document_id` and `job_id`
- [X] T010 [P] [US1] Create RecognizedEntity and EntityOccurrence models in `src/models/entity.py` with document-scoped entity deduplication fields (`document_id`, canonical `name`, `entity_type`, `total_occurrences`) and occurrence span fields (`entity_id`, `document_id`, 1-based `page_number`, 0-based `start_offset`, 0-based `end_offset`, `surface_text`, float `confidence` between 0.0 and 1.0)
- [X] T011 [US1] Implement Xberg OCR content extraction HTTP client in `src/services/extraction.py` using `httpx.AsyncClient` calling `POST /extract` with multipart `files={"files": file_bytes}` and JSON config `{"ocr": {"backend": "tesseract", "language": ["eng"]}, "force_ocr": true}`, parsing page-by-page results into `DocumentPage` models
- [X] T012 [US1] Implement GLiNER named entity recognition service in `src/services/ner.py` loading `knowledgator/gliner-multitask-large-v0.5`, delegating `predict_entities` to worker threads via `asyncio.to_thread`, extracting recognized entities with labels and character offsets
- [X] T013 [US1] Implement pipeline coordinator in `src/services/ingestion.py` orchestrating end-to-end execution: registering `IngestionJob` and `Document`, dispatching extraction, saving pages to MongoDB, running NER per page, deduplicating entities per document, saving occurrences, and updating job status to `"completed"`
- [X] T014 [US1] Implement Typer CLI entrypoint and `ingest` command in `src/main.py` accepting `FILE_PATH: Path`, `--labels`, and `--threshold` (default: 0.5), executing the ingestion pipeline coordinator via `asyncio.run()`, outputting formatted summary to `sys.stdout` and error logs to `sys.stderr` per `contracts/cli-contract.md`
- [X] T015 [US1] Verify end-to-end standard ingestion against `data/assessment-of-the-threat-from-russia.pdf` using the CLI command in `src/main.py` and inspect database records in MongoDB

**Checkpoint**: At this point, User Story 1 (MVP) is fully functional and independently testable.

---

## Phase 4: User Story 2 - Uniform OCR-Driven Extraction Across All Document Types (Priority: P2)

**Goal**: Guarantee uniform OCR extraction across both scanned image-only and native digital PDF pages unconditionally, preserving sequential page numbering and handling blank or low-text pages gracefully.

**Independent Test**: Run ingestion against image-only and mixed-content PDF documents, verifying that OCR is invoked unconditionally for every page and blank pages record empty content without pipeline abortion.

### Implementation for User Story 2

- [X] T016 [US2] Enhance `src/services/extraction.py` to enforce unconditional OCR extraction across all document formats (scanned physical papers and digitally generated PDFs), passing `force_ocr=True` in Xberg JSON config and handling page-by-page text assembly and layout normalization
- [X] T017 [US2] Add empty page and blank image handling in `src/services/ingestion.py` so that pages with zero characters are recorded with `extraction_status="completed"`, empty string `content`, and NER is cleanly bypassed without error
- [X] T018 [US2] Verify OCR extraction consistency and page numbering on multi-page mixed digital/scanned documents using `src/main.py`

**Checkpoint**: User Stories 1 and 2 work independently and uniformly across all document types.

---

## Phase 5: User Story 3 - Execution Tracking and Resilient Failure Handling (Priority: P3)

**Goal**: Deliver resilient failure isolation, graceful page degradation for unparseable text, graceful SIGINT (Ctrl+C) termination with database audit status `Failed (Interrupted)`, and descriptive CLI error diagnostics.

**Independent Test**: Test pipeline with missing files, invalid non-PDF inputs, corrupt pages, and manual SIGINT signals; verify appropriate non-zero exit codes (1 or 130) and audited status in the MongoDB `jobs` collection.

### Implementation for User Story 3

- [X] T019 [US3] Implement page-level graceful NER degradation in `src/services/ingestion.py`: when entity recognition raises an exception on an individual page, record `ner_status="failed"` and the error description on that `DocumentPage`, continue processing remaining pages, and mark `IngestionJob` status as `"partially_completed"`
- [X] T020 [US3] Implement SIGINT / Ctrl+C signal handling in `src/main.py` and `src/services/ingestion.py` to catch interruption, cancel in-flight tasks, update active job status in MongoDB to `"failed"` with reason `"Execution interrupted by user"`, and exit cleanly with code 130
- [X] T021 [US3] Implement input validation and error audit handling in `src/main.py` and `src/services/ingestion.py` for non-existent paths, non-PDF formats, and corrupted files, ensuring a failed job record is saved to MongoDB and an actionable message is printed to stderr with exit code 1
- [X] T022 [US3] Verify failure isolation and graceful degradation scenarios using `src/main.py` with invalid files and simulated signal cancellation

**Checkpoint**: All three user stories are functional, resilient, and independently verifiable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, typing validation, and documentation updates across all user stories.

- [X] T023 [P] Review and enforce explicit type annotations across all files in `src/` to ensure zero typing errors under strict linting
- [X] T024 [P] Update `README.md` with complete usage instructions, Docker Compose startup commands, and Typer CLI arguments
- [X] T025 Execute complete end-to-end pipeline verification using `data/assessment-of-the-threat-from-russia.pdf` per `specs/001-ingestion-pipeline/quickstart.md`
- [X] T026 Validate all requirements against `specs/001-ingestion-pipeline/checklists/ingestion.md` and report readiness

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. Delivers working MVP.
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion. Enhances extraction uniformity.
- **User Story 3 (Phase 5)**: Depends on User Story 1 completion. Adds resilience and signal handling.
- **Polish (Phase 6)**: Depends on all user story phases being complete.

### User Story Dependencies

```text
[Phase 1: Setup] ──► [Phase 2: Foundational]
                             │
                             ▼
                 [Phase 3: User Story 1 (MVP)]
                             │
                 ┌───────────┴───────────┐
                 ▼                       ▼
    [Phase 4: User Story 2]  [Phase 5: User Story 3]
                 │                       │
                 └───────────┬───────────┘
                             ▼
                     [Phase 6: Polish]
```

### Parallel Opportunities

- **Setup**: `T002` (docker-compose) and `T003` (scaffolding) can run in parallel with `T001`.
- **Foundational**: `T005` (logging) and `T007` (.env.example) can run in parallel with `T004`/`T006`.
- **User Story 1**: Models `T008` (`job.py`), `T009` (`document.py`), and `T010` (`entity.py`) can be implemented in parallel.
- **Polish**: `T023` (type annotations) and `T024` (`README.md`) can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (`T001` - `T003`)
2. Complete Phase 2: Foundational (`T004` - `T007`)
3. Complete Phase 3: User Story 1 (`T008` - `T015`)
4. **STOP and VALIDATE**: Run `python -m src.main ingest data/assessment-of-the-threat-from-russia.pdf` to verify MVP functionality.

### Incremental Delivery

1. Foundation ready (`T001` - `T007`)
2. Ingestion pipeline working for clean PDFs (`T008` - `T015`, MVP)
3. Unconditional OCR & blank page handling added (`T016` - `T018`)
4. Error handling, degradation & Ctrl+C interruption added (`T019` - `T022`)
5. Hardening, linting, and documentation finalized (`T023` - `T026`)
