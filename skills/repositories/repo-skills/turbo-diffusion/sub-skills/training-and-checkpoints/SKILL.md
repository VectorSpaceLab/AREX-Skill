---
name: training-and-checkpoints
description: "Operate TurboDiffusion rCM/SLA training setup, dry-run command
  construction, checkpoint conversion, model merge, quantized export, and
  data/checkpoint layout validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TurboDiffusion Training And Checkpoints

Use this sub-skill when the task is about TurboDiffusion rCM/SLA training setup, debug-only training command construction, Distributed Checkpoint (DCP) versus PyTorch `.pth` formats, merging SLA/rCM updates, converting sharded safetensors, or exporting modified/quantized Wan checkpoints.

Do **not** run full training or model conversion by default. Full training, dataset synthesis, checkpoint quantization, and inference-format conversion are GPU/model/data heavy and remain skip-expensive unless the user explicitly authorizes them and provides checkpoints, data, credentials policy, and backend readiness.

## Route first

- Use [references/training-and-data.md](references/training-and-data.md) for rCM/SLA training prerequisites, debug/dry-run planning, data shard layout, checkpoint roots, and WANDB/environment decisions.
- Use [references/checkpoint-workflows.md](references/checkpoint-workflows.md) for DCP-to-`.pth`, `.pth`-to-DCP, merge arithmetic, safetensors conversion, and `modify_model` export semantics.
- Use [references/cli-reference.md](references/cli-reference.md) for safe command templates and supported flags for public training/checkpoint utilities.
- Use [references/troubleshooting.md](references/troubleshooting.md) when a user reports DCP/PTH confusion, missing roots/shards, training extras, WANDB issues, mismatched model names, or quantization/SLA failures.

## Bundled safe helpers

These helpers only build commands or run a tiny CPU tensor arithmetic check; they do not download, train, execute model inference, or require the original checkout.

- [scripts/build_training_dryrun_command.py](scripts/build_training_dryrun_command.py): render a `torchrun ... -m scripts.train --dryrun` command with explicit config/checkpoint/data overrides.
- [scripts/build_modify_model_command.py](scripts/build_modify_model_command.py): render a `modify_model.py` checkpoint export/quantization command for Wan2.1/Wan2.2 model profiles.
- [scripts/build_safetensors_to_pth_command.py](scripts/build_safetensors_to_pth_command.py): render a sharded safetensors-to-`.pth` command with optional key prefixing.
- [scripts/tiny_merge_models_check.py](scripts/tiny_merge_models_check.py): create temporary tiny tensors and verify the source merge formula `base + w * (diff_target - diff_base)` on CPU.

## Operating rules

1. Start with layout validation: checkpoint root, teacher DCP, VAE, text encoder, negative embedding, output root, and WebDataset shard pattern.
2. For training requests, prefer a dry-run/config-composition command first. Explain that actual training needs CUDA/multi-GPU readiness, training extras, model/data files, and a WANDB/offline logging decision.
3. For DCP conversion, distinguish direction: `.pth` teacher checkpoint must be converted to DCP before FSDP training; saved training DCP directories can later be converted back to `.pth`.
4. For model merge, warn that mismatched shapes/keys are not fatal in the source utility but require manual key-coverage inspection before treating the output as good.
5. For quantized export, ensure the source checkpoint is already in the expected rCM/SLA state-dict shape, choose a valid Wan model name, and align `--quant_linear` with later inference/serving commands.
6. For source-layout use, mention the public package quirk: top-level imports such as `rcm`, `imaginaire`, `SLA`, `ops`, `scripts`, and `modify_model` often require setting `PYTHONPATH` to the package source directory.

## Cross-skill routing

- Route full T2V/I2V use of converted checkpoints to the `video-inference` sub-skill.
- Route interactive serving with converted checkpoints to the `interactive-serving` sub-skill.
- Route CUDA extension build, INT8/FastNorm op failures, plain SLA versus SageSLA backend decisions, or SpargeAttn installation issues to the `acceleration-backends` sub-skill.
