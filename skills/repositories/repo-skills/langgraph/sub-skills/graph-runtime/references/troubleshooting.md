# Graph Runtime Troubleshooting

Use this guide to diagnose custom `StateGraph` and compiled graph runtime failures.

## Install And Import Failures

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'langgraph'` | Package is not installed in the active Python environment. | Install `langgraph` in the environment running the script and rerun `python -c "import langgraph"`. |
| `ImportError` for `typing_extensions` or `langchain_core` | Incomplete or mismatched dependency install. | Reinstall/upgrade the package set with the package manager used by the project. |
| Import works in shell but not in app | App uses a different interpreter or environment. | Print `sys.executable` in the app, align the environment, and avoid relying on shell activation alone. |
| Optional saver/store imports fail | Persistence backend extras are not installed. | Use an in-memory saver for local runtime smoke checks or follow [persistence](../../persistence/SKILL.md) for backend-specific installation. |

## Builder And Compile Errors

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `StateGraph` has no `invoke` or `stream` | Trying to run the builder. | Call `compiled = builder.compile()` and run `compiled.invoke(...)`. |
| `Graph must have an entrypoint` | No edge from `START`. | Add `builder.add_edge(START, "node")` or `builder.set_entry_point("node")`. |
| `Found edge starting at unknown node` | Edge source is misspelled or node was not added. | Add the source node before compile or correct the edge. |
| `Found edge ending at unknown node` | Edge/branch target is missing. | Add the target node, use `END`, or fix `path_map`. |
| `Need to add_node ... first` | `add_edge` list-start validation found a missing node. | Add all join predecessor nodes before the waiting edge. |
| `END cannot be a start node` or `START cannot be an end node` | Sentinel misuse. | Use `START` only as an entry source and `END` only as a terminal target. |
| Duplicate node name error | Two callables infer the same name or a name is reused. | Pass explicit unique names, especially for lambdas/wrapped functions. |
| Branch visualization shows too many edges | Missing `path_map` or route return type hints. | Add `path_map` or return `Literal["a", "b", "__end__"]`. |

## Invalid State And Data Updates

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Invalid update error on a key | Multiple nodes wrote the same key without a reducer. | Use `Annotated[field_type, reducer]` or redesign so one node writes the key per step. |
| Node output ignored or malformed | Node returned a non-partial-state shape. | Return a dict/model matching state keys, or use `Command(update=...)` when routing. |
| Input schema validation surprises | `input_schema` differs from `state_schema`. | Check constructor and node-level `input_schema` choices; pass the expected input shape at `START`. |
| Reducer receives `None` | Initial value or update may be absent. | Make reducers tolerate `None` or ensure defaults are present in input. |
| Context values missing | Context was put in config instead of `context`. | Prefer `context_schema` and invoke with `context={...}` for run-scoped immutable data. |

## Invocation, Async, And Streaming Confusion

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Async node warnings or loop errors | Sync API used in async application. | Use `await graph.ainvoke(...)` or `async for ... in graph.astream(...)`. |
| Stream chunks are tuples instead of dicts | Multiple stream modes or subgraph streaming enabled. | Check if `stream_mode` is a list or `subgraphs=True`; unpack `(mode, data)` or `(namespace, mode, data)`. |
| `invoke` returns a list of chunks | `stream_mode` was not `values`. | Use `stream_mode="values"` for final output or call `stream` intentionally. |
| No custom stream output | Node did not request/use a `StreamWriter` or stream mode is not `custom`. | Accept the injected writer and run with `stream_mode="custom"` or a list containing it. |
| Messages stream metadata missing expected keys | Runnable/model does not emit message events or wrong stream version. | Verify model callbacks and inspect `stream_mode="debug"` or v2/v3 event APIs. |

## Interrupt And Resume Failures

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Interrupt appears but resume starts over | No checkpointer or different thread config. | Compile with a saver and reuse `config={"configurable": {"thread_id": "..."}}`. |
| Resume has no effect | Resume value was passed as normal state. | Invoke with `Command(resume=value)` as the input. |
| Error about missing configurable keys | Checkpointed run lacks `thread_id`. | Add a stable `thread_id` under `configurable`. |
| Wrong paused run resumes | Thread id reused across independent users/tasks. | Generate unique thread ids per independent run and keep them stable only for that run. |
| Multiple interrupts reject a single resume | Several interrupt ids are pending. | Inspect interrupts and pass a resume map keyed by interrupt id when required. |
| Static interrupt node not found | `interrupt_before` or `interrupt_after` names a missing node. | Fix the node name or compile after adding the node. |

## Low-Level Pregel Problems

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Input channel validation fails | `input_channels` names a missing channel or no node subscribes to it. | Add the channel and subscribe at least one node with `NodeBuilder().subscribe_only(...)` or `subscribe_to(...)`. |
| Output or stream channel validation fails | `output_channels` or `stream_channels` includes a missing channel. | Add the channel or correct the output/stream channel list. |
| Channel receives multiple writes in one step | `LastValue` or guarded `EphemeralValue` is used where concurrent writes occur. | Use `BinaryOperatorAggregate`, `Topic`, or redesign node scheduling so only one write reaches the channel per step. |
| `Pregel` output shape is surprising | A single output channel returns that channel's value; multiple output channels return a mapping. | Check whether `output_channels` is a string or sequence and align assertions accordingly. |

## Routing And Command Problems

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `Command(goto=...)` target does not run | Target is not a valid graph destination. | Add the destination node and, for edgeless/rendered graphs, document possible destinations with `destinations`. |
| Parent graph routing from subgraph fails | Missing `Command.PARENT` or parent destination. | Return `Command(graph=Command.PARENT, goto="parent_node", update=...)` and ensure the parent has that node. |
| Fan-out results overwrite each other | Workers update the same key without reducer. | Add reducer state before using `Send(...)` for parallel writes. |
| Conditional route loops forever | Stop condition is unreachable. | Stream `updates`, inspect state changes, and add a route to `END`. |
| Recursion limit reached | Graph did not hit a stop condition within configured steps. | Fix routing first; increase `recursion_limit` only for intentionally deep workflows. |

## Deprecation Warnings

- Replace `config_schema` with `context_schema`.
- Replace constructor `input` with `input_schema`.
- Replace constructor `output` with `output_schema`.
- Replace `checkpoint_during` with `durability`.
- Prefer `Interrupt.id` over deprecated `interrupt_id`.
- Prefer `GraphOutput.value` and `.interrupts` over dict-like access when using typed v2 output.

## Service, Backend, And Security Notes

- Local `StateGraph` execution does not require LangGraph Server, network access, or credentials.
- Persistence backends such as Postgres or SQLite have their own install and connection requirements; use [persistence](../../persistence/SKILL.md).
- Never put API keys, passwords, or user secrets in graph state if state will be checkpointed or streamed.
- Treat streamed `messages`, `debug`, and `checkpoints` output as potentially sensitive because they can include prompts, state, metadata, and intermediate task results.
- Avoid running untrusted node functions: graph execution invokes arbitrary Python callables in process.

## Source Material Exclusions

- Expensive notebooks and moved notebook pointers are not bundled as runtime checks.
- Maintainer-only release, CI, and benchmark code is excluded.
- Original repository test files are native verification candidates, not runtime dependencies for this public skill.
