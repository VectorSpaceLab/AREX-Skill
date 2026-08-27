---
name: training-core
description: "Build, convert, debug, and validate core Lightning training
  workflows with LightningModule, LightningDataModule, Trainer, callbacks,
  loggers, checkpointing, tuning, and reproducibility."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Lightning Training Core

Use this sub-skill when the task is about standard `lightning.pytorch` training, validation, testing, prediction, callbacks, loggers, checkpointing, or converting raw PyTorch training loops to Lightning.

## Start Here

1. Import the public API with `import lightning as L` for new code, or `import lightning.pytorch as pl` when existing code already follows the `pl` convention.
2. Put model math and steps in a `LightningModule`; put splits, transforms, and dataloaders in a `LightningDataModule` when data setup should be reusable.
3. Let `Trainer` own the loop, device movement, precision, callbacks, logging, checkpointing, and `fit`/`validate`/`test`/`predict` orchestration.
4. Use `fast_dev_run=True` or a tiny `max_steps`/`limit_*_batches` run before proposing longer training.
5. Run `scripts/lightning_smoke.py --help` or a one-step CPU smoke run to validate imports and the core workflow.

## Route Tasks

- Core model code, datamodules, `Trainer.fit`, `Trainer.validate`, `Trainer.test`, `Trainer.predict`, callbacks, loggers, checkpointing, tuning, and reproducibility: use this sub-skill.
- `LightningCLI`, YAML config, parser subclasses, `--print_config`, environment variable parsing, or config save behavior: route to `../cli-configuration/SKILL.md`.
- Fabric manual loops, `Fabric.setup`, `fabric.backward`, Fabric checkpoint IO, or expert-controlled PyTorch loops: route to `../fabric-expert-loops/SKILL.md`.
- Deep accelerator, strategy, FSDP, DeepSpeed, TPU, MPS, GPU, precision, launch, or cluster behavior: route to `../distributed-accelerators/SKILL.md`.
- Serving, export, pure prediction services, ONNX/TorchScript/TensorRT, or `lightning.pytorch.serve`: route to `../deployment-serving/SKILL.md`.

## References

- `references/api-reference.md`: common API imports, signatures, Trainer options, module/datamodule hooks, callback/logger/checkpoint surfaces.
- `references/workflows.md`: raw PyTorch conversion, standard train/eval/predict flows, checkpoint resume/load, tuning, reproducibility, validation steps.
- `references/troubleshooting.md`: installation/import, optional dependencies, monitor/logging, checkpoints, dataloaders, Trainer misuse, and CPU/GPU boundary issues.
- `scripts/lightning_smoke.py`: self-contained synthetic autoencoder smoke adapted from Lightning examples without downloads or source-repo dependencies.

## Quick Validation

```bash
python sub-skills/training-core/scripts/lightning_smoke.py --help
python sub-skills/training-core/scripts/lightning_smoke.py --max-steps 1 --fast-dev-run
```

Expected signal: the help command prints CLI options; the one-step run imports Lightning and Torch, creates synthetic tensors, runs a tiny CPU `Trainer.fit`, then prints a `LIGHTNING_SMOKE_OK` summary. If Lightning is missing, follow `references/troubleshooting.md` before changing model code.
