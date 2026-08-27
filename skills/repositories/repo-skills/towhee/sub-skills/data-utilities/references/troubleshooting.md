# Data utilities troubleshooting

## RuntimePipeline result looks empty or cannot be read twice

Symptoms:

- `len(towhee.DataCollection(result)) == 0`.
- A second attempt to call `result.get()`, `result.to_list()`, or `towhee.DataCollection(result)` has no rows.
- `DataQueue.to_list()` raises that the queue is not sealed.

Causes and fixes:

1. A pipeline with `.output()` and no output schema intentionally produces an empty visible result. Rebuild the pipeline with explicit output columns in the pipeline-programming sub-skill.
2. A filter, window, or flat-map path may produce zero output rows for the provided input. Inspect with `debug(..., tracer=True)` and check node outputs.
3. Queue reads are consuming. Convert once, then reuse the materialized representation:

   ```python
   dc = towhee.DataCollection(result_queue)
   rows = dc.to_list()
   snapshot = dc.to_dict()
   ```

4. Low-level `DataQueue.to_list()` requires a sealed queue. Normal `RuntimePipeline(...)` results are sealed; hand-built queues may not be.

## `Entity.combine()` returned `None`

`Entity.combine()` mutates the left-hand entity in place and intentionally returns `None`.

Wrong:

```python
entity = entity.combine(extra)
```

Right:

```python
entity.combine(extra)
assert entity.some_new_field is not None
```

If fields disappear, check for key collisions: later entities update `entity.__dict__` and overwrite existing names.

## Display output fails or is not notebook-style

Symptoms:

- `dc.show()` prints a console table when HTML was expected.
- Display imports fail for table, HTML, PIL, image, or audio handling.
- Large media values make table output unreadable.

Causes and fixes:

1. With `tablefmt=None`, Towhee chooses HTML only when an IPython environment is detected. Force a format when needed:

   ```python
   dc.show(limit=5, tablefmt='html')
   dc.show(limit=5, tablefmt='grid')
   ```

2. Console display depends on table rendering support; HTML/media display may rely on notebook, PIL/image, or frontend capabilities. Use `dc.prepare_table_data(limit=...)` for a renderer-independent structure.
3. `limit < 0` displays all rows. Keep the default or a small positive limit for large collections.
4. Treat display as a human visualization aid. For storage or assertions, use `to_dict()` or explicit row values.

## Numpy, PIL, mode, or shape errors for media wrappers

Symptoms:

- `to_pil(img)` raises because the array dtype/shape does not match the mode.
- Color conversion raises `ValueError: Can not convert image from ... to ...`.
- `Image.width`, `height`, or `channel` are surprising.

Causes and fixes:

1. `Image` expects image-like numpy data. For RGB/RGBA/L PIL conversion, prefer `uint8` arrays with shapes like `(height, width, channels)` or `(height, width)`.
2. `Image.width` is `shape[1]`, `height` is `shape[0]`, and `channel` is `shape[2]` only when a third dimension exists; otherwise channel is `1`.
3. Keep `mode` uppercase and aligned with data layout, such as `RGB`, `BGR`, `RGBA`, or `L`.
4. Direct `towhee.types.image_utils.to_image_color(img, target_mode)` uses OpenCV conversion flags named like `COLOR_RGB2BGR`. Unsupported source/target pairs raise `ValueError`.
5. The exported `towhee.types.to_image_color(mode)` is a callable preprocessor usually paired with `@towhee.types.arg(...)`; it is not the same function object as `towhee.types.image_utils.to_image_color(img, target_mode)`.
6. If PIL conversion is optional for the task, keep data as `towhee.types.Image` or plain numpy arrays and avoid round-tripping through PIL.

## `DataLoader` rejects the data source or batches incorrectly

Symptoms:

- `RuntimeError: Data source only support ops or iterator`.
- Parser errors happen before the pipeline receives data.
- The final batch has fewer items than expected.

Causes and fixes:

1. `data_source` must be iterable or callable. If callable, it must take no arguments and return an iterable:

   ```python
   loader = towhee.DataLoader(lambda: iter([1, 2, 3]))
   ```

2. `parser` is called once per source item before batching. Validate parser output shape against the pipeline input schema.
3. `batch_size=None` yields individual parsed values. A positive `batch_size` yields lists of parsed values; the last list may be shorter.
4. When using `RuntimePipeline.batch(batch)`, feed batches shaped for the runtime pipeline's declared inputs. For multi-input pipelines, route to pipeline-programming for batch input shape details.
5. Avoid `batch_size=0` or non-integer values; Towhee does not perform defensive validation before batching.

## Profiler or tracer is missing

Symptoms:

- `v.profiler is None`.
- `v.tracer is None`.
- `Visualizer.from_json(...)` fails on serialized output.

Causes and fixes:

1. Enable the needed surfaces at debug time:

   ```python
   v = runtime_pipeline.debug(data, profiler=True, tracer=True)
   ```

2. `profiler=True` is required for `PerformanceProfiler`; `tracer=True` is required for `DataVisualizer` node input/output collections.
3. JSON reconstruction expects tracer `node_collection` data. Use `profiler=True, tracer=True` before `to_json()` if you plan to call `Visualizer.from_json(...)`.
4. If profiler consistency checks fail after unusual low-level manipulation, rerun debug on a fresh pipeline or reset profiler state through the pipeline-programming workflow.

## Tracer node lookup returns a list or raises `KeyError`

`PipeVisualizer.__getitem__` matches node names by pattern. A broad pattern such as `'lambda'` can match multiple nodes and return a list. A pattern with no matches raises `KeyError` and includes available nodes.

Use more specific node names when possible:

```python
pipe_trace = v.tracer[0]
node = pipe_trace['lambda-0']
node.show_inputs()
node.show_outputs()
```

If names are not stable enough for the task, inspect `pipe_trace.nodes` and choose from the displayed list.

## Profiler timing interpretation is confusing

`PerformanceProfiler.show()` aggregates timing across profiled executions. `node_report` fields split time into initialization, waiting for data, operator call, and output queuing. For batch debug, `len(prof.pipes_profiler)` can be greater than one. Use `prof.sort()` or `prof.max()` to identify the slowest execution, and `prof.dump(path)` when a Chrome trace JSON is needed.
