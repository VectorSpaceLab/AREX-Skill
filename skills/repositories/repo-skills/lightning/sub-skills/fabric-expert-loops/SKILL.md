---
name: fabric-expert-loops
description: "Use this sub-skill for Lightning Fabric expert-controlled PyTorch
  loops: setup, launch, backward, dataloaders, precision/devices, logging,
  checkpointing, wrapping, and custom trainer loops."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Fabric Expert Loops

Use this sub-skill when the user wants Lightning Fabric rather than the high-level `Trainer`: manual PyTorch training loops, custom loop engines, explicit optimizer stepping, gradient accumulation, checkpoint dictionaries, rank-aware printing, Fabric CLI launch, or wrapping existing PyTorch code with minimal abstraction.

## Route Here

- Convert a raw PyTorch loop to Fabric while preserving manual control over epochs, batches, optimizers, schedulers, metrics, and checkpoint timing.
- Build a custom trainer loop around `lightning.Fabric` or `lightning.fabric.Fabric`.
- Use `Fabric.setup`, `Fabric.setup_dataloaders`, `Fabric.backward`, `Fabric.save`, `Fabric.load`, `Fabric.print`, `Fabric.log`, and rank/world utilities.
- Choose practical Fabric constructor options for `accelerator`, `strategy`, `devices`, `num_nodes`, `precision`, `plugins`, `callbacks`, and `loggers`.
- Diagnose Fabric-specific launch, wrapping, dataloader, precision, checkpoint, and API-mixing failures.

## Route Elsewhere

- High-level `Trainer`, `LightningModule`, callbacks, and `LightningDataModule` training workflows: `../training-core/SKILL.md`.
- FSDP, DeepSpeed, DDP, TPU, MPS, GPU visibility, multi-node, and precision deep dives: `../distributed-accelerators/SKILL.md`.
- `LightningCLI` / YAML config-driven `Trainer` applications: `../cli-configuration/SKILL.md`.

## Start Here

1. Confirm the user really needs manual loop control. If not, route to `training-core` and recommend `Trainer`.
2. For Fabric, start with the API table in `references/api-reference.md` and the conversion patterns in `references/workflows.md`.
3. For a local environment sanity check, run `python sub-skills/fabric-expert-loops/scripts/fabric_smoke.py --help`, then `python sub-skills/fabric-expert-loops/scripts/fabric_smoke.py --max-steps 2 --checkpoint-path fabric-smoke.pt` from a writable working directory.
4. For launch syntax, use `fabric run --accelerator=cpu --devices=1 sub-skills/fabric-expert-loops/scripts/fabric_smoke.py --max-steps 2`. When using `fabric run`, do not also call `fabric.launch()` in user code.
5. If the issue involves hardware support or distributed strategy internals, cross-check with `../distributed-accelerators/SKILL.md` before giving final advice.

## References

- `references/api-reference.md`: Fabric imports, constructor, core methods, wrappers, launch CLI, logging, and checkpoint APIs.
- `references/workflows.md`: raw PyTorch conversion, gradient accumulation, custom trainer loops, dataloaders, checkpoint resume, and validation patterns.
- `references/troubleshooting.md`: install/import, optional dependencies, launch/API misuse, device/precision, dataloader, wrapping, and checkpoint failures.
- `scripts/fabric_smoke.py`: self-contained CPU-safe tiny Fabric training loop with synthetic tensors and optional checkpoint round-trip.
