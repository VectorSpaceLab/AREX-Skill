# Ray Data Workflows

These recipes are self-contained starting points for common Ray Data tasks. They intentionally avoid source-repository dependencies and external network assumptions.

## Start A Small Local Pipeline

```python
import ray

ray.init(ignore_reinit_error=True)

ds = ray.data.from_items(
    [{"id": i, "text": f"item-{i}", "value": float(i)} for i in range(8)],
    override_num_blocks=2,
)

result = (
    ds.map(lambda row: {**row, "label": row["id"] % 2})
    .map_batches(
        lambda batch: {**batch, "value2": batch["value"] * 10},
        batch_format="numpy",
        batch_size=4,
    )
)

print(result.schema())
print(result.take(3))
print(result.materialize().stats())
ray.shutdown()
```

Use this pattern before touching real storage. If it fails, debug package installation, imports, object-store memory, or UDF code before debugging cloud/NFS credentials.

## Load Local Or Shared Files

### Shared Local/NFS Paths

Use ordinary paths when every worker can see the same mounted path:

```python
import ray

ray.init(ignore_reinit_error=True)
ds = ray.data.read_parquet("<shared-data-dir>/events/", columns=["user_id", "ts", "amount"])
print(ds.schema())
print(ds.take(2))
```

### Driver-Local Files

Use `local://` only when files live on the local node that submits the job. This is convenient for one-node development but limits distributed reads because other nodes cannot access that path.

```python
ds = ray.data.read_csv("local://<driver-local-input.csv>", override_num_blocks=1)
```

If a local file path is accessible on all nodes, omit `local://` so Ray can schedule read tasks across the cluster.

## Load Cloud Files

Cloud URIs require credentials and compatible filesystem packages on every worker node.

```python
import ray

ray.init(ignore_reinit_error=True)
ds = ray.data.read_parquet(
    "s3://bucket/prefix/",
    columns=["id", "feature"],
    concurrency=64,
    ray_remote_args={"num_cpus": 0.25},
)
print(ds.materialize().stats())
```

For GCS, Azure, or custom filesystems, create a PyArrow-compatible filesystem object and pass it as `filesystem=...`. Install only the narrow dependency needed, such as `gcsfs` or `adlfs`.

## Build CSV-To-Parquet With Pandas Batches

```python
import pandas as pd
import ray

ray.init(ignore_reinit_error=True)

def clean(batch: pd.DataFrame) -> pd.DataFrame:
    required = {"user_id", "amount"}
    missing = required.difference(batch.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    batch = batch.copy()
    batch["amount"] = pd.to_numeric(batch["amount"], errors="coerce").fillna(0.0)
    batch["amount_bucket"] = (batch["amount"] // 10).astype("int64")
    return batch

ds = ray.data.read_csv(
    "<shared-data-dir>/raw_csv/",
    override_num_blocks=128,
    ignore_missing_paths=False,
)
cleaned = ds.map_batches(
    clean,
    batch_format="pandas",
    batch_size=10_000,
    concurrency=32,
)
print(cleaned.materialize().stats())
cleaned.write_parquet(
    "<shared-data-dir>/curated_parquet/",
    partition_cols=["amount_bucket"],
    max_rows_per_file=250_000,
    mode="overwrite",
)
```

Schema mismatch recovery:

- Print `ds.schema()` immediately after the read.
- Validate required columns inside the UDF and raise a concise error.
- Use `pd.to_numeric(..., errors="coerce")`, explicit casts, or PyArrow reader options when source files have mixed types.
- If individual files differ in columns, first read a representative subset and decide whether to normalize upstream, add missing columns in the UDF, or read with explicit Arrow options.

## Use PyArrow Batches To Reduce Copies

Many file readers produce Arrow-backed blocks. Use `batch_format="pyarrow"` when transforms are naturally Arrow or Polars operations.

```python
import pyarrow as pa
import pyarrow.compute as pc
import ray

ray.init(ignore_reinit_error=True)

def add_flag(table: pa.Table) -> pa.Table:
    is_large = pc.greater(table["amount"], 100)
    return table.append_column("is_large", is_large)

ds = ray.data.read_parquet("<shared-data-dir>/events/", columns=["id", "amount"])
out = ds.map_batches(add_flag, batch_format="pyarrow", batch_size=50_000)
print(out.take(2))
```

## Use NumPy Dict Batches For Array Data

```python
import numpy as np
import ray

ray.init(ignore_reinit_error=True)

def normalize(batch):
    values = batch["value"].astype("float64")
    return {"id": batch["id"], "value": values, "z": (values - values.mean()) / (values.std() + 1e-9)}

ds = ray.data.from_items([{"id": i, "value": i * 2} for i in range(100)], override_num_blocks=4)
print(ds.map_batches(normalize, batch_format="numpy", batch_size=25).take(3))
```

## Write Outputs Safely

- Write to a directory, not an existing data file.
- Prefer shared/NFS/cloud destinations for distributed jobs.
- Control file sizes to avoid many tiny files.
- Use `partition_cols` only for low/medium-cardinality columns.
- Round-trip a small read after writing when correctness matters.

```python
out.write_parquet(
    output_path,
    partition_cols=["date"],
    max_rows_per_file=500_000,
    concurrency=16,
    mode="overwrite",
)
check = ray.data.read_parquet(output_path)
print(check.schema())
print(check.take(1))
```

## Integrate With Core Tasks And Actors

Use Ray Data for dataset-level work; route low-level task/actor design to the Core sub-skill when needed.

Typical integration choices:

- Use `map_batches` functions for stateless parallel transforms.
- Use callable classes with `concurrency` for stateful transforms that need one-time setup per worker.
- Use `num_cpus`, `num_gpus`, `memory`, and custom `resources` to reserve logical resources for Data tasks/actors.
- Avoid manually creating many Core tasks over `ds.take_all()` output; that defeats streaming and object-store management.

## Hand Off To Train Or Tune

Use this sub-skill to create and validate the `Dataset`; route trainer/tuner configuration to the Train/Tune sub-skill.

Checklist before handoff:

- `ds.schema()` matches the trainer's expected columns.
- `ds.take(2)` validates row values and types.
- `ds.materialize().stats()` shows reasonable block sizes and no unexpected excessive materialization.
- Data jobs leave enough CPU/object-store capacity for training workers or Tune trials.
- If Tune trials run concurrently, cap `max_concurrent_trials` or Data execution resources so trial workers do not starve Data read/map tasks.

## Validate Lazy Pipelines

Ray Data transformations are lazy. Trigger execution deliberately:

```python
print(ds.schema())        # May inspect metadata/schema.
print(ds.take(5))         # Executes enough to fetch sample rows.
mat = ds.materialize()    # Executes and stores dataset blocks.
print(mat.stats())        # Shows operator names, task counts, rows, blocks, timings.
mat.write_parquet(path)   # Executes and writes the full pipeline.
```

If a pipeline appears to do nothing, confirm that a terminal action such as `take`, `iter_batches`, `materialize`, or a write has been called.
