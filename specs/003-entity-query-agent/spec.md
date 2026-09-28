# Feature Specification: Entity Query AI Agent

**Feature Branch**: `003-entity-query-agent`

**Created**: 2026-09-28

**Status**: Draft

**Input**: User description: "Create an ai agent. Runnable via cli command, into a chat like behaviour, but it does not keep conversation history. The agent's only task is to answer user's natural language query on entities using the available tool, and not its own knowledge. It does not invent any information and always checks with the tool before answering. It should have access to tool(one or more) to query entities related information (case insensitive) from the database like: count total entity types, count unique entity types, list all entity types, check if an entity type exists, via value, count total entities, count unique entities, list all entities, check if an entity exists, via value, check for all occurences of an entity, should list all target documents, page number, offset, etc., check for all occurences of an entity type, should list all target documents, page number, offset, etc. Tool should not retrieve job level information. If user query is not about entities/types/occurences, the agent should deny the request clearly. If no information could be retrieved via tools, agent should inform clearly instead of inventing information. If any error occurs, agent should retry maximum 3 times and then stop with clear response."

## Clarifications

### Session 2026-09-28

- Q: When an entity or entity type has a large volume of occurrences across documents, how should the agent present the results to the user in the CLI? → A: Option A: Top-N preview with summary (display total occurrence count per document, detail the first 10 occurrences with doc, page, offsets, and state remaining count).
- Q: How should the agent interactively prompt the user and signal its readiness for input? → A: Option A: Prompt format with `You: ` prompt and `Agent: ` reply, with a startup welcome banner and exit instructions (`Type 'exit' or 'quit' to end`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Natural Language Entity Querying via Interactive CLI (Priority: P1)

An analyst launches an interactive CLI chat session to explore extracted entities stored in the database using plain natural language questions (e.g., "How many unique organizations were detected?", "Does Vladimir Putin exist in the documents?", "Where does Ukraine appear?"). For each query, the agent parses the user's intent, invokes the appropriate database inspection tool (case-insensitively), and formats an accurate response derived exclusively from the tool's findings. Each turn is processed independently without retaining past conversational history, guaranteeing clean, isolated answers.

**Why this priority**: Delivers the primary value of the conversational intelligence layer, transforming stored entity data and occurrence offsets into easily accessible answers without requiring users to write raw database queries.

**Independent Test**: Can be tested independently by running the CLI agent command, submitting natural language questions about entity counts, listings, existence, and occurrence locations, and verifying that each response accurately reflects the database state retrieved via tools without conversational bleed between turns.

**Acceptance Scenarios**:

1. **Given** stored entity data in the database, **When** the user asks "How many total entities and unique entities are recorded?", **Then** the agent calls the entity counting tool and returns the exact numerical figures retrieved.
2. **Given** stored entity occurrences across documents, **When** the user asks "Show all occurrences of entity 'Russia'", **Then** the agent executes a case-insensitive entity occurrence lookup and reports the target document names, page numbers, and character offsets retrieved.
3. **Given** an active chat session, **When** the user enters a second question following a previous question, **Then** the agent evaluates the new question entirely on its own merits without using previous conversation context.

---

### User Story 2 - Domain Scope Enforcement and Strict Grounding Guardrails (Priority: P2)

A user queries the agent with questions outside the scope of entity metadata (e.g., general knowledge questions like "What is the capital of France?", conversational chit-chat, or requests for pipeline job execution logs). The agent enforces domain guardrails: it clearly denies out-of-scope requests, refuses to retrieve job-level pipeline execution data, and informs the user directly when no entities or types match their query rather than inventing plausible answers.

**Why this priority**: Prevents hallucinations and unauthorized data leaks, ensuring the agent acts strictly as a trusted, grounded entity exploration interface.

**Independent Test**: Can be tested independently by submitting out-of-scope queries (general trivia, pipeline job queries, or non-existent entity searches) and confirming that the agent emits standard, clear denials or "not found" statements without fabricating facts.

**Acceptance Scenarios**:

1. **Given** a user query unrelated to entities, types, or occurrences (e.g., "Summarize the weather in Paris"), **When** processed by the agent, **Then** the agent denies the request with a clear message stating it only answers questions regarding extracted entities and occurrences.
2. **Given** a user query asking about pipeline executions or job IDs (e.g., "Show me the status of job 123"), **When** processed by the agent, **Then** the agent denies the request, stating job-level information is outside its scope.
3. **Given** a valid entity query for an entity not present in the database, **When** the tool returns zero matches, **Then** the agent explicitly states that no matching entity or occurrences were found.

---

### User Story 3 - Resilient Tool Calling and Automated Error Recovery (Priority: P3)

During entity querying, an intermittent tool failure or database communication glitch occurs. The agent automatically retries the tool execution up to three times. If the error persists after three attempts, the agent stops retrying and provides a clear, polite error response explaining that the operation could not be completed, avoiding infinite loops or unhandled CLI crashes.

**Why this priority**: Guarantees reliability and predictable failure behavior under transient network or database errors.

**Independent Test**: Can be tested independently by simulating a transient failure in the tool layer and verifying that the agent retries exactly three times before returning a graceful failure message.

**Acceptance Scenarios**:

1. **Given** a transient failure on tool invocation, **When** the tool call errors, **Then** the agent automatically retries the operation up to 3 times before returning an error response to the user.
2. **Given** a persistent tool error exceeding 3 attempts, **When** retries are exhausted, **Then** the agent stops and displays a clear error explanation to the user.

---

### Edge Cases

- **Case-Insensitive Variations**: When an entity is queried in all-caps, title-case, or lower-case (e.g., "NATO", "Nato", "nato"), the tool retrieval normalizes the casing to find all matching entity records.
- **Ambiguous Queries**: When a query could refer to an entity name or an entity type (e.g., "Show me Date"), the agent clarifies whether it searched for the type or entity name, or queries both.
- **Large Result Sets**: When an entity has dozens or hundreds of occurrences, the agent provides a concise summarized breakdown (e.g., total count per document and page) rather than flooding the console with hundreds of unformatted lines.
- **Session Termination**: The interactive loop must provide standard exit signals (e.g., typing "exit", "quit", or sending SIGINT / Ctrl+C) to gracefully terminate the session.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a CLI command to launch an interactive entity chat session, displaying a startup welcome banner with instructions (`Type 'exit' or 'quit' to end session`), styling user turns as `You: ` and agent responses as `Agent: `.
- **FR-002**: The agent MUST operate in a single-turn conversational paradigm, evaluating each natural language query independently without maintaining or referencing conversational history across turns.
- **FR-003**: The agent MUST answer user queries exclusively using data retrieved via its integrated entity tools, never answering from its own internal pre-trained knowledge base.
- **FR-004**: The agent MUST provide tools to query entity information in a case-insensitive manner, supporting:
  - Counting total entity types
  - Counting unique entity types
  - Listing all entity types
  - Checking if a specific entity type exists
  - Counting total entity records
  - Counting unique entities
  - Listing all entities
  - Checking if a specific entity exists
  - Retrieving all occurrences of an entity with document name, page number, and character offsets
  - Retrieving all occurrences of an entity type with document name, page number, and character offsets
- **FR-005**: The entity querying tools MUST NOT expose, access, or retrieve pipeline execution or job-level data (e.g., job IDs, task statuses, or execution logs).
- **FR-006**: The agent MUST validate query relevance and clearly deny any user request that does not pertain to entities, entity types, or entity occurrences.
- **FR-007**: When an entity or entity type cannot be found via the tools, the agent MUST explicitly inform the user that no matching information exists in the database.
- **FR-008**: When a tool invocation or query execution encounters an error, the agent MUST retry the operation up to a maximum of 3 times before halting and returning a clear failure notification.
- **FR-009**: The interactive CLI session MUST support graceful termination when the user enters standard exit keywords (`exit`, `quit`, `q`) or triggers an interrupt signal (`Ctrl+C`), displaying a polite farewell message.
- **FR-010**: All occurrence results returned to the user MUST include the target document name, 1-based page number, and character offsets (`start_offset`, `end_offset`); when results exceed 10 mentions, the agent MUST summarize total counts per document, detail the first 10 occurrences, and report the count of remaining occurrences.

### Key Entities

- **Entity Query**: Represents the incoming user prompt in natural language, specifying an intent to count, list, verify, or locate entities or entity types.
- **Entity Tool Result**: The structured data payload returned by the database retrieval tool, containing counts, entity lists, boolean existence flags, or occurrence references.
- **Occurrence Record**: Represents a localized mention of an entity, comprising document name, 1-based page index, start offset, end offset, surface text, and confidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of factual entity claims in agent responses are directly traceable to tool execution results.
- **SC-002**: 100% of out-of-scope queries (general trivia, coding questions, job/pipeline queries) are denied with a clear domain scope refusal.
- **SC-003**: Zero conversational state leakage between turns: consecutive unrelated questions produce answers unaffected by preceding turns.
- **SC-004**: Case-insensitive matching succeeds with 100% consistency across uppercase, lowercase, and mixed-case entity queries.
- **SC-005**: In the event of persistent tool execution failures, the agent halts retries after exactly 3 attempts and reports a descriptive error.
- **SC-006**: Typical query turnaround time from user prompt to agent response is under 4 seconds when the database is responsive.

## Assumptions

- The database containing extracted entities and occurrences is populated and accessible prior to starting the agent session.
- The agent runs within a terminal environment supporting standard stdin/stdout interactive loops.
- Standard general entity types (e.g., Person, Organization, Location, Date, Event) are the primary categories stored in the database.
- Database queries executed by the tools perform case-insensitive collation or regex/normalization matches.
