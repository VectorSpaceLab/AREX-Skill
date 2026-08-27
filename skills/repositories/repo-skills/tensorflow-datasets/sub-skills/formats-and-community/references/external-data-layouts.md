# External data layouts

This reference covers externally produced TFDS-style shard directories: metadata files, shard filename templates, split statistics, and the safe path from raw `tf.train.Example` files to `builder_from_directory`.

## What TFDS can read directly

TFDS can read external files such as TFRecord or Riegeli when the directory supplies both data shards and TFDS metadata. The target record type is `tf.train.Example`; `tf.train.SequenceExample` is not covered by this workflow.

Required builder-directory contents:

```text
builder_dir/
  dataset_info.json
  features.json
  my_dataset-train.tfrecord-00000-of-00002
  my_dataset-train.tfrecord-00001-of-00002
  my_dataset-test.tfrecord-00000-of-00001
```

Other metadata sidecars such as label files, citations, or README text may be present, but the two JSON files are the core read-only reconstruction inputs.

## Default filename template

The default TFDS shard template is:

```text
{DATASET}-{SPLIT}.{FILEFORMAT}-{SHARD_X_OF_Y}
```

Template variables supported by TFDS-style names:

| Variable | Meaning | Example |
|---|---|---|
| `{DATASET}` | dataset name | `my_dataset` |
| `{SPLIT}` | split name | `train` |
| `{FILEFORMAT}` | file suffix / format | `tfrecord`, `riegeli`, `array_record`, `parquet` |
| `{SHARD_INDEX}` | zero-based shard index | `00000` |
| `{NUM_SHARDS}` | total shards in split | `00002` |
| `{SHARD_X_OF_Y}` | combined shard index and count | `00000-of-00002` |

Shard heuristics to verify before loading:

- All shards for one split agree on dataset name and file format suffix.
- Shard indices start at zero and are contiguous for each split.
- Every shard for a split declares the same `NUM_SHARDS` value.
- The declared shard count equals the number of shard files for that split.
- Metadata split names match shard split names.
- Metadata shard-length lists, when present, have the same length as the shard count.

## Feature metadata contract

`features.json` must describe the same feature tree that the serialized examples contain. Common pattern:

```python
import tensorflow as tf
import tensorflow_datasets as tfds

features = tfds.features.FeaturesDict({
    "image": tfds.features.Image(shape=(256, 256, 3)),
    "label": tfds.features.ClassLabel(names=["cat", "dog"]),
    "objects": tfds.features.Sequence({
        "camera/K": tfds.features.Tensor(shape=(3,), dtype=tf.float32),
    }),
})
```

If you control the writer, serialize examples with the same `FeaturesDict` to avoid drift:

```python
serialized = features.serialize_example(example_dict)
```

If you do not control the writer, inspect `features.get_serialized_info()` and `features.tf_example_spec` while designing the feature tree, then verify by reading at least one example after metadata is written.

## Split statistics

TFDS needs exact examples per shard for `len(ds)`, split slicing, and split percentages. Provide them in one of these ways:

- explicit `tfds.core.SplitInfo(name="train", shard_lengths=[...], num_bytes=...)` values;
- output from `tfds.folder_dataset.compute_split_info_from_directory(...)` or `compute_split_info(...)`;
- a directory of precomputed split-info files consumed by `write_metadata`.

Counting very large shard sets can become a Beam task. Route Beam runner, Dataflow/Flink, and shard-size scaling decisions to `beam-and-performance`.

## Writing metadata

Use `tfds.folder_dataset.write_metadata` once the feature tree and split counts are known.

```python
import tensorflow_datasets as tfds

split_infos = [
    tfds.core.SplitInfo(name="train", shard_lengths=[1024, 1000], num_bytes=0),
    tfds.core.SplitInfo(name="test", shard_lengths=[256], num_bytes=0),
]

tfds.folder_dataset.write_metadata(
    data_dir="builder_dir",
    features=features,
    split_infos=split_infos,
    filename_template="{DATASET}-{SPLIT}.{FILEFORMAT}-{SHARD_X_OF_Y}",
    description="Short dataset description.",
    supervised_keys=("image", "label"),
)
```

Important details:

- When `version` is omitted, TFDS tries to infer it from the builder directory name if the name is a valid semantic version; otherwise it falls back to `1.0.0`.
- `check_data=True` attempts to read one example after writing metadata. Keep it on for small local checks; disable only when the cost/dependencies are understood.
- The file format stored in metadata comes from the shard suffix and should match the actual adapter.
- Additional `DatasetInfo` fields such as homepage, citation, and description are optional but useful for handoff.

## Loading after metadata exists

Direct read-only path:

```python
import tensorflow_datasets as tfds

builder = tfds.builder_from_directory("builder_dir")
print(builder.info.splits)
ds = builder.as_dataset(split="train[:10%]")
```

Multiple prepared directories:

```python
builder = tfds.builder_from_directories([
    "producer_a/builder_dir",
    "producer_b/builder_dir",
])
```

Data directory compatibility path:

```text
data_dir/
  dataset_name/
    1.0.0/
      dataset_info.json
      features.json
      ...shards...
  dataset_with_config/
    config_name/
      1.0.0/
        dataset_info.json
        features.json
        ...shards...
```

When the directory follows this shape, `tfds.load("dataset_name", data_dir="data_dir")` or `tfds.load("dataset_with_config/config_name", data_dir="data_dir")` can find it. Use `data-loading` for general split strings, decoding, batching, and public loading decisions.

## Standalone validator workflow

Run the bundled checker before writing or relying on metadata:

```bash
python scripts/check_external_tfrecord_layout.py builder_dir --dataset-name my_dataset --file-format tfrecord --split train --split test
```

Use `--template` for custom shard names, for example:

```bash
python scripts/check_external_tfrecord_layout.py builder_dir --template '{SPLIT}/data.{FILEFORMAT}-{SHARD_X_OF_Y}' --file-format tfrecord --split train
```

The checker does not import TensorFlow or TensorFlow Datasets. It validates filesystem and JSON heuristics only; it cannot prove that serialized bytes match the `FeaturesDict`. Follow with a one-example read check in the prepared runtime when feasible.
