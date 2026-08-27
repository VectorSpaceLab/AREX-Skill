# PocketFlow core API reference

This page summarizes the public runtime surface that future agents can rely on when using PocketFlow as a graph engine.

## Public classes

### `BaseNode`

- `BaseNode()`
- `set_params(params)`
- `next(node, action="default")`
- `prep(shared)`
- `exec(prep_res)`
- `post(shared, prep_res, exec_res)`
- `_exec(prep_res)`
- `_run(shared)`
- `run(shared)`
- `__rshift__(other)` for `>>`
- `__sub__(action)` for `- "action"`

Behavior notes:

- `BaseNode` is the raw node-orchestration base.
- `run(shared)` on a node warns if successors exist, because `run()` does not follow transitions.
- `post()` may return an action string; if it returns `None`, the flow treats that as `default`.

### `Node`

- `Node(max_retries=1, wait=0)`
- `exec_fallback(prep_res, exc)`
- Retries only wrap `exec()`.

Behavior notes:

- `max_retries` counts total attempts, not extra retries beyond the first try.
- `wait` sleeps between attempts in seconds.
- `self.cur_retry` is the current 0-based retry index.
- If all attempts fail, `exec_fallback()` runs and its return value becomes `exec_res`.

### `BatchNode`

- `BatchNode(max_retries=1, wait=0)`
- `prep(shared)` should return an iterable of items.
- `exec(item)` runs once per item.
- `post(shared, prep_res, exec_res_list)` receives the list of per-item results.

Behavior notes:

- `BatchNode` is the map half of a map-reduce style step.
- The node itself still uses the normal `Node` retry/fallback semantics for each item.

### `Flow`

- `Flow(start=None)`
- `start(start)`
- `get_next_node(curr, action)`
- `_orch(shared, params=None)`
- `_run(shared)`
- `post(shared, prep_res, exec_res)`

Behavior notes:

- A flow is itself a node-like object that can be nested inside another flow.
- `Flow` orchestrates the current node, reads the action returned by that node's `post()`, and follows the matching successor.
- `Flow.post()` returns the execution result unchanged by default.
- The flow uses `copy.copy()` internally when moving between nodes, so successor nodes should not depend on identity mutation across transitions.

### `BatchFlow`

- `BatchFlow(start=None)`
- `_run(shared)`

Behavior notes:

- `BatchFlow.prep(shared)` should return a list of parameter dicts.
- Each dict is merged into the flow params and applied to the child flow.
- Child nodes read those values through `self.params`.

### `AsyncNode`

- `AsyncNode(max_retries=1, wait=0)`
- `prep_async(shared)`
- `exec_async(prep_res)`
- `exec_fallback_async(prep_res, exc)`
- `post_async(shared, prep_res, exec_res)`
- `run_async(shared)`
- `_run_async(shared)`

Behavior notes:

- Use async methods instead of sync ones when you need awaited I/O.
- `AsyncNode._run(shared)` is not valid; use `run_async()`.
- Async retry semantics mirror `Node` retry semantics.

### `AsyncBatchNode`

- Async version of `BatchNode`.
- Processes each item sequentially under async control.

### `AsyncParallelBatchNode`

- Async version of `BatchNode` that gathers `exec_async()` tasks in parallel.
- Use only for independent, I/O-bound work.

### `AsyncFlow`

- `AsyncFlow(start=None)`
- `_orch_async(shared, params=None)`
- `_run_async(shared)`
- `post_async(shared, prep_res, exec_res)`

Behavior notes:

- Can include sync nodes and async nodes in the same flow.
- Uses `run_async()` for async nodes and `_run()` for sync nodes.

### `AsyncBatchFlow`

- Async equivalent of `BatchFlow`.
- Iterates through parameter dicts sequentially with async node execution.

### `AsyncParallelBatchFlow`

- Async equivalent of `BatchFlow` that fans out each batch iteration concurrently.
- Good for many independent I/O-bound subflows.

## Shared-store contract

The shared store is usually a plain dict. Typical keys are:

- input payloads such as `question`, `topic`, `files`, or `data`
- intermediate state such as `outline`, `retrieved_chunk`, or `chunks`
- final outputs such as `answer`, `summary`, or `results`
- control state such as `attempts`, `errors`, or `status`

Do not mutate the shared store inside `exec()` unless the task is intentionally side-effectful. The cleanest pattern is:

- `prep()` reads from `shared`
- `exec()` computes from its input
- `post()` writes back to `shared`

## Action rules

- Return `None` from `post()` for the default transition.
- Return a string to branch or loop.
- If no successor exists for an action, the flow ends and warns.

## Signature reminders

- `Node.exec(self, prep_res)`
- `Node.post(self, shared, prep_res, exec_res)`
- `Flow.get_next_node(self, curr, action)`
- `BatchFlow.prep(self, shared)` returns parameter dicts
- `AsyncNode.exec_async(self, prep_res)`
- `AsyncFlow.post_async(self, shared, prep_res, exec_res)`
