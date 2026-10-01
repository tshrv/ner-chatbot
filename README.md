# ner-chatbot: Content Ingestion Pipeline & Conversational Entity AI Agent

An asynchronous document intelligence system combining an OCR-driven content extraction and named entity recognition pipeline with a conversational AI agent powered by Pydantic AI and Google Cloud Vertex AI.

---

## Overview & Key Capabilities

1. **Ingestion Pipeline (`ingest` CLI)**:
   - **Unconditional OCR Extraction**: Extracts page-level textual content from scanned or native PDF documents via a containerized [Xberg](https://github.com/xberg-io/xberg) API server (`ghcr.io/xberg-io/xberg:1.2.9`).
   - **Named Entity Recognition (NER)**: Identifies entities, categories, and surface mentions using [GLiNER](https://github.com/urchade/GLiNER) (`knowledgator/gliner-multitask-large-v0.5`) offloaded to worker threads via `asyncio.to_thread`.
   - **Persistent Lineage in MongoDB**: Asynchronously stores jobs, documents, page content, document-scoped unique entities, and character offset occurrence spans (`start_offset`, `end_offset`) via Motor.
   - **Execution Tracking & Fault Isolation**: Generates unique UUID4 job and document IDs per invocation. Degrades gracefully on page-level errors (`partially_completed`) and audits signal interrupts (`Ctrl+C` / SIGINT) as `failed`.

2. **Conversational Entity AI Agent (`chat` CLI)**:
   - **Pydantic AI Integration**: Built with [Pydantic AI](https://github.com/pydantic/pydantic-ai) utilizing Google Cloud Vertex AI (`gemini-3.8-flash`) authenticated via API key.
   - **Single-Turn Statelessness**: Processes each natural language query independently without retaining conversation history between turns.
   - **Strict Tool Grounding**: Answers queries exclusively via 8 asynchronous database inspection tools; never answers from internal pre-trained weights or invents facts.
   - **Domain Guardrails**: Automatically refuses out-of-scope requests (general knowledge, coding, chit-chat) and strictly bars access to pipeline execution/job data.
   - **Occurrence Breakdown & Top-10 Preview**: Summarizes occurrences by document and details the top 10 occurrences with page numbers and character offsets.
   - **Resilience**: Automatically retries up to 3 times on transient tool or model errors before halting with a clear message.

---

## Project Structure

```text
ner-chatbot/
├── docker-compose.yaml          # Pinned MongoDB 7.0 and Xberg 1.2.9 services
├── pyproject.toml               # Project dependencies and [tool.ruff] configuration
├── .env.example                 # Environment variables template
├── data/
│   └── assessment-of-the-threat-from-russia.pdf  # Benchmark test PDF
├── src/
│   ├── __init__.py              # Root source package
│   ├── main.py                  # Typer CLI application entrypoint (ingest & chat)
│   ├── config.py                # Pydantic BaseSettings configuration
│   ├── database.py              # Async Motor MongoDB connection & index lifecycle
│   ├── models/                  # Domain models & lifecycle enums
│   │   ├── __init__.py
│   │   ├── job.py               # IngestionJob & JobStatus enum
│   │   ├── document.py          # Document, DocumentPage & Extraction/NerStatus enums
│   │   └── entity.py            # RecognizedEntity & EntityOccurrence models
│   ├── services/                # Integration services & coordinator
│   │   ├── __init__.py
│   │   ├── extraction.py        # Xberg REST API HTTP client
│   │   ├── ner.py               # GLiNER entity recognition service
│   │   ├── ingestion.py         # End-to-end ingestion pipeline coordinator
│   │   └── agent_tools.py       # 8 read-only async database query tools for the agent
│   ├── agent/                   # AI Agent package
│   │   ├── __init__.py
│   │   ├── schemas.py           # Pydantic schemas for agent tool outputs
│   │   └── core.py              # Pydantic AI Agent, system prompt & Vertex AI provider
│   └── utils/
│       ├── __init__.py
│       └── logging.py           # Loguru structured logging configuration
└── specs/                       # Feature specifications, plans, checklists, and tasks
    ├── 001-ingestion-pipeline/
    ├── 002-format-codebase/
    └── 003-entity-query-agent/
```

---

## Prerequisites

- **Operating System**: Ubuntu Linux or WSL on Windows 11
- **Python**: 3.12+
- **Package Manager**: [`uv`](https://github.com/astral-sh/uv)
- **Container Runtime**: Docker & Docker Compose

---

## Getting Started

### 1. Start Containerized Services

Start MongoDB 7.0 and Xberg OCR server:

```bash
docker compose up -d
```

Verify service health:

```bash
docker compose ps
curl -s http://localhost:8000/health
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` to configure your settings:

```ini
# MongoDB Connection
MONGODB_URI=mongodb://root:example@localhost:27017
DATABASE_NAME=ner_chatbot

# Xberg OCR Extraction Service
XBERG_API_URL=http://localhost:8000
XBERG_OCR_LANGUAGE=eng

# GLiNER Named Entity Recognition
GLINER_MODEL_NAME=knowledgator/gliner-multitask-large-v0.5
NER_LABELS=Person,Organization,Location,Date,Event,Country
NER_THRESHOLD=0.5

# GCP Vertex AI / AI Agent
GCP_VERTEX_AI_API_KEY=your_gcp_vertex_ai_api_key_here
LLM_MODEL_NAME=gemini-3.8-flash
AGENT_MAX_RETRIES=3
```

### 3. Install Dependencies

Install all pinned project and development dependencies via `uv`:

```bash
uv sync
```

---

## CLI Usage

The application provides two primary Typer subcommands: `ingest` and `chat`.

```bash
uv run python -m src.main --help
```

### 1. Ingestion Pipeline (`ingest`)

Extract text from a PDF file using OCR, run entity recognition, and store the results in MongoDB:

```bash
uv run python -m src.main ingest <FILE_PATH> [OPTIONS]
```

#### Examples

```bash
# Standard ingestion on benchmark document
uv run python -m src.main ingest data/assessment-of-the-threat-from-russia.pdf

# Custom labels and confidence threshold
uv run python -m src.main ingest data/assessment-of-the-threat-from-russia.pdf --labels "Person,Organization,Location,Date" --threshold 0.6

# Verbose debug logging to stderr
uv run python -m src.main ingest data/assessment-of-the-threat-from-russia.pdf --verbose
```

#### Options

| Option | Flag | Type | Default | Description |
|---|---|---|---|---|
| `file_path` | | `Path` | *(Required)* | Local filesystem path to the target PDF document |
| `--labels` | `-l` | `str` | From `.env` | Comma-separated list of target entity labels for GLiNER |
| `--threshold` | `-t` | `float` | `0.5` | Confidence threshold for entity recognition (0.0 to 1.0) |
| `--verbose` | `-v` | `bool` | `False` | Enable detailed debug logs to `stderr` |

#### Output Summary

```text
============================================================
              INGESTION PIPELINE SUMMARY
============================================================
Job ID:             4f7b1b0e-8f77-4935-b194-81130b6c515c
Document ID:        dc311741-f1ab-4b02-96ae-b88af7f451bc
Document Name:      assessment-of-the-threat-from-russia.pdf
File Path:          data/assessment-of-the-threat-from-russia.pdf
Status:             COMPLETED
Total Pages:        3
Pages Extracted:    3
Pages Analyzed:     3
Entities Discovered: 57 (unique: 26)
Elapsed Time:       16.7s
============================================================
```

---

### 2. Conversational AI Agent (`chat`)

Start an interactive single-turn chat session to query stored entities, types, counts, and occurrence locations:

```bash
uv run python -m src.main chat [OPTIONS]
```

#### Options

| Option | Flag | Type | Default | Description |
|---|---|---|---|---|
| `--model` | `-m` | `str` | `gemini-3.8-flash` | Gemini model name |
| `--verbose` | `-v` | `bool` | `False` | Enable detailed debug logs to `stderr` |

#### Interactive Session Example

```text
============================================================
              ENTITY INTELLIGENCE CHAT AGENT
============================================================
Ask questions about entities, types, and occurrences.
Type 'exit' or 'quit' to end the session.
============================================================

You: List all entity types and count them.
Agent: There are 5 unique entity types (with 156 total type assignments recorded in the database):
1. Date
2. Event
3. Location
4. Organization
5. Person

You: Where does the entity "Europe" appear?
Agent: The entity "Europe" (Location) appears a total of 18 times across 1 document:
- Document: assessment-of-the-threat-from-russia.pdf (18 occurrences)

Top occurrences:
1. Document: assessment-of-the-threat-from-russia.pdf | Page: 1 | Offsets: 347–353 | Surface Text: "Europe"
2. Document: assessment-of-the-threat-from-russia.pdf | Page: 1 | Offsets: 2275–2281 | Surface Text: "Europe"
...
There are 8 additional occurrences remaining across the documents.

You: What is the weather in Paris?
Agent: I am an entity intelligence assistant and can only answer questions regarding extracted entities, entity types, and their occurrences in the database.

You: exit
Goodbye!
```

---

## Database Architecture

MongoDB stores data under the `ner_chatbot` database across 5 collections:

| Collection | Description | Key Indexes |
|---|---|---|
| **`jobs`** | Pipeline execution lineage, timestamps, and status (`pending`, `in_progress`, `completed`, `partially_completed`, `failed`) | `status`, `started_at` |
| **`documents`** | Ingested document metadata, file paths, and total page counts | `job_id` |
| **`pages`** | Per-page extracted text, 1-based page numbers, and extraction/NER statuses | `{document_id: 1, page_number: 1}` (unique), `job_id` |
| **`entities`** | Unique document-scoped entities classified by label (e.g., Person, Organization) | `{document_id: 1, name: 1, entity_type: 1}` (unique) |
| **`occurrences`** | Page-level mentions with 0-based character spans (`start_offset`, `end_offset`), surface text, and confidence | `entity_id`, `{document_id: 1, page_number: 1}` |

---

## Code Quality & Standards

All code is strictly formatted and imports organized using `ruff` in accordance with Constitution Principle VIII:

- **Format code and sort imports**:
  ```bash
  uv run ruff check --select I,F401 --fix src/ && uv run ruff format src/
  ```

- **Verify formatting compliance (check-only)**:
  ```bash
  uv run ruff check src/ && uv run ruff format --check src/
  ```

---

## Testing

There are end-to-end tests for ingestion and ingestion + agent conversation.  
Ensure the containerized services are running and the `.env` is in place, run following command to execute tests.
```bash
uv run pytest
```

