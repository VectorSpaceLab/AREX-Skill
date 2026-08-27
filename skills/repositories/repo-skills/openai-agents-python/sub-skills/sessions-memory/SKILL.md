---
name: sessions-memory
description: "Choose and configure session memory, server-managed continuation,
  backends, compaction, and multi-turn history for openai-agents-python."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Sessions and Memory

Use this sub-skill when a task mentions `session`, `memory`, `SQLiteSession`, `RedisSession`, `SQLAlchemySession`, `conversation_id`, `previous_response_id`, compaction, or multi-turn history.

## Route First

| Need | Use | Details |
| --- | --- | --- |
| SDK-managed client-side history | `session=...` with a `Session` backend | See [backends](references/backends.md) and [workflows](references/workflows.md). |
| OpenAI server-managed continuation | `conversation_id`, `previous_response_id`, or `auto_previous_response_id` | Do not combine with `session`; see [workflows](references/workflows.md#choose-session-memory-or-server-managed-continuation). |
| Basic agent loop behavior | Core runtime | Route to [core-runtime](../core-runtime/SKILL.md). |
| Provider auth, model defaults, transport selection | Models/providers | Route to [models-providers](../models-providers/SKILL.md). |
| Sandbox filesystem/process memory | Sandbox agents | Route to [sandbox-agents](../sandbox-agents/SKILL.md) unless normal SDK sessions are involved. |

## What To Configure

- Pick one history owner: either an SDK `Session` backend or OpenAI server-managed continuation, never both in the same run.
- For local or simple persistent memory, start with `SQLiteSession(session_id, db_path=...)`.
- For production storage, choose an extension backend by deployment constraints, required extras, and lifecycle ownership in [backends](references/backends.md).
- For long conversations, use `SessionSettings(limit=...)`, `RunConfig.session_input_callback`, or compaction depending on whether you need retrieval limiting, custom merge logic, or stored-history replacement.
- For approval or interruption resumes, pass the same `session` object or another instance pointing at the same backing store when calling `Runner.run(agent, state, session=session)`.

## Required Safety Checks

- Before recommending a backend, run or adapt the bundled no-network helper: `python scripts/check_session_backend.py --backend sqlite --json`.
- When optional backends fail to import, report the missing extra and avoid constructing network clients unless the user explicitly asks.
- When behavior is surprising, consult [troubleshooting](references/troubleshooting.md) before changing runtime code.
