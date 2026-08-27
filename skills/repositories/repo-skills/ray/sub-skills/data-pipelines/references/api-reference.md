# Ray Data API Reference

This reference summarizes the Ray Data APIs most often needed for data-pipeline tasks. It is based on the Ray Data package surface and repository docs/tests, distilled into self-contained guidance.

## Installation And Imports

- Use `pip install "ray[data]"` for Ray Data workflows. Add `pandas`, `pyarrow`, image, cloud filesystem, or ML libraries only when the selected source or transform requires them.
- Use `import ray` and access Data APIs through `ray.data`.
- Python support is `>=3.10` for this Ray version family.
- The inspected public package imports `ray.data` successfully and exposes the Data APIs below.

## Dataset Creation

| API | Use For | Notes |
| --- | --- | --- |
| `ray.data.from_items(items, *, parallelism=-1, override_num_blocks=None)` | Small in-memory Python lists; fixtures; synthetic tests | Dict items become row columns; non-dict values become an `item` column. `override_num_blocks` controls initial blocks but is capped by item count. Returns a materialized dataset. |
| `ray.data.from_pandas(df)` | Single-node pandas DataFrame | Preserves tabular columns; useful before scaling with `map_batches(batch_format="pandas")`. |
| `ray.data.from_numpy(array)` | NumPy arrays | Treats the outer axis as rows; the default column is usually `data`. |
| `ray.data.from_arrow(table)` | PyArrow tables | Good for schema-first tabular pipelines and lower-copy `batch_format="pyarrow"` transforms. |

Validation checks:

```python
ds = ray.data.from_items([{"id": 1, "value": 2}], override_num_blocks=1)
print(ds.schema())
print(ds.take(1))
```

## File Readers

### CSV

```python
ds = ray.data.read_csv(
    paths,
    filesystem=None,
    parallelism=-1,
    ray_remote_args=None,
    partition_filter=None,
    partitioning="hive default",
    include_paths=False,
    ignore_missing_paths=False,
    shuffle=None,
    file_extensions=None,
    concurrency=None,
    override_num_blocks=None,
    **arrow_csv_args,
)
```

Key options:

- `paths`: a string or list of file/directory paths. Use normal paths for shared local/NFS storage, `local://...` for node-local files on the submitting node, and cloud URIs when all workers can authenticate.
- `arrow_csv_args`: forwarded to PyArrow CSV reading; use these for delimiter, schema, convert, or parse options.
- `arrow_open_stream_args={"compression": "gzip"}` handles compressed inputs when the Arrow codec supports them.
- `include_paths=True` adds source path metadata where the reader supports it.
- `ignore_missing_paths=True` tolerates missing paths; use only when partial data is acceptable.
- `concurrency` caps concurrent read tasks; `ray_remote_args={"num_cpus": 0.25}` allows more IO tasks per CPU for IO-bound reads.
- `override_num_blocks` requests the number of output blocks/read tasks and also influences fused downstream map tasks.

### Parquet

```python
ds = ray.data.read_parquet(
    paths,
    filesystem=None,
    columns=None,
    parallelism=-1,
    ray_remote_args=None,
    tensor_column_schema=None,
    partition_filter=None,
    partitioning="hive default",
    shuffle=None,
    include_paths=False,
    file_extensions=["parquet"],
    concurrency=None,
    override_num_blocks=None,
    **arrow_parquet_args,
)
```

Key options:

- `columns=[...]` performs projection pushdown and is preferred over reading all columns then calling `select_columns`.
- `partitioning`/`partition_filter` handle directory partition layouts, commonly Hive-style paths.
- `filesystem` accepts a PyArrow-compatible filesystem object for GCS, Azure, custom fsspec, or authenticated cloud access.
- `override_num_blocks` and `concurrency` have the same tuning role as in CSV reads.

### Images And Text

- `ray.data.read_images(path, include_paths=True)` creates image tensor rows, commonly with an `image` column and optional `path` metadata.
- `ray.data.read_text(path)` creates rows with a text column.
- Image decoding and cloud filesystems may require extra packages beyond base Ray.

## Row And Batch Transforms

| API | Function Shape | Use When |
| --- | --- | --- |
| `Dataset.map(fn, *, num_cpus=None, num_gpus=None, memory=None, concurrency=None, fn_args=None, fn_kwargs=None, **ray_remote_args)` | `dict -> dict` | Exactly one output row per input row; simple per-row parsing or feature addition. |
| `Dataset.flat_map(fn, *, concurrency=None, fn_args=None, fn_kwargs=None, **ray_remote_args)` | `dict -> list[dict]` | One input row may produce zero, one, or many output rows. |
| `Dataset.map_batches(fn_or_class, *, batch_size=None, batch_format="default", zero_copy_batch=True, fn_args=None, fn_kwargs=None, fn_constructor_args=None, fn_constructor_kwargs=None, num_cpus=None, num_gpus=None, memory=None, concurrency=None, ray_remote_args_fn=None, **ray_remote_args)` | pandas, PyArrow, or NumPy batch in/out | Vectorized transforms, schema changes, model inference, stateful setup, or row-count-changing batch operations. |

`map_batches` batch formats:

- `batch_format="numpy"`: input is a `dict[str, numpy.ndarray]`.
- `batch_format="pandas"`: input is a `pandas.DataFrame`; convenient for CSV-like tabular transforms.
- `batch_format="pyarrow"`: input is a `pyarrow.Table`; often lowest-copy for file readers that produce Arrow blocks.
- `batch_format="default"`: Ray chooses the default representation, commonly NumPy dict batches for user functions.
- `zero_copy_batch=True` can avoid copies when the format matches the block representation, but user code must not mutate read-only views unless it copies first.

Stateful transforms:

```python
class Transformer:
    def __init__(self, scale):
        self.scale = scale

    def __call__(self, batch):
        batch["value2"] = batch["value"] * self.scale
        return batch

ds = ds.map_batches(
    Transformer,
    fn_constructor_args=(2,),
    batch_format="pandas",
    concurrency=2,
)
```

Use class callables when setup is expensive or state must be reused. Ray Data executes function transforms with tasks and class transforms with actors.

## Writers

### Parquet

```python
ds.write_parquet(
    path,
    partition_cols=None,
    filesystem=None,
    filename_provider=None,
    min_rows_per_file=None,
    max_rows_per_file=None,
    num_rows_per_file=None,
    mode="append",
    concurrency=None,
    ray_remote_args=None,
    **arrow_parquet_args,
)
```

Key options:

- `path`: destination directory/URI. Use a shared filesystem or cloud URI for distributed writes; a local temp directory is fine for local smoke tests.
- `partition_cols=[...]`: writes Hive-style partition directories by column values.
- `mode`: defaults to append semantics; set an overwrite mode only when the destination can safely be replaced.
- `min_rows_per_file`, `max_rows_per_file`, or `num_rows_per_file`: control file sizing. Avoid creating many tiny files.
- `concurrency` caps write tasks; `ray_remote_args` controls writer resources.

Validation checks:

```python
materialized = ds.materialize()
print(materialized.stats())
materialized.write_parquet(output_dir, mode="overwrite")
roundtrip = ray.data.read_parquet(output_dir)
print(roundtrip.schema())
print(roundtrip.take(3))
```

## Context And Execution Knobs

```python
ctx = ray.data.DataContext.get_current()
ctx.read_op_min_num_blocks = 200
ctx.target_min_block_size = 1 * 1024 * 1024
ctx.target_max_block_size = 128 * 1024 * 1024
ctx.execution_options.preserve_order = False
ctx.execution_options.resource_limits = ctx.execution_options.resource_limits.copy(
    cpu=10,
    gpu=0,
    object_store_memory=2e9,
)
```

Common use:

- `read_op_min_num_blocks`: lower for small local jobs, higher for large files or autoscaled clusters.
- `target_min_block_size`: raise to avoid tiny block overhead.
- `target_max_block_size`: lower to avoid OOMs; raise to reduce block overhead when memory is ample.
- `execution_options.preserve_order=True`: deterministic block order at a performance cost.
- `execution_options.resource_limits`: reserve cluster capacity when multiple Ray Data jobs, Train jobs, or Tune trials share a cluster.

Prefer per-reader/per-transform parameters (`override_num_blocks`, `concurrency`, `ray_remote_args`, `batch_size`) before changing global context in reusable code.
