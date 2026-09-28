# Quickstart & Verification Guide: Ingestion Pipeline

**Feature**: Ingestion Pipeline (`001-ingestion-pipeline`)  
**Date**: 2026-09-28  
**Status**: Ready  

---

## 1. Prerequisites

- **Host Environment**: Ubuntu Linux / WSL on Windows 11 with Python 3.12+.
- **Package Manager**: `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
- **Container Runtime**: Docker & Docker Compose installed and running.

---

## 2. Environment Configuration

Create or inspect the `.env` file in the project root:

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

---

## 3. Start Containerized Services

Start the containerized external dependencies (MongoDB and Xberg OCR server):

```bash
docker compose up -d
```

Verify service health:

```bash
docker compose ps
curl -s http://localhost:8000/health
```

Expected output for Xberg:
```json
{"status":"healthy","version":"1.2.9"}
```

---

## 4. Install Dependencies

Install all pinned project dependencies via `uv`:

```bash
uv sync
```

---

## 5. Run Ingestion Pipeline CLI

Execute the pipeline on a local PDF file:

```bash
uv run python -m src.main ingest data/assessment-of-the-threat-from-russia.pdf
```

With custom labels or options:

```bash
uv run python -m src.main ingest data/assessment-of-the-threat-from-russia.pdf --labels Person,Organization,Date --threshold 0.6
```

---

## 6. End-to-End Verification Scenarios

### Scenario 1: Standard Ingestion
1. Execute the CLI command on a valid PDF.
2. Confirm console displays:
   - Unique Job ID (UUID)
   - Unique Document ID (UUID)
   - Total pages extracted and analyzed
   - Total recognized entities and summary table
3. Verify MongoDB documents using `mongosh`:
   ```bash
   mongosh "mongodb://root:example@localhost:27017/ner_chatbot?authSource=admin" --eval '
     print("Jobs:", db.jobs.countDocuments());
     print("Documents:", db.documents.countDocuments());
     print("Pages:", db.pages.countDocuments());
     print("Entities:", db.entities.countDocuments());
     print("Occurrences:", db.occurrences.countDocuments());
   '
   ```

### Scenario 2: Error Handling on Missing File
1. Execute command with a non-existent file path:
   ```bash
   uv run python -m src.main ingest /path/to/missing.pdf
   ```
2. Verify:
   - CLI exits with non-zero code (`1`).
   - Diagnostic error message displayed on `stderr`.

### Scenario 3: Graceful Interruption
1. Start an ingestion run on a multi-page PDF.
2. Send `SIGINT` (`Ctrl+C`) while processing is active.
3. Verify:
   - CLI terminates cleanly with exit code `130`.
   - The corresponding Job in MongoDB has `status: "failed"` and `error_message: "Execution interrupted by user"`.
