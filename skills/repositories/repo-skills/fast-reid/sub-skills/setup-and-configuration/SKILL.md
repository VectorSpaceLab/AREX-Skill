---
name: setup-and-configuration
description: "Set up FastReID from a source-only checkout, verify imports, and
  manage config creation, merge, freeze, YAML inheritance, command-line
  overrides, and model-zoo recipe selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Setup and Configuration

Use this sub-skill for FastReID environment preparation and config inspection.
It covers source-only install notes, import checks, config creation and merge,
`_BASE_` inheritance, command-line `opts`, freeze handling, and model-zoo recipe
selection.

## Use this sub-skill when

- You need to confirm that a FastReID checkout imports cleanly from source.
- You need to merge a config, apply `opts`, freeze it, or inspect selected keys.
- You need to choose the right recipe/config family for a benchmark or model zoo
  entry.

## Route elsewhere when needed

- Dataset directory layouts, dataset registration, and loader validation belong
  to the dataset sub-skill.
- Training/evaluation launch, distributed flags, and checkpoint workflows belong
  to the training sub-skill.
- Backbone/head/loss/model registry details belong to the modeling sub-skill.
- ONNX, Caffe, TensorRT, and project-extension deployment flows belong to the
  deployment sub-skill.

## Bundled references

- [references/configuration.md](references/configuration.md) — config lifecycle,
  safe file loading, `_BASE_` inheritance, freeze/defrost, and CPU-friendly
  override patterns.
- [references/model-zoo-and-recipes.md](references/model-zoo-and-recipes.md) —
  recipe families, dataset-to-config selection, and model-zoo guidance.
- [references/troubleshooting.md](references/troubleshooting.md) — source-only
  install, dependency gaps, Python 3.10+ `collections.Mapping`, unsafe YAML,
  missing weights, malformed `opts`, and legacy demo import mismatches.

## Bundled script

- [scripts/config_merge_check.py](scripts/config_merge_check.py) — merge a
  config with optional `--opts`, print selected keys, and optionally freeze the
  result without training or downloads.

## Public facts to remember

- FastReID is version `1.3`.
- The checkout is source-only, so import help comes from a repo-root `sys.path`
  entry or a private `.pth` file, not from editable distribution metadata.
- `get_cfg()` returns a `CfgNode`.
- `merge_from_file()` supports `_BASE_` and defaults to safe YAML loading.
- `merge_from_list()` applies CLI overrides.
- `MODEL.DEVICE` defaults to `cuda`, so CPU dry-runs must override it
  explicitly.
