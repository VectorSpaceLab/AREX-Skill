# Visualization and profiling output patterns

Towhee pipeline debug output is represented by `towhee.tools.visualizer.Visualizer`. This reference explains how to read those objects after a pipeline has already been built and executed. For pipeline construction and `debug()` option selection, route to the pipeline-programming sub-skill.

## Debug result shape

```python
v = runtime_pipeline.debug(input_value, profiler=True, tracer=True)
```

A visualizer may expose three different surfaces:

| Surface | How to enable | What it contains | First checks |
|---|---|---|---|
| `v.result` | Present for normal debug execution. | A Towhee result `DataQueue`. | `v.result.get()` for low-level row data, or `towhee.DataCollection(v.result)` before repeated row access. |
| `v.profiler` | `profiler=True` | `PerformanceProfiler` with timing summaries and per-node reports. | `v.profiler is not None`, then inspect `timing` and `node_report`. |
| `v.tracer` | `tracer=True` | `DataVisualizer` containing per-node input/output `DataCollection` snapshots. | `v.tracer is not None`, then inspect `len(v.tracer)`, `v.tracer.nodes`, and `v.tracer[0]`. |

If `profiler=True` or `tracer=True` was omitted, the corresponding property returns `None` and logs a warning.

## Reading `v.result`

`v.result` is a `DataQueue`. It is suitable for a one-time low-level read:

```python
raw_row = v.result.get()
```

For repeated inspection or display, convert it immediately:

```python
dc = towhee.DataCollection(v.result)
rows = dc.to_list()
```

Be mindful that both `get()` and `DataCollection(...)` consume queue contents. If you need a portable copy, call `dc.to_dict()` after wrapping.

## Reading tracer data

With `tracer=True`, `v.tracer` is a `DataVisualizer`. It acts like a list of per-execution `PipeVisualizer` objects.

```python
trace = v.tracer
print(len(trace))          # number of traced executions
print(trace.nodes)         # node names from the first execution
pipe_trace = trace[0]
node = pipe_trace['lambda'] # regex-style node-name matching
node.show_inputs()
node.show_outputs()
```

Objects and fields:

| Object | Access | Useful fields/methods |
|---|---|---|
| `DataVisualizer` | `v.tracer` | `show(limit=1)`, `len(...)`, `visualizers`, `nodes`, `tracer[index]`. |
| `PipeVisualizer` | `v.tracer[index]` | `show()`, `nodes`, `pipe_visualizer[name_pattern]`. |
| `NodeVisualizer` | `pipe_visualizer[name_pattern]` | `name`, `inputs`, `outputs`, `previous_node`, `next_node`, `op_input`, `show()`, `show_inputs()`, `show_outputs()`. |

`pipe_visualizer[name_pattern]` uses pattern matching. If one node matches, it returns one `NodeVisualizer`; if multiple nodes match, it returns a list; if none match, it raises `KeyError` and includes the available node names.

Tracer node input/output values are `DataCollection` snapshots. You can inspect them the same way as normal pipeline results:

```python
node = v.tracer[0]['_input']
first_input_dc = node.inputs[0]
assert first_input_dc.to_list()
```

## Reading profiler data

With `profiler=True`, `v.profiler` is a `PerformanceProfiler`.

```python
prof = v.profiler
prof.show()
print(prof.timing)
print(prof.node_report)
```

Profiler summary surfaces:

| Surface | Meaning |
|---|---|
| `len(prof)` | Number of profiled pipeline executions in this profiler object. |
| `prof.timing` | Tuple-like summary: total timeline, average, max, and min per execution, rounded to seconds. |
| `prof.node_report` | Dict keyed by node id with per-node timing aggregates. |
| `prof.pipes_profiler` | List of `PipelineProfiler` objects, one per profiled execution. |
| `prof.sort()` | Pipeline profilers sorted by elapsed execution time. |
| `prof.max()` | Slowest `PipelineProfiler`. |
| `prof.dump(file_path)` | Writes Chrome tracing JSON. |
| `prof.gen_profiler_json()` | Returns Chrome tracing events as Python data. |

Each node report has these fields:

| Field | Meaning |
|---|---|
| `node` | Display name with iterator type. |
| `ncalls` | Number of operator calls. |
| `total_time` | Time between queue input and queue output. |
| `init` | Operator initialization time. |
| `wait_data` | Time waiting for data between queue input and process input. |
| `call_op` | Time spent inside the operator call. |
| `output_data` | Time between process output and queue output. |

`prof.dump(path)` writes a Chrome trace JSON file and prints a message telling the user to open `chrome://tracing/` and load the file.

## Visualizer JSON round-trip

`Visualizer.to_json()` serializes result/profiler/tracer information using Towhee's serializer. `Visualizer.from_json(json_text)` reconstructs a `Visualizer` and converts serialized node input/output snapshots back into `DataCollection` objects.

Use JSON round-trip only when tracer data is present:

```python
from towhee.tools.visualizer import Visualizer

v0 = runtime_pipeline.debug(1, profiler=True, tracer=True)
json_text = v0.to_json()
v1 = Visualizer.from_json(json_text)
assert v1.tracer is not None
```

If JSON was produced without a `node_collection`, reconstruction can fail because tracer collections are expected during `from_json()`.

## Graph visualization

For an already-built runtime pipeline, `towhee.tools.visualizer.show_graph(runtime_pipeline)` or `GraphVisualizer(runtime_pipeline.dag_repr).show()` prints a table describing nodes, operator inputs/outputs, graph edges, next nodes, and iterator parameters. This is a read-only graph display; do not use it as the source of pipeline construction details.
