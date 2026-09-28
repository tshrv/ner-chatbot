# Research & Technical Decisions: Codebase Formatting and Import Sorting

**Feature**: Codebase Formatting and Import Sorting (`002-format-codebase`)  
**Date**: 2026-09-28  
**Status**: Completed  

---

## 1. Tool Selection & Packaging

### Decision
Use `ruff` as the unified linter and formatter, added as a pinned development dependency via `uv add --dev ruff`.

### Rationale
- Mandated directly by Constitution Principle VIII ("Mandatory Formatting & Import Sorting with Ruff").
- Extreme performance (written in Rust, formats large codebases in milliseconds).
- Drop-in replacement for Black, Flake8, and isort, combining formatting, import ordering, and safe unused import elimination in a single tool.

### Alternatives Considered
- `black` + `isort` + `autoflake`: Slower, requires coordinating three separate tools with potential formatting conflicts.
- `flake8`: Diagnostic only, does not auto-format code.

---

## 2. Configuration & Exclusions Strategy

### Decision
Declare all formatting and isort rules centrally in `pyproject.toml` under `[tool.ruff]`:
- `line-length = 100`: Balance between modern wide screens and readability.
- `target-version = "py312"`: Matches project runtime target (Python 3.12+).
- `extend-exclude = [".notes", "src/playground"]`: Strictly respects Constitution Section "Structural Constraints & Excluded Directories".
- `[tool.ruff.lint.isort] known-first-party = ["src"]`: Guarantees local project modules are cleanly partitioned from standard library and third-party packages.

### Rationale
- Centralized configuration prevents configuration fragmentation and ensures deterministic results across local dev, CI, and pre-commit workflows.
- Explicit folder exclusions prevent automated modifications to prohibited directories.

---

## 3. Safe Import Removal & Preservation Policy

### Decision
- Auto-fix import sorting (`--select I`) and unreferenced imports (`--select F401`).
- Strictly preserve `__init__.py` module re-exports (which declare package entrypoints) and files containing explicit `__all__` lists.
- For `__init__.py` files, configure Ruff to treat unused imports as public exports or ignore `F401` in `__init__.py` files via `per-file-ignores = {"__init__.py" = ["F401"]}`.

### Rationale
- Prevents accidental breakage of public package imports while cleaning up actual clutter in internal modules.
- Guarantees zero behavioral regressions across the codebase.

---

## 4. Verification & Validation Workflow

### Decision
Establish two standard CLI workflows:
1. **Formatting Execution**:
   ```bash
   uv run ruff check --select I,F401 --fix src/
   uv run ruff format src/
   ```
2. **Non-Destructive Compliance Check**:
   ```bash
   uv run ruff check src/
   uv run ruff format --check src/
   ```
3. **Behavioral Regression Check**:
   Run the Ingestion Pipeline CLI against `data/assessment-of-the-threat-from-russia.pdf` to verify that execution output, exit codes, and database operations remain 100% identical.

### Rationale
- Meets Success Criteria SC-001 through SC-004.
- Provides immediate developer feedback and enables CI gating.
