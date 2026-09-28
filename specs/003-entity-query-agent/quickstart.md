# Quickstart & Verification Guide: Entity Query AI Agent

**Feature**: Entity Query AI Agent (`003-entity-query-agent`)  
**Date**: 2026-09-28  
**Status**: Ready  

---

## 1. Prerequisites

1. MongoDB container running with populated entity data from `assessment-of-the-threat-from-russia.pdf`:
   ```bash
   docker compose up -d mongodb
   ```
2. Google Cloud Vertex AI API key configured in `.env`:
   ```ini
   GCP_VERTEX_AI_API_KEY=your_key_here
   ```
3. Dependencies installed via `uv`:
   ```bash
   uv sync
   ```

---

## 2. Launch the Agent

Start the interactive chat session:

```bash
uv run python -m src.main chat
```

---

## 3. Verification Scenarios

### Scenario 1: Entity Types Query
```text
You: List all entity types and count them.
Agent: There are 5 unique entity types in the database: Date, Event, Location, Organization, and Person.
```

### Scenario 2: Existence & Occurrence Lookup
```text
You: Does "Europe" appear in the documents, and on what pages?
Agent: Yes, "Europe" (Location) exists in the database with 3 occurrences across 1 document:
- assessment-of-the-threat-from-russia.pdf (Page 1: 1 occurrence, Page 2: 1 occurrence, Page 3: 1 occurrence)
Offsets:
1. assessment-of-the-threat-from-russia.pdf (Page 1, offsets 347-353): "Europe"
...
```

### Scenario 3: Out-of-Scope Query Denial
```text
You: Write a python function to calculate fibonacci numbers.
Agent: I am an entity intelligence assistant and can only answer questions regarding extracted entities, entity types, and their occurrences in the database.
```

### Scenario 4: Clean Session Termination
```text
You: exit
Goodbye!
```
Confirm return code `0`.
