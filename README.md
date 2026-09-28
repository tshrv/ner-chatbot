# Ingestion Pipeline: Content Extraction & Named Entity Recognition

An asynchronous document ingestion pipeline and CLI tool that extracts page-level text from PDF documents using optical character recognition (OCR) via Xberg, executes named entity recognition (NER) using GLiNER, and persists structured jobs, document metadata, pages, recognized entities, and character offset occurrences into MongoDB.

---

## Architecture & Features

- **CLI Interface via Typer**: Single command-line entrypoint with typed arguments, options, and structured execution summary table.
- **Asynchronous Execution**: Fully asynchronous I/O utilizing `httpx.AsyncClient` for Xberg API and `motor` for MongoDB persistence, offloading CPU-heavy GLiNER inference to worker threads via `asyncio.to_thread`.
- **Unconditional OCR**: Integrates with containerized Xberg (`ghcr.io/xberg-io/xberg:1.2.9`) executing OCR extraction across all document pages.
- **Open-Vocabulary NER**: Uses GLiNER multitask (`knowledgator/gliner-multitask-large-v0.5`) with configurable entity labels and document-scoped deduplication.
- **Execution Tracking & Resilience**: Every trigger creates an isolated `IngestionJob` record with UUID. Handles corrupted pages via graceful degradation (`partially_completed`) and traps `SIGINT` (Ctrl+C) to record an audited failed state.
- **Containerized Infrastructure**: Pinned MongoDB 7.0 and Xberg OCR server managed through Docker Compose.

---

## Prerequisites

- **Python**: 3.12+ on Ubuntu Linux / WSL
- **Package Manager**: `uv`
- **Containers**: Docker & Docker Compose

---

## Getting Started

### 1. Start Containerized Services

Start MongoDB and the Xberg OCR extraction server:

```bash
docker compose up -d
```

Verify service health:

```bash
docker compose ps
curl -s http://localhost:8000/health
```

### 2. Environment Configuration

Copy `.env.example` to `.env` if not already present:

```bash
cp .env.example .env
```

Configuration variables:

```ini
# MongoDB Connection
MONGODB_URI=mongodb://root:example@localhost:27017
DATABASE_NAME=ner_chatbot

# Xberg OCR Extraction Service
XBERG_API_URL=http://localhost:8000
XBERG_OCR_LANGUAGE=eng

# GLiNER Entity Recognition
GLINER_MODEL_NAME=knowledgator/gliner-multitask-large-v0.5
NER_LABELS=Person,Organization,Location,Date,Event
NER_THRESHOLD=0.5
```

### 3. Install Dependencies

Install all dependencies using `uv`:

```bash
uv sync
```

---

## CLI Usage

### Basic Ingestion

Run the ingestion pipeline on a target PDF file:

```bash
uv run python -m src.main ingest data/assessment-of-the-threat-from-russia.pdf
```

### Custom Labels & Threshold

Specify custom entity recognition labels and confidence threshold:

```bash
uv run python -m src.main ingest data/assessment-of-the-threat-from-russia.pdf --labels "Person,Organization,Location,Date" --threshold 0.6
```

### Verbose Mode

Enable detailed debug logging to `stderr`:

```bash
uv run python -m src.main ingest data/assessment-of-the-threat-from-russia.pdf --verbose
```

---

## Code Quality & Formatting

All Python source code is automatically formatted and imports sorted using `ruff` in accordance with Constitution Principle VIII:

- **Format code and sort imports**:
  ```bash
  uv run ruff check --select I,F401 --fix src/ && uv run ruff format src/
  ```

- **Verify formatting compliance (check-only)**:
  ```bash
  uv run ruff check src/ && uv run ruff format --check src/
  ```

---

## Database Collections

MongoDB stores data under the `ner_chatbot` database across 5 collections:

1. **`jobs`**: Execution lineage, timestamps, page counters, and lifecycle status (`pending`, `in_progress`, `completed`, `partially_completed`, `failed`).
2. **`documents`**: Target document metadata, file paths, size, and total page counts.
3. **`pages`**: Per-page extracted textual content, 1-based page numbers, and extraction/NER statuses.
4. **`entities`**: Unique document-scoped entities classified by label (e.g. Person, Organization).
5. **`occurrences`**: Exact page mentions with 0-based character spans (`start_offset`, `end_offset`), exact surface text, and confidence scores.
