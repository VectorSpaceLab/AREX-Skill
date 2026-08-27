# Debugging and profiling Towhee pipelines

Use this reference after a `RuntimePipeline` has been built with `output(...)`. Debugging is local runtime inspection; it does not deploy a service and it does not require Hub access for lambda/callable pipelines.

## Signature

```python
RuntimePipeline.debug(
    *inputs,
    batch: bool = False,
    profiler: bool = False,
    tracer: bool = False,
    include=None,
    exclude=None,
)
```

Rules:

- Set at least one of `profiler=True` or `tracer=True`; otherwise Towhee raises `ValueError`.
- `profiler=True` records timing and call counts per pipeline run and per node.
- `tracer=True` records intermediate node input/output data queues.
- `include` and `exclude` accept a string or list of strings; Towhee treats them as regular-expression patterns matched against generated node names such as `lambda-0`, `_input`, and `_output`.
- `batch=True` means the first positional input to `debug` is a batch input collection, matching `RuntimePipeline.batch(...)` shape.

## Single-run debug

```python
from towhee import pipe

p = (
    pipe.input('x')
        .map('x', 'y', lambda x: x + 1)
        .output('x', 'y')
)

viz = p.debug(3, profiler=True, tracer=True, include='lambda')
assert viz.result.get() == [3, 4]
assert len(viz.profiler) == 1
assert len(viz.tracer) == 1
```

Useful attributes and methods:

| Object | Access | Meaning |
| --- | --- | --- |
| `viz.result` | `viz.result.get()` or `viz.result.to_list()` | Pipeline output queue from the debug run. Reading consumes rows. |
| `viz.profiler` | `viz.profiler.show()` | Aggregate timing table with total/avg/max/min and per-node call timings. |
| `viz.profiler[0]` | One pipeline run profiler | Per-run timing details. |
| `viz.profiler.dump(path)` | Writes JSON trace | Creates a trace file that can be opened in a browser tracing UI. Ask before writing large artifacts. |
| `viz.tracer` | `viz.tracer.nodes`, `viz.tracer.show(limit=...)` | Data visualizer for traced node queues. |
| `viz.tracer[0]` | First run visualizer | Inspect nodes from one pipeline execution. |
| `viz.tracer[0]['lambda']` | Regex node lookup | Returns a node visualizer for the matched generated node. |

The tracer node visualizer exposes:

- `name`
- `inputs`
- `outputs`
- `previous_node`
- `next_node`
- `op_input`
- `show_inputs()`
- `show_outputs()`
- `show()`

Prefer programmatic assertions before display calls in automated smoke tests:

```python
node = viz.tracer[0]['lambda']
assert node.previous_node == ['_input']
assert node.next_node == ['_output']
```

## Batch debug

For a one-column pipeline:

```python
p = pipe.input('x').map('x', 'y', lambda x: x + 1).output('y')
viz = p.debug([1, 2, 3], batch=True, profiler=True, tracer=True, exclude=['input', 'output'])
assert [row.get() for row in viz.result] == [[2], [3], [4]]
assert len(viz.profiler) == 3
assert len(viz.tracer) == 3
```

For multi-column input, the debug batch argument follows the same row shape as `batch(...)`:

```python
p = (
    pipe.input('a', 'b')
        .map(('a', 'b'), 'sum_', lambda a, b: a + b)
        .output('sum_')
)
viz = p.debug([[1, 10], [2, 20]], batch=True, profiler=True)
assert [row.get() for row in viz.result] == [[11], [22]]
```

## Include/exclude strategy

- Start with `include='lambda'` for small lambda/callable pipelines.
- Use `exclude=['input', 'output']` to focus on processing nodes while still collecting all non-input/output generated nodes.
- Use more precise regex strings if a pipeline has several lambda nodes and you only need one.
- If `tracer.nodes` is empty, your include/exclude patterns filtered out every node. Re-run with no `include` and a narrow `exclude`, or inspect generated node names through the tracer.

## Profiling strategy

1. Start with a one-row debug run using `profiler=True` and `tracer=True`.
2. Confirm that outputs are correct before interpreting timing.
3. Move to `batch=True` only after single-row behavior is correct.
4. For timing comparisons, avoid first-run Hub operator/model downloads; preloaded or cached operators give more meaningful timings.
5. Use `profiler.show()` for human-readable timing and `profiler.dump(path)` only when the user wants a trace artifact.

## Debugging side effects and flush

`debug(...)` executes the pipeline. If the pipeline writes to an index, database, file, or any buffered sink operator, the debug run may have side effects. For pipelines with buffered sinks, call `flush()` after normal or debug execution if the operator requires it:

```python
p(...)
p.flush()
```

For pure lambda/callable smoke pipelines, `flush()` is safe and generally does nothing.

## Safe local debug smoke

The bundled smoke script builds a lambda-only pipeline, runs single and batch inputs, and constructs profiler/tracer objects without display side effects:

```bash
python ../scripts/pipeline_smoke.py --verbose
```
