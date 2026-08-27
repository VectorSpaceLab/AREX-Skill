---
name: distributed-accelerators
description: "Choose, configure, validate, and troubleshoot Lightning Trainer
  and Fabric accelerators, devices, precision, DDP, FSDP, DeepSpeed, model
  parallel, cluster, and hardware backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Lightning Distributed Accelerators

Use this sub-skill when the task involves `Trainer` or `Fabric` accelerator/device selection, precision, distributed strategies, FSDP, DeepSpeed, DDP, tensor/model parallel, CUDA/GPU, MPS, TPU/XLA, multi-node clusters, or optional dependency and hardware troubleshooting.

## Route Here

- Choose `accelerator`, `devices`, `num_nodes`, `strategy`, `precision`, plugins, and cluster environment settings for `lightning.pytorch.Trainer` or `lightning.Fabric`.
- Diagnose GPU visibility, device-count mismatches, CPU fallback, MPS/TPU/XLA limitations, NCCL/Gloo launch problems, and optional dependency import failures.
- Configure `DDPStrategy`, `FSDPStrategy`, `DeepSpeedStrategy`, `ModelParallelStrategy`, precision plugins, or strategy registry entries.
- Plan large-model training with DDP, FSDP, DeepSpeed ZeRO, activation checkpointing, CPU offload, tensor parallelism, or 2D parallelism.

## Route Elsewhere

- Core `LightningModule`, `LightningDataModule`, callbacks, loggers, checkpoint callbacks, and standard `Trainer.fit` semantics: `../training-core/SKILL.md`.
- Manual Fabric loop structure, `fabric.setup`, `fabric.backward`, checkpoint IO, and custom loop ownership: `../fabric-expert-loops/SKILL.md`.
- `LightningCLI`, YAML, environment-variable, and parser syntax for these settings: `../cli-configuration/SKILL.md`.

## Start Here

1. Identify whether the user is using `Trainer`, `Fabric`, or CLI config; route to sibling sub-skills only for the non-distributed wiring.
2. Pick a baseline from `references/strategy-guide.md`: start with `strategy="auto"` for one process, `ddp` for normal multi-GPU, `fsdp` for DDP out-of-memory, and `deepspeed` for DeepSpeed-specific ZeRO/offload workflows.
3. Cross-check accelerator/device/precision support in `references/precision-and-devices.md` before recommending GPU, MPS, TPU, FP16, BF16, FP8, or quantization settings.
4. Validate syntax without launching workers:

```bash
python scripts/strategy_config_check.py --mode trainer --accelerator cpu --devices 1 --strategy auto --precision 32-true
python scripts/strategy_config_check.py --mode fabric --accelerator auto --devices 1 --strategy auto --precision bf16-mixed
```

5. For failures, use `references/troubleshooting.md` and report whether the evidence is import-only, syntax-only, or requires real distributed/GPU validation. This skill was drafted from CPU inspection evidence and does not claim GPU or distributed runtime was validated.

## Reference Map

- `references/strategy-guide.md`: decision table, Trainer/Fabric configuration patterns, DDP/FSDP/DeepSpeed/model-parallel examples, strategy constructor knobs, and cluster launch notes.
- `references/precision-and-devices.md`: accelerator names, `devices` formats, precision modes, optional precision plugins, and hardware support boundaries.
- `references/troubleshooting.md`: install/import, optional dependencies, invalid API usage, backend limitations, launch errors, device mismatch, and workflow-specific misconfigurations.
- `scripts/strategy_config_check.py`: safe public-package validator for import availability and syntactic configuration checks; it does not spawn subprocesses or start distributed workers.
