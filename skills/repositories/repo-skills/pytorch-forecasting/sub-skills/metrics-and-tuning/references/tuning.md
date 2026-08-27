# Learning-rate finder and Optuna tuning

This reference covers tuning around already-built `TimeSeriesDataSet` dataloaders. If the dataset, normalizer, or dataloader does not exist yet, route to the data-pipeline sub-skill first. If the model is not built yet, route to the forecasting-models sub-skill.

## Minimal optional dependencies

Base PyTorch Forecasting installs do not include the full tuning stack.

Install one of:

```bash
pip install "pytorch-forecasting[tuning]"
# or explicit packages
pip install "optuna>=3.1,<5" optuna-integration statsmodels
```

`optimize_hyperparameters()` checks for `optuna` and `statsmodels`, and imports `optuna.integration.PyTorchLightningPruningCallback`. With Optuna 3.3+ the `optuna-integration` package is required. `matplotlib` is only needed if you call `res.plot(...)` on a learning-rate finder result.

## Learning-rate finder recipe

Use the Lightning tuner on an already-created model and dataloaders. Disable expensive prediction logging while finding the LR.

```python
import lightning.pytorch as pl
from lightning.pytorch.callbacks import LearningRateMonitor
from lightning.pytorch.tuner import Tuner

from pytorch_forecasting import TemporalFusionTransformer
from pytorch_forecasting.metrics import QuantileLoss

loss = QuantileLoss(quantiles=[0.1, 0.5, 0.9])
model = TemporalFusionTransformer.from_dataset(
    training,
    loss=loss,
    output_size=len(loss.quantiles),
    learning_rate=0.03,          # temporary; overwritten after lr_find
    hidden_size=16,
    attention_head_size=1,
    dropout=0.1,
    hidden_continuous_size=8,
    log_interval=-1,
    log_val_interval=-1,
)

trainer = pl.Trainer(
    accelerator="auto",
    max_epochs=1,
    gradient_clip_val=0.1,
    callbacks=[LearningRateMonitor()],
    enable_model_summary=False,
)

res = Tuner(trainer).lr_find(
    model,
    train_dataloaders=train_dataloader,
    val_dataloaders=val_dataloader,
    min_lr=1e-5,
    max_lr=0.3,
    early_stop_threshold=1000.0,
    num_training=100,
)

suggested_lr = res.suggestion()
model.hparams.learning_rate = suggested_lr
```

Operational notes:

- Do not use `fast_dev_run=True` for LR finding.
- If a normal training trainer used an artificial small `limit_train_batches`, remove it or set it to full epoch semantics before LR finding; very small limits can prevent the finder from collecting enough points.
- Use a target normalizer in the training dataset. Missing or inappropriate target scaling is a frequent cause of non-finite losses during LR sweeps.
- If the finder stops too early, increase `early_stop_threshold` and narrow `max_lr` to a safer range.
- Skip plotting unless `matplotlib` is installed. `res.suggestion()` does not need plotting.
- If logging creates matplotlib warnings while no logger is configured, set model `log_interval=-1` and `log_val_interval=-1` during the finder.

## Temporal Fusion Transformer Optuna tuning

`pytorch_forecasting.models.temporal_fusion_transformer.tuning.optimize_hyperparameters()` tunes `TemporalFusionTransformer` hyperparameters. It requires dataloaders backed by `TimeSeriesDataSet` and returns an `optuna.Study`.

```python
import pickle

from pytorch_forecasting.metrics import QuantileLoss
from pytorch_forecasting.models.temporal_fusion_transformer.tuning import (
    optimize_hyperparameters,
)

loss = QuantileLoss(quantiles=[0.1, 0.5, 0.9])

study = optimize_hyperparameters(
    train_dataloaders=train_dataloader,
    val_dataloaders=val_dataloader,
    model_path="tft_optuna_checkpoints",
    max_epochs=3,
    n_trials=5,
    timeout=30 * 60,
    gradient_clip_val_range=(0.01, 1.0),
    hidden_size_range=(8, 64),
    hidden_continuous_size_range=(8, 64),
    attention_head_size_range=(1, 4),
    dropout_range=(0.1, 0.3),
    learning_rate_range=(1e-3, 1e-1),
    use_learning_rate_finder=False,
    trainer_kwargs={
        "accelerator": "auto",
        "limit_train_batches": 20,
        "limit_val_batches": 5,
        "enable_progress_bar": False,
        "enable_model_summary": False,
    },
    loss=loss,
    output_size=len(loss.quantiles),
    reduce_on_plateau_patience=4,
)

print(study.best_trial.value, study.best_trial.params)
with open("tft_optuna_study.pkl", "wb") as f:
    pickle.dump(study, f)
```

The function samples these core ranges unless overridden:

- `gradient_clip_val` from `gradient_clip_val_range` on a log scale.
- `hidden_size` from `hidden_size_range` on a log scale.
- `hidden_continuous_size` from `hidden_continuous_size_range`, capped at sampled `hidden_size`.
- `attention_head_size` from `attention_head_size_range`.
- `dropout` from `dropout_range`.
- `learning_rate` from `learning_rate_range` when `use_learning_rate_finder=False`; otherwise a Lightning LR finder is run inside each trial.

The objective creates a `TemporalFusionTransformer.from_dataset()` model for every trial, trains it with a Lightning `Trainer`, and returns `trainer.callback_metrics["val_loss"].item()`.

## Safe budget tiers

| Tier | Use when | Suggested limits |
| --- | --- | --- |
| Smoke | Checking code wiring and optional extras | `n_trials=1-2`, `max_epochs=1`, `timeout=5-10 min`, `limit_train_batches=1-5`, `limit_val_batches=1-2`, `use_learning_rate_finder=False` |
| Development | Searching a small dataset or tiny model | `n_trials=5-20`, `max_epochs=3-10`, `timeout=30-120 min`, modest train/val batch limits |
| Real search | Dataset and objective already validated | `n_trials=50-200`, `max_epochs=20-50`, multi-hour timeout, early stopping/pruning, stable storage |

Start with the smoke tier. Do not enable `use_learning_rate_finder=True` inside Optuna until a single standalone LR finder completes and the training loss is finite; running an LR sweep in every trial is expensive.

## Artifacts and persistence

`optimize_hyperparameters()` writes artifacts according to its arguments:

- `model_path`: trial checkpoint subdirectories such as `trial_0/`, `trial_1/`, each with a monitored checkpoint file.
- `log_dir`: TensorBoard logs under an `optuna` run name with the trial number as version.
- Returned `study`: in-memory Optuna study unless you pass an existing persistent study.

For resumable tuning, create and pass a persistent study yourself:

```python
import optuna

study = optuna.create_study(
    direction="minimize",
    storage="sqlite:///tft_optuna.db",
    study_name="tft_small_search",
    load_if_exists=True,
)
study = optimize_hyperparameters(
    train_dataloaders=train_dataloader,
    val_dataloaders=val_dataloader,
    model_path="tft_optuna_checkpoints",
    study=study,
    n_trials=20,
    timeout=2 * 60 * 60,
    use_learning_rate_finder=False,
)
```

Keep checkpoint/log paths in a project scratch area with enough disk space. Clean failed trial checkpoint directories after recording the best parameters if disk use matters.

## Failure modes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError` from `optimize_hyperparameters()` | Missing `optuna`, `optuna-integration`, or `statsmodels` | Install `pytorch-forecasting[tuning]` or the explicit packages. |
| Assertion that dataloaders must be built from `TimeSeriesDataSet` | Custom dataloader/dataset wrapper | Tune manually with your own Optuna objective or rebuild dataloaders from `TimeSeriesDataSet`. |
| LR finder has too few finite losses | Bad target scaling, too aggressive LR range, too small training limit, or unstable loss | Add/repair target normalizer, lower `max_lr`, increase `early_stop_threshold`, and collect more training batches. |
| All trials fail with shape errors | Loss and `output_size` mismatch | Use `from_dataset(..., loss=loss)` inference or set `output_size` to match the selected loss. |
| Trials are too slow | Large model/search ranges, LR finder in every trial, too many batches | Narrow hidden-size ranges, set `use_learning_rate_finder=False`, lower `max_epochs`, and use smaller batch limits for search. |
| No pruning effect | Metric name mismatch or callback not active | The built-in objective monitors `val_loss`; ensure validation runs and `val_loss` is produced. |
| Plotting LR finder fails | `matplotlib` missing | Skip `res.plot()` or install matplotlib; use `res.suggestion()` directly. |

## After tuning

Use the best trial parameters to build a fresh model and train it in the normal training workflow:

```python
params = study.best_trial.params
model = TemporalFusionTransformer.from_dataset(
    training,
    learning_rate=params.get("learning_rate", 0.03),
    hidden_size=params["hidden_size"],
    hidden_continuous_size=params["hidden_continuous_size"],
    attention_head_size=params["attention_head_size"],
    dropout=params["dropout"],
    gradient_clip_val=params.get("gradient_clip_val"),  # pass to Trainer, not model
    loss=loss,
    output_size=len(loss.quantiles),
)
```

`gradient_clip_val` belongs to `pl.Trainer`, not the model. Recreate the `Trainer` with the tuned clip value for final training.
