# Core Graph Workflows

Use these workflows to design, inspect, and execute Dask core graphs safely.

## Convert a Python Loop to Lazy Delayed Tasks

1. Keep ordinary Python control flow outside delayed functions when it is only building the graph.
2. Wrap functions, not results: use `dask.delayed(func)(arg)` or `@dask.delayed`, not `dask.delayed(func(arg))`.
3. Accumulate `Delayed` objects in a list or dict.
4. Combine delayed values with another delayed call such as `dask.delayed(sum)(parts)`.
5. Call `dask.compute(final)` or `final.compute()` once at the end.

Pattern:

```python
import dask

@dask.delayed(pure=True)
def transform(value, offset):
    return value + offset

@dask.delayed(pure=True)
def combine(values):
    return sum(values)

with dask.annotate(priority=10):
    parts = [transform(value, offset=3) for value in range(10)]

total = combine(parts)
result = total.compute(scheduler="threads")
```

When closures are involved, prefer binding closure values as explicit arguments. This makes tokenization, serialization, and debugging easier.

## Keep Graph Definition Lazy

Good graph construction:

```python
outputs = []
for item in items:
    outputs.append(dask.delayed(process)(item))
result = dask.delayed(merge)(outputs)
value = result.compute()
```

Avoid computing inside the loop:

```python
outputs = []
for item in items:
    outputs.append(dask.delayed(process)(item).compute())
```

The second version serializes the workflow because each iteration blocks before the next graph node is added.

## Inspect a Delayed Graph

Use graph inspection before execution:

```python
node = dask.delayed(lambda x: x + 1, pure=True)(1)
graph = node.__dask_graph__()
keys = node.__dask_keys__()
print(node.key)
print(type(graph).__name__)
print(keys)
```

If `graph` is a `HighLevelGraph`, inspect:

```python
print(list(graph.layers))
print({name: sorted(deps) for name, deps in graph.dependencies.items()})
```

If you need low-level tasks, use `dict(graph)` or `graph.to_dict()` where available, but remember this may materialize symbolic layers.

## Debug Dependency Structure

For low-level graph dicts:

```python
from dask.core import get_dependencies, get_deps, istask

for key, task in dsk.items():
    print(key, istask(task), get_dependencies(dsk, key))

dependencies, dependents = get_deps(dsk)
```

For high-level graphs, start with layer names and dependencies before materializing tasks. This helps avoid accidentally expanding very large graphs.

## Choose a Scheduler

| User goal | Recommended scheduler |
| --- | --- |
| Best stack traces and step-through debugging | `scheduler="synchronous"` |
| NumPy, Pandas, C/Cython-heavy tasks, low overhead | `scheduler="threads"` |
| Pure-Python functions with small serializable inputs/outputs | `scheduler="processes"` |
| Dashboard, futures, large shared intermediates, local cluster or remote cluster | `distributed.Client` |

Local examples:

```python
x.compute(scheduler="synchronous")
x.compute(scheduler="threads", num_workers=4)
x.compute(scheduler="processes", num_workers=4)
```

Global context:

```python
with dask.config.set(scheduler="threads", num_workers=4):
    result = dask.compute(a, b)
```

Use `synchronous` first when debugging correctness, then benchmark `threads` and `processes` for performance.

## Multiprocessing-Safe Script Pattern

Process workers must import or serialize the functions they run. Avoid lambdas and nested functions when using `scheduler="processes"`.

```python
import dask


def process_record(record):
    return record["value"] + 1


def main():
    tasks = [dask.delayed(process_record)({"value": i}) for i in range(10)]
    print(dask.compute(*tasks, scheduler="processes"))


if __name__ == "__main__":
    main()
```

If multiprocessing still fails, try `scheduler="threads"` to confirm the graph logic works, then make functions top-level/importable and reduce captured state.

## Use Annotations Correctly

`dask.annotate()` affects collections created inside its context. It does not retroactively modify existing graphs.

```python
with dask.annotate(priority=100, retries=2):
    important = dask.delayed(load)(path)

normal = dask.delayed(load)(other_path)
```

Annotations are soft metadata. Single-machine schedulers may ignore many annotations; distributed scheduling can use more of them.

## Compare Optimized and Unoptimized Behavior

Use `optimize_graph=False` to isolate whether a failure appears only after optimization:

```python
raw = x.compute(scheduler="synchronous", optimize_graph=False)
optimized = x.compute(scheduler="synchronous", optimize_graph=True)
```

For multiple related collections, optimize together:

```python
x2, y2 = dask.optimize(x, y)
```

Remember `dask.optimize()` may materialize HLG layers and lose annotations, so do not use it as a default step in user code.

## Tokenize Custom Inputs

Use deterministic keys when repeated identical calls should share work:

```python
@dask.delayed(pure=True)
def normalize(record):
    return record.strip().lower()
```

Use custom tokenization for classes whose identity should be based on semantic fields:

```python
class DatasetSpec:
    def __init__(self, uri, version):
        self.uri = uri
        self.version = version

    def __dask_tokenize__(self):
        return (type(self).__name__, self.uri, self.version)
```

When a user reports unstable keys, test with `dask.tokenize.tokenize(obj, ensure_deterministic=True)` and either simplify the object or add `__dask_tokenize__`.

## Graph Manipulation for Barriers and Re-Keying

Use these APIs sparingly:

- `checkpoint(collection)` creates a delayed barrier that completes after all chunks/partitions are computed.
- `wait_on(collection)` returns an equivalent collection whose downstream consumers wait for all chunks/partitions first.
- `bind(children, parents, omit=...)` forces dependency ordering between existing collections.
- `clone(collection, omit=...)` creates an equivalent collection with independent keys, useful when recomputation is preferable to retaining large intermediates.

For ordinary user workflows, prefer simple `compute`, `persist`, and collection APIs before graph manipulation.

## Custom Collection Checklist

Use this only when built-in collections and `delayed` are insufficient.

1. Define a graph and output keys.
2. Implement `__dask_graph__()` and `__dask_keys__()`.
3. Define `__dask_postcompute__()` to convert scheduler results to the public output.
4. Define `__dask_postpersist__()` to rebuild an equivalent collection from persisted results.
5. Set `__dask_scheduler__` to a scheduler get function.
6. Provide `__dask_optimize__` or `None`.
7. Provide stable `__dask_tokenize__()`.
8. Optionally inherit `DaskMethodsMixin` for `.compute()`, `.persist()`, and `.visualize()`.

If the collection is HLG-backed, also expose `__dask_layers__()`, but note that new projects are encouraged to avoid implementing custom HLG layers unless necessary.

## Use the Bundled Smoke Script

Run:

```bash
python sub-skills/core-graphs-schedulers/scripts/core_smoke.py --scheduler synchronous
python sub-skills/core-graphs-schedulers/scripts/core_smoke.py --scheduler threads --items 8
```

The script demonstrates delayed graph construction, HLG inspection, low-level dependency inspection, tokenization, and final compute. It is safe: no network, no file writes by default, and tiny in-memory data.
