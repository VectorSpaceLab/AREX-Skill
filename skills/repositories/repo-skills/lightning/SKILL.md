---
name: lightning
description: "Build, configure, debug, distribute, and deploy PyTorch Lightning
  and Lightning Fabric workflows using Trainer, LightningModule, LightningCLI,
  Fabric, accelerators, strategies, and serving utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Lightning Repo Skill

Use this skill when working with Lightning, PyTorch Lightning, or Lightning Fabric training code, CLI/config-driven experiments, distributed accelerators, expert Fabric loops, or production prediction/serving workflows.

## Start Here

1. Prefer modern imports for new code: `import lightning as L`, `import lightning.pytorch as pl`, or `from lightning.fabric import Fabric`.
2. Run a minimal import check before deeper debugging:

```bash
python -c "import lightning as L; import lightning.pytorch as pl; from lightning.fabric import Fabric; print(L.__version__, pl.Trainer, Fabric)"
```

3. Pick the route by user intent, not by source module name.
4. Use bundled smoke scripts for safe local validation before suggesting long training, downloads, GPUs, multi-process launch, or servers.
5. Treat original Lightning examples and tests as evidence only. This skill bundles reusable scripts and distilled references so future agents do not need the source checkout.

## Route Map

- `sub-skills/training-core/SKILL.md`: standard `LightningModule`, `LightningDataModule`, `Trainer`, callbacks, loggers, checkpointing, tuning, reproducibility, conversion from raw PyTorch, and train/validate/test/predict loops.
- `sub-skills/fabric-expert-loops/SKILL.md`: expert-controlled PyTorch loops with `Fabric`, `fabric.setup`, `fabric.backward`, manual optimizer steps, launch, logging, checkpoint IO, and custom trainers.
- `sub-skills/cli-configuration/SKILL.md`: `LightningCLI`, `LightningArgumentParser`, YAML config, environment variables, `--print_config`, subclass modes, optimizer/scheduler injection, and saved config behavior.
- `sub-skills/distributed-accelerators/SKILL.md`: `accelerator`, `devices`, `strategy`, `precision`, DDP, FSDP, DeepSpeed, model/tensor parallel, MPS/TPU/GPU, cluster, and backend troubleshooting.
- `sub-skills/deployment-serving/SKILL.md`: prediction-only code, checkpoint inference, pure PyTorch conversion, TorchScript/ONNX/`torch.export`, pruning/quantization, `ServableModule`, and serving validation.

## Shared References

- `references/package-overview.md`: package layout, install variants, import aliases, optional extras, and compatibility notes.
- `references/troubleshooting.md`: cross-cutting install/import, dependency, version, optional-extra, and environment issues.
- `references/repo-provenance.md`: source repository state, evidence paths, version, and refresh baseline.
- `scripts/lightning_env_report.py`: self-contained environment/import diagnostic helper for Lightning installations.

## Common Decisions

- Use `Trainer` when Lightning should own loops, devices, precision, callbacks, logging, and checkpoints.
- Use `Fabric` when the user needs a custom PyTorch loop but wants Lightning to handle device, precision, distributed setup, logging, or checkpoint helpers.
- Use `LightningCLI` when classes should be instantiated from command-line/YAML/env config instead of hand-written argparse.
- Use `distributed-accelerators` before recommending FSDP, DeepSpeed, TPU, MPS, FP8, or multi-node settings; runtime GPU/distributed validation is environment-specific.
- Use `deployment-serving` when the goal is inference, export, serving, or removing Lightning from a production runtime.

## Safe Validation Commands

```bash
python scripts/lightning_env_report.py --json
python sub-skills/training-core/scripts/lightning_smoke.py --help
python sub-skills/fabric-expert-loops/scripts/fabric_smoke.py --help
python sub-skills/cli-configuration/scripts/lightning_cli_smoke.py --help
python sub-skills/distributed-accelerators/scripts/strategy_config_check.py --help
python sub-skills/deployment-serving/scripts/servable_smoke.py --help
```

Run tiny CPU smoke executions only when the target environment has Lightning and Torch installed. Do not run long training, downloads, multi-process launch, server startup, or GPU-specific checks unless the user explicitly asks and the environment is suitable.

## Compatibility Notes

- New code should prefer the `lightning` package and `lightning.pytorch` namespace.
- Existing code may still use `pytorch_lightning`; keep migration advice practical and avoid rewriting imports unless it is part of the task.
- Some optional workflows require extras such as `jsonargparse[signatures]`, server packages, logger integrations, `deepspeed`, XLA, or accelerator-specific packages. Install the smallest extra that matches the selected workflow.
