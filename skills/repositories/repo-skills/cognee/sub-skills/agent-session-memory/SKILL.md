---
name: "agent-session-memory"
description: "Guides Cognee session memory, typed memory entries, feedback,
  agent isolation, and agent-memory decorator workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Cognee Agent and Session Memory

Use this sub-skill when the user wants Cognee to remember conversation state, store agent traces, record feedback, isolate memory per agent, or decorate an async agent with memory retrieval and persistence.

## Route here for

- `QAEntry`, `TraceEntry`, `FeedbackEntry`, and `SkillRunEntry` payloads.
- `recall(..., session_id=..., scope=...)` behavior.
- `@cognee.agent_memory(...)` decorator configuration.
- `cognee.agents.create/list/get/delete/register/unregister/list_connections/get_connection`.
- Session and feedback APIs: `get_session`, `add_feedback`, `delete_feedback`, frequency weights.
- Session distillation, feedback-influenced retrieval, and multi-user/agent isolation.

## Route away

- Basic permanent-memory storage and recall: [core-memory](../core-memory/SKILL.md).
- Retrieval mode tuning: [search-retrieval](../search-retrieval/SKILL.md).
- Backend/cache/env configuration: [configuration-backends](../configuration-backends/SKILL.md).
- CLI/MCP/UI service deployment: [api-cli-services](../api-cli-services/SKILL.md).

## Read first

1. [references/agent-session-memory.md](references/agent-session-memory.md)
2. [references/api-reference.md](references/api-reference.md)
3. [references/troubleshooting.md](references/troubleshooting.md)

## Safe helper

- [scripts/check_agent_memory_payloads.py](scripts/check_agent_memory_payloads.py) — validates typed memory payload JSON without writing to a database.

## Working rules

- Use a dedicated `session_id` per agent or task to avoid mixing unrelated traces.
- For feedback updates, keep the `qa_id` returned by a prior QA memory entry.
- Decorate only async functions with `@cognee.agent_memory`.
- Resolve dataset access before granting agent permissions.
- Route cache/provider failures to configuration instead of treating them as agent API problems.
