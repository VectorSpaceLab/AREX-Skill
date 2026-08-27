# Agent and Session Memory Workflows

Read this when building agent memory or session-aware workflows on top of Cognee.

## Typed memory entries

Cognee accepts structured memory payloads through `remember(...)` in addition to raw text/files.

```python
from cognee.memory import QAEntry, TraceEntry, FeedbackEntry, SkillRunEntry

await cognee.remember(QAEntry(question="What did we decide?", answer="Use Cognee."), session_id="agent-1")
```

| Entry | Use |
| --- | --- |
| `QAEntry` | Store a question/answer turn with optional context and feedback. |
| `TraceEntry` | Store one agent/tool trace step with status, params, result, and error text. |
| `FeedbackEntry` | Attach feedback to a previous QA entry by `qa_id`. |
| `SkillRunEntry` | Record a graph-backed skill execution and quality signal. |

## Recall scopes

`recall` understands these scope names:

- `auto`
- `graph`
- `session`
- `trace`
- `graph_context` (deprecated alias for graph)
- `session_context`
- `all`

Use `session_id` when asking about recent or session-specific memory. Use `scope="all"` when the task needs graph, session, trace, and session-context sources together.

## Agent decorator

Public pattern:

```python
import cognee

@cognee.agent_memory(
    agent_session_name="support-agent",
    with_memory=True,
    with_session_memory=True,
    save_session_traces=True,
    memory_query_from_method="question",
    dataset_name="support_docs",
    session_id="support-session",
)
async def answer(question: str) -> str:
    ...
```

Important constraints:
- The decorated function must be async.
- Only one of `memory_query_fixed` or `memory_query_from_method` may be set.
- `memory_query_from_method` must match a function parameter.
- `memory_top_k` and `session_memory_last_n` are positive sizing knobs.
- `save_session_traces` controls trace persistence; `persist_session_trace_after` can batch trace persistence.

## Agents namespace

Use `cognee.agents` when the user needs explicit agent identities or API keys.

| Method | Purpose |
| --- | --- |
| `create(name, datasets=None, user=None)` | Create an agent and optionally grant read/write on datasets the caller can read. |
| `list(user=None)` | List owned agents. |
| `get(agent_id, user=None)` | Show one agent. |
| `delete(agent_id, user=None)` | Delete one owned agent. |
| `register(...)` | Register a live agent connection. |
| `unregister(agent_session_name, user=None)` | Unregister by session name. |
| `list_connections(...)` / `get_connection(...)` | Inspect live/recorded connection state. |

Dataset authorization happens before minting an agent and before granting the agent access. This prevents orphaned agent keys after a failed permission check.

## Session and feedback APIs

- `get_session(session_id=None, last_n=None, user=None)` reads Q&A entries.
- `add_feedback(session_id, qa_id, feedback_text=None, feedback_score=None, user=None)` updates a QA entry.
- `delete_feedback(session_id, qa_id, user=None)` clears feedback.
- Frequency weights can store graph element ids used in an answer.

For retrieval tuning with `feedback_influence`, route to [search-retrieval](../../search-retrieval/SKILL.md).
