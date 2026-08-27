# Core Graphs and Schedulers API Reference

This reference covers Dask's core graph APIs and scheduler-facing concepts. Use collection-specific sibling sub-skills for array, dataframe, or bag APIs.

## Public Entry Points

| API | Current signature | Use |
| --- | --- | --- |
| `dask.delayed` | `(obj='__no__default__', name=None, pure=None, nout=None, traverse=True)` | Wrap a function or object in a lazy `Delayed` proxy. Call as `delayed(func)(*args)` or use as `@delayed`. |
| `dask.compute` | `(*args, traverse=True, optimize_graph=True, scheduler=None, get=None, **kwargs)` | Materialize one or more Dask collections together and return concrete Python results. |
| `dask.persist` | `(*args, traverse=True, optimize_graph=True, scheduler=None, **kwargs)` | Compute collection partitions and return equivalent Dask collections backed by cached results or futures. |
| `dask.optimize` | `(*args, traverse=True, **kwargs)` | Return equivalent collections sharing one merged optimized graph. Usually optional; may materialize graphs and lose HLG annotations. |
| `dask.annotate` | `(**annotations) -> Iterator[None]` | Context manager that attaches soft scheduler metadata to newly-created HighLevelGraph layers. Primarily useful for distributed scheduling. |
| `dask.visualize` | `(*args, filename='mydask', traverse=True, optimize_graph=False, maxval=None, engine=None, **kwargs)` | Render one or more graphs; requires Graphviz or another supported visualization engine. |

`dask.__init__` exports `compute`, `persist`, `optimize`, `annotate`, `get_annotations`, `is_dask_collection`, `visualize`, `istask`, and `delayed`. It also exposes `dask.get` as the synchronous local scheduler.

## Delayed Essentials

- `delayed(func)(x)` is lazy; `delayed(func(x))` computes `func(x)` immediately before wrapping the result.
- `Delayed` objects expose `.key`, `.dask`, `__dask_graph__()`, `__dask_keys__()`, `__dask_layers__()`, `__dask_tokenize__()`, `.compute()`, `.persist()`, and `.visualize()`.
- `pure=True` asks Dask to derive deterministic keys from function and arguments. `pure=False` uses unique UUID-like names to avoid accidental common-subexpression reuse.
- `nout=N` lets a delayed call with tuple-like output be unpacked into `N` delayed outputs. Iterating a delayed object without `nout` raises.
- `traverse=False` skips searching Python containers for nested Dask collections, which can reduce overhead for large concrete containers.
- Use `dask_key_name=` when calling a delayed function if you need a specific output task key; use `name=` on `delayed(obj, name=...)` only for the wrapped function/object key.

## Compute, Persist, Optimize

- `compute(*collections)` merges all inputs before optimization and scheduling, so common dependencies can be shared.
- `compute(..., scheduler='synchronous')` executes in the local thread and is best for debugging exceptions.
- `compute(..., scheduler='threads', num_workers=N)` uses the local threaded scheduler.
- `compute(..., scheduler='processes', num_workers=N)` uses the local multiprocessing scheduler and requires serializable functions, arguments, and results.
- `compute(..., optimize_graph=False)` runs the unoptimized graph where supported, useful when debugging fusion or culling effects.
- `persist()` blocks on single-machine schedulers but may return immediately with asynchronously running futures under `distributed`.
- `optimize()` is advanced: it rebuilds equivalent collections from a materialized optimized graph and can drop HLG layer annotations.

## Scheduler Get Functions

| Scheduler | Function | Best for | Notes |
| --- | --- | --- | --- |
| Synchronous | `dask.local.get_sync` / `dask.get` | Debugging, deterministic stack traces, tiny workloads | No parallelism. |
| Threads | `dask.threaded.get` | NumPy/Pandas/Cython work, low task overhead, shared memory | GIL limits pure-Python speedups. Accepts `num_workers`, `pool`, `cache`. |
| Processes | `dask.multiprocessing.get` | Pure-Python work with small inputs/outputs | Uses `cloudpickle`, process pools, culling/fusion by default; standalone scripts need `if __name__ == '__main__':`. |
| Distributed | `distributed.Client` | Dashboards, futures, clusters, large intermediate data | Covered only for scheduler selection here; use distributed docs/package for cluster details. |

Global scheduler selection uses `dask.config.set(scheduler='threads')`, `dask.config.set(scheduler='processes')`, `dask.config.set(scheduler='synchronous')`, a custom scheduler callable, or a `concurrent.futures.Executor`-like object.

## Low-Level Graph Helpers

A low-level Dask graph is a mapping from keys to either concrete data or tasks. A legacy task is commonly a tuple where the first element is callable and later elements are arguments or dependency keys.

| API | Purpose |
| --- | --- |
| `dask.core.get(dsk, out, cache=None)` | Synchronously compute keys from a low-level graph. |
| `dask.core.istask(x)` | True for runnable task tuples or non-data `GraphNode` instances. |
| `dask.core.get_dependencies(dsk, key=None, task=no_default, as_list=False)` | Immediate dependencies for a graph key or supplied task. |
| `dask.core.get_deps(dsk)` | Return `(dependencies, dependents)` mappings for the graph. |
| `dask.core.keys_in_tasks(keys, tasks, as_list=False)` | Find graph keys referenced by a collection of tasks. |
| `dask.core.flatten(seq, container=list)` | Flatten nested task-key structures. |
| `dask.core.literal(x)` | Mark a value as literal so it is not interpreted as a key. |

Prefer high-level collection APIs for user workflows. Reach for low-level helpers when debugging graph dependencies or implementing an advanced collection.

## HighLevelGraph and Layers

`HighLevelGraph(layers, dependencies, key_dependencies=None)` stores symbolic graph layers and their inter-layer dependencies. `HighLevelGraph.from_collections(name, layer, dependencies=...)` is the usual construction helper for collection implementers.

Important concepts:

- `Layer` is the abstract protocol for symbolic layers. Many default methods materialize; custom layers should override methods when non-materializing behavior matters.
- `MaterializedLayer(mapping, annotations=None, collection_annotations=None)` wraps an ordinary mapping of keys to tasks/data.
- `HighLevelGraph.layers` maps layer names to `Layer` objects; `HighLevelGraph.dependencies` maps layer names to dependency layer-name sets.
- `HighLevelGraph.cull(keys)` removes unnecessary tasks for requested output keys.
- `HighLevelGraph.visualize(filename='dask-hlg.svg', format=None, **kwargs)` renders layer structure and requires Graphviz.
- HLG layer annotations come from `dask.annotate()` at graph-construction time.

Dask also has expression-based internals. For new user workflows, do not implement custom HLG layers unless explicitly needed; prefer existing collections or `delayed`.

## Modern Task Spec

`dask._task_spec` is Dask's modern internal task representation. It is useful for reading optimized graphs or debugging internals.

| Class | Use |
| --- | --- |
| `TaskRef(key)` | References another task key inside modern task arguments. |
| `DataNode(key, value)` | Represents concrete data in a graph; has no dependencies. |
| `Task(key, func, /, *args, _data_producer=False, **kwargs)` | Represents a callable task with dependencies inferred from `TaskRef` and nested `GraphNode` arguments. |

Do not require user code to construct these classes unless implementing or debugging Dask internals. Legacy task tuples remain common in public examples and tests.

## Tokenization

| API | Current signature | Use |
| --- | --- | --- |
| `dask.tokenize.tokenize` | `(*args, ensure_deterministic=None, **kwargs) -> str` | Deterministic hash for graph names and task keys. |
| `dask.base.tokenize` | same public behavior | Common imported location in Dask examples and internals. |
| `dask.delayed.tokenize` | `(*args, pure=None, **kwargs)` | Delayed-specific naming helper; `pure=False` produces unique tokens. |

Configuration `tokenize.ensure-deterministic` or `tokenize(..., ensure_deterministic=True)` raises `TokenizationError` when an object cannot be deterministically tokenized. Custom classes can implement `__dask_tokenize__` for stable task names.

## Graph Manipulation

`dask.graph_manipulation` changes graph dependencies and keys; outputs are not always functionally equivalent in scheduling behavior even when final values match.

| API | Signature summary | Use |
| --- | --- | --- |
| `checkpoint(*collections, split_every=None)` | Return delayed `None` after all input chunks are computed. |
| `bind(children, parents, *, omit=None, seed=None, assume_layers=True, split_every=None)` | Make child collections depend on parent collections. |
| `clone(*collections, omit=None, seed=None, assume_layers=True)` | Re-key collections so equivalent computations are independent. |
| `wait_on(*collections, split_every=None)` | Return equivalent collections whose dependents wait until all input chunks complete. |

These are advanced controls for memory lifetime and dependency ordering. Avoid them for ordinary delayed workflows unless the user specifically needs scheduling barriers or independent recomputation.

## Custom Collection Protocol

A custom collection should usually inherit `dask.base.DaskMethodsMixin` for `.compute()`, `.persist()`, and `.visualize()` methods, but the protocol does not require a base class.

Minimum hooks commonly needed:

- `__dask_graph__()` returns graph-like object.
- `__dask_keys__()` returns output keys, often nested.
- `__dask_postcompute__()` returns `(finalize_callable, args_tuple)`.
- `__dask_postpersist__()` returns `(rebuild_callable, args_tuple)`.
- `__dask_tokenize__()` returns stable identity for tokenization.
- `__dask_optimize__(dsk, keys, **kwargs)` optimizes collection graphs, or `None` when no low-level optimizer is needed.
- `__dask_scheduler__` points to a scheduler get function such as `dask.threaded.get`.
- HLG-backed legacy collections also expose `__dask_layers__()`.

Use `dask.is_dask_collection(obj)` to check whether an object is recognized as a Dask collection.
