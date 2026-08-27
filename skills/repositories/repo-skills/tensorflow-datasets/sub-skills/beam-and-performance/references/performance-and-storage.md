# Performance And Storage

Use this reference to tune TFDS storage layout, sharding, GCS placement, and
reader pipelines after choosing the Beam workflow.

## Prepared-file formats

TFDS prepares examples into sharded record files. The supported file-format names
for generation are:

| Format | Notes |
|---|---|
| `tfrecord` | Default TFDS format. Supports `tf.data` reading. Does not provide random access positions. |
| `array_record` | Supports random access through `as_data_source`; not implemented for `.as_dataset()`/`tf.data` reading in this TFDS version. |
| `riegeli` | Supports `tf.data` reading when the Riegeli TensorFlow dependency is installed. |
| `parquet` | Supports random access and `tf.data` reading through a PyArrow-backed adapter; TFDS currently stores serialized examples in a single binary `data` column rather than exposing feature columns. |

CLI generation:

```bash
tfds build DATASET[/CONFIG] --file_format=tfrecord
```

Programmatic generation:

```python
builder.download_and_prepare(file_format="array_record")
```

Reading a dataset prepared in a non-default format may require specifying the
format or using the appropriate API:

```python
read_config = tfds.ReadConfig(file_format="parquet")
ds = builder.as_dataset(split="train", read_config=read_config)

# ArrayRecord is for data-source/random-access style reading.
source = builder.as_data_source(split="train")
```

Validate file-format support before rebuilding a large dataset. Changing format
usually means preparing a new dataset version/output directory or intentionally
rebuilding into an isolated data directory.

## Shard sizing and counts

TFDS can compute the shard count from dataset size, or you can force it.

CLI controls:

```bash
tfds build DATASET[/CONFIG] \
  --num_shards=128 \
  --max_shard_size_mb=1024
```

Programmatic controls:

```python
download_config = tfds.download.DownloadConfig(
    num_shards=128,
    min_shard_size=64 << 20,
    max_shard_size=1024 << 20,
)
builder.download_and_prepare(download_config=download_config)
```

Guidance:

- More shards can increase read parallelism but add file-listing overhead,
  metadata overhead, and remote-storage operation costs.
- Too few shards limit parallel reading and distributed-worker utilization.
- If `num_shards` is omitted, TFDS uses min/max shard size heuristics.
- `num_shards` is especially important with `nondeterministic_order=True`, where
  the no-shuffle Beam writer uses the configured shard count when present.
- For multi-worker training, avoid fewer shards than input workers. TFDS can
  raise an error when `ReadConfig.input_context.num_input_pipelines` exceeds the
  available shard count.

## GCS data directories and public GCS reads

TFDS can use Google Cloud Storage in two distinct ways:

1. **Use a `gs://` data directory** to store prepared data for cloud workers or
   shared readers:

   ```python
   ds = tfds.load("mnist", split="train", data_dir="gs://BUCKET/tensorflow_datasets")
   ```

2. **Read TFDS-hosted public datasets from GCS** when available:

   ```python
   if tfds.is_dataset_on_gcs("mnist"):
       ds = tfds.load("mnist", split="train", try_gcs=True)
   ```

Credential and cost boundaries:

- Anonymous access can work for public buckets; private buckets require Google
  account or service-account credentials.
- Do not write or publish to a bucket until the user has confirmed the target,
  overwrite policy, budget, and identity.
- Remote GCS reads can incur network cost and latency. Prefer colocating compute
  and storage for large training or Dataflow jobs.
- Some builders use file APIs that may not work with GCS paths; test a tiny
  generation/read path before committing to a large build.

## Reader performance knobs

### Benchmark first

```python
ds = tfds.load("DATASET", split="train").batch(32).prefetch()
tfds.benchmark(ds, batch_size=32)
```

Run the benchmark after constructing the real pipeline. Normalize by
`batch_size` so reports are examples/second rather than only iterations/second.

### Small datasets

Small TFDS datasets can be dominated by record-reading overhead. TFDS auto-cache
can apply when:

- total dataset size is known and under about 250 MiB; and
- `shuffle_files` is disabled, or only a single shard is read.

Opt out when memory is constrained:

```python
read_config = tfds.ReadConfig(try_autocache=False)
ds = tfds.load("DATASET", split="train", read_config=read_config)
```

Explicit cache order for small supervised training:

```python
ds = tfds.load("mnist", split="train", as_supervised=True)
ds = ds.map(normalize, num_parallel_calls=tf.data.AUTOTUNE)
ds = ds.cache()
ds = ds.shuffle(num_train_examples)
ds = ds.batch(128)
ds = ds.prefetch(tf.data.AUTOTUNE)
```

Apply random image augmentations after `cache()` and typically after `batch()` so
randomness is not cached and operations can be vectorized.

### Large datasets

Large sharded datasets should normally not be cached in memory. Use file-level
shuffling plus record-level shuffling for training:

```python
ds = tfds.load("DATASET", split="train", shuffle_files=True)
ds = ds.shuffle(buffer_size)
ds = ds.batch(batch_size)
ds = ds.prefetch(tf.data.AUTOTUNE)
```

When `shuffle_files=True`, TFDS can set `tf.data` deterministic behavior to
`False` for speed unless a seed or explicit options override it. If deterministic
training input is required, set `tfds.ReadConfig(shuffle_seed=...)` or configure
`tf.data.Options().deterministic` explicitly.

### Multi-worker reading

TensorFlow distributed input:

```python
input_context = tf.distribute.InputContext(
    input_pipeline_id=worker_id,
    num_input_pipelines=num_workers,
)
read_config = tfds.ReadConfig(input_context=input_context)
ds = tfds.load("DATASET", split="train", read_config=read_config)
```

This shards the already selected split across workers. File shuffling occurs
within each worker's assigned files, not across workers.

JAX-style split distribution:

```python
split = tfds.split_for_jax_process("train", drop_remainder=True)
ds = tfds.load("DATASET", split=split)
```

or equivalently choose from `tfds.even_splits("train", n=process_count)`.

### Memory pressure / RAM symptoms

If `tf.data` uses too much RAM:

```python
read_config = tfds.ReadConfig(override_buffer_size=1024)
ds = builder.as_dataset(split="train", read_config=read_config)
```

You can also disable selected automatic `tf.data` behaviors:

```python
options = tf.data.Options()
options.autotune.enabled = False
options.experimental_distribute.auto_shard_policy = (
    tf.data.experimental.AutoShardPolicy.OFF
)
options.experimental_optimization.inject_prefetch = False

ds = ds.with_options(options)
```

Use these only after measuring; disabling autotune or prefetch can reduce
throughput.

## Decode and feature skipping for throughput

For image-heavy or feature-rich datasets:

- Skip expensive decoding until after filtering/cropping.
- Decode only the features the model uses.
- Avoid carrying large unused text/images/audio through maps, batches, and host
  memory.

Common shape:

```python
ds = tfds.load(
    "DATASET",
    split="train",
    decoders={"image": tfds.decode.SkipDecoding()},
)
# Filter or crop first, then decode with a TensorFlow op.
```

For more generic decode syntax and loading examples, route to `data-loading`.

## Storage and performance checklist

Before expensive generation or reading:

1. Dataset/config/version and data directory are explicit.
2. File format matches the intended reader (`as_dataset` vs `as_data_source`).
3. Shard count is sufficient for expected worker parallelism.
4. Determinism and `nondeterministic_order` policy are documented.
5. GCS bucket, credentials, region, and network cost are approved when remote
   storage is involved.
6. Final training pipeline has benchmark results or a plan to collect them.
7. Cache, shuffle, batch, prefetch, decode, and unused-feature decisions are
   ordered intentionally.
