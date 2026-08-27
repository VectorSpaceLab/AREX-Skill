---
name: data-loading
description: "Load, inspect, split, decode, benchmark, and troubleshoot existing
  TensorFlow Datasets datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Loading

Use this sub-skill when the task is to consume an existing TensorFlow Datasets (TFDS) dataset: inspect metadata, select splits, load `tf.data.Dataset` objects, create NumPy/Python data sources, customize decoding, visualize examples, benchmark iteration, or troubleshoot read/download failures.

Do not use this sub-skill to author new dataset builders, run TFDS CLI workflows, configure Beam/Dataflow generation, or design external/community/folder dataset formats. Route those tasks to the sibling sub-skills `dataset-authoring`, `cli-workflows`, `beam-and-performance`, and `formats-and-community` respectively.

## Fast operating path

1. For safe metadata-first exploration, run the bundled inspector without download:

   ```bash
   python scripts/tfds_inspect_dataset.py mnist --split train
   ```

   Add `--download` only when the user explicitly accepts dataset download/preparation cost.
2. Pick the loading surface:
   - `tfds.builder(...)` for metadata, configs, versions, prepared-state checks, and explicit `download_and_prepare()` / `as_dataset()` control.
   - `tfds.load(...)` for the standard `tf.data.Dataset` path.
   - `tfds.data_source(...)` for TensorFlow-less Python sequence / NumPy-style consumption after data exists in a random-access format.
3. Choose splits and determinism controls before iteration. Use split strings or `tfds.even_splits(...)`, then configure `shuffle_files`, `tfds.ReadConfig`, and framework-level sharding deliberately.
4. Add decoding/performance changes only after confirming feature structure from `builder.info.features` or `info.features` returned by `with_info=True`.
5. If an error mentions missing manual files, checksum mismatch, GCS/authentication, unsupported visualization, random-access file format, or TensorFlow/Pandas/Torch/JAX boundaries, use the troubleshooting reference before retrying with downloads or broad optional dependencies.

## Bundled references

- [Loading workflows](references/loading-workflows.md): recipes for `tfds.load`, `tfds.builder`, `tfds.data_source`, NumPy/DataFrame conversion, visualization, Keras, JAX, PyTorch, and GCS decisions.
- [Splits, determinism, and performance](references/splits-determinism-performance.md): split string syntax, `tfds.even_splits`, `ReadConfig`, deterministic shuffling, multi-worker reads, `tfds.benchmark`, auto-cache, decoding, and memory controls.
- [API reference](references/api-reference.md): verified public signatures and option semantics for the loading APIs covered by this sub-skill.
- [Troubleshooting](references/troubleshooting.md): failure-mode table for no-download inspection, missing prepared data, manual downloads, checksum errors, GCS, optional dependencies, feature decoding, and framework boundaries.

## Bundled script

- [Dataset inspector](scripts/tfds_inspect_dataset.py): safely prints package version, builder metadata, splits, features, configs, and optional sample/spec information. It avoids downloads unless `--download` is passed.

## Safety defaults

- Prefer `download=False` or `tfds.builder(...)` inspection when the user only asks to inspect or debug metadata.
- Treat `download=True`, `builder.download_and_prepare()`, public GCS streaming, and manual download paths as potentially network-, storage-, or credential-sensitive.
- Do not promise TensorFlow-less usage from `tfds.load`; use `tfds.data_source` for Python sequence/DataLoader workflows and document that random-access formats such as ArrayRecord are expected.
- Keep deterministic and high-throughput training separate: `shuffle_files=True` improves shard-level shuffling for training but changes read determinism unless controlled with `ReadConfig`.
