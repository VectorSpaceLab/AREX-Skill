---
name: dataset-authoring
description: "Author, test, and debug custom TensorFlow Datasets builders and
  dataset collections."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TensorFlow Datasets Dataset Authoring

Use this sub-skill when the task is to create, revise, test, or debug a custom TensorFlow Datasets (TFDS) dataset builder or dataset collection. It is focused on repository-local or package-local authoring workflows, not on loading an already prepared dataset.

## Use this for

- Creating or reviewing a `tfds new`-style dataset folder.
- Implementing `tfds.core.GeneratorBasedBuilder` with `_info`, `_split_generators`, and `_generate_examples`.
- Choosing `DatasetInfo`, `BuilderConfig`, `Version`, `SplitGenerator` replacement patterns, `DownloadManager`, and feature connectors.
- Creating safe dummy data and `tfds.testing.DatasetBuilderTestCase` tests.
- Handling checksums, manual downloads, version/release-note changes, and common implementation gotchas.
- Authoring dataset collections with collection metadata, versioned references, and collection tests.

## Route elsewhere

- CLI command syntax, `tfds build`, `tfds new` options, and command construction: route to `cli-workflows`.
- Beam/Dataflow/Flink generation, distributed transforms, or performance scaling: route to `beam-and-performance`.
- External TFRecord layouts, folder datasets, Croissant, HuggingFace/community wrappers, and format-specific builders: route to `formats-and-community`.
- Loading, inspecting, decoding, splitting, or iterating existing datasets without authoring code: route to `data-loading`.

## Start-here workflow

1. Identify whether the user is authoring a dataset builder or a dataset collection.
2. For a builder, inspect the candidate folder with the bundled validator:
   - [`scripts/dataset_skeleton_check.py`](scripts/dataset_skeleton_check.py)
3. Use the references in this order:
   - [Builder authoring](references/builder-authoring.md)
   - [Feature connectors](references/feature-connectors.md)
   - [Testing and validation](references/testing-and-validation.md)
   - [Dataset collections](references/dataset-collections.md)
   - [Troubleshooting](references/troubleshooting.md)
4. Keep the authoring folder self-contained: implementation, metadata files, checksum file, test, and dummy data should live together.
5. Prefer small dummy-data tests and metadata/API checks before any full generation or network-dependent workflow.

## Installed API facts to rely on

The inspected package version exposes these authoring signatures:

- `tfds.core.GeneratorBasedBuilder(*, file_format=None, **kwargs)`
- `tfds.core.BuilderConfig(name, version=None, release_notes=None, supported_versions=<factory>, description=None, tags=<factory>)`
- `tfds.core.Version(version, experiments=None, tfds_version_to_prepare=None)`
- `tfds.core.SplitGenerator(name, gen_kwargs=None)`; this is legacy for new builders, which should return a `{split_name: generator}` dictionary from `_split_generators`.
- `tfds.core.DatasetInfo(*, builder, description=None, features=None, supervised_keys=None, disable_shuffling=False, nondeterministic_order=False, homepage=None, citation=None, metadata=None, license=None, redistribution_info=None, split_dict=None, alternative_file_formats=None, is_blocked=None)`

## Quick checks before handing off code

- `_generate_examples` yields unique, deterministic, comparable keys and feature dictionaries matching `_info().features`.
- Splits match the source data's official splits. If no official split exists, author one split and let users sub-split later.
- `ClassLabel` has human-readable `names` or `names_file` unless there is a specific reason not to.
- Image/video/audio shapes and dtypes are explicit when known.
- Dummy data is non-copyrighted, small, structurally faithful, and split-disjoint unless overlap is intentional and declared in the test.
- Download URLs have registered checksums or the test explicitly explains why checksum validation is skipped.
- Dataset collection versions and referenced dataset versions are explicit and covered by a collection test.
