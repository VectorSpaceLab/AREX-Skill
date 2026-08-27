# V2 Package-Layer Reference

The v2 P layer is beta. It is convenient for experiments because it wraps D1/D2/M layers behind `fit()` and `predict()`, but it is not the stable production workflow for PyTorch Forecasting 1.8.0.

## P-layer constructor contract

All package wrappers covered here inherit the same high-level constructor pattern:

```python
pkg = SomeModel_pkg_v2(
    model_cfg={...},       # model constructor args except metadata
    trainer_cfg={...},     # lightning.pytorch.Trainer constructor args
    datamodule_cfg={...},  # compatible D2 datamodule constructor args except dataset
    ckpt_path=None,        # optional checkpoint path for reload workflows
)
```

The config arguments may be dictionaries or paths to `.yaml`, `.yml`, or `.pkl` files. Dictionary configs are the clearest for interactive beta work.

Package lifecycle:

```python
best_ckpt = pkg.fit(
    dataset_or_datamodule,
    save_ckpt=True,
    ckpt_dir="checkpoints",
    ckpt_kwargs={"monitor": "val_loss"},
)

predictions = pkg.predict(
    dataset_or_datamodule_or_dataloader,
    mode="prediction",          # "prediction", "quantiles", or "raw"
    return_info=["x"],          # optional; see return_info section below
    trainer_kwargs={"accelerator": "cpu", "devices": 1},
)
```

Input handling:

- `fit(data)` accepts a D1 `TimeSeries` or a compatible D2 Lightning datamodule.
- `predict(data)` accepts a D1 `TimeSeries`, a compatible D2 Lightning datamodule, or a PyTorch `DataLoader`.
- If `fit()` receives D1 data, the package builds its configured D2 datamodule, calls `setup(stage="fit")`, reads `datamodule.metadata`, then initializes the M-layer model with that metadata.
- If `predict()` receives D1 data, the package builds a D2 datamodule, calls `setup(stage="predict")`, obtains `predict_dataloader()`, then delegates to the underlying model's `predict()` helper.
- If `output_dir` is passed to `predict()`, predictions are saved to `predictions.pkl` and the method returns `None`.

## Standard config dictionaries

Use small CPU configs for wiring tests. Increase epochs, batch size, logger settings, or accelerators only after metadata and batch shapes are proven.

```python
from lightning.pytorch.callbacks import EarlyStopping
from pytorch_forecasting.metrics import MAE, SMAPE

# EncoderDecoder packages: TFT, Samformer, TIDE, DecoderMLP_v2, SOFTS
encoder_decoder_datamodule_cfg = dict(
    max_encoder_length=24,
    max_prediction_length=6,
    batch_size=16,
    num_workers=0,
    train_val_test_split=(0.7, 0.15, 0.15),
)

# Tslib packages: DLinear, TimeXer
tslib_datamodule_cfg = dict(
    context_length=24,
    prediction_length=6,
    batch_size=16,
    num_workers=0,
    train_val_test_split=(0.7, 0.15, 0.15),
    add_relative_time_idx=True,
)

model_cfg = dict(
    loss=MAE(),
    logging_metrics=[MAE(), SMAPE()],
    optimizer="adam",
    optimizer_params={"lr": 1e-3},
    lr_scheduler="reduce_lr_on_plateau",
    lr_scheduler_params={"mode": "min", "factor": 0.1, "patience": 5},
    # plus model-specific keys such as hidden_size or n_heads
)

trainer_cfg = dict(
    max_epochs=2,
    accelerator="cpu",
    devices=1,
    enable_progress_bar=False,
    log_every_n_steps=1,
    callbacks=[EarlyStopping(monitor="val_loss", patience=3)],
)
```

Notes:

- Include `loss` in `model_cfg`; tests may fill defaults internally, but user package code should be explicit.
- For `TIDE`, use its model-specific optimizer names (`optim`, `optim_config`, `scheduler_config`) if you need those controls; do not blindly copy the standard `optimizer` keys into a TIDE-only config.
- Keep `num_workers=0` for first smoke checks to avoid multiprocessing noise.
- Set `save_ckpt=False` in `fit()` for short wiring checks when you do not need checkpoint artifacts.

## Package/model/datamodule compatibility

| P package | Underlying M model | Internal D2 datamodule | Import |
|---|---|---|---|
| `TFT_pkg_v2` | `TFT` | `EncoderDecoderTimeSeriesDataModule` | `from pytorch_forecasting.models.temporal_fusion_transformer._tft_pkg_v2 import TFT_pkg_v2` |
| `DLinear_pkg_v2` | `DLinear` | `TslibDataModule` | `from pytorch_forecasting.models.dlinear._dlinear_pkg_v2 import DLinear_pkg_v2` |
| `Samformer_pkg_v2` | `Samformer` | `EncoderDecoderTimeSeriesDataModule` | `from pytorch_forecasting.models.samformer._samformer_v2_pkg import Samformer_pkg_v2` |
| `TIDE_pkg_v2` | `TIDE` | `EncoderDecoderTimeSeriesDataModule` | `from pytorch_forecasting.models.tide._tide_dsipts._tide_v2_pkg import TIDE_pkg_v2` |
| `TimeXer_pkg_v2` | `TimeXer` | `TslibDataModule` | `from pytorch_forecasting.models.timexer._timexer_pkg_v2 import TimeXer_pkg_v2` |
| `DecoderMLP_pkg_v2` | `DecoderMLP_v2` | `EncoderDecoderTimeSeriesDataModule` | `from pytorch_forecasting.models.mlp._decodermlp_pkg_v2 import DecoderMLP_pkg_v2` |
| `SOFTS_pkg_v2` | `SOFTS` | `EncoderDecoderTimeSeriesDataModule` | `from pytorch_forecasting.models.softs._softs_pkg_v2 import SOFTS_pkg_v2` |

## Minimal package examples

### `TFT_pkg_v2` with encoder/decoder metadata

```python
from pytorch_forecasting.metrics import MAE, SMAPE
from pytorch_forecasting.models.temporal_fusion_transformer._tft_pkg_v2 import TFT_pkg_v2

pkg = TFT_pkg_v2(
    datamodule_cfg=dict(
        max_encoder_length=24,
        max_prediction_length=6,
        batch_size=16,
        num_workers=0,
    ),
    model_cfg=dict(
        loss=MAE(),
        logging_metrics=[MAE(), SMAPE()],
        hidden_size=32,
        num_layers=1,
        attention_head_size=4,
        dropout=0.1,
        optimizer="adam",
        optimizer_params={"lr": 1e-3},
    ),
    trainer_cfg=dict(max_epochs=2, accelerator="cpu", devices=1, enable_progress_bar=False),
)

pkg.fit(dataset, save_ckpt=False)
out = pkg.predict(dataset, mode="prediction", return_info=["x"])
assert "prediction" in out
```

### `TimeXer_pkg_v2` with Tslib metadata

```python
from pytorch_forecasting.metrics import MAE, SMAPE
from pytorch_forecasting.models.timexer._timexer_pkg_v2 import TimeXer_pkg_v2

pkg = TimeXer_pkg_v2(
    datamodule_cfg=dict(
        context_length=24,
        prediction_length=6,
        add_relative_time_idx=True,
        batch_size=16,
        num_workers=0,
    ),
    model_cfg=dict(
        loss=MAE(),
        logging_metrics=[MAE(), SMAPE()],
        hidden_size=64,
        n_heads=4,
        e_layers=2,
        d_ff=256,
        patch_length=4,
        optimizer="adam",
        optimizer_params={"lr": 1e-3},
    ),
    trainer_cfg=dict(max_epochs=2, accelerator="cpu", devices=1, enable_progress_bar=False),
)

pkg.fit(dataset, save_ckpt=False)
out = pkg.predict(dataset, mode="raw")
assert "prediction" in out
```

## Model-specific `model_cfg` reminders

| Package | Minimal extra `model_cfg` beyond `loss` | Notes |
|---|---|---|
| `TFT_pkg_v2` | Optional: `hidden_size`, `num_layers`, `attention_head_size`, `dropout`. | Uses encoder/decoder metadata keys including categorical/continuous counts. |
| `DLinear_pkg_v2` | Optional: `moving_avg`, `individual`. | Tslib metadata; best with continuous numeric data. |
| `Samformer_pkg_v2` | Required by source signature: `hidden_size`, `use_revin`. | Add `out_channels` and `persistence_weight` when needed. |
| `TIDE_pkg_v2` | Required: `hidden_size`, `d_model`, `n_add_enc`, `n_add_dec`, `dropout_rate`. | Uses `optim`, `optim_config`, `scheduler_config` for optimizer options. |
| `TimeXer_pkg_v2` | Optional but common: `hidden_size`, `n_heads`, `e_layers`, `d_ff`, `dropout`, `patch_length`. | Use `n_heads`, not `nhead`. |
| `DecoderMLP_pkg_v2` | Optional: `hidden_size`, `n_hidden_layers`, `dropout`, `norm`, `activation_class`. | Uses decoder/static dimensions from encoder/decoder metadata. |
| `SOFTS_pkg_v2` | Optional: `hidden_size`, `d_core`, `d_ff`, `n_layers`, `dropout`, `use_revin`. | Validate metadata because defaults can mask missing dimensions. |

## `predict()` modes and `return_info`

`pkg.predict()` forwards keyword arguments to the underlying M-layer `BaseModel.predict()`.

Common modes:

- `mode="prediction"`: point forecasts under `out["prediction"]`, usually 2D for point output.
- `mode="quantiles"`: quantile forecasts under `out["prediction"]`, usually 3D when the loss supports quantiles.
- `mode="raw"`: raw model output dictionary; tests expect a `"prediction"` tensor.

`return_info` can request additional data copied from prediction batches:

```python
out = pkg.predict(
    dataset,
    mode="prediction",
    return_info=["x", "decoder_lengths"],
    trainer_kwargs={"accelerator": "cpu", "devices": 1, "enable_progress_bar": False},
)
```

Recognized keys in the callback are `x`, `y`, `index`, and `decoder_lengths`; unknown keys trigger a warning. Because API-v2 batching is still changing, `x` and `decoder_lengths` are the safest inspection keys. If `index` or `y` fail with a custom dataloader, first inspect the dataloader batch structure and retry with `return_info=["x"]`.

## Checkpoint and reload workflow

When `save_ckpt=True`, `fit()` attaches a Lightning `ModelCheckpoint`, returns the best checkpoint path, and saves sidecar config/metadata artifacts next to the checkpoint. A package can be reloaded with `ckpt_path`:

```python
best_ckpt = pkg.fit(
    dataset,
    save_ckpt=True,
    ckpt_dir="checkpoints",
    ckpt_kwargs={"monitor": "train_loss_epoch"},
)

loaded = TFT_pkg_v2(ckpt_path=best_ckpt)
out = loaded.predict(dataset, mode="prediction")
```

Use checkpoint reload only after a non-checkpoint smoke path works. For beta experiments, always keep the exact `datamodule_cfg` and model package class with the checkpoint so metadata shape changes are diagnosable.

## Package workflow validation steps

1. Run a D1/D2 smoke first, or use the bundled `tiny_v2_data_smoke.py` helper.
2. Confirm the package's internal datamodule family matches your config keys.
3. Start with CPU, `max_epochs=1` or `2`, small batch size, and `save_ckpt=False`.
4. After `fit()`, call `predict(..., mode="raw")` once to verify raw output includes `"prediction"`.
5. Then test `mode="prediction"` or `mode="quantiles"` and the minimal `return_info` keys you need.
6. If this is for a production pipeline, stop and migrate the requirement to the stable v1 sub-skills instead of hardening API-v2 code.
