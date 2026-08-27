# Towhee pipeline troubleshooting

Use this page for local custom pipeline construction and `RuntimePipeline` execution problems. Route operator packaging, service deployment, data display/types, or training-specific failures to the matching sibling sub-skill named in `SKILL.md`.

## Quick triage

1. Confirm Towhee imports in the active Python environment.
2. Run the safe lambda smoke check before introducing Hub operators or model downloads.
3. Validate schema names and output columns.
4. Reproduce with `debug(..., profiler=True, tracer=True)` if the pipeline imports and builds.
5. Add Hub, GPU, Triton, or optional dependencies only after a local lambda/callable pipeline works.

```bash
python ../scripts/pipeline_smoke.py --verbose
```

## Common failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Schema can only consist of letters, numbers, and underscores` | A column name contains a comma, space, hyphen, punctuation, or starts with a digit. | Rename schemas to identifiers such as `image_path`, `text`, `vec_1`. Valid pattern: `^[A-Za-z_][A-Za-z_0-9]*$`. |
| `ValueError` while building `filter(...)` | `input_schema` and `output_schema` lengths differ, or `filter_columns` are not declared upstream. | Keep `filter(input_schema, output_schema, ...)` one-to-one. Filter only declared upstream columns. |
| `DAG Nodes inputs ... is not valid, which is not declared` | A node or `output(...)` refers to a column that no earlier node created or carried. | Walk the chain and list columns after each node. Change `output(...)` to declared columns or add a node producing the missing column. |
| Output contains `Empty()` | A branch/filter/window produced sparse rows or side-by columns did not align with transformed columns. | Keep filtered/transformed columns aligned; avoid outputting side columns after filters unless sparse rows are expected. |
| `debug()` raises `You should set at least one of profiler or tracer to True` | `debug(...)` was called with both flags false. | Call `p.debug(..., profiler=True)`, `p.debug(..., tracer=True)`, or both. |
| `AutoPipes.pipeline(...)` returns `None` or logs `Can not find the pipeline` | Name does not match a local file, built-in pipeline, or reachable/cached Hub pipeline. | Use a valid local file path for offline checks, verify the built-in name, or ensure Hub/cache/network access is intentionally available. |
| First Hub/built-in run takes minutes or fails with dependency errors | Hub operators or built-in pipelines may download operator code, model weights, tokenizers, or optional Python/system dependencies. | Prove the custom pipeline with lambda/callable nodes first. Then install/cache required operator dependencies in the target environment with user approval. |
| `ModuleNotFoundError: No module named 'pkg_resources'` during Towhee import | Active environment lacks `setuptools`/`pkg_resources`, which Towhee 1.1.x imports through its operator loader. | Install or repair `setuptools` in the active environment, then re-run the smoke script. |
| `RuntimeError` from `batch(...)` | At least one batch item does not match the input schema or a callable raises on a batch item. | For one input column, pass `[x1, x2]`; for multiple input columns, pass `[[a1, b1], [a2, b2]]`. Re-run the failing item with `debug(...)`. |
| `concat()` raises `The parameter of concat cannot be None` | `concat()` was called with no pipeline arguments. | Pass one or more sibling `Pipeline` builders, for example `branch_a.concat(branch_b)`. |
| Unexpected column value after `concat(...)` | Multiple branches wrote the same output column name; concat order can overwrite duplicates. | Rename branch outputs to unique names unless overwriting is intentional and tested. |
| `time_window(...)` produces surprising grouping | Timestamp units or window units are wrong. | Pass timestamp column values in milliseconds; pass `size` and `step` as seconds. Ensure `timestamp_col` exists upstream and is monotonic enough for the intended grouping. |
| `reduce(...)` rejects a nested pipeline callable | Towhee disallows a `RuntimePipeline` object as the reduce function. | Use a lambda/callable/operator that accepts lists and returns reduced outputs. |

## Schema and output checklist

Before running a pipeline, sketch the columns:

```text
input('x')                    -> x
map('x', 'y', fn)             -> x, y
filter('y', 'z', 'y', pred)   -> x, z   # only for kept rows
output('x', 'z')              -> valid if x and z are present
```

Avoid these names:

```python
pipe.input('a,')       # comma invalid
pipe.input('my col')   # space invalid
pipe.input('1st')      # leading digit invalid
pipe.input('text-id')  # hyphen invalid
```

Use these names:

```python
pipe.input('a')
pipe.input('my_col')
pipe.input('_tmp1')
pipe.input('text_id')
```

## Output shape checklist

- One output column: return a scalar from `map`, `window`, `window_all`, or `reduce`; return a list of scalars from `flat_map`.
- Multiple output columns: return tuple/list values aligned to `output_schema`.
- `flat_map(('a', 'b'), ('x', 'y'), fn)` should return an iterable of two-item rows, such as `[(x1, y1), (x2, y2)]`.
- `window`/`time_window`/`window_all` callables receive lists for each input column, not scalar row values.

## Debug checklist

```python
viz = p.debug(input_value, profiler=True, tracer=True, include='lambda')
print(viz.result.to_list())
print(viz.tracer.nodes)
viz.profiler.show()
```

If this fails:

1. Remove `include` and `exclude` to avoid filtering out all nodes.
2. Use a single input before batch debug.
3. Replace Hub operators with lambda placeholders to isolate schema/dataflow errors.
4. Restore the real operator only after the lambda pipeline passes.

## AutoPipes and Hub checklist

- For offline-safe checks, use direct `pipe.input` pipelines or a local `AutoPipes` file path.
- Built-in pipeline names can still instantiate Hub operators and model libraries.
- Hub names require network/cache availability unless already cached.
- Optional operator dependencies can include deep-learning frameworks, tokenizers, image/audio/video libraries, connector clients, or model files.
- Do not treat a Hub/cache miss as a pipeline schema failure; first prove the same shape with lambdas.
