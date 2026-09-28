# Implementation Plan: Codebase Formatting and Import Sorting

**Branch**: `002-format-codebase` | **Date**: 2026-09-28 | **Spec**: [specs/002-format-codebase/spec.md](spec.md)

**Input**: User instruction: "use ruff to format all code and sort imports, make changes to code if needed but ensure no behavioural changes are done" and feature specification from `specs/002-format-codebase/spec.md`.

## Summary

Configure and apply `ruff` as the repository's deterministic linter, import sorter, and code formatter. Add `ruff` as a pinned dev dependency, establish configuration in `pyproject.toml` (target Python 3.12, 100 character line length, strict exclusions for `.notes` and `src/playground`), sort and organize imports across all production files under `src/`, format code layout in-place, and verify zero behavioral regressions by running the Ingestion Pipeline CLI against the benchmark document.

## Technical Context

**Language/Version**: Python 3.12+ (Ubuntu Linux on WSL)  
**Primary Dependencies**: `ruff>=0.7.0` (as development dependency), `uv` package manager  
**Storage**: N/A  
**Testing**: Human-authored tests only; verification via `ruff check` and behavioral execution of `src.main`  
**Target Platform**: Ubuntu Linux under WSL on Windows 11  
**Project Type**: Code quality tooling & formatting  
**Performance Goals**: Verification check completes in <5s across repository  
**Constraints**: Zero runtime behavioral regressions; strictly exclude `.notes` and `src/playground`; preserve `__all__` and `__init__.py` re-exports  
**Scale/Scope**: All production Python source files under `src/` (14 files)  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I: Code Quality & Modularity**: Enhances readability, maintainability, and clean code formatting across all modules.
- [x] **Principle II: CLI Interface via Typer**: Preserves Typer CLI interfaces and argument parsing without modifications.
- [x] **Principle III: Asynchronous by Default**: Does not modify asynchronous event loop or coroutine behavior.
- [x] **Principle IV: Containerized Dependencies First**: Development tooling runs in host environment; does not alter Docker services.
- [x] **Principle V: Strict Dependency Pinning & Packaging via uv**: `ruff` is installed and locked via `uv add --dev ruff`.
- [x] **Principle VI: Human-Authored Testing Policy**: AI does not generate or modify test files.
- [x] **Principle VII: Comprehensive Observability & Structured Logging with Loguru**: Preserves all Loguru logging calls and structured attributes.
- [x] **Principle VIII: Mandatory Formatting & Import Sorting with Ruff**: Directly implements this core constitutional mandate.
- [x] **Structural Constraints**: `.notes` and `src/playground` are explicitly excluded in `pyproject.toml` configuration.

## Project Structure

### Documentation (this feature)

```text
specs/002-format-codebase/
├── plan.md              # Implementation plan
├── research.md          # Technical decisions and trade-offs
├── data-model.md        # File scope and configuration schema
├── quickstart.md        # Verification workflows
├── contracts/           # Tooling commands contract
│   └── format-contract.md
└── checklists/          # Specification quality checklist
    └── requirements.md
```

### Source Code (repository root)

```text
pyproject.toml           # Configured with [tool.ruff] settings and exclusions
src/
├── __init__.py          # Formatted & imports sorted
├── main.py              # Formatted & imports sorted
├── config.py            # Formatted & imports sorted
├── database.py          # Formatted & imports sorted
├── models/
│   ├── __init__.py      # Formatted & imports sorted
│   ├── job.py           # Formatted & imports sorted
│   ├── document.py      # Formatted & imports sorted
│   └── entity.py        # Formatted & imports sorted
├── services/
│   ├── __init__.py      # Formatted & imports sorted
│   ├── extraction.py    # Formatted & imports sorted
│   ├── ner.py           # Formatted & imports sorted
│   └── ingestion.py     # Formatted & imports sorted
└── utils/
    ├── __init__.py      # Formatted & imports sorted
    └── logging.py       # Formatted & imports sorted
```

**Structure Decision**: Applies formatting in-place across `pyproject.toml` and existing `src/` modules without changing file locations or architecture.

## Complexity Tracking

*No constitutional violations; no complexity exemptions required.*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| None | N/A | N/A |
