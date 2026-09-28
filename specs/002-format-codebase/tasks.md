# Tasks: Codebase Formatting and Import Sorting

**Input**: Design documents from `/specs/002-format-codebase/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/format-contract.md`, `quickstart.md`)  
**Prerequisites**: `plan.md`, `spec.md`, `data-model.md`, `contracts/format-contract.md`  
**Tests**: Excluded per Constitution Principle VI (Human-Authored Testing Policy)  
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.  

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`)
- Every task includes exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependency installation and tool configuration in `pyproject.toml`.

- [X] T001 Add `ruff` as a pinned development dependency via `uv add --dev ruff` in `pyproject.toml`
- [X] T002 [P] Configure `[tool.ruff]` in `pyproject.toml` with `target-version = "py312"`, `line-length = 100`, `extend-exclude = [".notes", "src/playground"]`, `select = ["E", "F", "I"]`, `known-first-party = ["src"]`, and `per-file-ignores = {"__init__.py" = ["F401"]}` per `specs/002-format-codebase/data-model.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Verify linter and formatter executable availability and configuration validation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Verify `ruff` configuration by running `uv run ruff check --version` and inspecting `pyproject.toml` settings

**Checkpoint**: Tooling and configuration validated.

---

## Phase 3: User Story 1 - Standardized Code Formatting and Import Organization Across the Repository (Priority: P1) 🎯 MVP

**Goal**: Automatically format all Python code in `src/` to 100-character line width, organize imports into canonical groups (standard library, third-party, local), remove unreferenced imports safely, and ensure zero behavioral regressions.

**Independent Test**: Execute `uv run ruff check --select I,F401 --fix src/` and `uv run ruff format src/`, then run `uv run python -m src.main ingest data/assessment-of-the-threat-from-russia.pdf` to confirm exit code 0 and identical output summary.

### Implementation for User Story 1

- [X] T004 [US1] Sort imports and safely remove unreferenced imports across all production files in `src/` by executing `uv run ruff check --select I,F401 --fix src/`
- [X] T005 [US1] Format all Python code layout and indentation across `src/` to 100-character line width by executing `uv run ruff format src/`
- [X] T006 [US1] Inspect all package root files (`src/__init__.py`, `src/models/__init__.py`, `src/services/__init__.py`, `src/utils/__init__.py`, `src/utils/logging.py`) to confirm that all public re-exports, docstrings, and `__all__` definitions remain completely intact
- [X] T007 [US1] Verify zero behavioral regression by executing the ingestion CLI `uv run python -m src.main ingest data/assessment-of-the-threat-from-russia.pdf` and confirming successful completion with exit code 0

**Checkpoint**: User Story 1 (MVP) complete and verified with zero behavioral regressions.

---

## Phase 4: User Story 2 - Automated Formatting Compliance Verification (Priority: P2)

**Goal**: Provide non-destructive check commands to inspect the repository for any code formatting or import ordering violations.

**Independent Test**: Execute `uv run ruff check src/` and `uv run ruff format --check src/` and verify that both commands exit with code 0 indicating 100% compliance.

### Implementation for User Story 2

- [X] T008 [US2] Execute non-destructive lint and import sorting check `uv run ruff check src/` verifying 0 errors across all production files
- [X] T009 [US2] Execute non-destructive code formatting check `uv run ruff format --check src/` verifying 0 files requiring formatting modifications

**Checkpoint**: User Stories 1 and 2 work independently and verified.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Update documentation and perform final verification.

- [X] T010 [P] Update `README.md` to document code formatting and import sorting commands (`uv run ruff check --select I,F401 --fix src/` and `uv run ruff format src/`)
- [X] T011 Run complete quickstart validation per `specs/002-format-codebase/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. Formats code and verifies zero regressions.
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion. Validates check-only compliance.
- **Polish (Phase 5)**: Depends on all user story phases being complete.

```text
[Phase 1: Setup] ──► [Phase 2: Foundational] ──► [Phase 3: User Story 1] ──► [Phase 4: User Story 2] ──► [Phase 5: Polish]
```

### Parallel Opportunities

- `T002` (pyproject.toml config) can run alongside `T001`.
- `T010` (README update) can run alongside `T011`.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (`T001` - `T002`)
2. Complete Phase 2: Foundational (`T003`)
3. Complete Phase 3: User Story 1 (`T004` - `T007`)
4. **STOP and VALIDATE**: Verify that files in `src/` are formatted and `src.main ingest` executes successfully.
