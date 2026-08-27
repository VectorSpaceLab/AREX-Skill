# Hydra Configuration Reference

## Composition roots

- `configs/train.yaml` composes training defaults: `_self_`, data, model, callbacks, logger, trainer, paths, extras, hydra, optional experiment, optional hparams search, optional local config, and optional debug config.
- `configs/eval.yaml` composes evaluation defaults: data, model, logger, trainer, paths, extras, and hydra. It requires `ckpt_path`.
- Defaults order matters: later defaults and CLI overrides can change earlier choices.

## Main config groups

| Group | Default or options | Use |
| --- | --- | --- |
| `data` | `mnist` | Selects a `LightningDataModule` config. |
| `model` | `mnist` | Selects a `LightningModule`, net component, optimizer, scheduler, and compile flag. |
| `callbacks` | `default`, `none`, individual callbacks | Adds checkpointing, early stopping, model summary, rich progress bar. |
| `logger` | `null`, `csv`, `tensorboard`, `wandb`, `many_loggers`, others | Selects Lightning logger configs. Online loggers need optional packages/credentials. |
| `trainer` | `default`, `cpu`, `gpu`, `ddp`, `ddp_sim`, `mps` | Selects Lightning Trainer preset. |
| `paths` | `default` | Sets root/data/log/output/work dirs. |
| `extras` | `default` | Controls warnings, tag enforcement, and Rich config printing. |
| `debug` | `default`, `fdr`, `limit`, `overfit`, `profiler` | Adds safe debugging overrides. |
| `experiment` | `example` | Stores reproducible experiment overrides. |
| `hparams_search` | `mnist_optuna` | Configures Hydra Optuna sweeper and `optimized_metric`. |

## Override patterns

```bash
# replace a config group
python src/train.py trainer=cpu logger=csv

# change an existing scalar
python src/train.py trainer.max_epochs=20 model.optimizer.lr=1e-4

# add a new key with +
python src/train.py +trainer.gradient_clip_val=0.5

# select a versioned experiment
python src/train.py experiment=example

# disable callbacks/loggers for smoke or debug
python src/train.py callbacks=null logger=null debug=fdr
```

Hydra list overrides can require shell escaping. If `tags=["mnist","exp"]` is eaten by the shell, try escaping brackets or quote the whole override.

## Paths and outputs

`rootutils` sets `PROJECT_ROOT`, and `configs/paths/default.yaml` uses it as `paths.root_dir`. The default Hydra run directory is:

```text
${paths.log_dir}/${task_name}/runs/${now:%Y-%m-%d}_${now:%H-%M-%S}
```

Multirun output is under:

```text
${paths.log_dir}/${task_name}/multiruns/${now:%Y-%m-%d}_${now:%H-%M-%S}/${hydra.job.num}
```

Trainer output and callback checkpoints use `${paths.output_dir}`, which resolves to Hydra's runtime output directory unless the project changes it.

## Experiment configs

Use `configs/experiment/*.yaml` when a set of overrides should be versioned. A good experiment file:

- starts with `# @package _global_`;
- overrides the data/model/callback/trainer groups it relies on;
- sets tags and seed;
- changes only the parameters needed for that experiment;
- keeps logger-specific tags/groups under `logger` when needed.

## Config validation checklist

1. Run `train_command --help` or the bundled `render_config_summary.py` to confirm groups exist.
2. Compose the intended config with the same CLI overrides the run will use.
3. For no-network safety, instantiate data/model/trainer but do not call `prepare_data()` or `fit()`.
4. If an `_target_` fails, use the target checker from [customize-data-model](../../customize-data-model/SKILL.md).
5. If a metric is used for callbacks or Optuna, verify the model logs that exact key.
