# Streaming and Run Results

This reference covers `Runner.call`, `Runner.acall`, `Runner.astream`, final result handling, step history, and event consumption. Provider-specific token streaming is configured in the model-client/generator sub-skill; this reference focuses on the agent-side event contract.

## RunnerResult

`Runner.call(...)` and `await Runner.acall(...)` return `RunnerResult`:

```python
RunnerResult(
    step_history=[...],  # list[StepOutput]
    answer=...,          # final processed answer or a no-output/error message
    error=None,          # error string when execution failed or stopped on an error
)
```

A `StepOutput` records one non-final action:

```python
StepOutput(
    step=0,
    action=Function(...),
    function=Function(...),
    observation="what the next planner step sees",
    ctx=None,
)
```

Notes:

- Final planner actions (`Function(_is_answer_final=True, _answer=...)`) are processed directly into `RunnerResult.answer` and are not normally appended to `step_history`.
- Tool errors captured in `FunctionOutput.error` can become step observations so the planner can try another step.
- If the planner returns `GeneratorOutput(data=None, error="...")`, `Runner` records a step with `function=None` and the error as `observation` until max steps or an unrecoverable error is reached.
- If no final answer appears before `max_steps`, `RunnerResult.answer` states that no output was generated after the step limit.

## Sync call pattern

```python
result = runner.call(
    prompt_kwargs={"input_str": "Use the tools to answer the question."},
    model_kwargs=None,
    use_cache=None,
    id="optional-run-id",
)

if result.error:
    # Inspect result.step_history for the failing step.
    handle_error(result.error)
else:
    use_answer(result.answer)
```

Use sync `call` for scripts, local smoke tests, and simple command-line workflows. Avoid invoking sync `call` from an already-running async event loop when the runner has permission handling or async tools; prefer `acall` there.

## Async call pattern

```python
result = await runner.acall(
    prompt_kwargs={"input_str": "Use the tools to answer the question."},
    model_kwargs=None,
)
```

Use `acall` when tools are async, the host application is async, or the planner model client is async. `acall` collects generator/async-generator tool outputs into non-activity values for the final step observation.

## Streaming result object

`Runner.astream(...)` returns `RunnerStreamingResult`, starts a background task on the current event loop, and exposes:

- `stream_events()` async iterator for `RawResponsesStreamEvent` and `RunItemStreamEvent`.
- `stream_to_json(file_name)` async iterator that also writes event summaries to a JSON file.
- `stream_to_json_sync(file_name)` helper for sync contexts.
- `answer`, `step_history`, and `is_complete` after completion.
- `cancel()` and `wait_for_completion()` for lifecycle control.

Call `astream` from inside an async function so an event loop is active:

```python
from adalflow.core.types import RawResponsesStreamEvent, RunItemStreamEvent

async def run_stream(runner):
    streaming = runner.astream(
        prompt_kwargs={"input_str": "Answer with tool progress."},
        model_kwargs={"stream": True},  # provider support is configured elsewhere
    )

    async for event in streaming.stream_events():
        if isinstance(event, RawResponsesStreamEvent):
            handle_raw_model_chunk(event.data, error=event.error)
        elif isinstance(event, RunItemStreamEvent):
            handle_runner_event(event.name, event.item)

    assert streaming.is_complete
    return streaming.answer
```

## Event types and names

Agent-side event wrappers:

| Wrapper | Common item | Meaning |
|---|---|---|
| `RawResponsesStreamEvent` | raw planner/model chunk or final parsed data | Planner output stream or non-streaming planner data. |
| `RunItemStreamEvent(name="agent.tool_permission_request")` | `ToolCallPermissionRequest` | A tool requires approval before execution. |
| `RunItemStreamEvent(name="agent.tool_call_start")` | `ToolCallRunItem` | Tool execution is about to begin. |
| `RunItemStreamEvent(name="agent.tool_call_activity")` | `ToolCallActivityRunItem` | A generator tool yielded intermediate progress. |
| `RunItemStreamEvent(name="agent.tool_call_complete")` | `ToolOutputRunItem` | Tool execution completed with a `FunctionOutput`. |
| `RunItemStreamEvent(name="agent.step_complete")` | `StepRunItem` | One agent planning/execution step is complete. |
| `RunItemStreamEvent(name="agent.execution_complete")` | `FinalOutputItem` | Runner execution is complete. |

`RunItemStreamEvent.name` is the most convenient switch. For robust code, also check `isinstance(event.item, ...)` because event naming may evolve.

## Tool streaming

A tool can stream progress by being a sync or async generator. During `Runner.astream`, yield `ToolCallActivityRunItem` for intermediate progress and yield a final non-activity value, commonly `ToolOutput`, as the completed output:

```python
from adalflow.core.types import ToolCallActivityRunItem, ToolOutput


def staged_lookup(topic: str):
    """Lookup topic with progress updates."""
    yield ToolCallActivityRunItem(data=f"starting lookup for {topic}")
    yield ToolCallActivityRunItem(data="checked local cache")
    yield ToolOutput(
        output={"topic": topic, "fact": "cached fact"},
        observation=f"Found cached fact for {topic}",
        display="Lookup complete",
    )
```

In non-streaming `call`/`acall`, activity items are skipped and non-activity yielded values are collected. In streaming mode, activity items are emitted as `agent.tool_call_activity` events, and the final non-activity value is emitted through `agent.tool_call_complete`.

## Finalization and answer type

Finalization depends on the planner returning a `Function` with `_is_answer_final=True` and `_answer` set:

```python
Function(name="finish", _is_answer_final=True, _answer="final answer")
```

`Runner` then processes `_answer` with `answer_data_type`:

- For `str`, `int`, `float`, `bool`, `list`, `dict`, etc., it casts directly.
- For Pydantic models, pass a dict or JSON string representing a dict.
- For AdalFlow dataclasses, pass a dict or JSON string accepted by `from_dict`.

If the final answer is structured and parsing fails, `Runner` raises or reports a processing error. Test structured finalization with a fake planner before connecting a live provider.

## Error and max-step behavior

Recoverable planner parsing errors:

- `GeneratorOutput(data=None, error="parse error")` becomes a step observation.
- The loop continues until a final action, unrecoverable error, or max steps.

Unrecoverable planner errors:

- Errors containing HTTP `400`, `404`, `429`, or `connection error` are treated as unrecoverable by the runner and stop execution.

Max-step exhaustion:

- If the planner repeatedly returns non-final actions, the runner stops at `max_steps`.
- The answer becomes a no-output message and `step_history` contains the executed non-final steps.
- Lower `max_steps` for smoke tests and raise it only when real tasks need deeper reasoning.

## Cancellation

For streaming workflows:

```python
streaming = runner.astream(prompt_kwargs={"input_str": "long task"})
# later
await runner.cancel()
await streaming.wait_for_completion()
```

Cancellation sets the runner cancellation flag and attempts to cancel the active streaming task. Always drain or wait for the streaming result so task exceptions do not leak into the host application.

## Safe event loop guidance

- Use `asyncio.run(main())` around an async top-level function in scripts.
- Call `Runner.astream` only when an event loop is running.
- Do not nest `asyncio.run` inside an existing event loop; use `await runner.acall(...)` or create a task instead.
- Generator tools that produce async generators should be consumed exactly once. Do not iterate the same generator output in both logging and business logic.

## Minimal event-consumption skeleton

```python
from adalflow.core.types import (
    RawResponsesStreamEvent,
    RunItemStreamEvent,
    ToolCallRunItem,
    ToolOutputRunItem,
    StepRunItem,
    FinalOutputItem,
)

async def consume(streaming):
    final = None
    async for event in streaming.stream_events():
        if isinstance(event, RawResponsesStreamEvent):
            if event.error:
                print("planner error:", event.error)
            elif event.data is not None:
                print("raw:", event.data)
        elif isinstance(event, RunItemStreamEvent):
            if isinstance(event.item, ToolCallRunItem):
                print("tool starting:", event.item.data.name)
            elif isinstance(event.item, ToolOutputRunItem):
                print("tool output:", event.item.data.output)
            elif isinstance(event.item, StepRunItem):
                print("step observation:", event.item.data.observation)
            elif isinstance(event.item, FinalOutputItem):
                final = event.item.data
    return final or streaming.answer
```
