# Implementation Plan: Ingestion Pipeline

**Branch**: `001-ingestion-pipeline` | **Date**: 2026-09-28 | **Spec**: [specs/001-ingestion-pipeline/spec.md](spec.md)

**Input**: Feature specification from `specs/001-ingestion-pipeline/spec.md`, user tech-stack preferences (Typer, MongoDB via Docker Compose, Pydantic, Xberg OCR v1.2.9, GLiNER `knowledgator/gliner-multitask-large-v0.5`), and user instruction: "Use document data/assessment-of-the-threat-from-russia.pdf to test the pipeline".

## Summary

Build an end-to-end document ingestion pipeline accessible via Typer CLI. Each run creates a fresh execution with a unique Job ID. The pipeline ingests a local PDF, registers document metadata, performs unconditional OCR-enabled page extraction via the containerized Xberg HTTP API server, and stores page content and metadata in MongoDB asynchronously via Motor. Upon extraction, named entity recognition is executed on each page using GLiNER in worker threads, deduplicating recognized entities at the document level and storing character-level occurrence spans in MongoDB. The CLI outputs a structured summary to stdout with contextual structured logging via Loguru to stderr.

## Technical Context

**Language/Version**: Python 3.12+ (Ubuntu Linux on WSL)  
**Primary Dependencies**: `typer>=0.12.0`, `pydantic>=2.7.0`, `pydantic-settings>=2.2.0`, `httpx>=0.28.1`, `motor>=3.5.0`, `gliner`, `loguru>=0.7.3`, `aiofiles>=25.1.0`  
**Storage**: MongoDB 7.0+ via Docker Compose (`docker-compose.yaml`), accessed asynchronously via `motor`  
**Testing**: Human-authored tests only (AI test generation strictly prohibited per Constitution Principle VI)  
**Target Platform**: Ubuntu Linux under WSL on Windows 11  
**Project Type**: CLI tool & pipeline  
**Performance Goals**: Process standard 10-page document within 60 seconds; CLI start feedback within 5 seconds  
**Constraints**: Unconditional OCR extraction on every page; CPU-heavy GLiNER inference offloaded to worker threads via `asyncio.to_thread` without blocking async loop; graceful degradation on page-level errors  
**Scale/Scope**: Single PDF processing per CLI invocation, handling documents up to 500MB and arbitrary page counts  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I: Code Quality & Modularity**: Modular separation of concerns (`models`, `services`, `config`, `cli`), explicit Python type hints throughout, dependency injection in service constructors.
- [x] **Principle II: CLI Interface via Typer**: CLI entrypoints use `typer` with typed arguments/options, descriptive help text, stdout for primary summaries, stderr for diagnostics.
- [x] **Principle III: Asynchronous by Default**: All I/O operations (HTTP calls to Xberg via `httpx.AsyncClient`, database queries via `motor`) use `async`/`await`. CPU-heavy GLiNER model calls are isolated via `asyncio.to_thread`.
- [x] **Principle IV: Containerized Dependencies First**: MongoDB and Xberg OCR server run in Docker Compose with pinned tags, health checks, and isolated networks/volumes.
- [x] **Principle V: Strict Dependency Pinning & Packaging via uv**: Dependencies managed strictly with `uv` targeting Ubuntu/WSL.
- [x] **Principle VI: Human-Authored Testing Policy**: No test files generated or modified by AI. Architecture provides decoupled interfaces for human test authoring.
- [x] **Principle VII: Comprehensive Observability & Structured Logging with Loguru**: All logging uses `loguru.logger` with structured contextual bindings (`job_id`, `document_id`, `page_number`).
- [x] **Structural Constraints**: `.notes` and `src/playground` remain completely untouched and unreferenced.

## Project Structure

### Documentation (this feature)

```text
specs/001-ingestion-pipeline/
├── plan.md              # This implementation plan
├── research.md          # Technical decisions and trade-off analysis
├── data-model.md        # Domain entities, schemas, and MongoDB indexes
├── quickstart.md        # Step-by-step verification guide
├── contracts/           # CLI interaction contracts
│   └── cli-contract.md
└── checklists/          # Requirements and review checklists
    └── requirements.md
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── main.py                  # Typer CLI application entrypoint
├── config.py                # Pydantic BaseSettings (.env loading, defaults)
├── database.py              # Async MongoDB connection & client lifecycle (Motor)
├── models/
│   ├── __init__.py
│   ├── job.py               # IngestionJob model & status enums
│   ├── document.py          # Document & DocumentPage models
│   └── entity.py            # RecognizedEntity & EntityOccurrence models
├── services/
│   ├── __init__.py
│   ├── extraction.py        # Xberg API HTTP client (OCR extraction)
│   ├── ner.py               # GLiNER entity recognition service
│   └── ingestion.py         # End-to-end pipeline coordinator
└── utils/
    ├── __init__.py
    └── logging.py           # Loguru structured logger configuration
```

**Structure Decision**: Single project layout with clear separation between transport/CLI (`main.py`), domain models (`src/models/`), business logic and external integrations (`src/services/`), configuration (`src/config.py`), and database access (`src/database.py`).

## Complexity Tracking

*No constitutional violations; no complexity exemptions required.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| None | N/A | N/A |
