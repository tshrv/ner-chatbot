# CLI Contract: Ingestion Pipeline

**Feature**: Ingestion Pipeline (`001-ingestion-pipeline`)  
**Date**: 2026-09-28  
**Status**: Completed  

---

## 1. Command Specification

The CLI entrypoint is built with `typer` and exposed via the project runner or python module:

```bash
uv run python -m src.main ingest <FILE_PATH> [OPTIONS]
```

Or via direct typer command when installed:

```bash
ner-chatbot ingest <FILE_PATH> [OPTIONS]
```

### 1.1 Arguments

| Argument | Type | Required | Description |
|---|---|---|---|
| `FILE_PATH` | `Path` (file) | **Yes** | Local filesystem path to the target PDF document. |

### 1.2 Options

| Option | Flag | Type | Default | Description |
|---|---|---|---|---|
| `--labels` | `-l` | `List[str]` | Configured from `.env` or `["Person", "Organization", "Location", "Date", "Event"]` | Space/comma-separated list of entity labels for GLiNER recognition. |
| `--threshold` | `-t` | `float` | `0.5` | Minimum confidence score threshold for entity predictions (0.0 to 1.0). |
| `--ocr-language` | | `str` | `"eng"` | Language code for OCR processing. |
| `--verbose` | `-v` | `bool` | `False` | Enable detailed diagnostic output to stderr. |

---

## 2. Standard Output (stdout) Contract

Primary pipeline outputs and execution summaries are printed to `stdout` in formatted plain text or JSON depending on flags.

### Successful Execution Output (`stdout`)

```text
============================================================
              INGESTION PIPELINE SUMMARY
============================================================
Job ID:             3fa85f64-5717-4562-b3fc-2c963f66afa6
Document ID:        8d9b231c-0e78-43d1-9f22-d784a9c68021
Document Name:      sample.pdf
File Path:          /absolute/path/to/sample.pdf
Status:             COMPLETED
Total Pages:        5
Pages Extracted:    5
Pages Analyzed:     5
Entities Discovered: 24 (unique: 9)
Elapsed Time:       14.2s
============================================================
```

### Partially Completed Output (`stdout`)

```text
============================================================
              INGESTION PIPELINE SUMMARY
============================================================
Job ID:             3fa85f64-5717-4562-b3fc-2c963f66afa6
Document ID:        8d9b231c-0e78-43d1-9f22-d784a9c68021
Document Name:      sample.pdf
Status:             PARTIALLY_COMPLETED
Total Pages:        5
Pages Extracted:    5
Pages Analyzed:     4 (Page 3 failed NER)
Entities Discovered: 18 (unique: 7)
Elapsed Time:       16.1s
Warning: Page 3 entity recognition failed: Model timeout.
============================================================
```

---

## 3. Diagnostic / Error Output (stderr) Contract

All operational diagnostic messages, progress logs, and error traces are routed to `stderr` via `loguru.logger`.

### Progress Log Format (`stderr`)

```text
2026-09-28 12:00:00.120 | INFO     | [job=3fa85f64] Initializing ingestion job for /path/to/sample.pdf
2026-09-28 12:00:01.450 | INFO     | [job=3fa85f64, doc=8d9b231c] Document registered. Dispatching OCR to Xberg...
2026-09-28 12:00:08.230 | INFO     | [job=3fa85f64, doc=8d9b231c] Xberg OCR completed: 5 pages extracted.
2026-09-28 12:00:09.010 | INFO     | [job=3fa85f64, page=1] Running GLiNER entity recognition...
2026-09-28 12:00:10.500 | INFO     | [job=3fa85f64, page=1] Discovered 6 entities. Persisted to database.
...
2026-09-28 12:00:14.300 | INFO     | [job=3fa85f64] Pipeline completed successfully.
```

### Fatal Error Output (`stderr`)

```text
2026-09-28 12:00:00.050 | ERROR    | File not found: /path/to/nonexistent.pdf
Error: Target PDF file does not exist or is not accessible.
```

---

## 4. Exit Codes

| Exit Code | Meaning |
|---|---|
| `0` | Success (`completed` or `partially_completed` with graceful warning). |
| `1` | General validation error (invalid CLI arguments, unsupported file format, missing file). |
| `2` | External dependency unavailable (MongoDB unreachable, Xberg API down). |
| `130` | Interrupted by user signal (`SIGINT` / Ctrl+C), job marked `failed` in database. |
