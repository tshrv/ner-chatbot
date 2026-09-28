# Tooling Contract: Codebase Formatting and Import Sorting

**Feature**: Codebase Formatting and Import Sorting (`002-format-codebase`)  
**Date**: 2026-09-28  
**Status**: Completed  

---

## 1. Commands Specification

### 1.1 Formatting & Auto-fix Command

Formats all Python code and sorts import statements in-place:

```bash
uv run ruff check --select I,F401 --fix src/ && uv run ruff format src/
```

- **Inputs**: Files in `src/` (excluding `src/playground/` via config).
- **Behavior**:
  - Reorders imports into standard library, third-party, and first-party blocks.
  - Removes unreferenced imports in regular modules (preserving `__init__.py`).
  - Formats lines to maximum width of 100 characters.
  - Rewrites target files on disk.
- **Exit Code**: `0` on success.

---

### 1.2 Non-Destructive Verification Command

Verifies that all files conform to formatting standards without writing changes to disk:

```bash
uv run ruff check src/ && uv run ruff format --check src/
```

- **Exit Codes**:
  - `0`: All files pass formatting and import sorting rules.
  - `1`: One or more files violate formatting rules or have unsorted imports.

---

## 2. Standard Output Contract

### On Compliant Codebase

```text
All checks passed!
14 files already formatted
```

### On Non-Compliant Codebase (Verification Mode)

```text
src/main.py:4:1: I001 Import block is un-sorted or un-formatted
Found 1 error.
Would reformat: src/main.py
1 file would be reformatted, 13 files already formatted
```
