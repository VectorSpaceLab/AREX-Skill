---
name: tensorflow-datasets
description: "Use TensorFlow Datasets for dataset loading, builder authoring,
  tfds CLI workflows, external/community formats, Beam scaling, and
  TFDS-specific troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TensorFlow Datasets

Use this repo skill when a task involves TensorFlow Datasets (TFDS), the
`tensorflow_datasets` Python package, the `tfds` CLI, TFDS dataset builders,
prepared TFDS directories, community datasets, split slicing, checksum/manual
download behavior, or Beam/GCS dataset generation.

Do not use it for generic TensorFlow `tf.data` tuning that does not involve
TFDS, Hugging Face `datasets` workflows without TFDS wrappers, or model training
that only consumes an already-built input pipeline.

## Install and minimal checks

Typical public installs:

```bash
python -m pip install tensorflow-datasets
# or, for latest dataset definitions:
python -m pip install tfds-nightly
```

Add optional dependencies only for selected workflows:

```bash
python -m pip install tensorflow-cpu      # tf.data/Keras/most CLI paths on CPU
python -m pip install apache-beam         # Beam/Dataflow/Flink or convert_format Beam paths
python -m pip install mlcroissant         # build_croissant/CroissantBuilder
python -m pip install datasets            # HuggingFace community wrapper
```

Minimal import/metadata smoke:

```bash
python - <<'PY'
import tensorflow_datasets as tfds
print(tfds.__version__)
print(tfds.builder('mnist').info.features)
print(tfds.even_splits('train', 3))
PY
```

If CLI workflows are relevant, also run:

```bash
tfds --version
tfds --help
```

For a broader optional-dependency and CLI probe, run
[`scripts/check_tfds_environment.py`](scripts/check_tfds_environment.py) from the
root of this skill directory.

## Route map

| User need | Read next |
|---|---|
| Load or inspect an existing dataset, choose splits, use `tfds.load`, `tfds.builder`, `tfds.data_source`, `as_numpy`, decoding, visualization, deterministic reading, or metadata-first troubleshooting | [`sub-skills/data-loading/SKILL.md`](sub-skills/data-loading/SKILL.md) |
| Create, review, test, or debug a custom `GeneratorBasedBuilder`, `DatasetInfo`, feature schema, dummy-data test, checksum file, version/config, or dataset collection | [`sub-skills/dataset-authoring/SKILL.md`](sub-skills/dataset-authoring/SKILL.md) |
| Build a safe `tfds` command for `build`, `new`, `convert_format`, or `build_croissant`; inspect flags; avoid accidental downloads, overwrites, or publishes | [`sub-skills/cli-workflows/SKILL.md`](sub-skills/cli-workflows/SKILL.md) |
| Use folder datasets, external TFRecord/prepared layouts, `builder_from_directory`, `ImageFolder`, `TranslateFolder`, Croissant, CoNLL, HuggingFace/community namespaces, or dataset collections | [`sub-skills/formats-and-community/SKILL.md`](sub-skills/formats-and-community/SKILL.md) |
| Scale generation or reading with Beam/Dataflow/Flink/GCS, file formats, shard sizing, deterministic order, worker dependencies, or performance knobs | [`sub-skills/beam-and-performance/SKILL.md`](sub-skills/beam-and-performance/SKILL.md) |

## Shared references

- Read [`references/api-overview.md`](references/api-overview.md) to choose a
  public API, CLI, class, optional dependency, or sub-skill route.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for
  install/import, optional dependency, protobuf, GCS, and cross-workflow triage.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) before
  deciding whether this skill matches a current checkout or should be refreshed.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json)
  stores structured router metadata for managed repo-skill import.

## Operating rules

1. Start metadata-first. Prefer `tfds.builder(...)`, no-download inspectors, CLI
   `--help`, or generated command review before full downloads, conversions, or
   cloud jobs.
2. Make side effects explicit. `tfds.load` defaults to `download=True`,
   `tfds build` writes prepared data, `convert_format` can mutate or overwrite
   dataset directories, and Beam/Dataflow/GCS workflows can spend money or need
   credentials.
3. Install optional dependencies per workflow, not as a broad all-extras set.
   Dataset-specific builders may need additional packages or system binaries.
4. Use public package paths and bundled scripts/references from this skill. Do
   not depend on source-repo docs, notebooks, tests, or maintainer scripts being
   present in the user's working directory.
5. Route ambiguous tasks by the artifact named in the user request: dataset
   name/split/load error -> data loading; builder class/features/checksums ->
   authoring; `tfds` command text -> CLI; external directory/namespace/Croissant
   -> formats/community; Beam/GCS/performance -> Beam and performance.
