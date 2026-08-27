---
name: formats-and-community
description: "Use TensorFlow Datasets format-specific builders, external
  prepared layouts, community namespaces, HuggingFace wrappers, Croissant
  metadata, folder datasets, and dataset collections."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Formats and Community

Use this sub-skill when a TensorFlow Datasets (TFDS) task starts from an existing data format, prepared shard directory, folder layout, community namespace, HuggingFace repository, Croissant JSON-LD description, or dataset collection rather than from a handwritten generic builder.

Do not use this sub-skill for core `GeneratorBasedBuilder` authoring, detailed CLI flag construction, Beam/Dataflow/Flink scaling, or ordinary public dataset loading. Route those tasks to `dataset-authoring`, `cli-workflows`, `beam-and-performance`, and `data-loading` respectively.

## Fast operating path

1. Classify the source shape before touching data:
   - image tree: `split/label/image.{jpg,jpeg,png}` -> `tfds.ImageFolder`
   - translation files: `language.split.txt` -> `tfds.TranslateFolder`
   - already-prepared TFDS folder -> `tfds.builder_from_directory` or `tfds.builder_from_directories`
   - external `tf.train.Example` shards -> validate metadata and shard names, then use read-only loading
   - in-memory `tf.data.Dataset` or keyed iterator -> `tfds.dataset_builders.store_as_tfds_dataset` / `AdhocBuilder`
   - Croissant JSON-LD -> `tfds.dataset_builders.CroissantBuilder`
   - HuggingFace repository or namespace -> `tfds.load('huggingface:...')`, `tfds.builder('huggingface:...')`, or `HuggingfaceDatasetBuilder`
   - benchmark/task bundle -> `tfds.dataset_collection(...)`
2. Prefer metadata-first checks. Do not trigger large downloads, full builds, cloud runners, or authenticated catalog access unless the user explicitly accepts the cost and credentials boundary.
3. For external shard folders, run the bundled standalone checker first:

   ```bash
   python scripts/check_external_tfrecord_layout.py builder_dir --dataset-name my_dataset --file-format tfrecord --split train --split test
   ```

4. Choose the read surface deliberately:
   - `builder.as_dataset(...)` / `tfds.load(...)` returns `tf.data.Dataset` and needs the TensorFlow path.
   - `builder.as_data_source(...)` / `tfds.data_source(...)` is for Python/random-access consumption and only works for supported random-access formats such as ArrayRecord or Parquet.
   - `builder_from_directory(...)` produces a read-only builder for prepared data; it is not a regeneration path.
5. If the work becomes defining `_info`, `_split_generators`, feature connectors, dummy-data tests, or release/version policy for a custom builder, switch to `dataset-authoring`. If it becomes command syntax for `tfds build`, `tfds new`, `convert_format`, or `build_croissant`, switch to `cli-workflows`.

## Verified API anchors

The inspection environment verified TFDS `4.9.10+nightly` public signatures for this sub-skill, including:

- `tfds.builder_from_directory(builder_dir, file_format=None)`
- `tfds.builder_from_directories(builder_dirs, filetype_suffix=None)`
- `tfds.ImageFolder(root_dir, shape=None, dtype=None)`
- `tfds.TranslateFolder(root_dir)`
- `tfds.dataset_builders.AdhocBuilder(...)`
- `tfds.dataset_builders.TfDataBuilder(...)` as a legacy compatibility wrapper
- `tfds.dataset_builders.CroissantBuilder(...)`
- `tfds.dataset_builders.HuggingfaceDatasetBuilder(...)`

## Bundled references

- [Format-specific builders](references/format-builders.md): `ImageFolder`, `TranslateFolder`, prepared builder folders, external/in-memory format builders, Croissant, HuggingFace, CoNLL, and `as_dataset` versus `as_data_source` choices.
- [External data layouts](references/external-data-layouts.md): TFDS metadata files, shard filename templates, `write_metadata`, split statistics, multi-directory reads, and validator workflow.
- [Community catalogs and collections](references/community-and-collections.md): `community-datasets.toml`, namespaces, HuggingFace routing, community path types, and dataset collection loader workflows.
- [Troubleshooting](references/troubleshooting.md): common failure modes for metadata, folder layouts, community namespaces, HuggingFace, Croissant, CoNLL, and data-source boundaries.

## Bundled script

- [External TFRecord layout checker](scripts/check_external_tfrecord_layout.py): validates metadata file presence, JSON readability, default or custom shard naming templates, split membership, contiguous shard indices, declared shard counts, and selected metadata consistency without importing TensorFlow Datasets or the source checkout.

## Safety defaults

- Treat HuggingFace, community package paths, Croissant URLs, public GCS paths, and `download_and_prepare()` as network/cache/credential-sensitive.
- Keep manual Croissant mappings explicit and keyed by the exact file-object names from the JSON-LD metadata.
- Do not call `download_and_prepare()` on `ImageFolder`, `TranslateFolder`, or read-only builders as if they were standard generation builders.
- Do not claim TensorFlow-less consumption from `as_dataset`; use the data-source path only when the stored file format supports random access.
- Keep runtime advice self-contained; do not depend on original repository docs, tests, scripts, or local checkout paths.
