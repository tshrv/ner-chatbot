# Quickstart & Verification Guide: Codebase Formatting and Import Sorting

**Feature**: Codebase Formatting and Import Sorting (`002-format-codebase`)  
**Date**: 2026-09-28  
**Status**: Ready  

---

## 1. Prerequisites

- Development environment: Ubuntu Linux / WSL with Python 3.12+
- `uv` package manager installed
- `ruff` installed via development dependencies (`uv add --dev ruff`)

---

## 2. Execution Workflows

### Workflow 1: Format Codebase & Sort Imports

Apply formatting and import sorting across all production code:

```bash
uv run ruff check --select I,F401 --fix src/
uv run ruff format src/
```

### Workflow 2: Verify Formatting Compliance

Check repository compliance without modifying files:

```bash
uv run ruff check src/
uv run ruff format --check src/
```

Expected result:
```text
All checks passed!
14 files already formatted.
```

### Workflow 3: Behavioral Non-Regression Verification

Confirm that existing CLI pipelines execute with identical output after formatting:

```bash
uv run python -m src.main ingest data/assessment-of-the-threat-from-russia.pdf
```

Expected output:
- Returns exit code `0`.
- Outputs completion summary table with 3 pages and 57 entities discovered.
- No syntax or import errors.
