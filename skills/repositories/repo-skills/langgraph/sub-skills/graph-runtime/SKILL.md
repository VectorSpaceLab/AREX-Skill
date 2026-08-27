---
name: graph-runtime
description: "Build, compile, invoke, stream, debug, interrupt, and route custom
  LangGraph StateGraph/Pregel workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Graph Runtime

Use this sub-skill when an agent needs to implement or repair custom LangGraph runtime logic: `StateGraph` construction, node wiring, conditional routing, reducers, compiled graph invocation, streaming, debug output, interrupts, resume commands, subgraphs, and low-level `Pregel` channel execution concerns.

## When To Use

- Build a custom `StateGraph` or compiled graph instead of using a prebuilt agent.
- Convert linear workflow code into graph nodes, edges, conditional branches, or subgraphs.
- Add reducer state with `typing_extensions.Annotated` so concurrent node updates merge safely.
- Invoke or stream a compiled graph with sync or async APIs.
- Debug missing edges, unknown nodes, recursion-limit failures, invalid updates, interrupts, or stream output shapes.
- Add human-in-the-loop pauses using `interrupt()` and resume with `Command(resume=...)`.
- Route with `Command(goto=...)`, `Send(...)`, `add_conditional_edges(...)`, or `set_conditional_entry_point(...)`.

For prebuilt `create_react_agent` workflows, route to [prebuilt-agents](../prebuilt-agents/SKILL.md). For checkpoint saver choices, persistent stores, thread history, and production durability, route to [persistence](../persistence/SKILL.md). For server deployment and config files, route to [cli-deployment](../cli-deployment/SKILL.md). For REST/SDK calls against a deployed graph, route to [sdk-clients](../sdk-clients/SKILL.md).

## Core Runtime Pattern

1. Define a state schema with `TypedDict`, dataclass, or Pydantic model.
2. Use `Annotated[field_type, reducer]` on state fields that multiple nodes may update in one step.
3. Create a `StateGraph(state_schema, context_schema=None, input_schema=None, output_schema=None)` builder.
4. Add nodes with `add_node(name, callable)` or `add_sequence([...])`.
5. Add edges with `add_edge(START, node)`, `add_edge(node, END)`, `set_entry_point(node)`, or `set_finish_point(node)`.
6. Add routing with `add_conditional_edges(source, route_fn, path_map=...)` when the next node depends on state.
7. Call `compile(...)` before `invoke`, `stream`, `ainvoke`, or `astream`; the builder itself is not executable.
8. Validate behavior with the bundled smoke script: `python skills/langgraph/sub-skills/graph-runtime/scripts/smoke_state_graph.py`.

Minimal example:

```python
from typing_extensions import TypedDict
from langgraph.graph import END, START, StateGraph

class State(TypedDict):
    value: int

def inc(state: State) -> State:
    return {"value": state["value"] + 1}

builder = StateGraph(State)
builder.add_node("inc", inc)
builder.add_edge(START, "inc")
builder.add_edge("inc", END)
graph = builder.compile()
assert graph.invoke({"value": 1}) == {"value": 2}
```

## Builder APIs To Reach For

- `StateGraph(...)`: graph builder for shared-state node workflows; accepts `context_schema`, `input_schema`, and `output_schema`.
- `add_node(...)`: adds a callable or runnable; node names must be unique and cannot be `START` or `END`.
- `add_edge(start, end)`: adds fixed routing; list starts wait for all named nodes before the target runs.
- `add_conditional_edges(source, path, path_map=None)`: routes after a node based on a callable result.
- `set_entry_point(node)` and `set_finish_point(node)`: convenience wrappers for `START` and `END` edges.
- `add_sequence(nodes)`: creates a linear chain from callables or `(name, callable)` pairs.
- `set_node_defaults(...)`: applies default retry, cache, timeout, or error-handler policies at compile time.
- `compile(checkpointer=None, cache=None, store=None, interrupt_before=None, interrupt_after=None, debug=False, name=None)`: returns the executable compiled graph.

See [API Reference](references/api-reference.md) for parameter details, deprecations, and output shapes.

## Invocation And Streaming

- Use `graph.invoke(input, config=None, *, context=None, stream_mode="values", interrupt_before=None, interrupt_after=None, durability=None)` for sync final output.
- Use `await graph.ainvoke(...)` when any node or surrounding application is async.
- Use `graph.stream(input, stream_mode="updates")` or `async for chunk in graph.astream(...)` for stepwise output.
- Valid stream modes include `values`, `updates`, `messages`, `custom`, `checkpoints`, `tasks`, and `debug`.
- Passing a list such as `stream_mode=["updates", "values"]` yields mode-tagged chunks.
- Use `print_mode` only for console debugging; it does not change returned data.
- Use `subgraphs=True` when you need child graph events included with namespace paths.
- Use `version="v2"` for typed stream parts from `stream`/`astream`; use `stream_events(..., version="v3")` when working with event transformers.

See [Workflows](references/workflows.md) for reducer, conditional routing, interrupt/resume, subgraph, low-level Pregel, and streaming recipes.

## Interrupts And Resume

- Add a checkpointer at compile time when state must persist across interrupts or later resumes.
- Invoke checkpointed graphs with `config={"configurable": {"thread_id": "unique-run-id"}}`.
- Inside a node, call `interrupt(value)` to pause and surface a resumable request.
- Resume with `graph.invoke(Command(resume=value), config)` or stream the same command.
- Multiple simultaneous interrupts may require a resume map keyed by interrupt id.
- Use `interrupt_before=["node"]` or `interrupt_after=["node"]` at compile or call time to pause around known nodes.

Checkpoint and thread management belongs in [persistence](../persistence/SKILL.md), but this sub-skill covers how runtime code calls interrupts and commands.

## Debugging Checklist

- If `invoke` is missing, confirm you called `compile()` and are not executing the builder.
- If compilation fails with missing entrypoint, add an edge from `START` or call `set_entry_point`.
- If an edge target is unknown, add the node before compiling or fix the path map target.
- If multiple nodes write the same key, add a reducer via `Annotated` or ensure only one update reaches that key per step.
- If routing visualizations look too broad, add `path_map` or annotate the routing function return type with `Literal[...]`.
- If a checkpointed interrupt cannot resume, reuse the same `thread_id` and pass `Command(resume=...)` as the input.
- If async code hangs or errors, use `ainvoke`/`astream` and avoid blocking sync work in async nodes.
- If stream output shape surprises you, check `stream_mode`, whether a list of modes was supplied, whether `subgraphs=True` is enabled, and whether `version="v2"` is enabled.
- If low-level `Pregel` validation fails, verify every `input_channels`, `output_channels`, and `stream_channels` entry exists and at least one input channel is subscribed by a node.

See [Troubleshooting](references/troubleshooting.md) for error patterns and fixes.

## Bundled Script

- [scripts/smoke_state_graph.py](scripts/smoke_state_graph.py): self-contained smoke check that builds a reducer-backed conditional graph, compiles it, invokes it, and verifies stream output.

Run:

```bash
python skills/langgraph/sub-skills/graph-runtime/scripts/smoke_state_graph.py --help
python skills/langgraph/sub-skills/graph-runtime/scripts/smoke_state_graph.py
python skills/langgraph/sub-skills/graph-runtime/scripts/smoke_state_graph.py --start 3 --limit 5 --json
```

Expected default result includes a final state with `value` equal to `3` and a history showing routed node execution.

## Evidence And Scope Notes

This guidance is distilled from LangGraph state graph source, runtime types, Pregel execution APIs, runtime tests for state, interruption, Pregel behavior, and stream events, plus public README claims about LangGraph as a durable stateful orchestration framework.

Runtime content intentionally excludes maintainer CI, release tooling, benchmark-only flows, expensive notebooks, and original checkout dependencies. The subgraph notebook evidence was only a moved-document pointer, so subgraph guidance here is based on runtime source/tests rather than a bundled notebook adaptation.
