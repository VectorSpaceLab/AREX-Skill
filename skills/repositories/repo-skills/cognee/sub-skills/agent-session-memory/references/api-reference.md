# Agent and Session API Reference

## Typed payload schemas

### `QAEntry`

Fields:
- `type="qa"`
- `question: str`
- `answer: str`
- `context: str = ""`
- `feedback_text: str | None`
- `feedback_score: int | None`
- `used_graph_element_ids: dict | None`

### `TraceEntry`

Fields:
- `type="trace"`
- `origin_function: str`
- `status: "success" | "error" = "success"`
- `method_params: dict | None`
- `method_return_value: Any | None`
- `memory_query: str`
- `memory_context: str`
- `error_message: str`
- `generate_feedback_with_llm: bool`

### `FeedbackEntry`

Fields:
- `type="feedback"`
- `qa_id: str`
- `feedback_text: str | None`
- `feedback_score: int | None`

### `SkillRunEntry`

Fields include `run_id`, `selected_skill_id`, `task_text`, `result_summary`,
`success_score`, `feedback`, `error_type`, `error_message`, timing fields,
`candidate_skill_ids`, `task_pattern_id`, `router_version`, `tool_trace`, and `node_set`.

Validation notes:
- `success_score` must be between 0.0 and 1.0 when set.
- `feedback` must be between -1.0 and 1.0.
- Timing fields are non-negative.

## Agent-memory decorator

```python
agent_memory(
    *,
    agent_session_name: str | None = None,
    with_memory: bool = True,
    with_session_memory: bool = False,
    save_session_traces: bool = False,
    memory_query_fixed: str | None = None,
    memory_query_from_method: str | None = None,
    memory_system_prompt: str | None = None,
    memory_top_k: int = 5,
    memory_only_context: bool = False,
    session_memory_last_n: int = 5,
    session_id: str | None = None,
    user: User | None = None,
    dataset_name: str | None = None,
    session_trace_summary: bool = True,
    persist_session_trace_after: int | None = None,
    persist_session_trace_raw_content: bool = False,
    persist_session_trace_node_set_name: str | None = None,
)
```

The decorator registers an agent connection, retrieves memory context before the wrapped call, persists trace context after the call, and unregisters/deactivates the connection when appropriate.

## Session APIs

```python
await cognee.session.get_session(session_id=None, last_n=None, user=None)
await cognee.session.add_feedback(session_id, qa_id, feedback_text=None, feedback_score=None, user=None)
await cognee.session.delete_feedback(session_id, qa_id, user=None)
```

A bare `get_session()` requires an existing default dataset scope. Passing an explicit `session_id` avoids ambiguity.

## Agents namespace

```python
await cognee.agents.create("support-bot", datasets=["support_docs"])
await cognee.agents.list()
await cognee.agents.get(agent_id)
await cognee.agents.delete(agent_id)
await cognee.agents.register("support-session", session_id="support-1")
await cognee.agents.unregister("support-session")
await cognee.agents.list_connections(range_key="30d")
```

The SDK strips the internal `+{parent_id}` part from agent emails before displaying them.
