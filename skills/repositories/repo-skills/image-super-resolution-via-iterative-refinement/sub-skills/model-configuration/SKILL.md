---
name: model-configuration
description: "Route config parsing, SR3/DDPM selection, conditional inputs, beta
  schedules, checkpoints, GPU ids, and model API facts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Configuration

Use this sub-skill when a request is about the repo's comment-bearing JSON configs, model family choice, noise schedules, checkpoint resume, GPU selection, or the diffusion model object's public API.

## What this sub-skill owns

- JSON-with-comments config files under `config/`.
- The `which_model_G` switch between `ddpm` and `sr3`.
- Conditional super-resolution versus unconditional generation.
- Beta schedules, `resume_state`, `gpu_ids`, and W&B project metadata.
- Verified method signatures and save/load behavior in `model/`.
- A local config inspector for quick summaries.

## Start here

1. Read [references/configuration.md](references/configuration.md) for field meaning and config-family mapping.
2. Read [references/model-api.md](references/model-api.md) for the verified class and method contracts.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when a config looks valid but parse, load, or runtime setup fails.
4. Run [scripts/inspect_config.py](scripts/inspect_config.py) to summarize one or more comment-bearing config files.

## Route elsewhere

- Dataset layout, LR/HR preparation, and LMDB/image-store checks are outside this sub-skill.
- Long training, validation, inference, and sampling workflows are outside this sub-skill except for the config facts they consume.
- Evaluation metrics and result-folder inspection are outside this sub-skill.

## Operating notes

- Treat `config/*.json` as JSON-with-comments, not strict JSON.
- The CLI `-p/--phase` and `-gpu/--gpu_ids` flags override config values at runtime.
- The stored `phase` is only the default input; `core.logger.parse` rewrites it from the CLI.
- `path.resume_state` names the checkpoint stem only; the loader appends `_gen.pth` and `_opt.pth`.
- `conditional=true` implies a 6-channel UNet input in this repo; `conditional=false` uses 3 channels.
- `gpu_ids` controls `CUDA_VISIBLE_DEVICES` and distributed wrapping; verify the rendered GPU string before assuming multi-GPU behavior.
- `norm_groups` must divide every UNet stage width.
- W&B logging is split between the JSON `wandb.project` field and CLI flags such as `-enable_wandb`, `-log_wandb_ckpt`, `-log_eval`, and `-log_infer`.

## Evidence basis

This router is grounded in the project README, the `config/*.json` families, `core/logger.py`, `model/networks.py`, `model/model.py`, `model/ddpm_modules/*`, and `model/sr3_modules/*`.
