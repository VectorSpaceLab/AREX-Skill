# Core abstraction troubleshooting

## Flow ends earlier than expected

### Symptoms
- The last node runs, but the next node never starts.
- A warning says the flow ended because an action was not found.

### Likely causes
- `post()` returned an action string that has no successor.
- `post()` returned `None`, but no default successor was wired.
- The successor was attached to the wrong action string.

### Fix
- Check the exact action string returned by the node.
- Wire the matching successor with `node - "action" >> next_node`.
- If you want the default path, wire `node >> next_node` and return `None` or omit a return.

## `node.run()` did not follow successors

### Symptoms
- A node executes, but the rest of the graph does not.

### Likely cause
- `run()` executes only the node itself.

### Fix
- Use `Flow(start=...).run(shared)` when you expect transitions.
- Use `node.run(shared)` only for isolated debugging.

## BatchFlow cannot see data

### Symptoms
- Child nodes cannot find the expected file name, id, or task parameters.

### Likely cause
- The code stored task identifiers in `shared` instead of `self.params`.
- `BatchFlow.prep()` did not return a list of dictionaries.

### Fix
- Make `BatchFlow.prep()` return `[{...}, {...}]`.
- Read those values in child nodes with `self.params[...]`.
- Put long-lived outputs in `shared`.

## BatchNode results look wrong

### Symptoms
- The reduce step receives an unexpected value or a flattened structure that is not what you expected.

### Likely causes
- `exec()` returned the wrong per-item shape.
- `post()` assumed a single item instead of a list of item results.

### Fix
- Treat `exec_res` in `post()` as a list of per-item results.
- Decide whether the map step should return numbers, strings, tuples, or dicts and keep that shape consistent.

## Retry and fallback confusion

### Symptoms
- The node keeps failing, or fallback is never called.
- The output changes between retries in unexpected ways.

### Likely causes
- `exec()` has side effects that are not safe to retry.
- `exec_fallback()` was not overridden.
- The node is mutating `shared` inside `exec()`.

### Fix
- Keep `exec()` idempotent when possible.
- Move shared-state writes into `post()`.
- Override `exec_fallback()` only if you want graceful recovery.

## Async node does not run

### Symptoms
- Nothing happens, or you get a runtime error when using sync APIs on async nodes.

### Likely cause
- `AsyncNode` was executed with `run()` instead of `run_async()`.

### Fix
- Use `await node.run_async(shared)` or `await flow.run_async(shared)`.
- Keep async and sync node methods aligned with the flow class you use.

## Parallel batch surprises

### Symptoms
- Parallel execution is slower than expected or triggers remote throttling.

### Likely causes
- The work is CPU-bound rather than I/O-bound.
- The upstream service has rate limits.
- The items are not independent.

### Fix
- Reserve parallel async batch nodes for independent I/O-heavy operations.
- Add throttling or batching if a provider rate-limits parallel calls.
- Fall back to sequential batch execution if ordering or dependencies matter.

## Shared-store and params misuse

### Symptoms
- State seems to disappear between nodes.
- A child flow receives stale identifiers.

### Likely causes
- The code stored identifiers in `shared` instead of params.
- The flow or node expected params that were never set.

### Fix
- Keep identifiers in `self.params` for batch-style routing.
- Keep durable results in `shared`.
- Set parent params at the topmost flow, not on nested children unless you are deliberately testing them.
