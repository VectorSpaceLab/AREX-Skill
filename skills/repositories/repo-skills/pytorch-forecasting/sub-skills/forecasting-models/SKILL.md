---
name: forecasting-models
description: "Select, instantiate, train, checkpoint, predict, and interpret
  PyTorch Forecasting v1 model families from TimeSeriesDataSet datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Forecasting Models Sub-skill

Use this sub-skill when a PyTorch Forecasting 1.8.0 task already has, or is ready to build, v1 `TimeSeriesDataSet` train/validation/prediction objects and needs to choose a model family, instantiate it with `.from_dataset()`, run Lightning training, load a checkpoint, call `predict()`, or interpret model outputs.

## Route here for

- Choosing among `Baseline`, `TemporalFusionTransformer`, `NBeats`, `NBeatsKAN`, `NHiTS`, `DeepAR`, `RecurrentNetwork`, `DecoderMLP`, `TiDEModel`, `TimeXer`, and `xLSTMTime` for a concrete forecasting task.
- Using `.from_dataset(training_dataset, ...)` to transfer `TimeSeriesDataSet` metadata into a v1 model.
- Creating `lightning.pytorch.Trainer` objects with early stopping, learning-rate monitoring, CPU/GPU settings, debugging batch limits, checkpointing, and fast prediction.
- Calling `BaseModel.predict()` or `DeepAR.predict()` with `return_index`, `return_decoder_lengths`, `return_x`, `return_y`, `mode`, `mode_kwargs`, `n_samples`, and `trainer_kwargs`.
- Loading trained models with `ModelClass.load_from_checkpoint()` and using model-specific interpretation or plotting helpers when optional plotting packages are available.

## Route away

- Data schema design, `TimeSeriesDataSet` construction, encoders, normalizers, missing timesteps, dataloaders, and dataset serialization belong in `../data-pipeline/SKILL.md`.
- Loss choice, metric semantics, quantile/distribution details, Optuna tuning, and full learning-rate finder strategy belong in `../metrics-and-tuning/SKILL.md`.
- Experimental v2 package/data-module workflows, including the v2-only `SOFTS` layer, belong in `../api-v2-workflows/SKILL.md`.

## Bundled references and scripts

- Use [`references/model-selection.md`](references/model-selection.md) when deciding which model family matches target-only, covariate-rich, probabilistic, multivariate, long-horizon, or fixed-window requirements.
- Use [`references/training-prediction-workflows.md`](references/training-prediction-workflows.md) for concrete v1 `.from_dataset()`, `Trainer.fit()`, checkpoint, `predict()`, and interpretation recipes.
- Use [`references/model-troubleshooting.md`](references/model-troubleshooting.md) when training freezes, diverges, LR finder stalls, plotting/logging fails, or a dataset/model compatibility assertion appears.
- Use [`scripts/tiny_forecasting_smoke.py`](scripts/tiny_forecasting_smoke.py) to run a dependency-light CPU smoke check that builds tiny pandas data, creates a `TimeSeriesDataSet`, and performs a default `Baseline` prediction without long training.

## Minimal operating pattern

```python
import lightning.pytorch as pl
from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor
from pytorch_forecasting import TemporalFusionTransformer
from pytorch_forecasting.metrics import QuantileLoss

# `training`, `validation`, `train_loader`, and `val_loader` come from the data-pipeline sub-skill.
model = TemporalFusionTransformer.from_dataset(
    training,
    learning_rate=0.03,
    hidden_size=16,
    attention_head_size=1,
    dropout=0.1,
    hidden_continuous_size=8,
    output_size=7,               # 7 default quantiles for QuantileLoss()
    loss=QuantileLoss(),
    log_interval=-1,             # avoid plotting/logging overhead while debugging
    reduce_on_plateau_patience=4,
)

callbacks = [
    EarlyStopping(monitor="val_loss", min_delta=1e-4, patience=5, mode="min"),
    LearningRateMonitor(),
]
trainer = pl.Trainer(
    max_epochs=20,
    accelerator="auto",
    devices="auto",
    gradient_clip_val=0.1,
    callbacks=callbacks,
    enable_checkpointing=True,
)
trainer.fit(model, train_dataloaders=train_loader, val_dataloaders=val_loader)

best_path = trainer.checkpoint_callback.best_model_path
loaded = TemporalFusionTransformer.load_from_checkpoint(best_path)
preds = loaded.predict(
    val_loader,
    return_index=True,
    return_decoder_lengths=True,
    return_x=True,
    return_y=True,
    trainer_kwargs={"accelerator": "cpu"},
)
```

## Safety and verification checklist

1. Confirm the dataset shape and column roles in `../data-pipeline/SKILL.md` before blaming the model.
2. Start with `Baseline().predict(...)` or the bundled smoke script to prove the installed package, dataloader, Lightning, pandas, torch, and CPU path work.
3. For neural models, instantiate with `.from_dataset()` instead of manually copying feature-cardinality metadata.
4. Keep `num_workers=0`, `accelerator="cpu"`, `limit_train_batches=1`, `limit_val_batches=1`, and tiny model sizes while debugging.
5. Use `model.size()` before training; unexpectedly huge parameter counts usually indicate an oversized architecture or too many high-cardinality categorical embeddings.
6. Treat v2-only or package-layer APIs as out of scope for this v1 model workflow unless the task explicitly routes to `../api-v2-workflows/SKILL.md`.
