# Event Hooks and Ordering

CrewAI Flows run on the same event bus architecture as crews, agents, tasks, tools, memory, checkpointing, and tracing. Use this reference when a task is about custom event listeners, method event order, temporary debug hooks, or before/after kickoff adjacency.

## Event Bus Basics

Custom event listeners usually subclass `BaseEventListener` and register handlers inside `setup_listeners`:

```python
from crewai.events import BaseEventListener, FlowStartedEvent, FlowFinishedEvent

class FlowAuditListener(BaseEventListener):
    def setup_listeners(self, crewai_event_bus):
        @crewai_event_bus.on(FlowStartedEvent)
        def on_flow_started(source, event):
            print(f"Flow started: {event.flow_name}")

        @crewai_event_bus.on(FlowFinishedEvent)
        def on_flow_finished(source, event):
            print(f"Flow finished: {event.flow_name}")

flow_audit_listener = FlowAuditListener()
```

A listener must be imported and instantiated before the flow runs. Defining the class alone does not register handlers.

For one-off debugging or tests, use scoped handlers:

```python
from crewai.events import crewai_event_bus, MethodExecutionStartedEvent

with crewai_event_bus.scoped_handlers():
    @crewai_event_bus.on(MethodExecutionStartedEvent)
    def capture(source, event):
        print(event.method_name)

    MyFlow().kickoff()
```

`scoped_handlers()` removes temporary handlers after the block.

## Flow Event Lifecycle

For a simple linear flow, expect this shape:

1. `FlowStartedEvent`
2. `MethodExecutionStartedEvent` for each start method
3. `MethodExecutionFinishedEvent` for each completed method
4. Listener `MethodExecutionStartedEvent`/`MethodExecutionFinishedEvent` pairs as graph conditions are satisfied
5. `FlowFinishedEvent`

On errors, a method can emit `MethodExecutionFailedEvent`. On async human feedback pauses, expect `MethodExecutionPausedEvent` and `FlowPausedEvent`.

Flow plots emit `FlowPlotEvent` when `flow.plot(...)` writes the visualization.

`Flow.ask()` emits `FlowInputRequestedEvent` and `FlowInputReceivedEvent`.

`@human_feedback` emits `HumanFeedbackRequestedEvent` and `HumanFeedbackReceivedEvent`; async providers can additionally pause method/flow execution.

## Event Payloads to Know

| Event | Useful fields |
| --- | --- |
| `FlowStartedEvent` | `flow_name`, `inputs` |
| `MethodExecutionStartedEvent` | `flow_name`, `method_name`, `state`, `params` |
| `MethodExecutionFinishedEvent` | `flow_name`, `method_name`, `result`, `state` |
| `MethodExecutionFailedEvent` | `flow_name`, `method_name`, `error` |
| `FlowFinishedEvent` | `flow_name`, `result`, `state` |
| `FlowPlotEvent` | `flow_name` |
| `FlowInputRequestedEvent` | `flow_name`, `method_name`, `message`, `metadata` |
| `FlowInputReceivedEvent` | `flow_name`, `method_name`, `message`, `response`, `metadata`, `response_metadata` |
| `HumanFeedbackRequestedEvent` | `flow_name`, `method_name`, `output`, `message`, `emit`, `request_id` |
| `HumanFeedbackReceivedEvent` | `flow_name`, `method_name`, `feedback`, `outcome`, `request_id` |

Flow events inherit common base event fields such as `timestamp`, `type`, and event identifiers used for ordering and causality.

## Ordering and Causality

CrewAI tests verify these important ordering properties:

- A start method's `MethodExecutionStartedEvent` has no `triggered_by_event_id`.
- A listener's `MethodExecutionStartedEvent.triggered_by_event_id` points to the upstream method's `MethodExecutionFinishedEvent.event_id`.
- Chained listeners preserve the causal chain: first finish → second start; second finish → third start.
- Parallel listeners triggered by the same method can share the same triggering finish event id.
- `or_(...)` listeners point to whichever upstream method actually satisfied the condition.
- `and_(...)` listeners run only after all required upstream triggers are satisfied.

Do not rely on simple append order from async handlers when collecting events. Sort by timestamp or use event counters/ids if the order matters.

## Event Listeners vs Flow Decorators

Use Flow decorators for graph control:

- `@start` starts graph execution.
- `@listen` reacts to method outputs or router labels.
- `@router` emits route labels.
- `@human_feedback` pauses/branches inside the graph.

Use event listeners for side-channel behavior:

- Logging and lightweight audit trails.
- Metrics or debugging information.
- Integrating with a local UI or test harness.
- Temporary diagnostics around event order.

Event listeners should not mutate primary flow state unless you intentionally want cross-cutting side effects. Keep handlers light and resilient; exceptions in handlers can obscure the real flow error.

## Before/After Kickoff Adjacency

CrewAI has several callback/hook surfaces. Route correctly:

| Need | Surface | Sub-skill |
| --- | --- | --- |
| Run code before or after a Crew kickoff | Crew `before_kickoff_callbacks` / `after_kickoff_callbacks` or decorators | [observability-and-hooks](../../observability-and-hooks/SKILL.md) for hook setup; [core-runtime](../../core-runtime/SKILL.md) for crew semantics |
| Run code before or after a Flow method | `@listen` graph methods or event bus `MethodExecution*Event` handlers | This sub-skill |
| Trace/export spans to providers | Tracing/observability configuration | [observability-and-hooks](../../observability-and-hooks/SKILL.md) |
| Branch a Flow after a method result | `@router` and `@listen("label")` | This sub-skill |

For flows that orchestrate crews, a flow method may call `crew.kickoff()`. Flow method events wrap the method; crew kickoff events occur inside that method's execution. If both Crew before/after hooks and Flow event listeners are installed, keep their responsibilities separate to avoid duplicate logging.

## Checkpoint Event Hooks

Checkpointing subscribes to selected event types and writes snapshots when those events fire. For flows, common triggers include:

```python
CheckpointConfig(on_events=["method_execution_finished"])
```

Use high-frequency events such as `llm_call_completed` only when necessary, and set `max_checkpoints` to cap storage.

Manual checkpoint handlers can accept a third `state` parameter supplied by the event system:

```python
from crewai.events import crewai_event_bus
from crewai.events.types.llm_events import LLMCallCompletedEvent

@crewai_event_bus.on(LLMCallCompletedEvent)
def on_llm_done(source, event, state):
    path = state.checkpoint("./checkpoints")
```

This is advanced and should be used when built-in `CheckpointConfig` triggers are not enough.

## Human Feedback Events

For `@human_feedback`, use route labels for graph behavior and events for observability:

- `HumanFeedbackRequestedEvent` tells UIs or logs which method needs review.
- `HumanFeedbackReceivedEvent` captures raw feedback and the collapsed `outcome` when `emit` was set.
- `MethodExecutionPausedEvent` and `FlowPausedEvent` are for async providers that pause the run until a callback resumes it.

Do not model ordinary chat follow-up messages as human feedback events. Conversational flows should use `handle_turn()` and message history.

## Debugging with Event Hooks

A safe local event collector:

```python
from crewai.events import crewai_event_bus
from crewai.events.types.flow_events import (
    FlowStartedEvent,
    FlowFinishedEvent,
    MethodExecutionStartedEvent,
    MethodExecutionFinishedEvent,
)

def capture_flow_events(flow):
    events = []
    with crewai_event_bus.scoped_handlers():
        for event_type in (
            FlowStartedEvent,
            MethodExecutionStartedEvent,
            MethodExecutionFinishedEvent,
            FlowFinishedEvent,
        ):
            @crewai_event_bus.on(event_type)
            def capture(source, event, _event_type=event_type):
                events.append(event)
        result = flow.kickoff()
    return result, sorted(events, key=lambda event: event.timestamp)
```

Use this only on flows that are safe to execute. For untrusted or LLM-backed flows, first inspect statically with [validate_flow_graph.py](../scripts/validate_flow_graph.py) and `flow.plot(...)`.

## Listener Registration Checklist

- Instantiate custom listeners before `kickoff()` or `plot()`.
- Keep listener instances in module scope so they are not garbage-collected.
- Use `scoped_handlers()` for tests or temporary diagnostics.
- Do not register the same global listener repeatedly in hot-reload code without cleanup.
- Keep event handlers lightweight; offload slow I/O to application queues where possible.
- Use flow graph routing for business logic; use event handlers for cross-cutting observation.
