# CLI Configuration Troubleshooting

Use this guide when a `LightningCLI` or `LightningArgumentParser` script fails before training starts, parses unexpected values, cannot instantiate classes, or saves config unexpectedly.

## Missing CLI Extras

Signal examples:

- `ModuleNotFoundError` mentioning `jsonargparse[jsonnet,signatures]>=...`.
- Importing `LightningArgumentParser` works, but constructing it fails with a jsonargparse requirement message.
- `--help` does not show signature-derived class arguments.

Fix:

```bash
pip install "jsonargparse[signatures]"
# or
pip install "lightning[pytorch-extra]"
```

Then verify:

```bash
python -c "from lightning.pytorch.cli import LightningCLI, LightningArgumentParser; print('cli-ok')"
```

## Import Package Confusion

Prefer:

```python
import lightning as L
from lightning.pytorch.cli import LightningCLI
```

Legacy `pytorch_lightning` compatibility may exist, but new CLI examples should use `lightning.pytorch`. Avoid mixing imports from `lightning.pytorch` and `pytorch_lightning` in the same script because class identity checks and subclass discovery can become confusing.

## Parser Exits Without a Useful Stack Trace

CLI parse failures normally exit with a short message and non-zero code. Enable debug mode while developing:

```bash
JSONARGPARSE_DEBUG=true python train.py fit --config config.yaml
```

This exposes a stack trace from `jsonargparse`/Lightning and usually points to the unresolved type, import path, or invalid value.

## `--config` Is Ignored or Applied to the Wrong Scope

Check placement:

```bash
python train.py --config config-with-fit-section.yaml fit
python train.py fit --config fit-body-only.yaml
```

A global config with `fit:`, `validate:`, `test:`, or `predict:` sections should be passed before the subcommand. A body config containing `trainer:`, `model:`, and `data:` directly should be passed after the subcommand.

## Environment Variables Do Not Apply

Checklist:

1. `parser_kwargs={"default_env": True}` is set.
2. The prefix matches `env_prefix`, default `PL`.
3. The subcommand is included when `run=True`.
4. Nested keys use double underscores.
5. Values are strings that parse to the expected type.

Examples:

```bash
export PL_FIT__TRAINER__MAX_EPOCHS=1
export PL_FIT__TRAINER__LOGGER=False
export PL_FIT__DATA__BATCH_SIZE=16
python train.py fit
```

Inspect actual env names with:

```bash
python train.py fit --help
```

If `run=False`, use names such as `PL_TRAINER__MAX_EPOCHS` without `FIT`.

## Config Override Surprises

Remember precedence:

1. Source defaults.
2. `default_config_files`.
3. Whole-config env variables.
4. Individual env variables.
5. Command line from left to right.

If a value is unexpected, print the final config:

```bash
python train.py fit --config base.yaml --config experiment.yaml --print_config
```

Then move the desired override later on the command line or into the later config file.

## Subclass Mode Cannot Find a Class

Signals:

- Parser rejects `--model MyModel` or `class_path: MyModel`.
- `--model.help MyModel` fails.
- A config works in one Python process but not another.

Fixes:

- Use a full import path: `--model my_package.models.MyModel`.
- Ensure the package/module defining the subclass is importable before the CLI runs.
- Ensure selected classes subclass the configured base class when `subclass_mode_model=True` or `subclass_mode_data=True`.
- For generated configs, prefer full `class_path` entries for portability.

## `--print_config` Omits Subclass Arguments

In subclass mode, Lightning cannot know which subclass to inspect until one is selected. Include the class before printing:

```bash
python train.py fit --model my_package.models.MyModel --print_config
python train.py fit --data my_package.data.MyDataModule --print_config
```

For help on subclass-specific args:

```bash
python train.py fit --model.help my_package.models.MyModel
python train.py fit --data.help my_package.data.MyDataModule
```

## Type Hints or Constructor Defaults Break Parsing

Signals:

- Parse error for an untyped parameter.
- A class-valued argument cannot be serialized in `--print_config`.
- Mutable default instances behave inconsistently across runs.

Fixes:

- Add type hints to configurable `__init__` parameters.
- Add docstrings for clearer help output.
- Avoid instantiated modules/classes as defaults, such as `backbone=MyBackbone()`.
- Use `None`, a string sentinel, a `class_path` config, or `jsonargparse.lazy_instance(...)` for class defaults.
- Use `dict_kwargs` only for genuinely unresolvable dynamic arguments.

## `configure_optimizers` Gets Overridden Unexpectedly

With `auto_configure_optimizers=True`, passing `--optimizer` can cause LightningCLI to override the model's `configure_optimizers`. This is expected and can emit a warning.

Use one of these approaches:

- Accept automatic CLI optimizer wiring and configure through `--optimizer` / `--lr_scheduler`.
- Set `auto_configure_optimizers=False` and keep all optimizer logic in the model.
- Type-hint optimizer callables in the model constructor for dependency injection, then instantiate them in `configure_optimizers`.

If a scheduler has no effect, confirm an optimizer was configured. CLI scheduler arguments need an optimizer target.

## ReduceLROnPlateau Missing Monitor

For `ReduceLROnPlateau`, include a monitor metric:

```bash
python train.py fit --optimizer=Adam --lr_scheduler=ReduceLROnPlateau --lr_scheduler.monitor=val_loss
```

The model must log the metric, usually through `self.log("val_loss", value, on_epoch=True, prog_bar=True)` in validation. Metric semantics belong in `../training-core/SKILL.md`.

## Saved Config Collides With an Existing File

Signal:

- `RuntimeError: Aborting to avoid overwriting ...`

Fixes:

```python
LightningCLI(MyModel, save_config_kwargs={"overwrite": True})
LightningCLI(MyModel, save_config_kwargs={"config_filename": "new_name.yaml"})
LightningCLI(MyModel, save_config_callback=None)
```

For development smoke runs, `--trainer.fast_dev_run=1` skips config saving.

## Custom SaveConfigCallback Fails

If setting `save_to_log_dir=False`, subclass `SaveConfigCallback` and override `save_config`. Passing `save_to_log_dir=False` to the base callback without overriding is invalid.

Do not use distributed collectives inside `save_config`; it runs only on rank zero and can deadlock if other ranks wait for a collective.

## Callback or Logger Config Does Not Instantiate

Use full class paths in YAML when portability matters:

```yaml
trainer:
  logger:
    class_path: lightning.pytorch.loggers.CSVLogger
    init_args:
      save_dir: logs
  callbacks:
    - class_path: lightning.pytorch.callbacks.ModelCheckpoint
      init_args:
        monitor: val_loss
```

If an optional logger dependency fails, either install the logger package or switch to a built-in/available logger. For example, W&B logger workflows need `wandb` installed and authenticated; otherwise use `CSVLogger` or `logger: false` for CLI smoke tests.

## Hardware, Accelerator, and Backend Failures

This sub-skill only covers CLI syntax for settings such as:

```bash
python train.py fit --trainer.accelerator=cpu --trainer.devices=1
python train.py fit --trainer.accelerator=gpu --trainer.devices=1 --trainer.strategy=ddp
```

If runtime errors mention unavailable CUDA devices, unsupported precision, multi-process launch, FSDP, DeepSpeed, TPU, MPS, or distributed sampler behavior, route to `../distributed-accelerators/SKILL.md`. The bundled smoke script validates CPU behavior only.

## Trainer or LightningModule API Misuse

CLI can instantiate invalid combinations that only fail during Trainer execution. Route these to `../training-core/SKILL.md` when errors mention:

- Missing `training_step`, `configure_optimizers`, dataloaders, or validation hooks.
- Invalid metric logging or checkpoint monitor names.
- Callback ordering or Trainer loop behavior.
- Manual `.cuda()` / `.to(device)` anti-patterns inside the module.

## Serving-Specific CLI Confusion

If a CLI wraps a prediction or serving script, this sub-skill can help parse config. If the failure is about `ServableModule`, endpoint availability, FastAPI/MLServer/TorchServe/SageMaker dependencies, export formats, or prediction-only runtime structure, route to `../deployment-serving/SKILL.md`.

## Quick Isolation Commands

```bash
python train.py --help
python train.py fit --help
python train.py fit --print_config > lightning_cli_config.yaml
python train.py fit --config lightning_cli_config.yaml --trainer.fast_dev_run=1 --trainer.accelerator=cpu --trainer.devices=1
JSONARGPARSE_DEBUG=true python train.py fit --config lightning_cli_config.yaml
```

For the bundled sub-skill script:

```bash
python scripts/lightning_cli_smoke.py fit --print_config
python scripts/lightning_cli_smoke.py fit --trainer.fast_dev_run=1
```
