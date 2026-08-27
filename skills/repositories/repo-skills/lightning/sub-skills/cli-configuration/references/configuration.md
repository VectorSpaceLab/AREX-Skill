# YAML, Environment, and Saved Configuration

LightningCLI uses `jsonargparse` to map command-line flags, YAML, environment variables, and class constructors into one parsed configuration. Use this reference for reproducible config workflows.

## Installation Check

CLI configuration requires extras beyond a minimal Lightning install:

```bash
python -c "from lightning.pytorch.cli import LightningCLI, LightningArgumentParser; print('ok')"
```

If this fails with a `jsonargparse` requirement message, install one of:

```bash
pip install "jsonargparse[signatures]"
pip install "lightning[pytorch-extra]"
```

## Inspect Available Options

```bash
python train.py --help
python train.py fit --help
python train.py fit --model.help my_package.models.MyModel
python train.py fit --data.help my_package.data.MyDataModule
```

The options come primarily from these signatures:

- `Trainer.__init__` under `trainer.*`.
- `LightningModule.__init__` under `model.*`.
- `LightningDataModule.__init__` under `data.*`.
- Additional classes added with `parser.add_lightning_class_args`, `parser.add_class_arguments`, `parser.add_optimizer_args`, or `parser.add_lr_scheduler_args`.

Use accurate type hints and docstrings in constructors so help output, config validation, and parse errors are useful.

## Generate a Starter YAML

```bash
python train.py fit --print_config > config.yaml
```

For subclass mode, include the class before printing:

```bash
python train.py fit --model my_package.models.MyModel --print_config > config.yaml
```

Useful `--print_config` modifiers are provided by `jsonargparse`, for example:

```bash
python train.py fit --print_config=comments,skip_null
python train.py fit --print_config=skip_default
```

Expected output begins with a Lightning version comment and then YAML. With subcommands, the printed body is the selected subcommand's config.

## Config File Layout

A simple `fit` body config looks like:

```yaml
seed_everything: 1234
trainer:
  max_epochs: 10
  logger: false
model:
  hidden_dim: 128
data:
  batch_size: 32
optimizer:
  class_path: torch.optim.Adam
  init_args:
    lr: 0.001
ckpt_path: null
```

A global multi-subcommand config wraps each command:

```yaml
fit:
  trainer:
    max_epochs: 20
  model:
    hidden_dim: 128
validate:
  trainer:
    limit_val_batches: 4
  ckpt_path: best
test:
  trainer:
    limit_test_batches: 4
```

Use it as:

```bash
python train.py --config config.yaml fit
python train.py --config config.yaml validate
```

A subcommand-body config is passed after the subcommand:

```bash
python train.py fit --config fit.yaml
python train.py fit --config fit.yaml --trainer.max_epochs=100
```

## Class Path Configs

Complex objects use `class_path` and `init_args`:

```yaml
trainer:
  callbacks:
    - class_path: lightning.pytorch.callbacks.ModelCheckpoint
      init_args:
        monitor: val_loss
        mode: min
    - class_path: lightning.pytorch.callbacks.LearningRateMonitor
      init_args:
        logging_interval: epoch
model:
  criterion:
    class_path: torch.nn.CrossEntropyLoss
    init_args:
      reduction: mean
```

When a subclass is imported before the CLI runs, shorthand names can work. Full import paths are safer for saved configs and cross-machine reproducibility.

If a constructor argument cannot be resolved by parser signatures, `dict_kwargs` can pass values through to instantiation without strict parsing:

```yaml
trainer:
  profiler:
    class_path: lightning.pytorch.profilers.PyTorchProfiler
    dict_kwargs:
      profile_memory: true
```

## Config Precedence

Final values are resolved in this order, later entries overriding earlier ones:

1. Defaults defined in Python source code.
2. Existing files listed in `default_config_files`, in order.
3. Entire config environment variable, such as `PL_FIT__CONFIG` when subcommands and env parsing are enabled.
4. Individual environment variables, such as `PL_FIT__SEED_EVERYTHING`.
5. Command-line arguments from left to right, including explicit `--config` files.

Example override:

```bash
python train.py fit --config base.yaml --config experiment.yaml --trainer.max_epochs=5
```

## Default Config Files

Global default config files:

```python
LightningCLI(
    MyModel,
    MyDataModule,
    parser_kwargs={"default_config_files": ["my_cli_defaults.yaml"]},
)
```

Per-subcommand default config files:

```python
LightningCLI(
    MyModel,
    MyDataModule,
    parser_kwargs={
        "fit": {"default_config_files": ["my_fit_defaults.yaml"]},
        "validate": {"default_config_files": ["my_validate_defaults.yaml"]},
    },
)
```

A common default file can contain subcommand sections:

```python
LightningCLI(MyModel, parser_kwargs={"default_config_files": ["defaults.yaml"]})
```

```yaml
fit:
  model:
    hidden_dim: 128
```

Default config files are read only if they exist.

## Environment Variables

Enable env parsing:

```python
LightningCLI(MyModel, MyDataModule, parser_kwargs={"default_env": True})
```

Default prefix is `PL`. With subcommands, names include the subcommand and nested keys:

```bash
export PL_FIT__MODEL__HIDDEN_DIM=128
export PL_FIT__DATA__BATCH_SIZE=32
export PL_FIT__TRAINER__LOGGER=False
export PL_FIT__TRAINER__MAX_EPOCHS=1
python train.py fit
```

To inspect all available environment variable names:

```bash
python train.py fit --help
```

For no-subcommand `run=False` mode, names omit the subcommand, for example `PL_MODEL__HIDDEN_DIM`.

Customize prefix by passing parser kwargs:

```python
LightningCLI(MyModel, parser_kwargs={"default_env": True, "env_prefix": "MYAPP"})
```

Then variables use `MYAPP_...` instead of `PL_...`.

## Variable Interpolation

If the task requires YAML interpolation such as `${model.hidden_dim}`, install `omegaconf` and set parser mode:

```bash
pip install omegaconf
```

```python
LightningCLI(MyModel, parser_kwargs={"parser_mode": "omegaconf"})
```

Prefer `parser.link_arguments(...)` instead of interpolation when a relationship is an invariant that should always hold.

## Automatic Saved Config

By default, `LightningCLI` adds `SaveConfigCallback` to the Trainer and saves the full config to the logging directory for `fit` runs. If no logger is active, it can save in the working directory.

Controls:

```python
LightningCLI(MyModel, save_config_callback=None)
LightningCLI(MyModel, save_config_kwargs={"config_filename": "experiment.yaml"})
LightningCLI(MyModel, save_config_kwargs={"overwrite": True})
LightningCLI(MyModel, save_config_kwargs={"save_to_log_dir": False})  # only with a custom SaveConfigCallback subclass
```

Important behavior:

- `fast_dev_run` skips config saving.
- Existing config files are protected by default; a second run can raise `RuntimeError: Aborting to avoid overwriting`.
- `SaveConfigCallback.save_config` runs on rank zero. Do not add collective communication in this hook.
- To log config text to a logger, subclass `SaveConfigCallback` and override `save_config`.

## Trainer Defaults vs YAML Defaults

Use `trainer_defaults` for non-negotiable source-code defaults:

```python
LightningCLI(
    MyModel,
    trainer_defaults={"max_epochs": 10, "logger": False},
)
```

Use default config files for experiment defaults that users should edit or override. Use `parser.set_defaults(...)` in `add_arguments_to_parser` for defaults of custom parser groups.

## Safe Validation Workflow

For a new CLI script:

```bash
python train.py --help
python train.py fit --help
python train.py fit --print_config > config.yaml
python - <<'PY'
import yaml
with open('config.yaml') as f:
    yaml.safe_load(f)
print('yaml-ok')
PY
python train.py fit --config config.yaml --trainer.fast_dev_run=1
```

For CI or quick local checks, prefer CPU-safe knobs:

```bash
python train.py fit \
  --trainer.fast_dev_run=1 \
  --trainer.accelerator=cpu \
  --trainer.devices=1 \
  --trainer.logger=False
```

For distributed, accelerator, or precision decisions, route to `../distributed-accelerators/SKILL.md` and then encode the selected values under `trainer.*` in CLI config.
