---
name: running-and-training
description: "Run, validate, and troubleshoot Scenic app/config/training
  workflows without accidentally launching expensive jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Scenic Running and Training Router

Use this sub-skill when a user wants to install-check Scenic, understand how the
Scenic application runner passes `--config`, `--workdir`, dataset-service, RNG,
and JAX backend flags into training, validate an experiment config before
launch, build a safe training command, or troubleshoot training utility imports.

## Read or run these bundled files

- Read [references/running-and-configuration.md](references/running-and-configuration.md)
  for app-run semantics, required flags, config shape, safe command construction,
  workdir/checkpoint behavior, dataset service notes, JAX backend flags, and
  no-training validation steps.
- Read [references/training-api.md](references/training-api.md) for
  `lr_schedules`, `optimizers`, `train_utils`, `TrainState`, checkpoint helpers,
  trainer flow, transfer/pretraining caveats, and source-script exclusion notes.
- Read [references/troubleshooting.md](references/troubleshooting.md) when an
  install/import, config, dataset/model/trainer name, TensorFlow Addons/Keras,
  JAX backend, checkpoint, or expensive-training failure appears.
- Run [scripts/scenic_config_probe.py](scripts/scenic_config_probe.py) when a
  user provides a Python config and asks whether it is structurally safe to
  launch. The helper imports the config, prints top-level keys, checks
  dataset/model/trainer/RNG/training-related fields, and never starts training.

## Fast routing

- **Config preflight or launch safety**: run the bundled config probe first,
  then inspect missing or warning fields in `running-and-configuration.md`.
- **Constructing a command**: require a Python config file and a fresh or
  intentionally resumed workdir; include `--config` and `--workdir`; add
  `--dataset_service_address` only with a compatible config.
- **Learning-rate, optimizer, TrainState, checkpoint, or transfer details**:
  read `training-api.md`.
- **`tensorflow_addons`, `keras.src.engine`, `big_vision`, or trainer import
  failures**: read `troubleshooting.md`; avoid importing the trainer registry
  for simple config/LR/optimizer checks.

## Boundaries

- Route model classes, model registry entries, Flax layer APIs, and metric/loss
  authoring to `../modeling-and-layers/SKILL.md`.
- Route dataset registry details, TFDS/raw data layout, and preprocessing
  pipeline internals to `../data-pipelines/SKILL.md`.
- Route project-specific mains, optional dependency catalogs, and project tools
  to `../baselines-and-projects/SKILL.md`.

Do not tell future agents to open or run the original repository's tests,
examples, notebooks, or source files for this sub-skill. Use the bundled
references and helper script as the runtime knowledge base.
