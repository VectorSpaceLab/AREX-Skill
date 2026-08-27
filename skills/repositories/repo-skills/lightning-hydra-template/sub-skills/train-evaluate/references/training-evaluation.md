# Training and Evaluation Reference

## Train flow

`train(cfg)` performs this sequence:

1. Seed with `L.seed_everything(cfg.seed, workers=True)` if `seed` is set.
2. Instantiate `cfg.data` as a `LightningDataModule`.
3. Instantiate `cfg.model` as a `LightningModule`.
4. Instantiate callbacks and loggers from `cfg.callbacks` and `cfg.logger`.
5. Instantiate `cfg.trainer` with callbacks and loggers.
6. If loggers exist, log hyperparameters.
7. If `cfg.train` is true, call `trainer.fit(..., ckpt_path=cfg.ckpt_path)`.
8. If `cfg.test` is true, call `trainer.test()` using the best checkpoint path from `trainer.checkpoint_callback.best_model_path`; if absent, test current weights.
9. Merge train and test callback metrics and return the metric requested by `optimized_metric` from the Hydra main function.

## Eval flow

`evaluate(cfg)` asserts `cfg.ckpt_path`, instantiates datamodule/model/loggers/trainer, logs hyperparameters if loggers exist, and calls:

```python
trainer.test(model=model, datamodule=datamodule, ckpt_path=cfg.ckpt_path)
```

For prediction workflows, the source includes a comment to use `trainer.predict(...)`; the template does not provide a ready prediction entry point.

## Commands

```bash
# Default training; can download MNIST and runs the configured max_epochs.
python src/train.py

# Installed console-script equivalent after pip install -e .
train_command

# Fast-dev smoke; still may touch data.
python src/train.py debug=fdr logger=null

# Train with versioned experiment and CSV logger.
python src/train.py experiment=example trainer=cpu logger=csv

# Resume from a last checkpoint.
python src/train.py ckpt_path=/path/to/checkpoints/last.ckpt

# Evaluate a checkpoint.
python src/eval.py ckpt_path=/path/to/checkpoints/last.ckpt logger=null
# or
eval_command ckpt_path=/path/to/checkpoints/last.ckpt logger=null
```

## Checkpoint and log layout

- Hydra sets each run's output directory from `configs/hydra/default.yaml`.
- `paths.output_dir` resolves to the Hydra runtime output directory.
- Default `ModelCheckpoint` writes to `${paths.output_dir}/checkpoints`.
- Default checkpoint config monitors `val/acc`, mode `max`, saves `last.ckpt`, and uses filenames like `epoch_000` with `auto_insert_metric_name: false`.
- `test_train_resume` in the repo expects `last.ckpt` and `epoch_000.ckpt` after one epoch, then `epoch_001.ckpt` after resume to max epoch 2.

## Safe validation before full training

- `train_command --help` and `eval_command --help` verify Hydra config groups and entry points.
- The root `check_lightning_hydra_project.py --instantiate` script verifies config composition and object construction without fitting/testing.
- `pytest tests/test_configs.py -q` is the safest native config test.
- Full train/eval tests can download MNIST and should be treated as optional unless data/cache/network are available.

## Metric and callback alignment

The default model logs `train/loss`, `train/acc`, `val/loss`, `val/acc`, `val/acc_best`, `test/loss`, and `test/acc`. Keep these aligned with:

- `callbacks/default.yaml` monitor: `val/acc`.
- `hparams_search/mnist_optuna.yaml` optimized metric: `val/acc_best`.
- Any custom model or checkpoint callback you introduce.
