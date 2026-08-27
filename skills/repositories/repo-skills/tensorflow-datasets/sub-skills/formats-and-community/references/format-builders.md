# Format-specific builders

Use this reference to turn an already-existing data representation into a TFDS builder or loadable dataset without starting from the generic builder authoring workflow.

## Quick chooser

| Source shape | Primary API | Output | Main caveat |
|---|---|---|---|
| Images under `split/label/*.jpg`, `*.jpeg`, or `*.png` | `tfds.ImageFolder` | `tf.data.Dataset` reading original image files | Labels come from folder names and unsupported extensions are ignored |
| Parallel files named `language.split.txt` | `tfds.TranslateFolder` | Translation examples keyed by language | Every language file for a split must have the same line count |
| Prepared TFDS builder directory | `tfds.builder_from_directory` | Read-only builder with standard metadata/load APIs | Metadata must already exist beside shards |
| Several prepared TFDS directories for one logical dataset | `tfds.builder_from_directories` | Merged read-only builder | Name, version, schema, and per-folder metadata must agree |
| `tf.data.Dataset`, keyed iterator, or Beam input already exists | `tfds.dataset_builders.store_as_tfds_dataset` or `AdhocBuilder` | Stored TFDS dataset | All split inputs should use the same input type |
| Croissant JSON-LD metadata | `tfds.dataset_builders.CroissantBuilder` | Configs from Croissant record sets | Manual local files require exact filename mapping |
| HuggingFace dataset repository | `tfds.load('huggingface:...')` or `HuggingfaceDatasetBuilder` | TFDS-loaded or TFDS-materialized data | Network, cache, package, token, or gated-repo constraints may apply |
| CoNLL / CoNLL-U text | `ConllDatasetBuilder` / `ConllUDatasetBuilder` | Sentence-level TFDS examples | Column order, separator, and config features must match exactly |

## Folder datasets

### `ImageFolder`

Use `ImageFolder` for classification trees where split and label are encoded in directories.

```text
image_root/
  train/
    cat/
      0001.jpg
    dog/
      0002.png
  test/
    cat/
      0003.jpeg
```

```python
import tensorflow as tf
import tensorflow_datasets as tfds

builder = tfds.ImageFolder(
    root_dir="image_root",
    shape=(128, 128, 3),      # optional; omit for variable image size
    dtype=tf.uint8,           # optional; defaults through tfds.features.Image
)
print(builder.info.features)
print(builder.info.splits)
ds = builder.as_dataset(split="train", shuffle_files=True)
```

Operational facts:

- Supported image extensions are `.jpg`, `.jpeg`, and `.png`, matched case-insensitively.
- The emitted features are `image`, `label`, and `image/filename`; supervised keys are `(image, label)`.
- Labels are inferred from label folder names and sorted.
- Example lists are deterministically shuffled by split before optional dataset-level shuffling.
- `download_and_prepare()` is intentionally not the workflow; the original image files are read directly.
- `decoders={"image": tfds.decode.SkipDecoding()}` keeps image bytes encoded when the caller needs filenames and raw bytes.

Route away when the caller needs multi-label annotations, sidecar metadata, non-classification folder depth, or generated examples; those require a custom builder in `dataset-authoring`.

### `TranslateFolder`

Use `TranslateFolder` when each split is represented by one text file per language.

```text
translate_root/
  en.train.txt
  de.train.txt
  en.test.txt
  de.test.txt
```

```python
import tensorflow_datasets as tfds

builder = tfds.TranslateFolder(root_dir="translate_root")
print(builder.info.features.keys())
print(builder.info.splits)
ds = builder.as_dataset(split="train", shuffle_files=True)
```

Operational facts:

- Filenames are split as `language.split.txt`; the middle segment becomes the split name.
- One line equals one example; empty lines are preserved as examples.
- For a given split, all language files must contain the same number of lines.
- All examples are loaded into memory during initialization, so very large corpora should use a streaming custom builder instead.
- Decoders are not supported by this builder.

## Prepared builder folders

Use `builder_from_directory` when the source is already a TFDS builder directory containing metadata and shards.

```python
import tensorflow_datasets as tfds

builder = tfds.builder_from_directory("prepared/my_dataset/1.0.0")
print(builder.info)
ds = builder.as_dataset(split="train")
```

Use `builder_from_directories` when several prepared directories are partitions of the same logical dataset.

```python
builder = tfds.builder_from_directories([
    "prepared/agent_a/my_dataset/1.0.0",
    "prepared/agent_b/my_dataset/1.0.0",
])
print(builder.info.splits)
```

Rules:

- Each directory needs its own `dataset_info.json`, `features.json`, and shard files.
- The data is read-only from TFDS's perspective. `download_and_prepare()` is not available.
- The multi-directory path merges split metadata; do not merge folders with different feature schemas, dataset names, versions, or file format assumptions.
- The `filetype_suffix` argument to `builder_from_directories` is legacy; prefer metadata that records the file format.
- If the folder follows `data_dir/dataset_name[/config]/version`, `tfds.load(..., data_dir="data_dir")` can find it; use `data-loading` for ordinary public loading recipes.

## External or in-memory format builders

### `AdhocBuilder`, `TfDataBuilder`, and `store_as_tfds_dataset`

Use this path when examples already exist as `tf.data.Dataset` splits, keyed Python iterables, or Beam inputs and the user wants them stored in TFDS format.

```python
import tensorflow as tf
import tensorflow_datasets as tfds

train = tf.data.Dataset.from_tensor_slices({"number": [1, 2, 3]})
test = tf.data.Dataset.from_tensor_slices({"number": [4, 5]})

builder = tfds.dataset_builders.store_as_tfds_dataset(
    name="my_dataset",
    version="1.0.0",
    config="single_number",
    data_dir="tfds_data",
    split_datasets={"train": train, "test": test},
    features=tfds.features.FeaturesDict({
        "number": tfds.features.Scalar(dtype=tf.int64),
    }),
    description="Small numeric example dataset.",
    release_notes={"1.0.0": "Initial version."},
)
```

Operational facts:

- `AdhocBuilder` is the underlying builder class and can accept `tf.data.Dataset`, keyed iterables, Beam transforms, or Beam collections per split.
- `TfDataBuilder` exists for backwards compatibility and warns; prefer `store_as_tfds_dataset(...)` for direct storage.
- Keep split inputs homogeneous. Mixing `tf.data.Dataset` in one split with a Python iterator in another is rejected.
- Provide a `FeaturesDict` that matches the serialized examples. Feature mismatches surface later as decode or metadata reconstruction errors.
- Use explicit `data_dir`, `version`, and `release_notes` when the stored output is meant to be shared.

### `as_dataset` versus `as_data_source`

- Use `as_dataset(...)` when the consumer wants a `tf.data.Dataset`, batching, TensorFlow decoders, or Keras-style pipelines.
- Use `as_data_source(...)` when the consumer wants Python indexing, NumPy-like iteration, PyTorch/JAX DataLoader-style access, or TensorFlow-less reads.
- `as_data_source(...)` requires a random-access file format. ArrayRecord is random-access but does not implement `as_dataset`; Parquet supports both paths. Plain TFRecord is the usual TensorFlow dataset path.
- If the task is only about loading an existing public dataset and split strings, route to `data-loading`.

## CroissantBuilder

Use Croissant when a dataset is described by a JSON-LD metadata graph that names record sets, fields, resources, and optional split information.

```python
import tensorflow_datasets as tfds

builder = tfds.dataset_builders.CroissantBuilder(
    jsonld="metadata.json",
    record_set_ids=["records"],          # optional; omitted means usable record sets become configs
    mapping={"document.csv": "manual/document.csv"},
    file_format="array_record",
    overwrite_version="1.0.0",          # optional version override
)
builder.download_and_prepare()
source = builder.as_data_source(split="default")
```

Operational facts:

- `jsonld` can be a local file, URL, or already-loaded mapping.
- Each selected record set becomes a TFDS config after TFDS-safe name conversion.
- If no split record set is joined, TFDS emits a single `default` split.
- `mapping` is `filename -> local path` for manual files. Keys must match the Croissant file-object names exactly.
- `filters` can restrict records at preparation time; empty outputs often mean filters are too narrow.
- `int_dtype` and `float_dtype` control numeric TFDS feature dtypes.
- CLI construction for `tfds build_croissant` belongs to `cli-workflows`; this reference only covers the builder semantics and manual mapping contract.

## HuggingFace builders and namespace loading

Use the namespace when the user wants TFDS's normal load API:

```python
import tensorflow_datasets as tfds

ds = tfds.load("huggingface:dataset_name", split="train")
builder = tfds.builder("huggingface:dataset_name")
```

Use the explicit builder when the user must materialize a HuggingFace repository into a TFDS data directory or control conversion options:

```python
builder = tfds.dataset_builders.HuggingfaceDatasetBuilder(
    hf_repo_id="dataset_name",
    hf_config="config_name",
    data_dir="tfds_data",
    file_format="array_record",
    hf_hub_token="${HUGGING_FACE_HUB_TOKEN}",
)
```

Operational facts:

- HuggingFace split names and config names are converted to TFDS-safe names.
- The builder converts HuggingFace features to TFDS features and writes TFDS shards directly.
- `hf_num_proc` controls HuggingFace preparation parallelism; `tfds_num_proc` controls TFDS shard writing parallelism.
- `ignore_verifications` and `ignore_hf_errors` relax checks; only use them with explicit user approval.
- Gated/private repositories need token and license/terms handling. Do not assume organization-wide access.
- Treat this path as network- and cache-sensitive unless the user confirms local cached data and installed optional dependencies.

## CoNLL and CoNLL-U helpers

Use the format-specific base classes for column-oriented sentence datasets when the format matches the built-in assumptions.

- `ConllDatasetBuilder` reads one token row at a time and yields sentence examples separated by blank lines or document boundaries.
- `ConllBuilderConfig` defines `separator` and ordered features; the number of columns in each row must match exactly.
- `ConllUDatasetBuilder` parses CoNLL-U annotated sentences and can accept a `process_example_fn` for non-standard universal-dependency variants.
- `ConllUBuilderConfig` provides the ordered feature structure for a language/config.

Use this sub-skill to choose the CoNLL-specific base class and diagnose column/feature mismatch. Route implementation details such as builder class files, tests, dummy data, and release policy to `dataset-authoring`.
