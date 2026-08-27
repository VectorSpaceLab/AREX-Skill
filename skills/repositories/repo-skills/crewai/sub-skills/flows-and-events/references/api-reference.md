# CrewAI Flow API Reference

This reference summarizes the public CrewAI Flow/event APIs that matter when building or debugging flow graphs. It is distilled from current CrewAI docs, source, tests, and installed package inspection for CrewAI `1.14.8a2`.

## Imports

Use these stable imports for ordinary Flow work:

```python
from crewai.flow.flow import Flow, and_, listen, or_, router, start
from crewai.flow.persistence import persist
from crewai.flow.human_feedback import human_feedback, HumanFeedbackResult
```

The package also exposes many of these through `crewai.flow`, including conversational helpers such as `ChatState`, `ConversationalConfig`, `ConversationalInputs`, and `human_feedback`.

## Flow Constructor

Installed signature summary:

```python
Flow(
    *,
    initial_state=None,
    name=None,
    tracing=None,
    stream=False,
    memory=None,
    input_provider=None,
    suppress_flow_events=False,
    defer_trace_finalization=False,
    human_feedback_history=[],
    last_human_feedback=None,
    persistence=None,
    max_method_calls=100,
    execution_context=None,
    checkpoint=None,
    checkpoint_completed_methods=None,
    checkpoint_method_outputs=None,
    checkpoint_method_counts=None,
    checkpoint_state=None,
)
```

Important fields:

| Field | Use |
| --- | --- |
| `initial_state` | Seed state with a `dict`, Pydantic model type/instance, or `None`. |
| `name` | Override the flow name visible in events/traces/plots. |
| `stream` | Return streaming chunks from `kickoff()` instead of only a final result. |
| `memory` | Use CrewAI unified memory from inside flow methods. |
| `input_provider` | Provider for `Flow.ask()` input collection. |
| `suppress_flow_events` | Hide console flow panels; events/tracing can still exist. |
| `persistence` | Persistence backend used by `@persist` flows/methods. |
| `checkpoint` | Enable event-driven checkpointing for `Crew`, `Flow`, or `Agent`. |
| `max_method_calls` | Guardrail for cycles or self-loops. |

## Decorator Signatures

Installed signatures:

```python
start(condition: FlowTrigger | None = None)
listen(condition: FlowTrigger)
router(condition: FlowTrigger, *, emit: Sequence[str] | str | None = None)
```

`FlowTrigger` can be:

- A method reference, such as `@listen(generate_outline)`.
- A method name string, such as `@listen("generate_outline")`.
- A router label string, such as `@listen("approved")`.
- A condition tree from `and_(...)` or `or_(...)`.

`@start()` marks entry points. A flow can have multiple unconditional starts, and all satisfied starts run when the flow begins or resumes. `@start("label_or_method")` can be used for conditional starts after a method or router label.

`@listen(...)` runs a method when its condition is satisfied. If the upstream method returns a value, the listener can accept it as a positional argument.

`@router(...)` is a listener that returns a string-like event label. Downstream methods listen to the returned label. Use `emit=["label_a", "label_b"]` or a `Literal[...]` return annotation so static plots and validators know possible outcomes.

`and_(a, b)` waits for all triggers. `or_(a, b)` fires when any trigger emits. Tests confirm complex nested `and_`/`or_` conditions, diamond joins, router cascades, and cyclic router loops are supported.

## Flow Execution APIs

```python
flow = MyFlow()
result = flow.kickoff(inputs={"topic": "..."})
result = await flow.kickoff_async(inputs={"topic": "..."})
```

`kickoff()`/`kickoff_async()` accept:

| Parameter | Purpose |
| --- | --- |
| `inputs` | State inputs and optional `id` for persisted state resume. |
| `input_files` | Named file inputs for flow methods. |
| `from_checkpoint` | Restore from a checkpoint snapshot. |
| `restore_from_state_id` | Fork from a `@persist` state snapshot into a new state id. |

Do not combine `from_checkpoint` and `restore_from_state_id`; CrewAI raises `ValueError` because checkpointing and `@persist` are separate recovery systems.

`Flow.ask(message, ...)` requests user input inside a method and emits flow input events. Use it for a wizard/clarification step, not for normal multi-turn chat.

## State APIs

Unstructured state uses dictionary access:

```python
class DraftFlow(Flow):
    @start()
    def init(self):
        self.state["topic"] = "AI governance"
```

Structured state uses Pydantic models:

```python
from pydantic import BaseModel

class DraftState(BaseModel):
    topic: str = ""
    approved: bool = False

class DraftFlow(Flow[DraftState]):
    @start()
    def init(self):
        self.state.topic = "AI governance"
```

Every flow state receives an `id`. For dict state, use `self.state["id"]`; for structured state, use `self.state.id`. The id is preserved across state updates and is the key used by persistence/resume patterns.

## Persistence and Checkpointing

`@persist` saves flow state at class or method level:

```python
@persist
class CounterFlow(Flow[CounterState]):
    @start()
    def step(self):
        self.state.counter += 1
```

Resume an existing persisted lineage with:

```python
flow.kickoff(inputs={"id": existing_state_id})
```

Fork from a persisted snapshot into a new lineage with:

```python
flow.kickoff(restore_from_state_id=existing_state_id)
```

Event-driven checkpointing is configured through `checkpoint=True` or `CheckpointConfig(...)` on `Crew`, `Flow`, or `Agent`. For flows, method-level events such as `method_execution_finished` are common checkpoint triggers. Checkpoint restore uses `from_checkpoint=CheckpointConfig(restore_from="...")` and skips work already represented by the checkpoint.

## Flow Plotting

```python
flow = MyFlow()
html_path = flow.plot("my_flow_plot")
```

`plot()` writes an HTML visualization and emits `FlowPlotEvent`. The default filename is `crewai_flow.html`; if no `.html` suffix is present, CrewAI adds it. Plotting reads the static flow definition, including starts, listeners, routers, condition trees, and `human_feedback.emit` outcomes.

For CLI plotting inside scaffolded projects, route to [cli-and-projects](../../cli-and-projects/SKILL.md).

## Human Feedback API

```python
@human_feedback(
    message="Approve this output?",
    emit=["approved", "needs_revision", "rejected"],
    llm="gpt-4o-mini",
    default_outcome="needs_revision",
)
@listen(or_("draft_ready", "needs_revision"))
def review(self):
    return self.state.draft
```

Key parameters:

| Parameter | Required | Meaning |
| --- | --- | --- |
| `message` | Yes | Prompt shown to the reviewer. |
| `emit` | No | Allowed route labels. If set, feedback is collapsed to one label. |
| `llm` | Required with `emit` | LLM used to classify feedback into an emitted label. |
| `default_outcome` | No | Fallback route; must be one of `emit`. |
| `provider` | No | Custom async/non-blocking feedback provider. |
| `learn` | No | Store lessons from feedback through memory. |

`HumanFeedbackResult` contains `output`, `feedback`, `outcome`, `timestamp`, `method_name`, and `metadata`. The flow tracks `last_human_feedback` and `human_feedback_history`.

## Flow Events

Core flow event classes:

| Event | Type string | Notes |
| --- | --- | --- |
| `FlowCreatedEvent` | `flow_created` | Flow object created. |
| `FlowStartedEvent` | `flow_started` | Kickoff begins; includes `inputs`. |
| `MethodExecutionStartedEvent` | `method_execution_started` | Includes `method_name`, `state`, and `params`. |
| `MethodExecutionFinishedEvent` | `method_execution_finished` | Includes `method_name`, `result`, and `state`. |
| `MethodExecutionFailedEvent` | `method_execution_failed` | Includes `method_name` and serialized error. |
| `MethodExecutionPausedEvent` | `method_execution_paused` | Method paused for async human feedback. |
| `FlowFinishedEvent` | `flow_finished` | Flow completes; includes final `state` and `result`. |
| `FlowPausedEvent` | `flow_paused` | Flow paused for async human feedback. |
| `FlowPlotEvent` | `flow_plot` | Flow plot created. |
| `FlowInputRequestedEvent` | `flow_input_requested` | `Flow.ask()` requested input. |
| `FlowInputReceivedEvent` | `flow_input_received` | `Flow.ask()` received or timed out. |
| `HumanFeedbackRequestedEvent` | `human_feedback_requested` | `@human_feedback` requested review. |
| `HumanFeedbackReceivedEvent` | `human_feedback_received` | Human response received; may include outcome. |

Event tests confirm `triggered_by_event_id` links listener starts to the method finish event that triggered them. Start methods have no triggering event id; parallel listeners can share the same triggering method finish event.

## Reference Notes

- Source flow templates and CLI commands were not copied into this sub-skill because CLI scaffolding and command execution belong to [cli-and-projects](../../cli-and-projects/SKILL.md).
- Tracing/export setup was not duplicated here because provider configuration belongs to [observability-and-hooks](../../observability-and-hooks/SKILL.md).
