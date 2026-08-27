# Workflow Orchestration Patterns

Use these distilled patterns to build ADK 2.0 workflows from function nodes, graph edges, dynamic nodes, joins, and HITL/resume logic. They avoid LLM calls unless an explicit agent node is supplied by the caller.

## Minimal no-LLM workflow

Use pure functions when you need deterministic orchestration tests or diagnostics.

```python
from google.adk import START, Workflow


def normalize(node_input: str) -> str:
    return node_input.strip().lower()


def label(node_input: str) -> dict[str, str]:
    return {"label": node_input}


root_agent = Workflow(
    name="root_agent",
    edges=[(START, normalize, label)],
)
```

Checks:

- Every function name becomes a node name, so duplicate function names conflict unless the same node object is intentionally reused.
- Keep node names valid Python identifiers.
- Terminal output is the final node output. If multiple terminal nodes produce output, add a `JoinNode` and aggregator.

## Explicit FunctionNode configuration

Use `@node` when a function needs resume, retries, timeout, node-input dict binding, auth, or parallel worker behavior.

```python
from google.adk import Context, Event
from google.adk.workflow import RetryConfig, node


@node(
    name="parse_payload",
    retry_config=RetryConfig(max_attempts=3, jitter=0.0),
    timeout=10.0,
    parameter_binding="node_input",
)
def parse_payload(text: str, source: str) -> dict[str, str]:
    return {"text": text.strip(), "source": source}


@node(rerun_on_resume=True)
async def orchestrate(ctx: Context, node_input: dict[str, str]):
    parsed = await ctx.run_node(parse_payload, node_input=node_input)
    yield Event(output=parsed)
```

Checks:

- With `parameter_binding="node_input"`, pass a dict whose keys match non-context function parameters.
- With default state binding, name the input parameter exactly `node_input` to receive predecessor data.
- If a node calls `ctx.run_node`, decorate it with `rerun_on_resume=True`.

## Static sequence and state routing

Use state when later nodes need named values rather than only the immediate predecessor output.

```python
from google.adk import Context, Event, START, Workflow


def capture(ctx: Context, node_input: str):
    ctx.state["original_text"] = node_input
    return node_input.strip()


def enrich(ctx: Context, node_input: str):
    return Event(
        output={"normalized": node_input.lower()},
        state={"last_normalized": node_input.lower()},
    )


root_agent = Workflow(name="root_agent", edges=[(START, capture, enrich)])
```

Checks:

- `ctx.state[...] = ...` changes are persisted on the next emitted/final event.
- `Event(state={...})` is declarative and visible after the event is processed.
- `Event(output=...)` is internal workflow data; use `Event(message=...)` for visible UI text.

## Conditional routing

Use `Event(route=...)` or `ctx.route` to choose downstream edges.

```python
from google.adk import Event, START, Workflow
from google.adk.workflow import DEFAULT_ROUTE


def decide(node_input: dict[str, int]):
    score = node_input.get("score", 0)
    if score >= 80:
        return Event(output=node_input, route="approve")
    if score < 50:
        return Event(output=node_input, route="reject")
    return Event(output=node_input, route="review")


def approve(node_input):
    return {"status": "approved", "payload": node_input}


def reject(node_input):
    return {"status": "rejected", "payload": node_input}


def manual_review(node_input):
    return {"status": "needs_review", "payload": node_input}


root_agent = Workflow(
    name="root_agent",
    edges=[
        (START, decide, {
            "approve": approve,
            "reject": reject,
            DEFAULT_ROUTE: manual_review,
        }),
    ],
)
```

Checks:

- Conditional edge keys must be `str`, `int`, or `bool` route values.
- Use a single `DEFAULT_ROUTE` fallback per source node.
- If no route matches and there is no default, the branch ends.
- Loops must include a conditional edge; unconditional cycles are rejected.

## Static fan-out and fan-in

Use tuple fan-out plus `JoinNode` to aggregate parallel static branches.

```python
from typing import Any
from google.adk import Event, START, Workflow
from google.adk.workflow import JoinNode


def uppercase(node_input: str) -> str:
    return node_input.upper()


def length(node_input: str) -> int:
    return len(node_input)


join_results = JoinNode(name="join_results")


def aggregate(node_input: dict[str, Any]):
    return {
        "upper": node_input["uppercase"],
        "length": node_input["length"],
    }


root_agent = Workflow(
    name="root_agent",
    edges=[(START, (uppercase, length), join_results, aggregate)],
)
```

Checks:

- `JoinNode` output keys are predecessor node names.
- Every static predecessor wired into the join must complete; do not make a join wait for mutually exclusive conditional branches.
- If parallel terminal branches all emit output without a join, workflow finalization fails with multiple terminal outputs.

## Parallel worker over a list

Use `parallel_worker=True` when the same node should run independently over every item in a list.

```python
from google.adk import START, Workflow
from google.adk.workflow import node


@node(name="score_item", parallel_worker=True)
def score_item(node_input: str) -> dict[str, int]:
    return {"chars": len(node_input)}


def summarize(node_input: list[dict[str, int]]):
    return {"total_chars": sum(item["chars"] for item in node_input)}


root_agent = Workflow(name="root_agent", edges=[(START, score_item, summarize)])
```

Checks:

- Input is a list; non-list input is wrapped as one item.
- Output order matches input order.
- One item failure fails the worker and cancels pending work.
- The current helper has no public continue-on-error mode.

## Dynamic fan-out/fan-in

Use `ctx.run_node` when the number of children depends on runtime data. Use `asyncio.gather` for parallel dynamic children and `use_sub_branch=True` for branch isolation.

```python
import asyncio
from google.adk import Context, Event, START, Workflow
from google.adk.workflow import node


def summarize_topic(node_input: str) -> dict[str, str]:
    return {"topic": node_input, "summary": node_input.title()}


@node(rerun_on_resume=True)
async def orchestrator(ctx: Context, node_input: str):
    topics = [part.strip() for part in node_input.split(",") if part.strip()]
    tasks = [
        ctx.run_node(
            summarize_topic,
            node_input=topic,
            use_sub_branch=True,
            run_id=f"topic_{index}",
        )
        for index, topic in enumerate(topics)
    ]
    results = await asyncio.gather(*tasks)
    yield Event(output={"items": results})


root_agent = Workflow(name="root_agent", edges=[(START, orchestrator)])
```

Checks:

- The parent node has `rerun_on_resume=True`.
- Child run IDs are deterministic and contain non-numeric text.
- Side effects live inside child nodes, not before the `ctx.run_node` calls, so resume replay does not duplicate them.
- Await `ctx.run_node` calls directly or through `asyncio.gather`; do not wrap them in unsupervised `asyncio.create_task` calls.

## Dynamic child as parent output

Use `use_as_output=True` when a dynamic child should become the calling node's output without an additional parent output event.

```python
from google.adk import Context, START, Workflow
from google.adk.workflow import node


def compute(node_input: str):
    return {"computed": node_input}


@node(rerun_on_resume=True)
async def delegate_output(ctx: Context, node_input: str):
    await ctx.run_node(compute, node_input=node_input, use_as_output=True)


root_agent = Workflow(name="root_agent", edges=[(START, delegate_output)])
```

Checks:

- Use `use_as_output=True` only once in a parent node execution.
- Do not also yield a parent output after delegation.
- Inspect `Event.node_info.output_for` when debugging which ancestor a delegated output satisfied.

## Human-in-the-loop route loop

Use `RequestInput` to pause and `ctx.resume_inputs` to resume. Use stable interrupt IDs for repeatable debug logs.

```python
from google.adk import Context, Event, START, Workflow
from google.adk.events import RequestInput
from google.adk.workflow import node


def draft(node_input: str):
    return f"Draft response for: {node_input}"


@node(rerun_on_resume=True)
def review(ctx: Context, node_input: str):
    response = ctx.resume_inputs.get("review_decision")
    if response is None:
        yield RequestInput(
            interrupt_id="review_decision",
            message="Reply approve, reject, or provide revision feedback.",
            payload={"draft": node_input},
        )
        return

    if response == "approve":
        yield Event(output=node_input, route="approved")
    elif response == "reject":
        yield Event(route="rejected")
    else:
        yield Event(state={"feedback": response}, route="revise")


def send(node_input: str):
    return {"sent": node_input}


def rejected():
    return {"status": "rejected"}


root_agent = Workflow(
    name="root_agent",
    edges=[
        (START, draft, review),
        (review, {"approved": send, "rejected": rejected, "revise": draft}),
    ],
)
```

Checks:

- `review` must have `rerun_on_resume=True` because it handles a resume path.
- On resume, the node sees `ctx.resume_inputs[interrupt_id]`.
- Loops should route conditionally; unconditional loops are invalid.
- If the node yields a route with no output, downstream nodes receive `None` unless they pull needed data from state.

## Retry and timeout node

Use retry for transient failures and timeout for runaway nodes.

```python
from google.adk import START, Workflow
from google.adk.workflow import RetryConfig, node


@node(
    retry_config=RetryConfig(
        max_attempts=3,
        initial_delay=0.5,
        backoff_factor=2.0,
        jitter=0.0,
        exceptions=[ConnectionError, "TimeoutError"],
    ),
    timeout=20.0,
)
async def fetch_item(node_input: str):
    return {"item": node_input}


root_agent = Workflow(name="root_agent", edges=[(START, fetch_item)])
```

Checks:

- `max_attempts` includes the first try.
- Retry attempt count is not persisted across resume.
- Retrying a non-idempotent operation can duplicate side effects; move irreversible effects behind explicit approval or dedupe keys.

## State schema and typed IO

Use Pydantic models to validate workflow state and node input/output contracts.

```python
from pydantic import BaseModel
from google.adk import START, Workflow


class StateModel(BaseModel):
    topic: str


class Payload(BaseModel):
    text: str


def extract(node_input: Payload) -> Payload:
    return Payload(text=node_input.text.strip())


root_agent = Workflow(
    name="root_agent",
    state_schema=StateModel,
    edges=[(START, extract)],
)
```

Checks:

- `state_schema` validates unprefixed state keys; prefixed keys such as `app:`, `user:`, and `temp:` bypass validation.
- Static edge validation checks matching `output_schema` and `input_schema` when both are set.
- A `FunctionNode` using state-bound parameters must declare non-context parameter names in `state_schema` if a workflow state schema is present.

## Event inspection checklist

When a workflow behaves unexpectedly, inspect emitted events for:

- `event.author`: Workflow sets child event author to the workflow name.
- `event.node_info.path`: Which node and run ID emitted the event.
- `event.node_info.output_for`: Whether a dynamic child output delegated to an ancestor.
- `event.output`: Internal data passed downstream.
- `event.content` / `event.message`: User-visible text.
- `event.actions.state_delta`: Persisted state changes.
- `event.actions.route`: Conditional route value.
- `event.long_running_tool_ids`: Pending interrupt IDs.

## Hard case: dynamic fan-out, join, typed state, HITL resume

For a request like “build a fan-out/fan-in workflow with dynamic nodes and a join node that preserves typed state and resumes after human input,” combine these patterns:

1. Use a static `Workflow` with `START -> seed_state -> dynamic_orchestrator -> review` or `START -> static fan-out -> JoinNode -> dynamic_orchestrator -> review` depending on whether fan-out cardinality is known at construction time.
2. Put typed session keys in `state_schema`; keep item-level results in node outputs, not only in state.
3. For static fan-out, aggregate with `JoinNode` before a single terminal output.
4. For dynamic fan-out, use an orchestrator decorated `@node(rerun_on_resume=True)` and `await asyncio.gather(*ctx.run_node(..., use_sub_branch=True, run_id=f"item_{i}"))`.
5. Use `RequestInput` in the review node, and on resume read `ctx.resume_inputs[interrupt_id]` before routing.
6. Keep side effects in child nodes; completed children are replayed from event history while parent orchestration code reruns.

## Hard case: resumed workflow reruns or skips a node

For a request like “why does a resumed workflow rerun or skip a node,” reason from these facts:

1. `Workflow.rerun_on_resume=True`, so the scheduler reconstructs prior child state from session events and seeds pending nodes.
2. Leaf nodes with `rerun_on_resume=False` can complete from resume inputs rather than re-executing; nodes with `rerun_on_resume=True` re-execute and receive `ctx.resume_inputs`.
3. Dynamic children are deduplicated by full `node_path` and deterministic run ID/name; if the path changed, the scheduler treats the child as fresh.
4. Completed static nodes may be intercepted from recovered events rather than run again.
5. Inspect `Event.node_info.path`, `run_id`, `output_for`, `long_running_tool_ids`, and matching function responses to decide whether the node was completed, waiting, replayed, or freshly scheduled.
