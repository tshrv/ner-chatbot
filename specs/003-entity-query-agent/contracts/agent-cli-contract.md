# CLI Contract: Entity Query AI Agent

**Feature**: Entity Query AI Agent (`003-entity-query-agent`)  
**Date**: 2026-09-28  
**Status**: Completed  

---

## 1. Command Specification

The conversational agent is launched via Typer CLI subcommand:

```bash
uv run python -m src.main chat [OPTIONS]
```

Or when installed:

```bash
ner-chatbot chat [OPTIONS]
```

### Options

| Option | Flag | Type | Default | Description |
|---|---|---|---|---|
| `--model` | `-m` | `str` | `gemini-3.8-flash` | Gemini model name |
| `--verbose` | `-v` | `bool` | `False` | Enable diagnostic logging to stderr |

---

## 2. Interactive Terminal Session Contract

### Startup Banner

```text
============================================================
              ENTITY INTELLIGENCE CHAT AGENT
============================================================
Ask questions about entities, types, and occurrences.
Type 'exit' or 'quit' to end the session.
============================================================
```

### Turn-by-Turn Conversational Interaction

User prompt format:
```text
You: How many unique entity types are in the database?
```

Agent reply format:
```text
Agent: There are 5 unique entity types in the database: Date, Event, Location, Organization, and Person.
```

Occurrence query example:
```text
You: Where does the entity "Russia" appear?
Agent: The entity "Russia" (Location) appears 8 times across 1 document:
- Document: assessment-of-the-threat-from-russia.pdf (8 occurrences)

Top occurrences:
1. assessment-of-the-threat-from-russia.pdf (Page 1, offsets 120-126): "Russia"
2. assessment-of-the-threat-from-russia.pdf (Page 1, offsets 450-456): "Russia"
3. assessment-of-the-threat-from-russia.pdf (Page 2, offsets 88-94): "Russia"
...
```

Out-of-scope refusal example:
```text
You: What is the capital of France?
Agent: I am an entity intelligence assistant and can only answer questions regarding extracted entities, entity types, and their occurrences in the database.
```

Not found example:
```text
You: Does "Elon Musk" appear in the documents?
Agent: No entity matching "Elon Musk" was found in the database.
```

Exit session:
```text
You: exit
Goodbye!
```

---

## 3. Exit Codes

| Exit Code | Meaning |
|---|---|
| `0` | Clean session termination via `exit`, `quit`, or `Ctrl+C`. |
| `1` | Configuration error (missing API key in `.env`). |
| `2` | Database unreachable on session start. |
