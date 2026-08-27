# Towhee pipeline API reference

This reference is distilled for Towhee 1.1.x custom pipeline programming. It is self-contained: do not rely on source-checkout files at runtime.

## Core mental model

A Towhee custom pipeline is a chained DAG builder:

```python
from towhee import pipe

p = (
    pipe.input('x')
        .map('x', 'y', lambda x: x + 1)
        .output('x', 'y')
)

p(1).get()  # [1, 2]
```

- `pipe.input(...)` starts a non-callable `Pipeline` builder.
- Each node appends transformation metadata and returns a new `Pipeline` builder.
- `output(...)` closes the DAG, preloads operators, and returns a callable `RuntimePipeline`.
- Calling the runtime pipeline returns a result queue with `get()` for the next row and `to_list()` for all rows.
- Column names are schema identifiers. Valid names match `^[A-Za-z_][A-Za-z_0-9]*$`; commas, spaces, hyphens, and leading digits are invalid.

## Pipeline node signatures and semantics

| API | Signature | Semantics | Notes |
| --- | --- | --- | --- |
| Input | `pipe.input(*schema)` or `Pipeline.input(*schema)` | Declares the pipeline input columns and starts a new builder. | At least one input column is normally required for useful pipelines. Schema entries are strings. |
| Map | `map(input_schema, output_schema, fn, config=None)` | Applies `fn` one row at a time and emits one output row for one input row. | `fn` can be a lambda, callable object/function, runtime sub-pipeline, or Towhee operator wrapper. |
| Flat map | `flat_map(input_schema, output_schema, fn, config=None)` | Applies `fn` and flattens an iterable/list result into multiple rows. | Use for tokenization, object detections, decoded frames, or any one-to-many expansion. Scalar side columns are repeated/aligned as needed. |
| Filter | `filter(input_schema, output_schema, filter_columns, fn, config=None)` | Evaluates `fn` on `filter_columns`; keeps or drops selected columns from rows. | `input_schema` and `output_schema` must have the same length. `filter_columns` may be one column or a tuple. |
| Window | `window(input_schema, output_schema, size, step, fn, config=None)` | Groups rows into row-count windows, then calls `fn` with lists for each input column. | `size` and `step` are positive integers. Final partial windows are emitted when present. |
| Time window | `time_window(input_schema, output_schema, timestamp_col, size, step, fn, config=None)` | Groups rows by a timestamp column and calls `fn` with lists for each input column. | Timestamp values are milliseconds; `size` and `step` are seconds. `timestamp_col` must exist upstream. |
| Window all | `window_all(input_schema, output_schema, fn, config=None)` | Collects all available rows into one window and calls `fn` once with lists. | Useful for final aggregation, whole-video embedding merges, or summary rows. |
| Reduce | `reduce(input_schema, output_schema, fn, config=None)` | Reduces all rows for the selected columns to one output row. | Similar aggregation intent to `window_all`, but implemented as a reduce node; it does not accept a `RuntimePipeline` as `fn`. |
| Concat | `concat(*pipes)` | Merges intermediate results from one or more sibling pipelines that derive from the same input builder. | Requires at least one `Pipeline`. If upstream branches output the same column name, later concat order can overwrite values. |
| Output | `output(*output_schema)` | Adds the output node, preloads operators, and returns `RuntimePipeline`. | Only ask for columns declared by upstream nodes. `output()` with no columns is a sink-style runtime. |

`input_schema` and `output_schema` accept a single string or a tuple of strings. Multi-column callables receive positional arguments in the order of `input_schema`; multi-column outputs should return a tuple/list aligned to `output_schema`.

## RuntimePipeline execution

Installed signatures:

```text
RuntimePipeline.__call__(self, *inputs)
RuntimePipeline.batch(self, batch_inputs)
RuntimePipeline.debug(self, *inputs, batch=False, profiler=False, tracer=False, include=None, exclude=None)
RuntimePipeline.flush(self)
```

### Single input

```python
from towhee import pipe

p = pipe.input('x').map('x', 'double', lambda x: x * 2).output('double')
res = p(3)
assert res.get() == [6]
```

### Multiple input columns

```python
p = (
    pipe.input('a', 'b')
        .map(('a', 'b'), 'sum_', lambda a, b: a + b)
        .output('sum_')
)
assert p(2, 5).get() == [7]
```

### Batch inputs

For a one-column input schema, pass a list of input values:

```python
p = pipe.input('x').map('x', 'y', lambda x: x + 1).output('y')
rows = p.batch([1, 2, 3])
assert [row.get() for row in rows] == [[2], [3], [4]]
```

For a multi-column input schema, pass a list where each item is a row-like sequence matching the schema:

```python
p = (
    pipe.input('a', 'b')
        .map(('a', 'b'), 'sum_', lambda a, b: a + b)
        .output('sum_')
)
rows = p.batch([[1, 10], [2, 20]])
assert [row.get() for row in rows] == [[11], [22]]
```

### Flush

`flush()` calls the `flush` method of loaded operators in the runtime operator pool. Use it after pipelines with buffered sinks or index writers that need explicit commit/flush behavior.

```python
p(...)
p.flush()
```

For pure lambda/callable pipelines, `flush()` is usually a no-op.

## Node patterns

### Map and output selection

```python
p = (
    pipe.input('text')
        .map('text', 'length', len)
        .map('length', 'bucket', lambda n: 'long' if n >= 8 else 'short')
        .output('text', 'length', 'bucket')
)
assert p('towhee').get() == ['towhee', 6, 'short']
```

### Flat map followed by window

```python
p = (
    pipe.input('items')
        .flat_map('items', 'item', lambda xs: xs)
        .window('item', 'pair_sum', 2, 2, sum)
        .output('pair_sum')
)
assert p([1, 2, 3]).to_list() == [[3], [3]]
```

### Filter semantics

```python
p = (
    pipe.input('x')
        .filter('x', 'kept', 'x', lambda x: x > 10)
        .output('kept')
)
assert p(11).get() == [11]
assert p(1).get() is None
```

If you output side-by columns that were not filtered the same way, you may see `Empty()` placeholders. Keep filtered schemas aligned unless you intentionally need sparse rows.

### Time window with millisecond timestamps

```python
p = (
    pipe.input('events')
        .flat_map('events', ('value', 'ts'), lambda rows: rows)
        .time_window('value', 'window_sum', 'ts', 3, 3, sum)
        .output('window_sum')
)
# Timestamps are milliseconds; size/step are seconds.
rows = [(1, 0), (2, 1000), (3, 2000), (10, 8000)]
assert p(rows).to_list() == [[6], [10]]
```

### Window all and reduce

```python
p_all = (
    pipe.input('xs')
        .flat_map('xs', 'x', lambda xs: xs)
        .window_all('x', 'total', sum)
        .output('total')
)
assert p_all([1, 2, 3]).get() == [6]

p_reduce = (
    pipe.input('xs')
        .flat_map('xs', 'x', lambda xs: xs)
        .reduce('x', 'total', sum)
        .output('total')
)
assert p_reduce([1, 2, 3]).get() == [6]
```

When no rows reach `window_all`, it can produce no output. `reduce` with Python `sum` over no rows produces `0` in the tested Towhee behavior.

### Concat branches from the same input

```python
base = pipe.input('a', 'b', 'c')
left = base.map('a', 'd', lambda a: a + 1)
right = base.map(('b', 'c'), 'e', lambda b, c: b - c)
combined = right.concat(left).output('d', 'e')
assert combined(1, 2, 3).get() == [2, -1]
```

Rules:

- Branches must derive from the same input builder lineage.
- `concat()` with no arguments raises an error.
- Passing anything other than `Pipeline` builders raises an error.
- Duplicate output column names are order-sensitive; avoid duplicate names unless overwriting is intentional.

## AutoConfig

Installed signatures:

```text
AutoConfig.LocalCPUConfig()
AutoConfig.LocalGPUConfig(device: int = 0)
AutoConfig.TritonCPUConfig(num_instances_per_device: int = 1, max_batch_size: int = None, batch_latency_micros: int = None, preferred_batch_size: list = None)
AutoConfig.TritonGPUConfig(device_ids: list = None, num_instances_per_device: int = 1, max_batch_size: int = None, batch_latency_micros: int = None, preferred_batch_size: list = None)
AutoConfig.load_config(name: str, *args, **kwargs)
```

| API | Local effect | Typical use |
| --- | --- | --- |
| `LocalCPUConfig()` | Returns config with `{'device': -1}`. | Force CPU execution for an operator node. |
| `LocalGPUConfig(device=0)` | Returns config with `{'device': device}`. | Use a local GPU id when the environment has the required GPU stack. |
| `TritonCPUConfig(...)` | Returns a `server` config with `device_ids=None`. | Prepare a node/pipeline config intended for Triton CPU serving; route deployment to `serving-and-triton`. |
| `TritonGPUConfig(...)` | Returns a `server` config with GPU `device_ids` defaulting to `[0]`. | Prepare Triton GPU configuration; verify GPU/Docker/Triton prerequisites elsewhere. |
| `load_config(name, *args, **kwargs)` | Loads a registered config from a local file, built-in pipeline, or Hub pipeline; returns `None` if no config is found. | Configure `AutoPipes.pipeline(...)` for built-in or reusable pipelines. |

`TowheeConfig` objects can be combined with `+` or `|`:

```python
from towhee import AutoConfig

config = AutoConfig.LocalGPUConfig(device=0) + AutoConfig.TritonGPUConfig(device_ids=[0])
assert config.config['device'] == 0
assert config.config['server']['device_ids'] == [0]
```

Pass node configs through pipeline builder methods:

```python
from towhee import pipe, AutoConfig

p = (
    pipe.input('x')
        .map('x', 'y', lambda x: x + 1, config=AutoConfig.LocalCPUConfig())
        .output('y')
)
```

## AutoPipes

Installed signature:

```text
AutoPipes.pipeline(name, *args, **kwargs) -> Optional[RuntimePipeline]
```

Resolution behavior:

1. If `name` is a file path, Towhee imports that local Python file. The file can register config and pipeline builders with `AutoConfig.register` and `AutoPipes.register`.
2. If `name` matches a built-in pipeline module, Towhee loads that built-in definition.
3. Otherwise, Towhee resolves a Hub pipeline. A name without `/` is prefixed as a Towhee namespace internally. This path may require network access, a populated cache, compatible optional dependencies, and model downloads.

Minimal local-file pattern:

```python
# local_pipe.py
from towhee import pipe, AutoPipes, AutoConfig

@AutoConfig.register
class MyConfig:
    def __init__(self, inc=1):
        self.inc = inc

@AutoPipes.register
def pipeline(config):
    return pipe.input('x').map('x', 'y', lambda x: x + config.inc).output('y')
```

Consumer:

```python
from towhee import AutoConfig, AutoPipes

config = AutoConfig.load_config('local_pipe.py', inc=2)
p = AutoPipes.pipeline('local_pipe.py', config)
assert p(10).get() == [12]
```

For offline-safe tasks, prefer local file paths or simple custom `pipe.input` pipelines. Treat built-in and Hub names as potentially download-heavy unless the target environment already has the operator/model cache and optional dependencies.

## Safe local smoke check

Use the bundled script for a no-network check of import, lambda pipeline execution, batch execution, debug profiler/tracer construction, and `AutoConfig.LocalCPUConfig`:

```bash
python ../scripts/pipeline_smoke.py --verbose
```
