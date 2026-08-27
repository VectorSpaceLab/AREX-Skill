---
name: training-and-configs
description: "Configure and launch DALLE2-pytorch decoder and diffusion-prior
  training with validated JSON configs, bundled launch wrappers, trainer APIs,
  checkpoint resume, and Accelerate caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and Configs

Use this sub-skill when a task involves DALLE2-pytorch training setup: `TrainDecoderConfig`, `TrainDiffusionPriorConfig`, JSON configs, bundled training launch wrappers, `DecoderTrainer`, `DiffusionPriorTrainer`, checkpoint save/load/resume, or Accelerate/DeepSpeed launch decisions.

## Route by Need

- For config object structure, required keys, validators, and safe template editing, read [Training Configs](references/training-configs.md).
- For direct Python trainer APIs, constructor signatures, optimizer/EMA behavior, save/load, and resume semantics, read [Trainer API](references/trainer-api.md).
- For command construction, launcher flags, bundled wrappers, and Accelerate examples, read [CLI Reference](references/cli-reference.md).
- For common failures and fixes, read [Troubleshooting](references/troubleshooting.md).
- To validate a config without starting training, run [`scripts/inspect_training_config.py`](scripts/inspect_training_config.py) with `--kind decoder|prior --config PATH`.
- To print but not execute a safe training command, run [`scripts/training_command_builder.py`](scripts/training_command_builder.py) with `--kind decoder|prior --config PATH --launcher python|accelerate`.
- To launch training from this skill tree, use [`scripts/run_decoder_training.py`](scripts/run_decoder_training.py) or [`scripts/run_diffusion_prior_training.py`](scripts/run_diffusion_prior_training.py). These can run for a long time and may download model or metric weights depending on the config.

## Safe Starting Templates

- Decoder CPU structural smoke template: [decoder-cpu-smoke.json](references/config-templates/decoder-cpu-smoke.json). It uses placeholders for WebDataset and embedding roots, console logging, local checkpoint saving, CPU device, no source test data dependency, and no torchmetrics image metrics by default.
- Prior minimal template: [prior-minimal.json](references/config-templates/prior-minimal.json). It uses placeholders for EmbeddingReader image and metadata URLs, console logging, local checkpoint saving, and short diffusion timesteps for config validation.

Always copy a template to a working config path, replace placeholders, then validate it before launching training.

## Boundaries

- WebDataset shard keys, sidecar embedding naming, `EmbeddingReader` folder layout, S3/fsspec setup, tracker credentials, and provider-specific W&B/HuggingFace token handling belong in `../data-and-tracking/`.
- Model construction, generation-only APIs, `DALLE2`, `DiffusionPrior`, `Decoder`, CLIP adapters for sampling, `dream`, VQGAN, and inpainting belong in `../generation-and-api/`.
