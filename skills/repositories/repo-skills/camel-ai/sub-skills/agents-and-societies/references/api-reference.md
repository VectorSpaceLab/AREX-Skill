# Agents And Societies API Reference

This reference summarizes CAMEL-AI APIs used to build agent workflows. Use it with the installed `camel-ai` package; avoid depending on a source checkout at runtime.

## Core Imports

```python
from camel.agents import ChatAgent, CriticAgent, TaskAgent
from camel.messages import BaseMessage
from camel.societies import RolePlaying
from camel.societies.workforce import Workforce, WorkforceMode
from camel.tasks import Task
from camel.terminators import ResponseWordsTerminator
```

`CriticAgent` and `TaskAgent` are routing-level collaborators: use them when a workflow needs critique or task decomposition, but prefer the higher-level `RolePlaying` and `Workforce` recipes unless the user explicitly needs custom agent internals.

## `ChatAgent`

Verified constructor shape for CAMEL-AI 0.2.91a4:

```python
ChatAgent(
    system_message=None,
    model=None,
    memory=None,
    message_window_size=None,
    summarize_threshold=50,
    token_limit=None,
    output_language=None,
    tools=None,
    external_tools=None,
    response_terminators=None,
    scheduling_strategy="round_robin",
    max_iteration=None,
    tool_execution_timeout=None,
    mask_tool_output=False,
    retry_attempts=3,
    retry_delay=1.0,
    step_timeout=None,
    on_request_usage=None,
    stream_accumulate=None,
    summary_window_ratio=0.6,
)
```

Use `ChatAgent` when the task is a single conversational worker or a reusable worker inside a society/workforce.

Important behavior:

- `system_message` can be `None`, a `str`, or a `BaseMessage`; strings are converted through `BaseMessage.make_system_message`.
- `model` may be a backend instance, a model manager, a string/model enum, a `(platform, model)` tuple, or a list of supported model specs. Route backend selection and credentials to `../models-and-configuration/`.
- `memory` defaults to `ChatHistoryMemory` when omitted. Use `message_window_size`, `token_limit`, `summarize_threshold`, and `summary_window_ratio` for context control. Route memory internals to `../memory-rag-and-data/`.
- `tools` are internal callable or `FunctionTool` objects. `external_tools` return tool call requests rather than executing internally. Route schema, MCP, and sandbox details to `../tools-runtimes-and-services/`.
- `response_terminators` are checked during `step()` loops. Pair them with a system prompt that tells the model which signal to emit.
- `max_iteration`, `tool_execution_timeout`, `step_timeout`, `retry_attempts`, and `retry_delay` are the first controls to inspect when a loop stalls or a backend is flaky.
- `on_request_usage` receives per-request/cumulative usage payloads during model requests. Keep callbacks lightweight and side-effect safe.
- Streaming responses may be iterable/awaitable wrappers. If using callbacks or streams, decide whether downstream code expects deltas or accumulated content and set `stream_accumulate` intentionally.

Common methods and properties:

- `agent.step(user_message_or_text)` sends one turn and returns a `ChatAgentResponse` with `.msgs`, `.msg`, `.terminated`, and `.info`.
- `agent.astep(...)` is the async equivalent.
- `agent.reset()` clears conversation state and resets terminators.
- `agent.add_tool(...)` and `agent.add_tools([...])` attach callable tools after construction.
- `agent.memory`, `agent.system_message`, `agent.role_name`, `agent.tool_dict`, `agent.token_limit`, and `agent.output_language` expose key workflow state.

## `BaseMessage`

Use `BaseMessage` for explicit role and multimodal message construction:

```python
sys_msg = BaseMessage.make_system_message(
    "You are a careful planner.",
    role_name="Planner System",
)
assistant_msg = BaseMessage.make_assistant_message(
    role_name="Planner",
    content="Ready.",
)
user_msg = BaseMessage.make_user_message(
    role_name="User",
    content="Plan a migration.",
)
```

Key fields are `role_name`, `role_type`, `meta_dict`, `content`, optional `image_list`, `video_bytes`, detail settings, `parsed`, and `reasoning_content`.

Useful conversions:

- `message.create_new_instance(content)` preserves role and attachments while changing content.
- `message.to_openai_system_message()`, `to_openai_user_message()`, `to_openai_assistant_message()`, and `to_openai_message(role_at_backend=...)` convert to backend formats.
- `message.to_dict()` serializes role, metadata, content, and attachments.

Avoid passing arbitrary dicts as `system_message`; use a string or `BaseMessage`. If a user reports type errors around system messages, validate the object before building the agent.

## `RolePlaying`

Verified constructor shape for CAMEL-AI 0.2.91a4 includes:

```python
RolePlaying(
    assistant_role_name,
    user_role_name,
    task_prompt="",
    with_task_specify=True,
    with_task_planner=False,
    with_critic_in_the_loop=False,
    model=None,
    output_language=None,
    assistant_agent=None,
    user_agent=None,
)
```

The source also supports keyword options such as `critic_role_name`, `critic_criteria`, `task_type`, `assistant_agent_kwargs`, `user_agent_kwargs`, `task_specify_agent_kwargs`, `task_planner_agent_kwargs`, `critic_kwargs`, `sys_msg_generator_kwargs`, `extend_sys_msg_meta_dicts`, `extend_task_specify_meta_dict`, and `stop_event`.

Use `RolePlaying` for two-party turn-taking. The normal lifecycle is:

```python
session = RolePlaying(
    assistant_role_name="Python Developer",
    user_role_name="Product Manager",
    task_prompt="Design a release checklist.",
    with_task_specify=False,
    assistant_agent_kwargs={"model": model},
    user_agent_kwargs={"model": model},
)
message = session.init_chat()
assistant_response, user_response = session.step(message)
```

Important behavior:

- If `model` is passed globally, it is used for internal agents unless agent-specific kwargs provide their own model.
- If `assistant_agent` or `user_agent` are supplied, they must have non-`None` system messages or `RolePlaying` raises `ValueError`.
- `with_task_specify=True` creates a task-specify agent and may call a model during initialization. Disable it for CI dry-runs without credentials.
- `with_task_planner=True` similarly invokes a planner agent.
- `with_critic_in_the_loop=True` allows multiple candidate responses to be reduced by a critic or human critic.
- `init_chat()` resets both internal agents and returns the first assistant message.
- `step(assistant_msg)` returns `(assistant_response, user_response)`. Check `.terminated` and `info["termination_reasons"]` before continuing.

## `Workforce`

Verified constructor shape for CAMEL-AI 0.2.91a4 includes:

```python
Workforce(
    description,
    children=None,
    coordinator_agent=None,
    task_agent=None,
    default_model=None,
    share_memory=False,
    task_timeout_seconds=None,
    mode=WorkforceMode.AUTO_DECOMPOSE,
)
```

The source also supports `new_worker_agent`, `graceful_shutdown_timeout`, `use_structured_output_handler`, `callbacks`, `stream_callback`, and `failure_handling_config`.

Use `Workforce` when a single agent or two-agent role-play is not enough: task decomposition, worker assignment, retries, recovery strategies, shared memory, callbacks, or a dependency pipeline.

Common setup:

```python
workforce = Workforce(
    description="Research report team",
    coordinator_agent=coordinator_agent,
    task_agent=planner_agent,
    task_timeout_seconds=120,
    failure_handling_config={
        "max_retries": 2,
        "enabled_strategies": ["retry", "replan"],
        "halt_on_max_retries": False,
    },
)
workforce.add_single_agent_worker(
    description="Summarizes technical sources",
    worker=summary_agent,
)
result_task = workforce.process_task(Task(content="Draft a report", id="report"))
```

Use pipeline mode for deterministic dependency graphs:

```python
workforce = Workforce("Report pipeline", mode=WorkforceMode.PIPELINE)
workforce.pipeline_add("Collect data", task_id="collect") \
    .pipeline_fork(["Analyze market", "Analyze risk"]) \
    .pipeline_join("Write final report", task_id="final") \
    .pipeline_build()
```

Runtime controls available in the docs/source include `pause()`, `resume()`, `stop_gracefully()`, `stop_immediately()`, `skip_gracefully()`, snapshot save/list/restore, task modification APIs, sync/async process methods, worker creation, and stream callbacks.

## `Task`

Verified constructor facts for CAMEL-AI 0.2.91a4:

```python
Task(
    content,
    id=<uuid factory>,
    state=TaskState.FAILED,
    type=None,
    parent=None,
    subtasks=[],
    result="",
    dependencies=[],
    image_list=None,
    video_bytes=None,
)
```

Additional fields include `failure_count`, `assigned_worker_id`, `additional_info`, image/video detail options, and Pydantic model configuration.

Use `Task` instead of plain strings when you need IDs, subtasks, dependencies, results, or Workforce processing.

Key methods:

- `Task.from_message(message)` creates a root task from a message.
- `task.reset()` resets state/result.
- `task.update_result(result)` sets result and marks the task `DONE`.
- `task.set_id(id)` and `task.set_state(state)` control identity/state.
- `task.add_subtask(task)` and `task.remove_subtask(id)` maintain hierarchy.
- `task.to_string(state=False)` and `task.get_result()` produce readable trees.
- `task.decompose(agent=...)` asks a `ChatAgent` to produce subtasks using `<task>...</task>` parsing.
- `task.compose(agent=...)` composes subtask results into the parent result.

Note that the default state is currently `FAILED` in source, with TODO notes for future `OPEN` behavior. Do not assume a newly constructed task means ready/running unless your workflow sets state explicitly or hands it to `Workforce`.

## Response Terminators

`ResponseWordsTerminator` terminates when configured words reach thresholds in response messages:

```python
from camel.terminators import ResponseWordsTerminator
from camel.types import TerminationMode

terminator = ResponseWordsTerminator(
    {"CAMEL_TASK_DONE": 1},
    case_sensitive=True,
    mode=TerminationMode.ANY,
)
agent = ChatAgent(
    system_message="End with CAMEL_TASK_DONE when the task is complete.",
    response_terminators=[terminator],
    max_iteration=5,
)
```

Always align terminators with the system prompt. A terminator cannot fire if the model was never instructed to emit the signal.

## Callback And Streaming Surfaces

- `ChatAgent(on_request_usage=callback)` can capture token usage per request.
- `Workforce(callbacks=[...])` expects `WorkforceCallback` instances for lifecycle events.
- `Workforce(stream_callback=callback)` receives `(worker_id, task_id, text, mode)` for worker streaming chunks.
- Async methods such as `astep()` and `process_task_async()` should be awaited, not called from synchronous code without an event-loop plan.

Keep callbacks fast and exception-safe. Use them for metrics/logging, not for blocking human approval or long network calls.
