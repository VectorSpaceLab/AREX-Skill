# Graph Runtime API Reference

This reference summarizes the runtime APIs future agents most often need when building custom LangGraph workflows.

## Imports

```python
from typing_extensions import Annotated, Literal, TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send, interrupt
```

Use `typing_extensions` for portable `TypedDict`, `Annotated`, and `Literal` support across Python versions.

## StateGraph Constructor

`StateGraph(state_schema, context_schema=None, *, input_schema=None, output_schema=None, **deprecated_kwargs)` creates a builder.

- `state_schema`: shared graph state type. Node functions typically accept this state and return a partial update.
- `context_schema`: run-scoped immutable context type available through `Runtime`; prefer this over deprecated `config_schema`.
- `input_schema`: input shape accepted at `START`; defaults to `state_schema`.
- `output_schema`: shape returned by graph output; defaults to `state_schema`.
- Deprecated kwargs: `config_schema`, `input`, and `output` still warn and should be replaced with `context_schema`, `input_schema`, and `output_schema`.

A `StateGraph` is only a builder. Always call `compile()` before execution.

## State Updates And Reducers

Node signature convention: `State -> Partial[State]`.

```python
def node(state: State) -> dict:
    return {"field": new_value}
```

If two or more nodes can update the same state key in one step, add a reducer:

```python
def append_items(left: list[str], right: list[str] | None) -> list[str]:
    return left + (right or [])

class State(TypedDict):
    items: Annotated[list[str], append_items]
```

Reducers receive the current value and the new value and return the merged value. Without a reducer, conflicting writes to a single key can raise invalid update errors.

## Builder Methods

### `add_node`

`add_node(node, action=None, *, defer=False, metadata=None, input_schema=None, retry_policy=None, cache_policy=None, error_handler=None, destinations=None, timeout=None)` adds a runtime node.

- If `node` is a callable, its function/class name becomes the node name.
- If `node` is a string, `action` supplies the callable or runnable.
- `input_schema` can narrow a node's expected input shape.
- `destinations` documents possible `Command` destinations for rendering; it does not drive execution.
- `timeout` supports async-node cancellation; sync nodes cannot be safely cancelled in process.
- Node names must be unique, cannot be `START` or `END`, and cannot contain reserved namespace separators.

### `add_edge`

`add_edge(start_key, end_key)` adds fixed routing.

- `add_edge(START, "node")` sets an entry edge.
- `add_edge("node", END)` marks completion after a node.
- A list start such as `add_edge(["a", "b"], "join")` waits for all start nodes before running `join`.
- `END` cannot be a start node; `START` cannot be an end node.

### `add_conditional_edges`

`add_conditional_edges(source, path, path_map=None)` routes after `source`.

- `path` returns a destination key, a sequence of destination keys, or `END`.
- `path_map` maps symbolic route labels to node names.
- Without `path_map` or a `Literal[...]` return annotation, graph visualization may assume the branch can target any node.
- Unknown branch targets fail validation during compile.

### `set_entry_point`, `set_conditional_entry_point`, `set_finish_point`

These are convenience methods over `START`/`END` edges:

- `set_entry_point("node")` equals `add_edge(START, "node")`.
- `set_conditional_entry_point(route, path_map)` routes immediately from `START`.
- `set_finish_point("node")` equals `add_edge("node", END)`.

### `add_sequence`

`add_sequence(nodes)` adds a linear chain from callables or `(name, callable)` pairs. Use it for simple pipelines, then add explicit conditional edges only where flow branches.

### `set_node_defaults`

`set_node_defaults(retry_policy=None, cache_policy=None, error_handler=None, timeout=None)` applies default policies at compile time.

- Per-node values override defaults.
- Retry and timeout defaults apply to regular and error-handler nodes.
- Cache and error-handler defaults apply only to regular nodes.
- Defaults are not inherited automatically by subgraphs.

## Compile

`compile(checkpointer=None, *, cache=None, store=None, interrupt_before=None, interrupt_after=None, debug=False, name=None, transformers=None)` returns `CompiledStateGraph`.

- `checkpointer`: `None`, `False`, `True`, or a checkpoint saver. Use a saver for pause/resume and state history.
- `cache`: optional cache backend for cached node execution.
- `store`: optional store available through runtime context for memory-like access.
- `interrupt_before` / `interrupt_after`: node names or `"*"` to pause around execution.
- `debug`: prints debug-oriented stream information.
- `name`: graph name used in tracing and display.
- `transformers`: stream event v3 transformers; advanced users can append custom factories.

When a checkpointer is enabled, invoke with a stable thread id:

```python
config = {"configurable": {"thread_id": "ticket-123"}}
graph.invoke(input_state, config)
```

## Compiled Graph Execution

Compiled graphs implement Runnable-style execution.

### `invoke`

`invoke(input, config=None, *, context=None, stream_mode="values", output_keys=None, interrupt_before=None, interrupt_after=None, durability=None, **kwargs)` returns final output for `stream_mode="values"`; for other modes it returns collected chunks.

### `ainvoke`

`await ainvoke(...)` is the async equivalent. Use it from async applications or when nodes are async.

### `stream`

`stream(input, config=None, *, context=None, stream_mode=None, print_mode=(), output_keys=None, interrupt_before=None, interrupt_after=None, durability=None, subgraphs=False, debug=None, version="v1")` yields stepwise chunks.

### `astream`

`async for chunk in graph.astream(...)` is the async streaming equivalent.

## Stream Modes

- `values`: full state after each step, including interrupts.
- `updates`: node/task names and updates after each step; multiple concurrent updates emit separately.
- `custom`: values emitted through an injected `StreamWriter`.
- `messages`: LLM message chunks plus metadata such as node and step info.
- `checkpoints`: checkpoint payloads equivalent to state snapshots.
- `tasks`: task start and task result events.
- `debug`: checkpoint and task-level debug events.

When passing multiple modes, outputs are tuples tagged by mode. With `subgraphs=True`, outputs include namespace tuples describing where child graph events originated.

## v2 Typed Output Shapes

With `version="v2"`, `stream`/`astream` and non-`values` `invoke`/`ainvoke` output use discriminated dictionaries with a `type`, `ns`, and `data` field. `invoke`/`ainvoke` with `stream_mode="values"` return a `GraphOutput` container with `.value` and `.interrupts` for typed final output plus interrupt metadata.

## Runtime Context

For immutable run-scoped data, define `context_schema` and pass `context={...}` at invocation. Nodes that accept `Runtime[Context]` can read `runtime.context`, use `runtime.store`, call `runtime.stream_writer`, or heartbeat for timeout-sensitive async work.

## Low-Level Pregel

Most custom workflows should start with `StateGraph`; it compiles into a Pregel-backed runnable. Reach for low-level `Pregel` only when a task must model explicit channels and subscriptions.

- Import `Pregel` and `NodeBuilder` from `langgraph.pregel`.
- Define channels with `langgraph.channels` classes such as `LastValue`, `EphemeralValue`, `Topic`, or `BinaryOperatorAggregate`.
- Build nodes with `NodeBuilder().subscribe_only(...)`, `subscribe_to(...)`, `do(...)`, and `write_to(...)`.
- Construct `Pregel(nodes=..., channels=..., input_channels=..., output_channels=..., stream_channels=...)` and then call the same `invoke`, `stream`, `ainvoke`, and `astream` runtime methods.
- `LastValue` and guarded `EphemeralValue` channels reject multiple writes in the same step; use `BinaryOperatorAggregate` or a topic-style channel when concurrent writes must merge.
- Validation requires input, output, and stream channels to exist, and at least one input channel must be subscribed by a node.

## Routing Primitives

### `Command`

Use `Command(update=..., goto=..., resume=..., graph=...)` when a node or resume call needs to update state and control routing. Common patterns:

```python
return Command(update={"status": "approved"}, goto="next")
graph.invoke(Command(resume="yes"), config)
```

`Command.PARENT` lets a subgraph route to a parent graph destination when explicitly designed for that flow.

### `Send`

Use `Send(node, arg)` for fan-out/map-like routing where a routing function or command sends different inputs to the same or different nodes.

```python
return [Send("worker", {"item": item}) for item in state["items"]]
```

Reducers are usually required on the keys workers update.

### `interrupt`

`interrupt(value)` pauses execution and surfaces an interrupt payload. Resume by invoking or streaming with `Command(resume=...)` using the same checkpoint thread config.
