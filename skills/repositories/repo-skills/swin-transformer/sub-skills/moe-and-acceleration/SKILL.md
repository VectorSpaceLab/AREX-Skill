---
name: moe-and-acceleration
description: "Use this repo skill for Swin-Transformer optional Swin-MoE, Tutel,
  Apex, fused window-process CUDA extension, distributed checkpoint, and backend
  probe workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# moe-and-acceleration

Use this sub-skill when a task involves Swin-MoE, Tutel, optional Apex fused layernorm/optimizers, `--fused_window_process`, the CUDA window-process extension, or distributed MoE checkpoint behavior.

## Covers

- `main_moe.py` command shape and distributed expectations.
- `MODEL.SWIN_MOE` config fields: experts, top-k, capacity factor, router type, aux loss, and MoE block placement.
- Tutel dependency and why CPU is not a truthful substitute for MoE runtime verification.
- Optional `swin_window_process` CUDA extension build/probe guidance.
- Apex optional flags: fused layernorm, `fused_adam`, `fused_lamb`.
- Rank-sharded MoE checkpoints and save/load caveats.

## Routes elsewhere

- Baseline Swin/SwinV2/Swin-MLP constructors: `core-models`.
- Ordinary supervised `main.py` commands: `training-eval-cli`.
- Generic checkpoint flag meaning and data layouts: `data-and-checkpoints`.
- SimMIM commands: `simmim-workflows`.

## Workflow

1. Run `scripts/check_optional_backends.py` to see which optional backends are actually available.
2. Read `references/moe-and-acceleration.md` for command and config rules.
3. If a command is requested, build it with the root `scripts/swin_cli_command_builder.py --workflow moe-train` or `moe-eval`.
4. If backend probes fail, read `references/troubleshooting.md` and avoid claiming runtime verification.

## Verification boundary

CPU import checks are not evidence that Tutel MoE, Apex fused ops, or the custom CUDA extension works. Treat those as optional backend capabilities that require compatible CUDA/PyTorch/toolkit/runtime evidence.

## Linked files

- `references/moe-and-acceleration.md` - MoE and optional acceleration workflow details.
- `references/troubleshooting.md` - missing Tutel/Apex/fused-kernel and distributed checkpoint issues.
- `scripts/check_optional_backends.py` - safe optional backend probe.
