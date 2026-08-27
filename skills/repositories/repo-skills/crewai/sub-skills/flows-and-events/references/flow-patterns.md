# Flow Patterns

Use this reference to design reliable CrewAI Flow graphs without reopening the source repository. The examples are intentionally small and avoid live LLM/network calls unless explicitly noted.

## Minimal Linear Flow

```python
from crewai.flow.flow import Flow, listen, start

class LinearFlow(Flow):
    @start()
    def collect(self):
        return "draft"

    @listen(collect)
    def refine(self, draft):
        return draft.upper()

result = LinearFlow().kickoff()
```

Design notes:

- Prefer method references when refactoring in the same class; prefer strings when listening to router labels or when a reference would be awkward.
- Listener arguments receive upstream results positionally. If a listener does not need the result, omit the parameter.
- The final `kickoff()` result is the output of the last completed method.

## Multiple Starts

```python
class MultiStartFlow(Flow):
    @start()
    def load_topic(self):
        self.state["topic"] = "CrewAI"

    @start()
    def load_constraints(self):
        self.state["constraints"] = ["short", "cited"]

    @listen(and_(load_topic, load_constraints))
    def ready(self):
        return self.state
```

Multiple unconditional starts are valid. All satisfied starts execute at the beginning. Do not assume source-order alone is a business dependency; use `and_(...)` when a downstream method needs all starts to finish.

## OR Fan-In and AND Joins

```python
class BranchFlow(Flow):
    @start()
    def begin(self):
        return "begin"

    @listen(begin)
    def path_a(self):
        return "a"

    @listen(begin)
    def path_b(self):
        return "b"

    @listen(or_(path_a, path_b))
    def log_each_ready_path(self, result):
        print(result)

    @listen(and_(path_a, path_b))
    def converge(self):
        return "both paths done"
```

Use `or_` for any-branch behavior and `and_` for convergence. Tests show complex nested conditions and diamond dependencies work, but explicit joins are easier to reason about than implicit state polling.

## Routers and Labels

```python
from typing import Literal

class ReviewFlow(Flow):
    @start()
    def draft(self):
        self.state["score"] = 0.9

    @router(draft, emit=["approved", "revise"])
    def decide(self) -> Literal["approved", "revise"]:
        return "approved" if self.state["score"] >= 0.8 else "revise"

    @listen("approved")
    def publish(self):
        return "published"

    @listen("revise")
    def revise(self):
        return "needs changes"
```

Router labels are just emitted event strings. Every expected label should have at least one `@listen("label")`, unless the label intentionally terminates the graph. `emit=[...]` and `Literal[...]` annotations make the labels visible to static graph tools and flow plots.

## Cascading Routers

```python
class CascadeFlow(Flow):
    @start()
    def begin(self):
        return "started"

    @router(begin, emit=["needs_review"])
    def first_route(self):
        return "needs_review"

    @listen("needs_review")
    def review(self):
        self.state["approved"] = True

    @router(review, emit=["approved", "blocked"])
    def second_route(self):
        return "approved" if self.state["approved"] else "blocked"
```

This is useful when a first routing decision triggers work that computes a second routing decision. Keep label names semantic and unique enough to avoid accidental cross-listening.

## Structured State

```python
from pydantic import BaseModel, Field

class ApprovalState(BaseModel):
    draft: str = ""
    revision_count: int = 0
    approved: bool = False

class ApprovalFlow(Flow[ApprovalState]):
    @start()
    def create(self):
        self.state.draft = "Initial draft"

    @listen(create)
    def mark_reviewed(self):
        self.state.revision_count += 1
```

Choose structured state when:

- Flow methods are maintained by multiple people.
- You need validation, autocomplete, or durable persisted state shape.
- You will resume/fork state after human feedback or failures.

Choose dict state for small prototypes or highly dynamic state. Both forms receive an automatic `id`.

## State Inputs and Trigger Payloads

`kickoff(inputs={...})` updates state and can also inject `crewai_trigger_payload` into start methods that declare it:

```python
class TriggerFlow(Flow):
    @start()
    def begin(self, crewai_trigger_payload=None):
        self.state["payload"] = crewai_trigger_payload
```

Use explicit input keys for normal state values and reserve `crewai_trigger_payload` for trigger-style integrations.

## Persistence with `@persist`

Class-level persistence saves after every flow method:

```python
from crewai.flow.persistence import persist

@persist
class CounterFlow(Flow[CounterState]):
    @start()
    def step(self):
        self.state.counter += 1
```

Method-level persistence saves only selected methods:

```python
class SelectiveFlow(Flow):
    @start()
    def begin(self):
        self.state["count"] = 1

    @persist
    @listen(begin)
    def important_step(self):
        self.state["important"] = True
```

Resume vs fork:

| Need | Call |
| --- | --- |
| Continue the same persisted lineage | `kickoff(inputs={"id": state_id})` |
| Seed a new lineage from a previous persisted state | `kickoff(restore_from_state_id=state_id)` |

Do not pass `from_checkpoint` and `restore_from_state_id` together.

## Checkpointing

Checkpointing is event-driven and separate from `@persist`.

```python
from crewai import CheckpointConfig

flow = MyFlow(
    checkpoint=CheckpointConfig(
        location="./flow_cp",
        on_events=["method_execution_finished"],
        max_checkpoints=5,
    )
)
flow.kickoff()
```

Use checkpointing when you need to resume a run after failure and skip completed work. Use `@persist` when the flow state itself is an application state store across runs. For high-frequency checkpoint events, set `max_checkpoints` to prevent runaway storage.

## Plotting Before Execution

```python
flow = MyFlow()
flow.plot("my_flow_plot")
```

Plot early to catch:

- A router label with no visible listener.
- Missing branches after refactoring method names.
- Unexpected multiple starts.
- Human feedback outcomes that branch differently than intended.

Plotting does not require `kickoff()`, but importing a user module can still run top-level code. Keep Flow definitions side-effect-free at import time.

## Human Feedback Approval Loop

```python
from crewai.flow.flow import Flow, listen, or_, start
from crewai.flow.human_feedback import human_feedback, HumanFeedbackResult

class ContentFlow(Flow[ApprovalState]):
    @start()
    def generate(self):
        self.state.draft = "Draft v1"
        return self.state.draft

    @human_feedback(
        message="Approve or request changes?",
        emit=["approved", "needs_revision", "rejected"],
        llm="gpt-4o-mini",
        default_outcome="needs_revision",
    )
    @listen(or_(generate, "needs_revision"))
    def review(self):
        self.state.revision_count += 1
        return self.state.draft

    @listen("approved")
    def publish(self, result: HumanFeedbackResult):
        self.state.approved = True
        return result.output
```

Key points:

- A `@start()` method runs once; put the self-loop on a listener, not directly on the start.
- The review method listens to both the upstream trigger and the revision label with `or_(...)`.
- Always set a safe `default_outcome` when pressing Enter should not accidentally approve.
- Use `last_human_feedback` or `human_feedback_history` for audit trails and repeated reviews.

## Async Human Feedback

For Slack/webhook/UI approval, implement a `HumanFeedbackProvider` that raises `HumanFeedbackPending`. `kickoff()` returns the pending object; later, use `Flow.from_pending(flow_id).resume(feedback)` or `await resume_async(feedback)`. The framework automatically persists state when pausing.

Do not use async feedback providers in static validation. They are runtime integrations and may require app-specific callback storage.

## Conversational Flows

Conversational apps should treat every user line as a new flow run with the same session id:

```python
flow.handle_turn("Where is my order?", session_id=session_id)
flow.handle_turn("What about returns?", session_id=session_id)
```

Use `handle_turn()` for chat messages and `flow.chat()` for a local REPL. Do not call `kickoff(user_message=..., session_id=...)`; `kickoff()` takes `inputs`, not those keywords. For session state, use `ConversationState`/`ChatState`, append assistant responses with `append_assistant_message`, and call `finalize_session_traces()` when a deferred session ends.

## Combining Crews with Flows

Flows can call crews, direct LLMs, tools, or ordinary Python code. Keep graph control in the Flow and route agent/task design details to [core-runtime](../../core-runtime/SKILL.md). A common pattern is:

1. `@start()` validates inputs and initializes state.
2. `@listen(...)` calls one crew and stores `CrewOutput.raw` or structured output in state.
3. `@router(...)` branches on typed state fields.
4. `@listen("approved")` writes final output or triggers the next crew.

## Pattern Checklist

Before running a complex flow:

- Every `@router` has declared or annotated possible labels.
- Every non-terminal router label has a matching listener.
- Every `and_(...)` condition waits for methods that can actually run in the same execution path.
- State fields mutated by listeners exist in structured state or are initialized in dict state.
- Human feedback loops use listeners, not self-looping starts.
- Resume logic picks either `@persist` resume/fork or checkpoint restore, not both.
- Plot output path is writable and has or can receive a `.html` suffix.
