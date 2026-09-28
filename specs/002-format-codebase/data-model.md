# Data & Configuration Model: Codebase Formatting and Import Sorting

**Feature**: Codebase Formatting and Import Sorting (`002-format-codebase`)  
**Date**: 2026-09-28  
**Status**: Completed  

---

## 1. Configuration Model (`pyproject.toml`)

The formatting and import sorting rules are configured under `[tool.ruff]` within `pyproject.toml`.

### Schema Definition

```toml
[tool.ruff]
# Target Python version compatibility
target-version = "py312"

# Maximum line length for code formatting
line-length = 100

# Explicit directory exclusions (mandated by constitution)
extend-exclude = [
    ".notes",
    "src/playground",
]

[tool.ruff.lint]
# Selected rule sets:
# E / W: Pycodestyle errors and warnings
# F: Pyflakes (syntax & undefined names / unused imports)
# I: isort (import organization and sorting)
select = ["E", "F", "I"]
ignore = []

[tool.ruff.lint.per-file-ignores]
# Preserve re-exports in __init__.py files
"__init__.py" = ["F401"]

[tool.ruff.lint.isort]
# Classify first-party package root
known-first-party = ["src"]
# Combine 'as' imports and standard section splitting
combine-as-imports = true
```

---

## 2. Source File Inventory & Target Scope

All production Python source files under `src/` are within active formatting scope:

| Module Path | Purpose | Formatting Focus |
|---|---|---|
| `src/__init__.py` | Package root | Preserve package-level docstring |
| `src/main.py` | Typer CLI entrypoint | Group standard library, third-party (`typer`), and first-party (`src.*`) imports |
| `src/config.py` | Pydantic BaseSettings | Clean import order, format field validators and ConfigDict |
| `src/database.py` | Motor async MongoDB connection | Standardize async function signatures and IndexModel definitions |
| `src/models/__init__.py` | Models package root | Preserve exports |
| `src/models/job.py` | IngestionJob & JobStatus | Model formatting |
| `src/models/document.py` | Document & DocumentPage | Model formatting |
| `src/models/entity.py` | RecognizedEntity & EntityOccurrence | Model formatting |
| `src/services/__init__.py` | Services package root | Preserve exports |
| `src/services/extraction.py` | Xberg HTTP client | Clean import order, format exception and async methods |
| `src/services/ner.py` | GLiNER entity service | Clean import order, format worker thread delegation |
| `src/services/ingestion.py` | Pipeline coordinator | Organize imports, format coordinator lifecycle logic |
| `src/utils/__init__.py` | Utils package root | Preserve exports |
| `src/utils/logging.py` | Loguru logging helper | Organize sys, typing, loguru imports |

---

## 3. Excluded File Inventory

Per project constitution structural constraints:
- `.notes/`: All files ignored.
- `src/playground/`: All files (`src/playground/extraction.py`, `src/playground/ner.py`) strictly excluded from automated formatting and linting.
