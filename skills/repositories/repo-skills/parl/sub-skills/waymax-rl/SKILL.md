---
name: waymax-rl
description: "Operate PARL's optional all-GPU Waymax-RL autonomous-driving
  workflow, validate Hydra configs, and handle JAX/Waymax data and GPU
  prerequisites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Waymax-RL

Use this sub-skill when a task involves PARL's optional Waymax-RL autonomous-driving workflow, Waymax simulator integration, all-GPU RL training, Hydra `ppo_config` files, JAX CUDA setup, Waymo Open Dataset TFRecord paths, or rl-games/PyTorch runner settings for the Waymax environment.

## Verification boundary

This Waymax-RL guidance is source-distilled only. The workflow was **not runtime-verified** during this skill production run because it requires a CUDA-capable GPU, a matching JAX CUDA install, a Waymax checkout at the required revision, and local Waymo-format data. Treat every runtime claim as a checklist to verify in the user's environment before training.

## Safety gate

Do **not** start training until all of these are true:

1. A CUDA GPU is available to JAX, not just to the OS or to PyTorch.
2. Waymax is installed at the required revision and imports cleanly.
3. The config's `params.config.env_config.backend` is `gpu`.
4. The config's `data_cfg.data_path` points to a real TFRecord file or a directory containing the intended files; the default placeholder path is replaced.
5. The user explicitly accepts that this is an all-GPU loop with no CPU substitute and that training can be long-running and memory-intensive.

Run the bundled static validator before any launch:

```bash
python scripts/validate_waymax_config.py <path-to-hydra-yaml>
```

The validator is intentionally static: it does not import JAX, Waymax, TensorFlow, Torch, Hydra, or rl-games, and it never starts training.

## Route map

- Read [`references/setup-and-training.md`](references/setup-and-training.md) for the installation sequence, runtime architecture, training entry point, and GPU/data readiness checklist.
- Read [`references/configuration.md`](references/configuration.md) for the Hydra config schema, important defaults, shape/path implications, and safe edits.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for CUDA JAX failures, missing Waymax revision, TensorFlow conflicts, placeholder data paths, Colab/local differences, and memory issues.
- Use [`scripts/validate_waymax_config.py`](scripts/validate_waymax_config.py) to statically inspect a config and surface placeholder paths, backend expectations, and `mixed_precision` / `multi_gpu` flags.
- Load sibling [`xparl-distributed`](../xparl-distributed/SKILL.md) only to contrast PARL's CPU/xparl distributed actor model with this optional Waymax all-GPU loop. Do not use xparl to replace Waymax-RL's GPU-resident simulator/trainer path.

## Non-goals

This sub-skill does not install CUDA, download Waymo data, clone external repositories, run Colab notebooks, verify a GPU, tune a production driving policy, or claim vehicle-readiness. It only captures the repo-local Waymax-RL operating workflow and the preflight checks needed before a user deliberately runs that workflow.
