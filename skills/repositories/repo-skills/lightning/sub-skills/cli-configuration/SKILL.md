---
name: cli-configuration
description: "Build and troubleshoot LightningCLI and LightningArgumentParser
  workflows for YAML, environment-variable, subclass, optimizer, scheduler, and
  saved-config driven Lightning training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Lightning CLI Configuration

Use this sub-skill when a task involves `LightningCLI`, `LightningArgumentParser`, config files, environment variables, `--print_config`, subclass modes, command subcommands, optimizer/scheduler CLI injection, or saved run configuration.

## Route First

- For LightningModule, LightningDataModule, Trainer loop, callback, logger, checkpoint, or metric semantics, use `../training-core/SKILL.md` first and return here only for CLI wiring.
- For `accelerator`, `devices`, `strategy`, precision, FSDP, DDP, DeepSpeed, TPU, MPS, or GPU behavior through CLI flags, use `../distributed-accelerators/SKILL.md` for the strategy decision and this sub-skill for config syntax.
- For prediction-only exports, `ServableModule`, endpoint validation, or production serving scripts, use `../deployment-serving/SKILL.md`; use this sub-skill only if the serving script is intentionally wrapped in `LightningCLI`.

## Start Here

1. Confirm CLI extras are installed: `python -c "from lightning.pytorch.cli import LightningCLI, LightningArgumentParser"`. If it fails, install `jsonargparse[signatures]` or `lightning[pytorch-extra]`.
2. Pick the CLI mode:
   - `LightningCLI(Model, DataModule)` for normal `fit`, `validate`, `test`, `predict` subcommands.
   - `LightningCLI(Model, DataModule, run=False)` for parse/instantiate-only flows where code calls `trainer.fit(...)` manually.
   - `LightningCLI(BaseModel, BaseData, subclass_mode_model=True, subclass_mode_data=True)` or omit a class to select implementations from config.
3. Generate an inspectable config before running training: `python train.py fit --print_config > config.yaml`.
4. Keep config changes in YAML or environment variables, then override only the last-mile settings on the command line.

## Reference Map

- `references/cli-reference.md` covers API signatures, subcommands, parser extension hooks, subclass modes, callbacks, optimizer/scheduler injection, and checkpoint loading support.
- `references/configuration.md` covers YAML layout, config precedence, default config files, environment variables, `--print_config`, config saving, and validation commands.
- `references/troubleshooting.md` covers missing extras, import issues, parse errors, subclass resolution, optimizer/scheduler mistakes, saved config collisions, optional dependencies, and CPU/GPU boundary checks.
- `scripts/lightning_cli_smoke.py` is a safe, synthetic CLI demo for `--help`, `--print_config`, env parsing, and a tiny CPU `fast_dev_run` smoke.

## Common Commands

```bash
python train.py --help
python train.py fit --help
python train.py fit --print_config > config.yaml
python train.py fit --config config.yaml --trainer.max_epochs=10
python train.py fit --model.help my_package.models.MyModel
python train.py fit --model my_package.models.MyModel --print_config
PL_FIT__TRAINER__MAX_EPOCHS=1 python train.py fit
JSONARGPARSE_DEBUG=true python train.py fit --config config.yaml
```

## Bundled Smoke Script

Run from this sub-skill directory or with an explicit path:

```bash
python scripts/lightning_cli_smoke.py --help
python scripts/lightning_cli_smoke.py fit --print_config
PL_FIT__TRAINER__MAX_EPOCHS=1 python scripts/lightning_cli_smoke.py fit --trainer.fast_dev_run=1
```

The script uses generated tensors, CPU-safe defaults, `save_config_callback=None`, and no downloads. It is intended to prove CLI parsing and minimal execution, not GPU, distributed, or dataset behavior.
