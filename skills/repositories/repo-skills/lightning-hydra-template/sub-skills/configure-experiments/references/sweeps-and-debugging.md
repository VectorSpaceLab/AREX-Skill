# Sweeps and Debugging

## Debug presets

| Preset | Effect | When to use |
| --- | --- | --- |
| `debug=default` | CPU, one epoch, no callbacks/loggers, debug logging, anomaly detection, no tag prompt. | General interactive debugging. |
| `debug=fdr` | Inherits default and sets `trainer.fast_dev_run=true`. | Fast train/val/test loop sanity check; may still touch data. |
| `debug=limit` | Inherits default, `max_epochs=3`, small train/val/test batch fractions. | Quick runtime checks after code changes. |
| `debug=overfit` | Overfits to 3 batches, disables callbacks. | Check whether the model can learn a tiny sample. |
| `debug=profiler` | One epoch with Lightning profiler. | Identify slow steps. |

Debug presets are config overrides, not a replacement for no-network checks. If the selected datamodule downloads in `prepare_data()`, debug training can still need data/network.

## Hydra multiruns

```bash
# grid over two values
python src/train.py -m model.optimizer.lr=0.005,0.01 logger=csv

# run all experiment configs
python src/train.py -m 'experiment=glob(*)' logger=csv

# repeated seeds
python src/train.py -m seed=1,2,3 trainer.deterministic=true logger=csv tags='[benchmark]'
```

Hydra composes each job at launch time. If code or config files change while a sweep is running, later jobs may use the changed state. For reproducibility, commit or snapshot the project before long sweeps.

## Optuna sweeps

The template provides `configs/hparams_search/mnist_optuna.yaml`:

- overrides `/hydra/sweeper: optuna`;
- sets `hydra.mode: MULTIRUN`;
- uses `optimized_metric: "val/acc_best"`;
- configures `n_trials`, `n_jobs`, `direction`, sampler, and search space.

Example:

```bash
python src/train.py -m hparams_search=mnist_optuna experiment=example logger=csv
```

Before running Optuna:

1. Confirm `hydra-optuna-sweeper` is installed.
2. Confirm the model logs the configured `optimized_metric` key.
3. Use `logger=csv` or a configured online logger; do not accidentally prompt for credentials in batch jobs.
4. Start with few trials and `debug=fdr` or small limits when testing syntax.
5. Remember the template documents Optuna sweeps as not failure-resistant; one crashing job can crash the sweep.

## Remote or cluster sweeps

The README discusses AWS/Ray and SLURM as ideas rather than implemented configs. Treat cluster launchers as a new project-specific extension: add a config group, verify the launcher plugin, and test locally with safe commands before submitting real jobs.
