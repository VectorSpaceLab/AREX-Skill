# Template File Map

## When to read

Read this when orienting in a Lightning-Hydra-Template checkout or explaining where to make a change. Paths below are target-project paths, not links to this skill's construction checkout.

## Main directories

| Path | Role | Common tasks |
| --- | --- | --- |
| `configs/train.yaml` | Main training composition root. | Choose default data/model/callback/logger/trainer/path/extras/hydra groups; set `train`, `test`, `ckpt_path`, `seed`, and tags. |
| `configs/eval.yaml` | Main evaluation composition root. | Require `ckpt_path`; choose data/model/logger/trainer/path/extras/hydra groups for test-time evaluation. |
| `configs/data/` | DataModule config group. | Replace `mnist.yaml`, change batch size, workers, splits, and `data_dir`. |
| `configs/model/` | LightningModule and network config group. | Replace model `_target_`, optimizer/scheduler partials, network component params, and `compile`. |
| `configs/trainer/` | Trainer presets. | Choose CPU/GPU/DDP/DDP-spawn simulation/MPS and adjust Lightning Trainer flags. |
| `configs/callbacks/` | Callback presets. | Configure `ModelCheckpoint`, `EarlyStopping`, `RichModelSummary`, and `RichProgressBar`. |
| `configs/logger/` | Logger presets. | Configure CSV, TensorBoard, W&B, Neptune, Comet, MLflow, Aim, or multiple loggers. |
| `configs/debug/` | Debug presets. | Use `debug=default`, `debug=fdr`, `debug=limit`, `debug=overfit`, or `debug=profiler`. |
| `configs/experiment/` | Versioned experiment overrides. | Store named experiment configs such as `experiment=example`. |
| `configs/hparams_search/` | Hydra sweeper configs. | Configure Optuna search space and `optimized_metric`. |
| `configs/hydra/` and `configs/paths/` | Hydra output/log path behavior. | Adjust run/multirun output directories and root/data/log/output/work paths. |
| `src/train.py` | Training entry point. | Instantiate configured datamodule/model/callbacks/loggers/trainer, optionally fit and test, return optimized metric. |
| `src/eval.py` | Evaluation entry point. | Assert checkpoint path, instantiate data/model/logger/trainer, run `trainer.test`. |
| `src/data/` | Example data package. | Replace `MNISTDataModule` or add new DataModules. |
| `src/models/` | Example model package. | Replace `MNISTLitModule`, add components, metrics, optimizers, scheduler behavior. |
| `src/utils/` | Template utilities. | Instantiate callbacks/loggers, apply extras, print config, enforce tags, log hyperparameters, rank-aware logging. |
| `tests/` | Pytest smoke and behavior tests. | Compose configs, instantiate targets, run training/eval/sweeps under controlled fixtures. |
| `Makefile` | Common commands. | `make train`, `make test`, `make test-full`, `make format`, `make clean`, `make clean-logs`. |
| `setup.py` | Package metadata and console scripts. | Rename distribution/import root; update `train_command`/`eval_command`. |
| `.project-root` | `rootutils` root marker. | Lets entry points find project root and set `PROJECT_ROOT`. |

## Typical change ownership

- Config syntax, defaults, groups, experiments, debug, sweeps: use [configure-experiments](../sub-skills/configure-experiments/SKILL.md).
- Train/eval runs, checkpoint paths, callbacks, loggers, accelerators: use [train-evaluate](../sub-skills/train-evaluate/SKILL.md).
- New datasets/models/components or target import errors: use [customize-data-model](../sub-skills/customize-data-model/SKILL.md).
- Tests, CI, package rename maintenance, and no-network smoke selection: use [test-maintain-template](../sub-skills/test-maintain-template/SKILL.md).
