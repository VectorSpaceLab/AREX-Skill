---
name: configuration-and-experiments
description: "Configure a MedicalDetectionToolkit experiment, inspect its CLI
  and fold lifecycle, onboard a bounded toy fixture, and diagnose configuration
  or experiment-directory failures without entering model internals or running
  training."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Configuration and experiments

Use this node when the task is to turn a detector idea into a checked
`experiments/<name>/configs.py` contract, choose a model and 2D/3D operating
dimension, create or inspect an experiment directory, select folds, or prepare a
small toy fixture. This repository is legacy and explicitly unmaintained; pin
the checkout/package version before treating a configuration as reproducible.
Do not start training, testing, analysis, or CUDA compilation while merely
validating configuration. The bundled scripts are safe inspection/fixture
helpers and do not import the source checkout.

## Route by intent

1. **Need a config or model/dimension decision?** Read
   [configuration.md](references/configuration.md), then route detector-specific
   behavior to [models-and-architectures](../models-and-architectures/SKILL.md)
and data shape/path behavior to [data-and-preprocessing](../data-and-preprocessing/SKILL.md).
2. **Need an invocation or lifecycle decision?** Read
   [cli-reference.md](references/cli-reference.md) and
   [experiment-layout.md](references/experiment-layout.md). Use
   [inspect_cli.py](scripts/inspect_cli.py) to print or validate the bounded
   command contract without importing `exec.py`.
3. **Need toy onboarding?** Read the toy section in
   [experiment-layout.md](references/experiment-layout.md) and use
   [generate_toy_fixture.py](scripts/generate_toy_fixture.py). It refuses to
   overwrite existing fixture files and has hard count, shape, and size caps.
   Adapt `n_train_val_data` in a copied config to the fixture count before
   attempting any framework workflow.
4. **A command/config fails?** Read
   [troubleshooting.md](references/troubleshooting.md) before changing paths or
   stored settings. Stop rather than silently switching folds, replacing a
   snapshot, or assuming a modern dependency is compatible.

## Operating contract

- A config module exposes a lowercase `configs` subclass with constructor
  `configs(server_env=None)`. It sets `self.model` and `self.dim`, then calls
  `DefaultConfigs.__init__(self, self.model, server_env, self.dim)` before
  applying experiment-specific paths, data, schedule, and model settings.
- Supported configuration labels evidenced by the experiment files are
  `mrcnn`, `retina_net`, `retina_unet`, `detection_unet`, `ufrcnn`, and in the
  shared default dispatch `ufrcnn_surrounding` and `prob_detector`. Availability
  is version/config dependent; the dispatch key must exist or construction
  fails.
- `dim=2` uses 2D patch/list settings; `dim=3` uses 3D settings. This choice
  affects channels, patch shape, augmentation, anchors, and model-specific
  defaults. Do not infer 3D support from a successful CPU import; route runtime
  prerequisites to [cuda-extensions](../cuda-extensions/SKILL.md) and model
  details to [models-and-architectures](../models-and-architectures/SKILL.md).
- Paths are configuration data, not portable defaults. Replace example machine
  paths with an existing preprocessed-data root and verify that its
  `input_df_name` (normally `info_df.pickle`) and expected `.npy` records exist.
  Do not point a new experiment at a snapshot or private dataset by accident.
- Training/testing snapshot scripts into `exp_dir`; testing then copies the
  stored model/backbone back to the source tree as temporary modules. This is a
  legacy mutable workflow. Inspect and obtain an explicit safe workspace before
  using it; this node does not perform those writes.
- `n_cv_splits` defaults to 5. With no `--folds`, train/test loops use
  `range(cf.n_cv_splits)`. A supplied fold list is not range-validated by the
  CLI, so validate it yourself and ensure fold IDs match `fold_ids.pickle` when
  the experiment is not hold-out.
- `--use_stored_settings` is a reproducibility choice, not a generic repair
  switch. Prefer the experiment snapshot for testing and for resumed work when
  it is complete; otherwise stop on missing or inconsistent `configs.py`,
  `default_configs.py`, `model.py`, or `backbone.py`.
- This node owns configuration/lifecycle routing only. It does not explain
  detector forward passes, data conversion, prediction consolidation,
  evaluation metrics, or custom-op builds; use the linked sibling nodes.

All detailed tables, source-backed values, and failure handling live in the
four linked references so this file remains a router.
