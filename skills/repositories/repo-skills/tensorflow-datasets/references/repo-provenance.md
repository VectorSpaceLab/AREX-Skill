# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
TensorFlow Datasets. If the current repo commit, dirty state, package version,
public entry points, or major evidence paths differ from this snapshot, run
`refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T03:46:33Z",
  "repository": {
    "name": "tensorflow-datasets",
    "remote_url": "https://github.com/tensorflow/datasets.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "470d259ad213ac458c5013f35e6fd01716c567a5",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "tensorflow-datasets",
      "version": "4.9.10+nightly",
      "import_names": ["tensorflow_datasets"],
      "console_scripts": ["tfds"]
    }
  ],
  "evidence": {
    "source_roots": [
      "tensorflow_datasets",
      "tensorflow_datasets/core",
      "tensorflow_datasets/scripts/cli",
      "tensorflow_datasets/testing",
      "tensorflow_datasets/dataset_collections"
    ],
    "docs": [
      "README.md",
      "docs/overview.ipynb",
      "docs/cli.ipynb",
      "docs/data_source.ipynb",
      "docs/dataset_collections.ipynb",
      "docs/determinism.ipynb",
      "docs/add_dataset.md",
      "docs/add_dataset_collection.md",
      "docs/beam_datasets.md",
      "docs/common_gotchas.md",
      "docs/decode.md",
      "docs/external_tfrecord.md",
      "docs/features.md",
      "docs/format_specific_dataset_builders.md",
      "docs/gcs.md",
      "docs/performances.md",
      "docs/splits.md",
      "docs/datasets_versioning.md",
      "docs/community_catalog/overview.md",
      "docs/community_catalog/huggingface.md"
    ],
    "tests": [
      "tensorflow_datasets/import_public_api_test.py",
      "tensorflow_datasets/import_without_tf_test.py",
      "tensorflow_datasets/core/load_test.py",
      "tensorflow_datasets/core/read_only_builder_test.py",
      "tensorflow_datasets/core/features/*_test.py",
      "tensorflow_datasets/testing/*_test.py",
      "tensorflow_datasets/scripts/cli/*_test.py",
      "tensorflow_datasets/core/folder_dataset/*_test.py",
      "tensorflow_datasets/core/community/*_test.py",
      "tensorflow_datasets/core/dataset_builder_beam_test.py",
      "tensorflow_datasets/core/beam_utils_test.py"
    ],
    "configs": ["setup.py", "pyproject.toml", "tensorflow_datasets/community-datasets.toml"],
    "scripts": ["tensorflow_datasets/scripts/cli", "tensorflow_datasets/scripts/download_and_prepare.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If the current checkout has source or documentation changes outside generated
  skill artifacts, refresh before relying on exact API or CLI guidance.
- If package metadata, public entry points, CLI subcommands, optional dependency
  behavior, or TFDS file-format support changed, refresh even on the same
  commit.
- The snapshot is dirty because the repository-local `skills/` production output
  was present during generation; source, docs, package metadata, and tests were
  otherwise taken from the commit listed above.
