# Loading Workflows

This reference covers existing-dataset consumption. It assumes a dataset is already implemented in TFDS or already generated on disk. For custom builder code, CLI command construction, Beam/Dataflow generation, or external/community format setup, route to the appropriate sibling sub-skill.

## Choose the API surface

| Goal | Preferred surface | Notes |
|---|---|---|
| Inspect metadata without preparing data | `tfds.builder(name, data_dir=..., try_gcs=...)` | Safe first step. `builder.info` exposes name, version, configs, supervised keys, features, citations, and any split metadata already known or found on disk. |
| Standard TensorFlow input pipeline | `tfds.load(name, split=..., as_supervised=..., with_info=...)` | Convenience wrapper around `builder()`, optional `download_and_prepare()`, then `builder.as_dataset()`. Can download large datasets unless `download=False`. |
| Explicit staged control | `builder = tfds.builder(...); builder.download_and_prepare(...); builder.as_dataset(...)` | Use when you need custom download config, prepared-state checks, file format selection, or repeated dataset reads. |
| Python sequence / JAX / PyTorch boundary | `tfds.data_source(...)` or `builder.as_data_source(...)` | Use for TensorFlow-less data loading after records exist in a random-access format. By default, `tfds.data_source` chooses ArrayRecord when no `data_dir` or builder file format is specified. |
| Small in-memory NumPy arrays | `tfds.load(..., batch_size=-1)` then `tfds.as_numpy(...)` | Only for datasets/splits that fit in memory. Variable-length features are padded when batched. |
| Notebook visualization | `tfds.as_dataframe(ds.take(n), info)` or `tfds.show_examples(ds, info)` | Consume only small subsets. `show_examples` is visualization-oriented and mainly supports image-style datasets. |

## Metadata-first inspection

Use `tfds.builder` or the bundled `scripts/tfds_inspect_dataset.py` before downloads:

```python
import tensorflow_datasets as tfds

builder = tfds.builder("mnist")
info = builder.info
print(info.full_name)
print(info.version)
print(info.features)
print(list(info.splits.keys()))
```

If split metadata is empty, the dataset may not be prepared locally and may not expose split metadata from packaged metadata. Use `download=False` to verify that prepared data exists before starting a download:

```python
ds, info = tfds.load(
    "mnist",
    split="train",
    download=False,
    with_info=True,
)
```

A missing-data error with `download=False` means the requested dataset/version/config is not present in the chosen `data_dir`; decide with the user whether to download, change `data_dir`, use public GCS, or inspect only builder metadata.

## Standard `tfds.load` recipes

### Dictionary examples

```python
ds, info = tfds.load("mnist", split="train", with_info=True)
for example in ds.take(1):
    image = example["image"]
    label = example["label"]
```

### Supervised `(input, label)` tuples

```python
ds, info = tfds.load(
    "mnist",
    split="train",
    as_supervised=True,
    with_info=True,
)
for image, label in ds.take(1):
    pass
```

`as_supervised=True` works only when the dataset metadata defines `supervised_keys`. If it fails or returns an unexpected structure, inspect `info.supervised_keys` and use dictionary examples instead.

### Multiple splits

```python
train_ds, test_ds = tfds.load(
    "mnist",
    split=["train", "test"],
    as_supervised=True,
)
```

When `split=None`, `tfds.load` returns a dictionary mapping split names to datasets. When `split` is a list, it returns matching datasets in list order.

### Explicit builder workflow

```python
builder = tfds.builder("mnist")
if not builder.is_prepared():
    builder.download_and_prepare()
ds = builder.as_dataset(split="train", shuffle_files=True, as_supervised=True)
```

Use this pattern when the task needs a prepared-state check, custom `DownloadConfig`, version/config inspection, or repeated calls to `as_dataset` with different splits/decoders.

## NumPy, DataFrame, and visualization

### `tfds.as_numpy`

`tfds.as_numpy` converts `tf.data.Dataset` elements and tensors into NumPy arrays or Python generators of NumPy arrays:

```python
ds = tfds.load("mnist", split="train", as_supervised=True)
for image, label in tfds.as_numpy(ds.take(2)):
    print(type(image), type(label))
```

For small full splits:

```python
images, labels = tfds.as_numpy(tfds.load(
    "mnist",
    split="test",
    batch_size=-1,
    as_supervised=True,
))
```

Avoid `batch_size=-1` on large datasets or variable-length-heavy datasets unless memory has been explicitly considered.

### `tfds.as_dataframe`

```python
ds, info = tfds.load("mnist", split="train", with_info=True)
df = tfds.as_dataframe(ds.take(8), info)
```

`as_dataframe` loads all examples passed to it into memory. Always call it on a small `.take(n)` subset unless the user explicitly wants a full in-memory DataFrame and the split is small.

### `tfds.show_examples`

```python
ds, info = tfds.load("mnist", split="train", with_info=True)
fig = tfds.show_examples(ds.take(12), info, rows=3, cols=4)
```

`show_examples` returns a Matplotlib figure for supported visualizers. If visualization is unsupported for a dataset, inspect features and fall back to `as_dataframe` or custom rendering.

## Keras / TensorFlow pipeline pattern

For supervised image-like training, use `as_supervised=True`, normalize/map before caching, shuffle with an informed buffer, then batch and prefetch:

```python
import tensorflow as tf
import tensorflow_datasets as tfds

(ds_train, ds_test), info = tfds.load(
    "mnist",
    split=["train", "test"],
    as_supervised=True,
    shuffle_files=True,
    with_info=True,
)

def normalize(image, label):
    return tf.cast(image, tf.float32) / 255.0, label

ds_train = ds_train.map(normalize, num_parallel_calls=tf.data.AUTOTUNE)
ds_train = ds_train.cache()
ds_train = ds_train.shuffle(info.splits["train"].num_examples)
ds_train = ds_train.batch(128)
ds_train = ds_train.prefetch(tf.data.AUTOTUNE)

ds_test = ds_test.map(normalize, num_parallel_calls=tf.data.AUTOTUNE)
ds_test = ds_test.batch(128).prefetch(tf.data.AUTOTUNE)
```

Guidelines:

- For large sharded datasets, set `shuffle_files=True` for training.
- Keep random augmentation after cache if you do not want randomness cached.
- Do not shuffle evaluation/test datasets unless the task specifically requires it.

## JAX and PyTorch boundaries with `tfds.data_source`

`tfds.data_source` returns Python sequence-like objects instead of `tf.data.Dataset` objects:

```python
sources = tfds.data_source("fashion_mnist", download=False)
train_source = sources["train"]
print(len(train_source))
print(train_source[0].keys())
```

Important boundaries:

- Prepared files must already exist when `download=False`.
- Random access requires a supported file format. When no `data_dir` or explicit builder file format is supplied, `tfds.data_source` defaults to ArrayRecord. TFRecord is not a random-access data-source format for this API.
- `decoders` are accepted, but some low-level deserialize modes ignore decoders. Keep default deserialize-and-decode unless intentionally doing advanced record handling.

### PyTorch sketch

```python
source = tfds.data_source("fashion_mnist", split="train", download=False)
loader = torch.utils.data.DataLoader(source, batch_size=128, shuffle=True)
for batch in loader:
    images = batch["image"]
    labels = batch["label"]
```

### JAX / Grain sketch

```python
source = tfds.data_source("fashion_mnist", split="train", download=False)
# Use the framework's sampler/loader to control shuffling, epochs, and sharding.
example = source[0]
```

For multi-process JAX work, derive non-overlapping split strings with `tfds.even_splits` or `tfds.split_for_jax_process` before calling the loader.

## GCS decisions for existing datasets

- `tfds.load(..., try_gcs=True)` and `tfds.builder(..., try_gcs=True)` first check whether the prepared dataset is available in the public TFDS GCS bucket and, if it is, stream/read from that prepared location instead of building locally.
- `tfds.is_dataset_on_gcs("name")` checks public prepared availability.
- `try_gcs=True` is not the same as `DownloadConfig(try_download_gcs=...)`: `try_gcs=True` changes the data source to the public prepared bucket, while `try_download_gcs` controls whether a local build may reuse prepared data from GCS during `download_and_prepare`.
- Private GCS buckets require credentials and user-approved `data_dir="gs://..."`; do not assume credentials exist.

## Loading specific versions and configs

Dataset names can include configs and versions:

```python
tfds.load("dataset_name/config_name:1.2.0", split="train", download=False)
tfds.builder("dataset_name/config_name:1.*.*")
```

Operational rules:

- Only the current/latest version is generally generated by code.
- Older versions can be read if already present on disk.
- Fixing a major version in reproducibility-sensitive work is safer than relying on an unqualified latest version.
- If a dataset has configs, include the config in the name or pass it through `builder_kwargs` when needed.
