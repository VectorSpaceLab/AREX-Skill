---
name: accelerate
description: "Use Hugging Face Accelerate for PyTorch training-loop migration,
  distributed launch/configuration, DeepSpeed/FSDP/TPU backend setup, big-model
  inference/offload, checkpointing, tracking, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Accelerate

Use this repo skill when a task involves Hugging Face Accelerate: adapting PyTorch code with `Accelerator`, building `accelerate launch` commands, validating config files, choosing distributed backends, loading large models with device maps/offload, or saving/logging training state.

## Install And Import Check

For normal package use:

```bash
pip install accelerate
python - <<'PY'
import accelerate
from accelerate import Accelerator
print(accelerate.__version__)
print(Accelerator)
PY
```

Install optional backends only for workflows that need them, such as DeepSpeed, torch-xla, transformer-engine, torchao, bitsandbytes, experiment trackers, or model libraries. Do not install broad development or testing extras unless the user explicitly asks for repository development coverage.

## Route By Task

- Use `sub-skills/training-loop-integration/` to migrate raw PyTorch training/evaluation loops to `Accelerator`, `prepare()`, `backward()`, mixed precision, dataloader handling, gradient accumulation, DDP kwargs, and distributed-loop debugging.
- Use `sub-skills/configuration-and-cli/` to create or validate Accelerate config YAML, construct `accelerate launch` commands, inspect `accelerate env`, estimate memory, merge weights, and plan multi-node or SLURM launches without executing them.
- Use `sub-skills/distributed-training-backends/` to choose and configure DeepSpeed, FSDP/FSDP2, Megatron-LM, TPU/XLA, FP8, quantization, compilation, tensor/context parallelism, Local SGD, or DDP communication hooks.
- Use `sub-skills/big-model-inference/` for `init_empty_weights`, `infer_auto_device_map`, `load_checkpoint_and_dispatch`, CPU/disk offload, model hooks, PiPPy/distributed inference, and memory-sizing workflows.
- Use `sub-skills/checkpointing-and-tracking/` for `save_state`, `load_state`, checkpoint hooks, `ProjectConfiguration`, model export, experiment trackers, distributed-safe logging, profiling, and memory cleanup.

## Shared References And Scripts

- Read `references/troubleshooting.md` first for cross-cutting install/import, CLI, optional dependency, hardware, and distributed hang triage.
- Read `references/repo-provenance.md` before deciding whether this skill matches a current Accelerate checkout or should be refreshed.
- Run `scripts/check_accelerate_environment.py --help` or the script itself for a safe import/CLI/backend availability diagnostic.

## Common Decision Points

- Prefer `Accelerator` and `accelerator.prepare(...)` for ordinary training loops; do not start with backend-specific plugins until the baseline loop is clear.
- Prefer `accelerate config` or a reviewed config YAML when launch commands become long, multi-node, or backend-specific.
- Treat DeepSpeed, FSDP, TPU/XLA, FP8, and quantization as optional backend surfaces with package, hardware, and version constraints.
- Use big-model dispatch/offload APIs for model loading and inference memory pressure; do not use them as a replacement for normal training-loop preparation.
- Use checkpointing/tracking helpers from the nearest sub-skill before adding custom save/load or logging code in distributed jobs.

## Safety Defaults

- Run helper scripts with `--help` first when adapting them.
- Avoid commands that download models/datasets, launch multi-process distributed jobs, require GPUs/TPUs/SLURM, or contact external tracker services unless the user explicitly asks and the environment is ready.
- For verification in limited environments, prefer parser checks, config validation, tiny CPU smoke tests, and static backend diagnostics over full distributed execution.
