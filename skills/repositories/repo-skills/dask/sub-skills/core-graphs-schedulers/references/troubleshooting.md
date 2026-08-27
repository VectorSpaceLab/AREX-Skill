# Core Graphs and Schedulers Troubleshooting

## Accidental Eager Compute During Graph Construction

Symptoms:

- The loop runs slowly before any final `compute()` call.
- Parallelism is poor because each iteration blocks.
- Prints, network calls, or expensive functions happen during graph setup.

Common causes:

- Calling `dask.delayed(func(arg))` instead of `dask.delayed(func)(arg)`.
- Calling `.compute()` or `.persist()` inside the graph-building loop.
- Calling delayed functions inside delayed functions rather than building the graph outside.
- Wrapping a Dask Array/DataFrame/Bag in `delayed` instead of using the collection's map/partition APIs.

Fix:

- Delay the function call, not its result.
- Accumulate delayed nodes and compute once at the end.
- Move graph-building loops outside delayed functions.
- Route array/dataframe/bag collection operations to the appropriate sibling sub-skill.

## Scheduler Choice Problems

Symptoms:

- Threads do not speed up pure-Python code.
- Processes are slower than threads for large intermediate data.
- Debugging exceptions is hard under parallel schedulers.
- `persist()` blocks unexpectedly or returns futures unexpectedly.

Fix:

- Use `scheduler="synchronous"` for debugging and deterministic stack traces.
- Use `scheduler="threads"` for NumPy/Pandas/C-extension work and low overhead.
- Use `scheduler="processes"` for pure-Python tasks only when inputs and outputs are small and serializable.
- Use distributed scheduling when users need dashboards, futures, clusters, or smarter handling of large intermediate data.
- Remember single-machine `persist()` blocks until data is computed; distributed `persist()` may submit work and return before completion.

## Multiprocessing Pickling Failures

Symptoms:

- Errors mentioning pickling, serialization, `cloudpickle`, local objects, lambdas, closures, or `Can't pickle`.
- Code works with `scheduler="threads"` or `scheduler="synchronous"` but fails with `scheduler="processes"`.
- Standalone scripts recursively spawn or fail on Windows/macOS-like spawn behavior.

Fix:

- Replace lambdas and nested functions with top-level functions.
- Pass captured closure state as explicit arguments.
- Keep arguments/results small and serializable.
- Add `if __name__ == "__main__": main()` around process-scheduler scripts.
- Fall back to `scheduler="threads"` when the workload is C-extension-heavy or when serialization risk outweighs process benefits.

Debug pattern:

```python
# First prove graph logic works.
result = x.compute(scheduler="synchronous", optimize_graph=False)

# Then prove parallel thread execution works.
result = x.compute(scheduler="threads")

# Only then try processes with top-level functions.
result = x.compute(scheduler="processes")
```

## Non-Deterministic Tokens and Task Keys

Symptoms:

- Repeated graph construction produces different keys when stable keys are expected.
- Identical computations are not shared.
- `TokenizationError` appears when deterministic tokenization is enforced.

Causes:

- `delayed(..., pure=False)` or default delayed purity producing unique names.
- Objects include random IDs, memory addresses, open handles, unordered state, or un-tokenizable fields.
- Custom classes do not implement `__dask_tokenize__`.

Fix:

- Use `pure=True` only for referentially transparent functions.
- Use `dask.tokenize.tokenize(obj, ensure_deterministic=True)` to reproduce the problem.
- Add `__dask_tokenize__` returning stable semantic fields for custom classes.
- Use explicit `dask_key_name=` only when the name is unique and collision-safe.

## Graph Visualization Dependency Errors

Symptoms:

- `.visualize()` raises `RuntimeError: No visualization engine detected`.
- Errors mention Graphviz executable, Python `graphviz`, or `ipycytoscape`.
- HLG visualization fails while computation works.

Fix:

- Install a supported visualization engine and system Graphviz if needed.
- For text-only inspection, avoid visualization and inspect `node.key`, `node.__dask_keys__()`, `graph.layers`, and `graph.dependencies`.
- Use `optimize_graph=False` to visualize the graph as built; use `optimize_graph=True` to visualize the graph after optimization where supported.

## Optimization and Fusion Surprises

Symptoms:

- Debug output shows fewer tasks than expected.
- Task names disappear or layers are fused.
- A failure only happens with optimized graphs.
- HLG annotations are missing after manual `dask.optimize()`.

Fix:

- Re-run with `compute(..., optimize_graph=False)`.
- Inspect the graph before and after `dask.optimize()` separately.
- Remember culling removes tasks not needed for requested outputs.
- Remember fusion may combine linear task chains.
- Avoid using `dask.optimize()` as a default user-facing step; it may materialize graphs and lose HLG annotations.

## Annotation Confusion

Symptoms:

- `dask.get_annotations()` is empty at compute time.
- Existing tasks do not reflect annotations added later.
- Single-machine scheduler seems to ignore annotations.

Fix:

- Create collections inside `with dask.annotate(...):`; annotations attach during graph construction.
- Treat annotations as soft metadata, especially outside distributed scheduling.
- Do not rely on annotations for correctness.
- Avoid manual `dask.optimize()` if preserving HLG annotations matters.

## Low-Level Graph Key Mistakes

Symptoms:

- `KeyError: '<key> is not a key in the graph'` from `dask.core.get`.
- A string argument is interpreted as a dependency key.
- Dependencies do not match expectations.

Fix:

- Ensure requested keys exist in the graph.
- Use `dask.core.literal(value)` when a value could be mistaken for a graph key.
- Use `get_dependencies(dsk, key)` and `get_deps(dsk)` to inspect direct dependencies and dependents.
- Prefer `delayed` or collection APIs for user workflows unless low-level task dicts are explicitly required.

## Custom Collection Protocol Errors

Symptoms:

- `dask.compute(custom)` returns the object unchanged.
- Scheduler selection fails across multiple custom collections.
- Persist returns wrong object types.
- Tokenization produces unstable collection names.

Fix:

- Check `dask.is_dask_collection(obj)` returns true.
- Implement `__dask_graph__`, `__dask_keys__`, `__dask_postcompute__`, `__dask_postpersist__`, `__dask_tokenize__`, `__dask_optimize__`, and `__dask_scheduler__` consistently.
- Ensure collections computed together either share compatible default schedulers or pass an explicit scheduler.
- Add `DaskMethodsMixin` only after protocol hooks are correct.
