# Ray Data Performance And Troubleshooting

Use this guide after the pipeline is functionally correct. Start with `ds.materialize().stats()` and change one tuning knob at a time.

## Block Sizing Basics

Ray Data stores intermediate and output data as blocks in the object store. Block counts affect read task count, downstream transform parallelism, object-store pressure, and scheduler overhead.

Default read block selection uses these heuristics:

1. Start from `DataContext.read_op_min_num_blocks`, defaulting to about `200`.
2. Avoid tiny blocks below `DataContext.target_min_block_size`, defaulting to about `1 MiB`.
3. Avoid very large blocks above `DataContext.target_max_block_size`, defaulting to about `128 MiB`.
4. Increase blocks to use available CPUs, commonly at least about `2x` available CPUs.

Practical targets:

- Tiny tests: `override_num_blocks=1` or `2`.
- Many medium files: start near file count or available CPUs, then inspect stats.
- Large files or OOM: increase blocks or lower `target_max_block_size`.
- Too many tiny blocks: coalesce with `map_batches(..., batch_size=...)` or repartition when exact block count is required.

## `override_num_blocks`, Fusion, And Materialization

`override_num_blocks` requests output blocks for readers and in-memory creation. When a read is followed by `map` or `map_batches`, Ray Data may fuse the read and transform so the same tasks read and transform.

Important behavior:

- If the number of input files is smaller than requested blocks, Ray can split read outputs into more blocks before downstream transforms.
- Splitting can prevent read+map fusion, materializing intermediate read output to the object store before the map runs.
- Setting `override_num_blocks` equal to actual read-task/file parallelism can preserve fusion when that is desirable.
- Even with `override_num_blocks=1`, a large task can emit multiple blocks if block-size safeguards split output.

Debug steps:

```python
mat = ds.materialize()
print(mat.stats())
```

Look for operator names such as `ReadCSV->MapBatches(...)` for fused execution or `ReadCSV->SplitBlocks(...)` followed by `Map...` for split/materialized execution.

## Read Concurrency And Resources

Use reader options before changing global cluster settings:

```python
ds = ray.data.read_parquet(
    path,
    columns=["id", "feature"],
    override_num_blocks=256,
    concurrency=128,
    ray_remote_args={"num_cpus": 0.25},
)
```

- `concurrency` caps active read tasks.
- `ray_remote_args={"num_cpus": 0.25}` increases IO concurrency per CPU for IO-bound readers.
- Use higher `num_cpus` or lower `concurrency` for CPU-heavy parsing or decompression.
- For cloud reads, ensure every worker has credentials and filesystem dependencies, not just the driver.

## Transform Concurrency And Resources

For `map_batches`:

- Use `batch_size` to control per-UDF memory and vectorization efficiency.
- Use `batch_format="pandas"` for pandas operations, `"pyarrow"` for Arrow/Polars operations, and `"numpy"` for array dicts.
- Use `concurrency=n` to cap active transform tasks or actors.
- Use `num_cpus`, `num_gpus`, and `memory` to reserve logical resources. These are scheduling reservations, not hard runtime memory limits.
- Use a callable class when setup is expensive; Ray Data reuses state through actors.
- For GPU `map_batches`, set an explicit integer `batch_size` and `num_gpus`.

If a transform mutates input batches and fails with read-only or unexpected shared-buffer errors, copy the batch before mutation or set `zero_copy_batch=False` when appropriate.

## Optional Dependencies

Common symptoms and fixes:

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: pyarrow` | Ray Data file IO dependency missing | Install `ray[data]` or `pyarrow`. |
| `ModuleNotFoundError: pandas` | pandas batch or DataFrame creation missing | Install `pandas` or avoid `batch_format="pandas"`. |
| GCS read fails with missing filesystem | `gcsfs` absent or not installed on workers | Install `gcsfs` wherever Ray workers run and pass a compatible filesystem when needed. |
| Azure read fails with missing filesystem | `adlfs` absent | Install `adlfs` wherever workers run. |
| Image read fails | image decoder dependencies missing | Install the image stack required by the selected reader. |

Prefer narrow extras (`ray[data]` plus the specific filesystem/image package) over broad `ray[all]` installs.

## Schema And Batch-Format Errors

### Missing Or Renamed Columns

```python
def validate(batch):
    missing = {"id", "amount"}.difference(batch.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    return batch
```

- Print `ds.schema()` immediately after reads.
- Read a tiny representative sample with `take` before launching large writes.
- For Parquet, use `columns=[...]` to request the exact set needed.
- For CSV, pass explicit PyArrow reader/convert options when inference creates wrong types.

### Wrong Batch Type

- A pandas UDF must use `batch_format="pandas"`.
- A PyArrow UDF must use `batch_format="pyarrow"`.
- A NumPy-dict UDF must use `batch_format="numpy"` or accept Ray's default format.
- Return one of the supported batch types: pandas DataFrame, PyArrow Table, or `dict[str, numpy.ndarray]`.

### Row Count Changes

`map_batches` can change row counts. When debugging row-count changes:

- Check `len(batch)` or `batch.num_rows` inside the UDF for input size.
- Validate output column lengths are equal.
- Use a tiny `from_items` fixture with known expected rows.
- Inspect `stats()` for input/output row counts per operator.

## OOM, Spilling, And Disk Pressure

Ray Data uses streaming execution, but large blocks, materialization, shuffles, and writes can exceed object-store capacity.

Symptoms:

- Object spilling messages.
- Disk filling during Data jobs.
- Worker OOM or object-store OOM.
- Slow jobs after a previously fast read/map chain.

Fix order:

1. Avoid unnecessary `materialize()` before a write or downstream iterator.
2. Increase blocks with `override_num_blocks` so each task processes less data.
3. Lower `batch_size` for `map_batches` if UDF memory spikes.
4. Lower `DataContext.target_max_block_size` for future jobs if blocks are too large.
5. Use `columns=[...]` for Parquet projection pushdown.
6. Reduce concurrent reads/transforms with `concurrency` or larger `num_cpus`/`memory` reservations.
7. Avoid all-to-all operations (`sort`, `groupby`, exact `repartition`) unless necessary.

## Tiny Blocks And Scheduler Overhead

Symptoms:

- `stats()` shows many blocks below `1 MiB`.
- Job spends more time scheduling than processing.
- Metadata overhead or driver memory is high.

Fixes:

- Reduce `override_num_blocks` for reads.
- Raise `target_min_block_size` for future reads if many tiny files are unavoidable.
- Coalesce with streaming `map_batches(lambda batch: batch, batch_size=desired_rows)`.
- Use `repartition(n)` only when exact partition count is required; it is an all-to-all operation.
- Control writer file sizing with `max_rows_per_file` or related writer options.

## Path And Cloud Issues

| Situation | Diagnosis | Fix |
| --- | --- | --- |
| `local://` works on one node but cluster read fails | Path exists only on driver | Use shared storage/cloud or copy data to all nodes. |
| Plain `/path` read fails on workers | Path not mounted everywhere | Use NFS/shared mount or `local://` for single-node development. |
| Cloud read works on driver but fails in tasks | Worker credentials/filesystem missing | Configure credentials and dependencies on every worker. |
| Missing files are silently skipped | `ignore_missing_paths=True` was used | Remove it unless partial input is intended. |
| Too many output files | Too many blocks or small row/file sizing | Reduce blocks or set writer row sizing. |

## Determinism And Ordering

Ray Data does not preserve block order by default for performance. If deterministic order is required:

```python
ctx = ray.data.DataContext.get_current()
ctx.execution_options.preserve_order = True
```

This can reduce performance on larger clusters. Prefer sorting by a stable key when sorted semantic output is required.

## Debug Checklist

1. Confirm imports: `import ray, ray.data`.
2. Verify extras: `ray[data]`, `pandas`, `pyarrow`, and any cloud/image filesystem package.
3. Start with a tiny `from_items` pipeline and `take`.
4. Print `schema()` after reads and after major transforms.
5. Trigger execution with `take`, `materialize`, `iter_batches`, or a writer.
6. Inspect `materialize().stats()` for task counts, block counts, row counts, fusion, and spilling clues.
7. Tune `override_num_blocks`, `concurrency`, `batch_size`, and projection before changing global `DataContext`.
8. If handing off to Train/Tune, reserve enough CPUs/object-store memory for both Data tasks and training/tuning workers.
