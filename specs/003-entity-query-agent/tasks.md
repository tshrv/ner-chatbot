# Tasks: Entity Query AI Agent

**Input**: Design documents from `/specs/003-entity-query-agent/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/agent-cli-contract.md`, `quickstart.md`)  
**Prerequisites**: `plan.md`, `spec.md`, `data-model.md`, `contracts/agent-cli-contract.md`  
**Tests**: Excluded per Constitution Principle VI (Human-Authored Testing Policy)  
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.  

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Every task includes exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependency installation, settings configuration, and agent package scaffolding.

- [X] T001 Add `pydantic-ai-slim[google]>=0.0.18` and `google-genai>=0.1.1` via `uv add "pydantic-ai-slim[google]>=0.0.18" "google-genai>=0.1.1"` in `pyproject.toml`
- [X] T002 [P] Update `src/config.py` to add `gcp_vertex_ai_api_key: Optional[str] = None`, `llm_model_name: str = "gemini-3.8-flash"`, and `agent_max_retries: int = 3` settings
- [X] T003 [P] Initialize package scaffolding for `src/agent/` with docstring and exports in `src/agent/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Tool schemas and database inspection functions that MUST be complete before the agent can be assembled.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Create Pydantic tool return schemas (`EntityTypeCountResult`, `EntityCountResult`, `EntityExistenceResult`, `OccurrenceDetail`, `OccurrenceQueryResult`) in `src/agent/schemas.py` per `specs/003-entity-query-agent/data-model.md`
- [X] T005 Implement read-only database query functions in `src/services/agent_tools.py` querying MongoDB `entities`, `occurrences`, and `documents` collections (barring `jobs` collection): `count_entity_types()`, `list_entity_types()`, `check_entity_type_exists(type_name: str)`, `count_entities()`, `list_entities(type_name: Optional[str] = None, limit: int = 50)`, `check_entity_exists(entity_name: str)`, `get_entity_occurrences(entity_name: str)`, and `get_entity_type_occurrences(type_name: str)`

**Checkpoint**: Schemas and database tools ready.

---

## Phase 3: User Story 1 - Natural Language Entity Querying via Interactive CLI (Priority: P1) 🎯 MVP

**Goal**: An analyst enters an interactive CLI chat session and submits natural language questions about entity counts, listings, existence, and occurrence locations; the agent answers using data strictly retrieved via tools, executing single-turn turns without conversation history.

**Independent Test**: Execute `uv run python -m src.main chat` and ask "How many unique entity types exist?" and "Show occurrences of Europe", verifying that answers accurately reflect MongoDB records without conversation history retention.

### Implementation for User Story 1

- [X] T006 [US1] Create the Pydantic AI agent instance and system prompt in `src/agent/core.py` using `GoogleModel(settings.llm_model_name)` and `GoogleCloudProvider(api_key=settings.gcp_vertex_ai_api_key)`, registering all 8 entity query tools and instructing the agent to ground all answers exclusively in tool outputs
- [X] T007 [US1] Implement interactive single-turn CLI chat session and `chat` command in `src/main.py` accepting `--model` and `--verbose` options, displaying startup banner, prompting user with `You: `, executing `agent.run(prompt)` without conversation history, and outputting response as `Agent: `
- [X] T008 [US1] Verify interactive natural language entity queries (entity type counts, entity listings, existence checks, occurrence lookup with document/page/offsets) on ingested test data using `uv run python -m src.main chat`

**Checkpoint**: User Story 1 (MVP) complete and independently functional.

---

## Phase 4: User Story 2 - Domain Scope Enforcement and Strict Grounding Guardrails (Priority: P2)

**Goal**: Guard the agent against out-of-scope requests (general knowledge, chit-chat, coding) and pipeline execution inquiries, and ensure it explicitly reports missing information rather than hallucinating.

**Independent Test**: In `src/main.py chat`, ask "What is the capital of France?", "What is the status of job 123?", and "Does Gandalf appear?", verifying clear domain refusals and a clean not-found response.

### Implementation for User Story 2

- [X] T009 [US2] Enhance system prompt and guardrail instructions in `src/agent/core.py` to strictly refuse out-of-scope queries (general knowledge, coding, weather, chit-chat), bar pipeline execution/job inquiries, and instruct the agent to explicitly state when an entity or type is not found
- [X] T010 [US2] Verify guardrail refusal behavior and not-found responses using `uv run python -m src.main chat` with off-topic and non-existent entity queries

**Checkpoint**: User Stories 1 and 2 work independently with verified domain boundaries.

---

## Phase 5: User Story 3 - Resilient Tool Calling and Automated Error Recovery (Priority: P3)

**Goal**: Ensure the agent automatically retries up to 3 times on transient tool or model errors, stopping with a clear message if errors persist, and terminates cleanly on `exit`, `quit`, or `Ctrl+C`.

**Independent Test**: Verify graceful termination on `exit` or `Ctrl+C` with return code 0, and confirm retry handling on transient network/tool exceptions.

### Implementation for User Story 3

- [X] T011 [US3] Implement retry mechanism in `src/agent/core.py` and `src/main.py` wrapping `agent.run()` in an automated retry loop of maximum 3 attempts on transient tool/model exceptions before halting with a clear diagnostic message
- [X] T012 [US3] Verify graceful session termination on `exit`, `quit`, and `Ctrl+C` interrupt signal with exit code 0 in `src/main.py`

**Checkpoint**: All three user stories are resilient, guarded, and independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Format code with Ruff, update documentation, and perform end-to-end quickstart validation.

- [X] T013 [P] Format all new and modified source code using `uv run ruff check --select I,F401 --fix src/` and `uv run ruff format src/` per Constitution Principle VIII
- [X] T014 [P] Update `README.md` to document the interactive AI agent CLI command (`uv run python -m src.main chat`) and example prompts
- [X] T015 Execute complete quickstart validation per `specs/003-entity-query-agent/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion.
- **User Story 1 (Phase 3)**: Depends on Foundational completion. Delivers working MVP agent.
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion. Enhances guardrails.
- **User Story 3 (Phase 5)**: Depends on User Story 1 completion. Enhances retries and signal handling.
- **Polish (Phase 6)**: Depends on all user story phases being complete.

```text
[Phase 1: Setup] ──► [Phase 2: Foundational] ──► [Phase 3: User Story 1 (MVP)]
                                                         │
                                             ┌───────────┴───────────┐
                                             ▼                       ▼
                                [Phase 4: User Story 2]  [Phase 5: User Story 3]
                                             │                       │
                                             └───────────┬───────────┘
                                                         ▼
                                                 [Phase 6: Polish]
```

### Parallel Opportunities

- `T002` (config) and `T003` (scaffolding) can run in parallel with `T001`.
- `T013` (Ruff formatting) and `T014` (README update) can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (`T001` - `T003`)
2. Complete Phase 2: Foundational (`T004` - `T005`)
3. Complete Phase 3: User Story 1 (`T006` - `T008`)
4. **STOP and VALIDATE**: Launch `python -m src.main chat` and test entity queries.
