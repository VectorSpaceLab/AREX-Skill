# Workflow Orchestration API Reference

This reference captures the ADK 2.0 workflow API surface needed to build graph workflows without reopening repository source. Examples assume `google-adk` 2.3.0, Python 3.10+, and import root `google.adk`.

## Imports

```python
from google.adk import Context, Event, START, Workflow
from google.adk.events import RequestInput
from google.adk.events.event import NodeInfo
from google.adk.workflow import DEFAULT_ROUTE, Edge, FunctionNode, JoinNode, RetryConfig, node
```

Use `google.adk.workflow` when you need graph-specific wrappers. `START` is a sentinel node and may also be written as the string `"START"` in edge tuples.

## Workflow

`Workflow` is a `BaseNode` that schedules a graph of child nodes.

Core fields:

- `name: str`: Required unique node name; names must be valid Python identifiers.
- `edges: list[EdgeItem]`: Graph structure. Items may be explicit `Edge` objects or chain tuples such as `(START, step_a, step_b)`.
- `max_concurrency: int | None`: Limits concurrently running static graph nodes. Dynamic nodes spawned by `ctx.run_node()` are excluded to avoid deadlock.
- `graph: Graph | None`: Compiled graph; normally let `Workflow` build this from `edges`.
- Inherited node fields include `description`, `rerun_on_resume`, `wait_for_output`, `retry_config`, `timeout`, `input_schema`, `output_schema`, and `state_schema`.

Important defaults and behavior:

- `Workflow.rerun_on_resume` defaults to `True` because workflow orchestration must replay/resume children after interrupts.
- Terminal node outputs determine workflow output. A workflow may have at most one terminal output; use a `JoinNode` or downstream aggregator when parallel branches all produce values.
- The graph is validated on construction for duplicate names, missing or invalid `START`, unreachable nodes, duplicate edges, default-route misuse, unconditional cycles, schema mismatches, and unsupported chat-agent wiring after non-`START` nodes.
- Static graph nodes that are `LlmAgent(mode="task")` are rejected. Use task agents as delegated sub-agents or dispatch them dynamically from a custom node instead.

## BaseNode and Node

`BaseNode` is the primitive execution contract. Most custom nodes either use a function with `@node`/`FunctionNode` or subclass `Node` and implement `run_node_impl()`.

Inherited configuration fields:

| Field | Purpose |
| --- | --- |
| `name` | Unique node identifier; must be a Python identifier. |
| `description` | Human-readable summary. |
| `rerun_on_resume` | Re-execute the node on resume; required when the node calls `ctx.run_node()`. |
| `wait_for_output` | Keep the node `WAITING` until it emits output or route. Useful for barriers, but can deadlock if no later trigger produces output/route. |
| `retry_config` | Retry policy for failures and timeouts. |
| `timeout` | Maximum node execution time in seconds. |
| `input_schema` | Optional input coercion/validation. |
| `output_schema` | Optional output coercion/validation. |
| `state_schema` | Optional Pydantic schema for allowed session state keys. |

Execution contract:

- `run()` is final and normalizes yielded values; do not override it.
- `_run_impl(ctx=..., node_input=...)` is the subclass extension point.
- `None` yields are skipped.
- A raw value becomes `Event(output=value)`.
- An `Event` passes through and may contain output, route, message/content, state delta, or interrupt IDs.
- A `RequestInput` becomes a workflow HITL interrupt event.
- A node may produce at most one output per execution. A second output raises an error.

## `node` decorator and `FunctionNode`

`@node` wraps a callable as a `FunctionNode`. It can also wrap an existing node-like object with overrides.

Common decorator parameters:

```python
@node(
    name="step_name",
    rerun_on_resume=True,
    retry_config=RetryConfig(max_attempts=3),
    timeout=30.0,
    parallel_worker=False,
    parameter_binding="state",
)
def step(ctx: Context, node_input: str) -> str:
    return node_input.upper()
```

`FunctionNode` constructor parameters:

- `func`: Sync function, async function, sync generator, or async generator.
- `name`: Optional override; defaults to `func.__name__`.
- `rerun_on_resume`: Defaults to `False`; set `True` when the function requests HITL input and handles resume itself, or when it calls `ctx.run_node()`.
- `retry_config`, `timeout`: Per-node reliability controls.
- `auth_config`: Requests user authentication before running; requires `rerun_on_resume=True`.
- `parameter_binding`: `"state"` by default; `"node_input"` binds dict keys from `node_input` to function parameters.
- `state_schema`: Optional Pydantic model for state validation.

Parameter binding rules:

- A parameter named `ctx` or type-hinted as `Context` receives the workflow context.
- A parameter named `node_input` receives the predecessor output or `ctx.run_node(..., node_input=value)` payload.
- With default `parameter_binding="state"`, other parameter names are looked up in `ctx.state`.
- With `parameter_binding="node_input"`, non-context parameters are looked up in the `node_input` dict.
- Type hints may coerce `dict` to Pydantic models and `types.Content` to `str` when the annotation expects text.

## Graph and edges

Edge-related types:

- `Edge(from_node=..., to_node=..., route=None)`: Explicit edge.
- `DEFAULT_ROUTE`: Fallback route marker for conditional routing.
- `RouteValue`: `bool | int | str`.
- `NodeLike`: `BaseNode`, `BaseTool`, callable, or `"START"`.

Supported edge syntax:

```python
# Sequential
edges=[(START, step_a, step_b)]

# Static fan-out
edges=[(START, step_a, (step_b, step_c))]

# Conditional route map
edges=[(START, router, {"approve": approve, "reject": reject, DEFAULT_ROUTE: fallback})]

# Explicit edges
edges=[
    Edge(from_node=START, to_node=router),
    Edge(from_node=router, to_node=approve, route="approve"),
]
```

Routing values are read from `Event(route=...)` or `ctx.route`. A list of routes may match multiple edges. If a node has conditional edges and none match, only the default edge runs if one is configured; otherwise the branch ends with a warning.

## JoinNode

`JoinNode(name="join_name")` waits for all static predecessor nodes that point to it, then emits a dictionary keyed by predecessor node name.

Use it after static fan-out:

```python
join_results = JoinNode(name="join_results")
workflow = Workflow(
    name="root_agent",
    edges=[(START, (extract_a, extract_b), join_results, aggregate)],
)
```

Notes:

- A `JoinNode` requires every predecessor declared in the graph to execute and complete.
- If a predecessor is behind a conditional path that is not taken, the join may wait forever.
- `input_schema` on `JoinNode` validates each predecessor output, not the aggregate dictionary as a whole.
- Its output is always a dict like `{"extract_a": ..., "extract_b": ...}`.

## Parallel worker

Set `parallel_worker=True` on `@node` or on compatible node/agent construction to wrap one worker over a list input.

```python
@node(name="score_one", parallel_worker=True)
def score_one(node_input: str) -> dict[str, int]:
    return {"length": len(node_input)}
```

Behavior:

- Non-list input is treated as a one-item list.
- Output is a list in the same order as the input items.
- Each item runs through `ctx.run_node(..., use_sub_branch=True)` under the hood.
- Fail-fast: one item failure cancels pending item tasks and fails the worker.

## Dynamic nodes through `Context.run_node`

Use dynamic nodes when the child list or control flow depends on runtime data.

Current signature includes:

```python
await ctx.run_node(
    node,
    node_input=None,
    use_as_output=False,
    run_id=None,
    use_sub_branch=False,
    override_branch=None,
    override_isolation_scope=None,
    raise_on_wait=False,
)
```

Rules:

- The calling node must have `rerun_on_resume=True`.
- Always await `ctx.run_node()` directly or through `asyncio.gather`; do not fire-and-forget it.
- Use deterministic child names/run IDs. Completed dynamic nodes are deduplicated by full node path.
- Explicit `run_id` must contain at least one non-numeric character; pure numeric IDs collide with framework-generated IDs.
- Set `use_sub_branch=True` for parallel dynamic children so their events and context remain isolated.
- Set `use_as_output=True` only once per parent execution; it makes the child output count as the parent output.
- Set `raise_on_wait=True` when a child with `wait_for_output=True` should leave the parent waiting instead of completing with no output.

## Event and NodeInfo

`Event` carries content, workflow output, state deltas, route decisions, and workflow metadata.

Useful constructor conveniences:

```python
Event(message="visible to UI")
Event(output={"score": 1})
Event(state={"score": 1})
Event(route="approved")
Event(long_running_tool_ids={"human_review"})
```

Important fields:

- `content` / `message`: User-visible content. `message` is a convenience alias.
- `output`: Internal data passed to downstream workflow nodes.
- `actions.state_delta`: Session state changes, populated by `Event(state=...)` or tracked `ctx.state` mutation.
- `actions.route`: Route value, populated by `Event(route=...)`.
- `long_running_tool_ids`: Interrupt IDs used for HITL and long-running tool pauses.
- `node_info: NodeInfo`: Framework-populated metadata.

`NodeInfo` fields:

- `path`: Full workflow node path, including run IDs such as `root/step@1/child@1`.
- `output_for`: Ancestor paths whose output this event represents when output is delegated.
- `message_as_output`: Marks content as node output when applicable.
- `run_id`, `parent_run_id`, and `name` are derived from `path`.

Do not manually set `node_info` or internal isolation fields in normal app logic; inspect them for debugging event paths and resume behavior.

## RequestInput and HITL

`RequestInput` pauses a workflow and asks the client/user for structured input.

Fields:

- `interrupt_id`: Identifier that the resume `FunctionResponse` must match.
- `message`: Prompt shown to the user.
- `payload`: Optional payload for the client.
- `response_schema`: Optional Python type, Pydantic model, generic alias, or raw JSON schema for expected response.

Pattern:

```python
@node(rerun_on_resume=True)
def human_review(ctx: Context, draft: str):
    response = ctx.resume_inputs.get("human_review")
    if response is None:
        yield RequestInput(
            interrupt_id="human_review",
            message="Approve, reject, or provide feedback.",
        )
        return
    yield Event(route="approved" if response == "approve" else "revise")
```

Clients resume by sending a matching function response for the interrupt ID. Runner/session details are handled by runtime services; this sub-skill focuses on node behavior and event interpretation.

## RetryConfig and timeout

`RetryConfig` fields:

- `max_attempts: int | None`: Attempts including the first; omitted defaults internally to 5, while `0` or `1` means no retries.
- `initial_delay: float | None`: First retry delay; omitted defaults internally to 1.0 seconds.
- `max_delay: float | None`: Delay cap; omitted defaults internally to 60.0 seconds.
- `backoff_factor: float | None`: Exponential multiplier; omitted defaults internally to 2.0.
- `jitter: float | None`: Randomness factor; use `0.0` for deterministic tests.
- `exceptions: list[str | type[BaseException]] | None`: Exception names/classes to retry; `None` means retry all exceptions.

Apply it to `@node`, `FunctionNode`, or other node-like wrappers. `timeout` integrates with retry: a timed-out node can be retried if the retry policy matches the timeout exception.

Retry limitations:

- Retry attempt count is in-memory for the current execution and is not persisted across HITL/resume or process restart.
- If retries exhaust, the node fails and the workflow stops unless surrounding logic routes or handles the failure elsewhere.

## Runner handoff

A `Workflow` is an agent-like root that can be registered in an ADK app and executed by a `Runner`. When constructing a runnable invocation outside the CLI, `Runner.run` requires keyword arguments `user_id`, `session_id`, and `new_message`, with optional `state_delta` and `run_config`. Session creation/persistence and app wiring are covered by `runtime-services` and CLI configuration guidance.
