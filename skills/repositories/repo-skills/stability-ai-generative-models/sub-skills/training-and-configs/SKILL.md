---
name: training-and-configs
description: "Author, inspect, adapt, and troubleshoot config-driven training
  and model construction for diffusion and autoencoding workflows in
  generative-models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and Configs

Use this sub-skill when a task involves `main.py --base`, OmegaConf dotlist overrides, `instantiate_from_config`, `DiffusionEngine` training configs, `AutoencodingEngine`, `GeneralConditioner`, toy MNIST configs, `USER` placeholders, resume behavior, or Lightning callbacks/log directories.

Do not use this sub-skill for inference execution, checkpoint sampling, UI demos, or watermarking. Route SDXL/API inference tasks to `../inference-api/SKILL.md`, video sampling scripts to `../video-sampling/SKILL.md`, and demos or watermarking to `../demos-and-watermarking/SKILL.md`.

## What This Covers

- Build and inspect `model`, `data`, and `lightning` YAML sections for config-driven training.
- Trace nested `target`/`params` objects that will be consumed by `instantiate_from_config`.
- Adapt diffusion configs around `DiffusionEngine`, denoisers, samplers, losses, conditioners, and first-stage autoencoders.
- Adapt autoencoding configs around `AutoencodingEngine` and legacy `AutoencoderKL` wrappers.
- Reason about `main.py` merge order, CLI overrides, trainer defaults, logging, callbacks, and resume semantics.
- Validate configs statically without starting training, downloading checkpoints, or probing GPUs.

## Fast Static Check

Use the bundled helper for safe inspection before any training command:

```bash
python sub-skills/training-and-configs/scripts/inspect_training_config.py \
  --config path/to/base.yaml \
  --dotlist lightning.trainer.devices=0 model.params.sampler_config.params.num_steps=10
```

Add `--json` when another tool needs structured output. The helper parses and merges config files, reports top-level sections, target paths, placeholders, likely missing `target` keys, data assumptions, resume/name conflicts, and a command template. It never imports training modules, instantiates models, downloads datasets, loads checkpoints, or calls the trainer.

## Required Mental Model

`main.py` treats YAML as the source of truth. It loads every `--base` config from left to right, builds an OmegaConf dotlist from unknown CLI tokens, merges the dotlist last, pops `lightning` out of the project config, and then instantiates `config.model` and `config.data` by calling `instantiate_from_config` on each object.

Every object meant for `instantiate_from_config` needs:

```yaml
target: dotted.import.Path
params:
  key: value
```

`target` resolves to a Python object and `params` are passed as keyword arguments. Missing `target` usually fails with `KeyError: Expected key `target` to instantiate.` Import typos fail later when the module/class path cannot be imported.

## Reference Map

- `references/configuration.md` explains schema patterns, merge rules, target paths, placeholders, and safe overrides.
- `references/api-reference.md` records config-facing signatures and important target classes verified against `sgm` version `0.1.0`.
- `references/workflows.md` gives safe authoring, adaptation, resume, and validation workflows.
- `references/troubleshooting.md` maps common symptoms to recoveries.
- `scripts/inspect_training_config.py` provides executable static validation help.

## Safety Rules

- Prefer static inspection over `main.py` for validation; even `--train false --no-test true` can still instantiate model/data objects and call data preparation.
- Do not recommend long training, checkpoint downloads, webdataset reads, or MNIST/CIFAR downloads as verification.
- Treat `CKPT_PATH`, `DATA_PATH`, `USER` comments, and dataset shard URLs as placeholders until a human supplies local values.
- Keep `--name` and `--resume` mutually exclusive; use `--resume_from_checkpoint` with `--name` only when intentionally creating a new log folder from a checkpoint.
- Assume GPU defaults unless `lightning.trainer.accelerator` and `lightning.trainer.devices` are explicitly reviewed.
