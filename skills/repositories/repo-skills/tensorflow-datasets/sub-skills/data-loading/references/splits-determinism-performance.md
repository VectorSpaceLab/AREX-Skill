# Splits, Determinism, and Performance

Use this reference before iterating over an existing TFDS dataset in training, evaluation, cross-validation, distributed, or benchmark workflows.

## Split string syntax

Pass split instructions to `tfds.load(..., split=...)` or `builder.as_dataset(split=...)`.

| Pattern | Example | Meaning |
|---|---|---|
| Plain split | `"train"`, `"test"` | Read the whole named split. Any split name can be used except reserved `"all"`. |
| List of splits | `["train", "test[:50%]"]` | Return one dataset per list item, preserving order. |
| Absolute slice | `"train[:4000]"`, `"train[123:450]"` | Select by absolute example positions in the split. |
| Percent slice | `"train[:75%]"`, `"train[25%:75%]"` | Select approximate percentage ranges; fractional percentages are supported. |
| Shard slice | `"train[:4shard]"`, `"train[4shard]"` | Select shard ranges or a shard by index. Inspect `info.splits[split].num_shards` first. |
| Union | `"train+test"`, `"train[:25%]+test"` | Interleave multiple split instructions together. |
| Full dataset | `"all"` | Union of all available splits. |

Examples:

```python
train75 = tfds.load("my_dataset", split="train[:75%]")
train_ds, test_ds = tfds.load("mnist", split=["train", "test[:50%]"])
combined = tfds.load("my_dataset", split="train[:20%]+validation")
```

## Split metadata

`DatasetInfo.splits` can report examples, filenames, shards, and file instructions for split slices:

```python
builder = tfds.builder("mnist")
info = builder.info
print(info.splits.keys())
print(info.splits["train"].num_examples)
print(info.splits["train"].num_shards)
print(info.splits["train[:15%]"].num_examples)
print(info.splits["train[:15%]"].file_instructions)
```

If a split expression fails in `info.splits[...]`, first check that split metadata exists for the prepared dataset/config/version.

## `tfds.even_splits` and distributed workers

`tfds.even_splits(split, n, drop_remainder=False)` returns non-overlapping sub-splits of the same source split expression:

```python
split0, split1, split2 = tfds.even_splits("train", n=3)
ds = tfds.load("my_dataset", split=split2)
```

Use it when each host/process should receive a different portion:

```python
splits = tfds.even_splits("train", n=num_workers, drop_remainder=True)
worker_split = splits[worker_index]
ds = tfds.load("my_dataset", split=worker_split, shuffle_files=True)
```

Operational details:

- With `drop_remainder=False`, remainder examples are distributed across early splits; counts can differ by at most one in uneven cases.
- With `drop_remainder=True`, TFDS drops examples that cannot be evenly divided.
- `tfds.split_for_jax_process(split, drop_remainder=True)` is a convenience wrapper that uses JAX process count/index to choose one even split.
- `even_splits` accepts composed split expressions such as `"train[75%:]+test"`.

## `ReadInstruction` and rounding

For explicit split objects rather than strings:

```python
split = (
    tfds.core.ReadInstruction("train", from_=50, to=75, unit="%")
    + tfds.core.ReadInstruction("test")
)
ds = tfds.load("my_dataset", split=split)
```

Units include absolute counts, percentages, and shard slices. Percent rounding can be controlled with `rounding="closest"` or `rounding="pct1_dropremainder"` where exact equal percent bucket sizes are needed.

## Determinism rules

TFDS aims for deterministic generation and reproducible split membership for a fixed dataset version, but read order depends on the input pipeline.

| Setting | Determinism behavior | Use when |
|---|---|---|
| `shuffle_files=False` (default) | Deterministic file order and example read order for the same read config. | Evaluation, debugging, reproducibility, metadata inspection. |
| Split slicing | Selects the same set of examples for a fixed version/split expression. | Cross-validation and reproducible subset definitions. |
| `shuffle_files=True` | Shuffles shards/files between epochs; read order is intentionally non-deterministic unless seeded/configured. | Large sharded training datasets. |
| `ReadConfig(shuffle_seed=...)` | Makes file shuffling deterministic for the given seed. Change seeds across epochs if you still need epoch variation. | Reproducible training experiments. |
| `ReadConfig(experimental_interleave_sort_fn=...)` | Gives direct control over file-instruction order. | Advanced recovery/debug/preemptable pipelines. |
| `ReadConfig(add_tfds_id=True)` | Adds a `tfds_id` field to dictionary examples for tracing example identity. | Debugging split membership/order. |

Important caveat: `ds.take(25)` on `split="train"` is not equivalent to `split="train[:25]"`. Split slicing selects by split-example IDs, while iteration order may be affected by shard interleave.

## `ReadConfig` knobs

Common loading-related fields:

```python
read_config = tfds.ReadConfig(
    shuffle_seed=123,
    shuffle_reshuffle_each_iteration=True,
    interleave_cycle_length=4,
    interleave_block_length=16,
    add_tfds_id=False,
    try_autocache=True,
    skip_prefetch=False,
    num_parallel_calls_for_decode=tf.data.AUTOTUNE,
    num_parallel_calls_for_interleave_files=tf.data.AUTOTUNE,
    override_buffer_size=None,
)

ds = tfds.load(
    "my_dataset",
    split="train",
    shuffle_files=True,
    read_config=read_config,
)
```

Guidance:

- `shuffle_files=True` may set TensorFlow dataset `deterministic` behavior to false for performance unless seed/options override it.
- `try_autocache=False` disables TFDS small-dataset auto-caching.
- `skip_prefetch=True` is useful when the caller will explicitly add prefetch later and wants to avoid double prefetching.
- `override_buffer_size` can reduce reader memory pressure when TFRecord/input buffers are too large.
- `enable_ordering_guard=True` helps catch operations that violate ordered-dataset assumptions.
- `assert_cardinality=True` checks that an epoch reads the expected number of examples from metadata.

## Multi-worker TensorFlow reads

For TensorFlow distributed training, pass a `tf.distribute.InputContext` through `ReadConfig`:

```python
input_context = tf.distribute.InputContext(
    input_pipeline_id=worker_id,
    num_input_pipelines=num_workers,
)
read_config = tfds.ReadConfig(input_context=input_context)
ds = tfds.load("my_dataset", split="train", read_config=read_config)
```

TFDS first applies the split expression, then shards files across workers. If the selected split has fewer shards than workers, some workers would be empty and TFDS raises an error. With `shuffle_files=True`, each worker shuffles only within its assigned file subset.

## Benchmarking

Use `tfds.benchmark` on any iterable, including a `tf.data.Dataset` or `tfds.as_numpy(ds)`. It consumes the iterable.

```python
ds = tfds.load("mnist", split="train").batch(32).prefetch(1)
result = tfds.benchmark(ds, batch_size=32)
```

Pass the real `batch_size` so examples/second is normalized correctly. Use `num_iter` for bounded checks:

```python
tfds.benchmark(ds, num_iter=100, batch_size=32)
```

Expect a second pass over small auto-cached datasets to be faster than the first pass.

## Small-dataset performance

For small datasets that fit in memory:

1. Decode/map deterministic preprocessing.
2. Cache.
3. Shuffle using a full or task-appropriate buffer.
4. Batch.
5. Prefetch.

```python
ds = ds.map(preprocess, num_parallel_calls=tf.data.AUTOTUNE)
ds = ds.cache()
ds = ds.shuffle(info.splits["train"].num_examples)
ds = ds.batch(128)
ds = ds.prefetch(tf.data.AUTOTUNE)
```

TFDS auto-caches datasets when the full dataset size is known, below the built-in small-dataset threshold, and file shuffling is disabled or only one shard is read. Disable with `tfds.ReadConfig(try_autocache=False)` when auto-caching is not desired.

## Large-dataset performance

For large sharded datasets:

- Prefer `shuffle_files=True` during training so each epoch varies shard order.
- Do not call `cache()` unless the selected subset truly fits in memory/disk cache and the user wants that behavior.
- Batch and prefetch after expensive deterministic preprocessing.
- Use `tfds.decode.SkipDecoding()` or `tfds.decode.PartialDecoding(...)` to avoid decoding unused or soon-to-be-filtered image/video/features.
- Consider `ReadConfig(override_buffer_size=...)` if reader buffers contribute to memory pressure.
- Use framework-level `tf.data.Options` to disable autotune, auto-shard, or injected prefetch only when diagnosing RAM or determinism issues.

## Faster or partial decoding

Skip image/video decoding before filtering or custom decode:

```python
ds, info = tfds.load(
    "imagenet2012",
    split="train",
    with_info=True,
    decoders={"image": tfds.decode.SkipDecoding()},
)

def decode_after_filter(example):
    example["image"] = info.features["image"].decode_example(example["image"])
    return example

ds = ds.filter(predicate).map(decode_after_filter)
```

Load only needed nested features:

```python
builder = tfds.builder("my_dataset")
ds = builder.as_dataset(
    split="train",
    decoders=tfds.decode.PartialDecoding({
        "image": True,
        "metadata": {"scene_name", "num_objects"},
        "objects": {"label"},
    }),
)
```

Partial decoding reuses feature metadata such as label names and shapes when the requested subset matches the actual feature structure.

## RAM triage checklist

When input pipelines use too much RAM:

1. Remove accidental full in-memory conversions (`batch_size=-1`, full `as_dataframe`, full `list(tfds.as_numpy(ds))`).
2. Avoid caching large datasets.
3. Lower reader buffer size:

   ```python
   read_config = tfds.ReadConfig(override_buffer_size=1024)
   ds = builder.as_dataset(split="train", read_config=read_config)
   ```

4. Skip unused feature decoding with `PartialDecoding`.
5. Explicitly set TensorFlow dataset options to disable autotune or injected prefetch only as a targeted diagnostic.
