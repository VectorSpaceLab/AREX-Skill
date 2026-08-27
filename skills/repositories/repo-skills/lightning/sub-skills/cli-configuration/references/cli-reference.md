# LightningCLI and LightningArgumentParser Reference

This reference targets Lightning `2.6.x` public APIs. The aggregate repo version is `2.6.2`; inspection also confirmed the same CLI surfaces against an installable `2.6.1` wheel when `2.6.2` was not yet available on the package index.

## Required Imports

```python
from lightning.pytorch.cli import LightningArgumentParser, LightningCLI, SaveConfigCallback
```

Legacy import compatibility can exist for `pytorch_lightning`, but prefer `lightning.pytorch` in new code.

## Minimal CLI

```python
from lightning.pytorch.cli import LightningCLI


def cli_main():
    LightningCLI(MyLightningModule, MyLightningDataModule)


if __name__ == "__main__":
    cli_main()
```

Do not call `trainer.fit` after the minimal form. With default `run=True`, the CLI adds subcommands and runs the selected `Trainer` method automatically.

## LightningCLI Constructor

High-value constructor arguments:

- `model_class`: `LightningModule` class or callable returning one. If `None`, the CLI expects model selection through config or `--model` and enables subclass selection.
- `datamodule_class`: `LightningDataModule` class or callable returning one. If `None`, datamodule selection is optional and subclass selection is enabled.
- `save_config_callback`: defaults to `SaveConfigCallback`; set `None` to disable automatic config saving.
- `save_config_kwargs`: pass `{"config_filename": "name.yaml"}`, `{"overwrite": True}`, or custom callback options.
- `trainer_class`: defaults to `Trainer`; can be a subclass/callable for custom command implementations.
- `trainer_defaults`: source-code defaults for Trainer arguments; callbacks here are always present and not user-configurable through YAML.
- `seed_everything_default`: default seed behavior for `--seed_everything`.
- `parser_kwargs`: arguments for `LightningArgumentParser`; supports global and per-subcommand parser settings.
- `parser_class`: parser class, normally `LightningArgumentParser` or a subclass.
- `subclass_mode_model`, `subclass_mode_data`: allow subclass selection for provided base classes.
- `args`: parse a list, dict, or `jsonargparse.Namespace` instead of `sys.argv` for tests or embedded callers.
- `run`: default `True`. Set `False` for parse/instantiate-only mode with no subcommands.
- `auto_configure_optimizers`: default `True`. Set `False` when the model owns all optimizer wiring.
- `load_from_checkpoint_support`: default `True`. Preserves parsed hyperparameters so `load_from_checkpoint` can reconstruct nested class configs.

## LightningArgumentParser Constructor

```python
LightningArgumentParser(
    description="Lightning Trainer command line tool",
    env_prefix="PL",
    default_env=False,
)
```

- `env_prefix="PL"` controls environment variable names.
- `default_env=True` enables environment parsing. For subcommands, variables look like `PL_FIT__MODEL__HIDDEN_DIM`.
- The parser extends `jsonargparse.ArgumentParser` and adds Lightning helpers such as `add_lightning_class_args`, `add_optimizer_args`, and `add_lr_scheduler_args`.

## CLI Commands and Argument Shape

With `run=True`, the default subcommands are:

- `fit`: runs `Trainer.fit`.
- `validate`: runs `Trainer.validate`.
- `test`: runs `Trainer.test`.
- `predict`: runs `Trainer.predict`.

Use nested keys that mirror the parsed config:

```bash
python train.py fit --model.hidden_dim=128 --data.batch_size=32
python train.py fit --trainer.max_epochs=10 --trainer.logger=False
python train.py validate --ckpt_path=best
python train.py predict --return_predictions=True
```

Place global `--config` before the subcommand when the YAML contains subcommand sections. Place subcommand-specific `--config` after the subcommand when the YAML contains only that subcommand's body.

## Parse and Instantiate Only

Use `run=False` when custom Python logic must choose the Trainer call:

```python
cli = LightningCLI(MyModel, MyDataModule, run=False)
cli.trainer.fit(cli.model, datamodule=cli.datamodule)
```

In this mode, subcommands are not added. Config keys are top-level (`trainer`, `model`, `data`) instead of nested under `fit`.

## Extending a CLI

Subclass `LightningCLI` and override hooks:

```python
class MyCLI(LightningCLI):
    def add_arguments_to_parser(self, parser: LightningArgumentParser) -> None:
        parser.add_argument("--notification_email", default=None)
        parser.link_arguments("data.batch_size", "model.batch_size")

    def before_fit(self) -> None:
        ...

    def after_fit(self) -> None:
        ...
```

Useful hooks:

- `add_arguments_to_parser(parser)`: add custom arguments, add configurable callbacks, set defaults, or link arguments.
- `before_instantiate_classes()`: inspect or mutate parsed config before model/data/trainer instantiation.
- `after_instantiate_classes()`: run setup after objects exist but before subcommand execution.
- `before_fit`, `after_fit`, `before_validate`, `after_validate`, `before_test`, `after_test`, `before_predict`, `after_predict`: wrap subcommand execution.
- `instantiate_trainer(**kwargs)`: create a new Trainer from parsed config plus overrides.
- `configure_optimizers(lightning_module, optimizer, lr_scheduler=None)`: customize automatic optimizer/scheduler return values.
- `subcommands()`: override only when a custom `trainer_class` exposes additional command methods.

## Configurable Callbacks

For callbacks users should configure in YAML, add the callback class in `add_arguments_to_parser`:

```python
from lightning.pytorch.callbacks import EarlyStopping

class MyCLI(LightningCLI):
    def add_arguments_to_parser(self, parser):
        parser.add_lightning_class_args(EarlyStopping, "early_stopping")
        parser.set_defaults({
            "early_stopping.monitor": "val_loss",
            "early_stopping.patience": 5,
        })
```

Config shape:

```yaml
early_stopping:
  monitor: val_loss
  patience: 5
trainer:
  callbacks:
    - class_path: lightning.pytorch.callbacks.ModelCheckpoint
      init_args:
        monitor: val_loss
```

Command-line append syntax for Trainer callback lists:

```bash
python train.py fit \
  --trainer.callbacks+=EarlyStopping --trainer.callbacks.monitor=val_loss \
  --trainer.callbacks+=LearningRateMonitor --trainer.callbacks.logging_interval=epoch
```

Callbacks passed through `trainer_defaults={"callbacks": ...}` are always present and are not editable from the config.

## Subclass Modes

Use subclass mode for projects with multiple model or data implementations:

```python
LightningCLI(
    BaseModel,
    BaseDataModule,
    subclass_mode_model=True,
    subclass_mode_data=True,
)
```

YAML shape:

```yaml
model:
  class_path: my_package.models.ResNetClassifier
  init_args:
    hidden_dim: 256
data:
  class_path: my_package.data.ImageDataModule
  init_args:
    batch_size: 32
```

Help and print-config for subclass-specific parameters require selecting the class first:

```bash
python train.py fit --model.help my_package.models.ResNetClassifier
python train.py fit --data.help my_package.data.ImageDataModule
python train.py fit --model my_package.models.ResNetClassifier --print_config
```

If a model/datamodule class is omitted in the `LightningCLI` constructor, Lightning treats the corresponding field as subclass-configured by default.

## Optimizers and LR Schedulers

With `auto_configure_optimizers=True`, the CLI can add `--optimizer` and `--lr_scheduler` arguments and override the model's `configure_optimizers` when an optimizer is supplied.

Common commands:

```bash
python train.py fit --optimizer=Adam --optimizer.lr=0.001
python train.py fit --optimizer=AdamW --optimizer.weight_decay=0.01
python train.py fit --optimizer=Adam --lr_scheduler=StepLR --lr_scheduler.step_size=10
python train.py fit --optimizer=Adam --lr_scheduler=ReduceLROnPlateau --lr_scheduler.monitor=val_loss
```

Custom parser wiring:

```python
class MyCLI(LightningCLI):
    def add_arguments_to_parser(self, parser):
        parser.add_optimizer_args(torch.optim.Adam, nested_key="optimizer")
        parser.add_lr_scheduler_args(torch.optim.lr_scheduler.ExponentialLR, nested_key="lr_scheduler")
```

For expert dependency injection, disable automatic override and type-hint callables in the model:

```python
class MyModel(LightningModule):
    def __init__(self, optimizer: OptimizerCallable = torch.optim.Adam):
        self.optimizer = optimizer

    def configure_optimizers(self):
        return self.optimizer(self.parameters())

LightningCLI(MyModel, auto_configure_optimizers=False)
```

## Argument Linking

Use `parser.link_arguments` when one config value should drive another:

```python
class MyCLI(LightningCLI):
    def add_arguments_to_parser(self, parser):
        parser.link_arguments("data.batch_size", "model.batch_size")
        parser.link_arguments("data.num_classes", "model.num_classes", apply_on="instantiate")
```

Use links for derived invariants, not YAML interpolation, when a setting must always remain synchronized.

## Checkpoint Loading Support

With `load_from_checkpoint_support=True`, parsed class/callable hyperparameters are saved in a format that supports `ModelClass.load_from_checkpoint(...)` even with subclass mode or dependency injection. Keep `self.save_hyperparameters()` in the model constructor when checkpoint reconstruction is required.

If `--ckpt_path` points to an existing checkpoint and contains CLI hyperparameters, LightningCLI attempts to merge model hyperparameters from the checkpoint into the parsed config. If parsing fails, it emits `Parsing of ckpt_path hyperparameters failed!`.

## Example Patterns Adapted

- The bundled smoke script adapts the repository's autoencoder-style `LightningCLI(Model, DataModule)` pattern, but replaces downloads with synthetic tensors.
- The fine-tuning example pattern of `add_lightning_class_args`, `link_arguments`, and `parser.set_defaults` is documented here instead of bundled because the original depends on external image data and optional vision packages.
- Serving examples are excluded from this sub-skill except when their script-level CLI configuration is relevant; production serving behavior belongs in `../deployment-serving/SKILL.md`.
