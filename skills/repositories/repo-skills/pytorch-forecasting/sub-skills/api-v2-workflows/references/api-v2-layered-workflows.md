# API-v2 Layered Workflows

API-v2 in PyTorch Forecasting 1.8.0 is beta and intended for experiments, not stable production pipelines. For production use, prefer the v1 `TimeSeriesDataSet` and v1 model workflows routed by sibling sub-skills.

## Layer map

| Layer | Main classes | Responsibility | Use when |
|---|---|---|---|
| D1 dataset | `pytorch_forecasting.data.timeseries.TimeSeries` | Ingest a pandas DataFrame, convert per-series arrays/tensors, and expose base metadata (`cols`, `col_type`, `col_known`). | You have raw tabular time-series data and want to try the API-v2 stack. |
| D2 datamodule | `EncoderDecoderTimeSeriesDataModule`, `TslibDataModule` | Split series, preprocess/scaling, make train/val/test/predict dataloaders, and derive model initialization metadata. | You need Lightning dataloaders or metadata for an M-layer model. |
| M model | `TFT`, `DLinear`, `Samformer`, `TIDE`, `TimeXer`, `DecoderMLP_v2`, `SOFTS` | Pure Lightning modules that receive batches from a compatible D2 datamodule. | You need direct Trainer control, custom callbacks, or batch-level debugging. |
| P package | `TFT_pkg_v2`, `DLinear_pkg_v2`, `Samformer_pkg_v2`, `TIDE_pkg_v2`, `TimeXer_pkg_v2`, `DecoderMLP_pkg_v2`, `SOFTS_pkg_v2` | High-level wrapper that builds D2 + M layer from config dictionaries and exposes `fit()`/`predict()`. | You want the shortest beta API with swappable v2 models. |

## D1: `TimeSeries` recipe

`TimeSeries` is a lightweight beta D1 dataset. It does not replace v1 `TimeSeriesDataSet`; it gives v2 datamodules a consistent source of raw sequence tensors and metadata.

Data assumptions that avoid most beta failures:

- Use a pandas DataFrame that fits in memory.
- Use string column names.
- Prefer integer, increasing `time` values within each `group`; timestamp-like values are used by tests, but integer indexes are the clearest path.
- Keep target columns numeric for the v2 models covered here.
- Keep categorical feature values numeric-coded for the current beta path; object/string categories can fail when the D1 layer converts arrays to torch tensors before later preprocessing.
- Use enough series and enough timesteps for the selected split and window lengths.

```python
import numpy as np
import pandas as pd

from pytorch_forecasting.data.timeseries import TimeSeries

n_series = 4
n_timesteps = 48
rows = []
for series_id in range(n_series):
    for time_idx in range(n_timesteps):
        rows.append(
            {
                "series_id": series_id,
                "time_idx": time_idx,
                "y": np.sin(time_idx / 6.0) + series_id * 0.1,
                "x": float(time_idx) / n_timesteps,
                "future_known_feature": float((time_idx + 1) % 7),
                "category": series_id % 3,              # numeric-coded category
                "static_feature": float(series_id),
                "static_feature_cat": series_id % 2,    # numeric-coded category
            }
        )

data_df = pd.DataFrame(rows)

dataset = TimeSeries(
    data=data_df,
    time="time_idx",
    target="y",
    group=["series_id"],
    num=["x", "future_known_feature", "static_feature"],
    cat=["category", "static_feature_cat"],
    known=["future_known_feature"],
    unknown=["x", "category"],
    static=["static_feature", "static_feature_cat"],
)

metadata = dataset.get_metadata()
assert metadata["cols"]["y"] == ["y"]
assert "future_known_feature" in metadata["cols"]["x"]
assert metadata["col_known"]["future_known_feature"] == "K"
```

D1 metadata shape:

```python
{
    "cols": {
        "y": ["target column names"],
        "x": ["feature columns excluding time/group/weight/target"],
        "st": ["static feature names"],
    },
    "col_type": {"feature_or_target": "F or C"},   # F numeric, C categorical
    "col_known": {"feature_or_target": "K or U"},  # K future-known, U unknown
}
```

`data_future` is accepted by `TimeSeries` for known future rows, but keep early experiments simple until D1/D2 behavior is validated on your schema.

## D2 option A: `EncoderDecoderTimeSeriesDataModule`

Use this datamodule for the encoder/decoder-style v2 models listed below. It derives metadata keys expected by `TFT`, `Samformer`, `TIDE`, `DecoderMLP_v2`, and `SOFTS`.

```python
from pytorch_forecasting.data.data_module import EncoderDecoderTimeSeriesDataModule
from pytorch_forecasting.data.encoders import TorchNormalizer

encoder_decoder_cfg = dict(
    max_encoder_length=24,
    min_encoder_length=None,          # defaults to max_encoder_length
    max_prediction_length=6,
    min_prediction_length=None,       # defaults to max_prediction_length
    batch_size=16,
    num_workers=0,
    train_val_test_split=(0.7, 0.15, 0.15),
    target_normalizer=TorchNormalizer(),
    categorical_encoders=None,        # beta: numeric-coded categories are safest
    scalers=None,                     # e.g. {"x": StandardScaler()}
    add_relative_time_idx=False,
    add_target_scales=False,
)

data_module = EncoderDecoderTimeSeriesDataModule(
    time_series_dataset=dataset,
    **encoder_decoder_cfg,
)

# Fit stage prepares train/val windows and fits configured normalizers/scalers.
data_module.setup(stage="fit")
train_loader = data_module.train_dataloader()

metadata = data_module.metadata
required_keys = {
    "encoder_cat",
    "encoder_cont",
    "decoder_cat",
    "decoder_cont",
    "target",
    "static_categorical_features",
    "static_continuous_features",
    "max_encoder_length",
    "max_prediction_length",
    "min_encoder_length",
    "min_prediction_length",
}
assert required_keys <= set(metadata)
```

Encoder/decoder batch keys include:

- `encoder_cat`, `encoder_cont`, `decoder_cat`, `decoder_cont`
- `encoder_lengths`, `decoder_lengths`, `decoder_target_lengths`
- `groups`, `target_past`, `target_scale`
- `encoder_time_idx`, `decoder_time_idx`
- `encoder_mask`, `decoder_mask`
- `static_categorical_features`, `static_continuous_features` when static features exist

Known-future features determine decoder inputs: a feature appears in `decoder_cont` or `decoder_cat` only when it is listed in D1 `known=[...]` and typed as continuous/categorical by D1 metadata.

## D2 option B: `TslibDataModule`

Use this datamodule for Time-Series-Library-style v2 models. In the covered package wrappers, `DLinear_pkg_v2` and `TimeXer_pkg_v2` build `TslibDataModule` internally.

```python
from pytorch_forecasting.data.data_module import TslibDataModule
from pytorch_forecasting.data.encoders import TorchNormalizer

tslib_cfg = dict(
    context_length=24,
    prediction_length=6,
    freq="h",
    add_relative_time_idx=True,
    add_target_scales=False,
    target_normalizer=TorchNormalizer(),
    scalers=None,
    shuffle=True,
    window_stride=1,
    batch_size=16,
    num_workers=0,
    train_val_test_split=(0.7, 0.15, 0.15),
)

tslib_dm = TslibDataModule(time_series_dataset=dataset, **tslib_cfg)
tslib_dm.setup(stage="fit")
metadata = tslib_dm.metadata
assert {"feature_names", "feature_indices", "n_features", "context_length", "prediction_length", "features"} <= set(metadata)
```

`TslibDataModule` metadata uses a different shape from the encoder/decoder datamodule:

- `feature_names`: lists for `categorical`, `continuous`, `static`, `known`, `unknown`, `target`, `all`, `static_categorical`, and `static_continuous`.
- `feature_indices`: positions for `categorical`, `continuous`, `known`, `unknown`, and `target`.
- `n_features`: counts for the `feature_names` groups.
- `context_length`, `prediction_length`, `freq`, and `features` (`S`, `MS`, or `M`).

Tslib batch keys include `history_cont`, `history_cat`, `future_cont`, `future_cat`, `history_target`, `future_target`, `history_length`, `future_length`, `history_mask`, `future_mask`, `groups`, and time-index fields.

## Direct M-layer model recipe

Use a direct M-layer workflow when you need custom Lightning `Trainer` behavior or want to inspect dataloaders before training. The critical handoff is `metadata=data_module.metadata` after the datamodule has been created and validated.

Encoder/decoder example with `TFT`:

```python
from lightning.pytorch import Trainer

from pytorch_forecasting.metrics import MAE, SMAPE
from pytorch_forecasting.models.temporal_fusion_transformer._tft_v2 import TFT

# dataset and data_module are from the D1/D2 recipes above
data_module.setup(stage="fit")

model = TFT(
    loss=MAE(),
    logging_metrics=[MAE(), SMAPE()],
    optimizer="adam",
    optimizer_params={"lr": 1e-3},
    lr_scheduler="reduce_lr_on_plateau",
    lr_scheduler_params={"mode": "min", "factor": 0.1, "patience": 10},
    hidden_size=64,
    num_layers=2,
    attention_head_size=4,
    dropout=0.1,
    metadata=data_module.metadata,
)

trainer = Trainer(max_epochs=2, accelerator="cpu", devices=1, enable_progress_bar=False)
trainer.fit(model, datamodule=data_module)

# Predict through the BaseModel helper after preparing a predict dataloader.
data_module.setup(stage="predict")
predictions = model.predict(
    data_module.predict_dataloader(),
    mode="prediction",
    return_info=["x", "decoder_lengths"],
    trainer_kwargs={"accelerator": "cpu", "devices": 1, "enable_progress_bar": False},
)
```

Tslib example with `TimeXer`:

```python
from lightning.pytorch import Trainer

from pytorch_forecasting.metrics import MAE, SMAPE
from pytorch_forecasting.models.timexer._timexer_v2 import TimeXer

# tslib_dm is from the TslibDataModule recipe
tslib_dm.setup(stage="fit")

model = TimeXer(
    loss=MAE(),
    logging_metrics=[MAE(), SMAPE()],
    hidden_size=64,
    n_heads=4,          # source-verified key; avoid tutorial typos such as nhead
    e_layers=2,
    d_ff=256,
    dropout=0.1,
    patch_length=4,
    optimizer="adam",
    optimizer_params={"lr": 1e-3},
    metadata=tslib_dm.metadata,
)

trainer = Trainer(max_epochs=2, accelerator="cpu", devices=1, enable_progress_bar=False)
trainer.fit(model, datamodule=tslib_dm)
```

## Direct M-layer compatibility quick table

| M-layer class | Import path suffix | Expected D2 metadata family | Important config notes |
|---|---|---|---|
| `TFT` | `models.temporal_fusion_transformer._tft_v2` | `EncoderDecoderTimeSeriesDataModule` | Requires `loss`; uses `hidden_size`, `num_layers`, `attention_head_size`, `dropout`, optimizer/scheduler keys. |
| `DLinear` | `models.dlinear._dlinear_v2` | `TslibDataModule` | Requires `loss`; accepts `moving_avg`, `individual`; continuous/target Tslib metadata is central. |
| `Samformer` | `models.samformer._samformer_v2` | `EncoderDecoderTimeSeriesDataModule` | Requires `loss`, `hidden_size`, and `use_revin`; output channels default to 1. |
| `TIDE` | `models.tide._tide_dsipts._tide_v2` | `EncoderDecoderTimeSeriesDataModule` | Requires `metadata`, `loss`, `hidden_size`, `d_model`, `n_add_enc`, `n_add_dec`, `dropout_rate`; optimizer keys are `optim`, `optim_config`, `scheduler_config`, not the standard BaseModel names. |
| `TimeXer` | `models.timexer._timexer_v2` | `TslibDataModule` | Requires `loss`; source key is `n_heads`; uses `context_length`/`prediction_length` metadata. |
| `DecoderMLP_v2` | `models.mlp._decodermlp_v2` | `EncoderDecoderTimeSeriesDataModule` | Requires `loss`; uses decoder/static dimensions from metadata. |
| `SOFTS` | `models.softs._softs_v2` | `EncoderDecoderTimeSeriesDataModule` | Requires `loss`; uses `hidden_size`, `d_core`, `d_ff`, `n_layers`, `use_revin`; metadata defaults can hide missing keys, so still validate metadata. |

## Translating v1-style requests into v2 configs

When a user gives a v1-style `TimeSeriesDataSet` request but asks for API-v2, translate cautiously:

| v1 concept | v2 D1/D2 equivalent |
|---|---|
| `time_idx` | D1 `TimeSeries(..., time="time_idx")` |
| `target` or multi-target | D1 `target="y"` or `target=["y1", "y2"]`; keep numeric for covered models. |
| `group_ids` | D1 `group=[...]` |
| `static_reals` / `static_categoricals` | D1 `static=[...]`; also include numeric static columns in `num` and categorical static columns in `cat` as appropriate. |
| `time_varying_known_reals` / known categoricals | D1 `known=[...]`; include columns in `num` or `cat`. These become decoder/future inputs. |
| `time_varying_unknown_reals` / unknown categoricals | D1 `unknown=[...]`; include columns in `num` or `cat`. These are not future-known decoder inputs. |
| `max_encoder_length` | Encoder/decoder `datamodule_cfg["max_encoder_length"]`; Tslib `datamodule_cfg["context_length"]`. |
| `max_prediction_length` | Encoder/decoder `datamodule_cfg["max_prediction_length"]`; Tslib `datamodule_cfg["prediction_length"]`. |
| `target_normalizer` | D2 `target_normalizer`. |
| `categorical_encoders` / `scalers` | D2 `categorical_encoders` and `scalers`, but validate with numeric-coded categories because v2 preprocessing is still beta. |

Always state that this is an experimental v2 translation; if the user needs the stable v1 object, route to the v1 data pipeline.

## Pre-flight validation checklist

Before constructing an M-layer model:

1. Confirm D1 metadata contains the expected target, feature, known/unknown, and static roles.
2. Confirm every series has at least `max_encoder_length + max_prediction_length` or `context_length + prediction_length` timesteps.
3. Confirm train/validation/test split leaves non-empty windows for the stage you will use.
4. Confirm the model's expected datamodule family matches the datamodule you built.
5. Print or assert the exact metadata keys consumed by the model before passing `metadata=...`.
6. Use CPU for tiny validation; CUDA/GPU is optional for this scope and is not required to validate API-v2 wiring.
