# API Reference for Data Loading

This reference records the public loading API surface verified for this sub-skill. Use it as a local operating guide rather than as a complete package API index.

## Core loading functions

### `tfds.load`

Verified signature:

```python
tfds.load(
    name,
    *,
    split=None,
    data_dir=None,
    batch_size=None,
    shuffle_files=False,
    download=True,
    as_supervised=False,
    decoders=None,
    read_config=None,
    with_info=False,
    builder_kwargs=None,
    download_and_prepare_kwargs=None,
    as_dataset_kwargs=None,
    try_gcs=False,
    file_format=None,
)
```

Semantics:

1. Calls `tfds.builder(name, data_dir=data_dir, try_gcs=try_gcs, **builder_kwargs)`.
2. Calls `builder.download_and_prepare(**download_and_prepare_kwargs)` when `download=True` and data is not already prepared.
3. Calls `builder.as_dataset(...)` with split, batching, supervised output, decoders, shuffle, read config, and any `as_dataset_kwargs`.
4. Returns a `tf.data.Dataset`, a split dictionary, or a list/structure matching the `split` argument. If `with_info=True`, returns `(dataset_or_structure, DatasetInfo)`.

Key options:

- `name`: `dataset`, `dataset/config`, `dataset:version`, or `dataset/config:version`. Some builder kwargs can also be embedded in the name for advanced cases, but explicit `builder_kwargs` is clearer.
- `split`: string, list, `ReadInstruction`, union expression, or `None` for all splits.
- `data_dir`: prepared-data root. Defaults to `TFDS_DATA_DIR` when set, otherwise the standard user TFDS cache location.
- `batch_size`: adds a batch dimension. `-1` loads the full split into one batch and should only be used for small data.
- `shuffle_files`: file/shard-level shuffling. Useful for large training datasets; affects determinism.
- `download`: set `False` for no-download checks or when data must already exist.
- `as_supervised`: returns `(input, label)` tuples when `info.supervised_keys` is defined.
- `decoders`: nested decoder tree for feature decode overrides.
- `read_config`: `tfds.ReadConfig` controlling input pipeline, determinism, parallelism, prefetch, autocache, file format, and related read behavior.
- `download_and_prepare_kwargs`: pass `download_config`, manual directories, checksum registration, and generation limits only when explicitly preparing data.
- `try_gcs`: check public prepared TFDS GCS data first and use it when available.
- `file_format`: choose among prepared file formats when a dataset directory contains more than one.

### `tfds.builder`

Verified signature:

```python
tfds.builder(name, *, try_gcs=False, **builder_kwargs)
```

Use for:

- metadata inspection with `builder.info`;
- configs, versions, and supervised key inspection;
- prepared-state checks with `builder.is_prepared()`;
- explicit `builder.download_and_prepare(...)`;
- repeated `builder.as_dataset(...)` or `builder.as_data_source(...)` calls.

`try_gcs=True` is equivalent to using the public prepared TFDS bucket as the data source when the dataset exists there. It is not the same as a download config that tries to reuse GCS during local preparation.

### `tfds.data_source`

Verified signature shape:

```python
tfds.data_source(
    name,
    *,
    split=None,
    data_dir=None,
    download=True,
    decoders=None,
    deserialize_method=tfds.core.decode.DeserializeMethod.DESERIALIZE_AND_DECODE,
    builder_kwargs=None,
    download_and_prepare_kwargs=None,
    try_gcs=False,
)
```

Use for Python sequence/data-loader workflows where examples are indexed or iterated outside TensorFlow:

```python
source = tfds.data_source("fashion_mnist", split="train", download=False)
print(len(source))
print(source[0])
```

Operational notes:

- When neither `builder_kwargs` nor `data_dir` is supplied, `tfds.data_source` defaults the builder file format to ArrayRecord because random access is required.
- If an explicit non-random-access file format such as TFRecord is passed for data source loading, TFDS raises a random-access unsupported error.
- If `deserialize_method` is not the default deserialize-and-decode mode, `decoders` may be ignored.
- The return is a `Sequence` for a single split or a dictionary/structure of sequences when split is omitted or structured.

## Metadata and read-only builders

### `DatasetInfo`

Common fields used by this sub-skill:

```python
info = tfds.builder("mnist").info
info.full_name
info.name
info.version
info.builder_config
info.supervised_keys
info.features
info.splits
info.citation
info.description
```

Split metadata examples:

```python
info.splits["train"].num_examples
info.splits["train"].num_shards
info.splits["train"].filenames
info.splits["train[:10%]"].file_instructions
```

Feature metadata examples:

```python
info.features
info.features["label"].names
info.features["image"].shape
info.features["image"].dtype
```

### Read-only prepared data

Public functions exposed for prepared dataset directories:

```python
tfds.builder_from_directory(builder_dir, file_format=None)
tfds.builder_from_directories(builder_dirs)
```

Use these only when the user points to a generated TFDS dataset directory and wants to read metadata/data without the original builder code. A read-only builder cannot generate the dataset; it reads already generated metadata and records.

## Split helpers

### `tfds.even_splits`

Verified signature:

```python
tfds.even_splits(split, n, drop_remainder=False)
```

Returns a list of non-overlapping split instructions:

```python
worker_splits = tfds.even_splits("train", n=4, drop_remainder=True)
ds = tfds.load("my_dataset", split=worker_splits[worker_id])
```

Use for cross-host or cross-validation partitioning when split membership must not overlap.

### `tfds.split_for_jax_process`

Convenience helper that maps the current JAX process to one `even_splits` element. Use only when JAX is available and the process count/index semantics match the training setup.

## `tfds.ReadConfig`

Constructor fields verified in source include:

```python
tfds.ReadConfig(
    options=None,
    try_autocache=True,
    repeat_filenames=False,
    add_tfds_id=False,
    shuffle_seed=None,
    shuffle_reshuffle_each_iteration=None,
    interleave_cycle_length=<default>,
    interleave_block_length=16,
    input_context=None,
    experimental_interleave_sort_fn=None,
    skip_prefetch=False,
    num_parallel_calls_for_decode=None,
    num_parallel_calls_for_interleave_files=<default>,
    enable_ordering_guard=True,
    assert_cardinality=True,
    override_buffer_size=None,
    file_format=None,
)
```

Use cases:

- deterministic file shuffling: `ReadConfig(shuffle_seed=123)`;
- example tracing: `ReadConfig(add_tfds_id=True)`;
- multi-worker TensorFlow reads: `ReadConfig(input_context=...)`;
- custom shard order: `ReadConfig(experimental_interleave_sort_fn=...)`;
- RAM triage: `ReadConfig(override_buffer_size=1024)`;
- no TFDS auto-cache: `ReadConfig(try_autocache=False)`;
- avoid double prefetch: `ReadConfig(skip_prefetch=True)`;
- read a non-default prepared file format: `ReadConfig(file_format="array_record")` or `tfds.load(..., file_format="array_record")`.

`ReadConfig.replace(**kwargs)` returns a modified dataclass copy.

## Conversion and visualization helpers

### `tfds.as_numpy`

```python
tfds.as_numpy(dataset)
```

Converts nested structures of TensorFlow datasets/tensors to matching structures of NumPy-generating iterables/arrays. Ragged tensors may remain ragged-like because NumPy has no exact equivalent.

### `tfds.as_dataframe`

```python
tfds.as_dataframe(ds, ds_info=None)
```

Converts all examples from an unbatched `tf.data.Dataset` into a Pandas DataFrame. Pass `ds.take(n)` and `ds_info` for safe notebook inspection and formatted feature display.

### `tfds.show_examples`

```python
tfds.show_examples(ds, ds_info, is_batched=False, **options_kwargs)
```

Displays supported example visualizations and returns a Matplotlib figure. Common `options_kwargs` include `rows` and `cols`. It consumes examples in order and is primarily for interactive image-like datasets.

### `tfds.benchmark`

```python
tfds.benchmark(ds, *, num_iter=None, batch_size=1)
```

Consumes an iterable and reports setup time, total execution time, and examples/second. Pass the true batch size and set `num_iter` for bounded checks.

## Decoding APIs

### Skip decoding

```python
ds = tfds.load(
    "imagenet2012",
    split="train",
    decoders={"image": tfds.decode.SkipDecoding()},
)
```

Returns serialized feature payloads for the selected feature, useful when filtering before image/video decode or using a custom fused decode operation.

### Partial decoding

```python
partial = tfds.decode.PartialDecoding({
    "image": True,
    "metadata": {"scene_name", "num_objects"},
    "objects": {"label"},
})
ds = tfds.builder("my_dataset").as_dataset(split="train", decoders=partial)
```

Selects only a subset of nested features, reusing feature metadata where the requested structure matches actual features.

### Custom decoder

```python
@tfds.decode.make_decoder()
def decode_example(serialized_value, feature):
    return feature.decode_example(serialized_value)

custom = decode_example()
ds = tfds.load("my_dataset", split="train", decoders={"feature": custom})
```

For sequence/video features, the decoder is applied to individual frames/items according to the feature connector.

## Download configuration touchpoints

For explicit preparation through `tfds.load(..., download_and_prepare_kwargs=...)` or `builder.download_and_prepare(...)`, construct a `tfds.download.DownloadConfig` when needed:

```python
download_config = tfds.download.DownloadConfig(
    manual_dir="MANUAL_DIR",
    try_download_gcs=False,
    max_examples_per_split=100,
)

builder.download_and_prepare(download_config=download_config)
```

Do not add this configuration casually: it affects downloads, generation, manual-file resolution, checksums, GCS reuse, and possibly dataset size.
