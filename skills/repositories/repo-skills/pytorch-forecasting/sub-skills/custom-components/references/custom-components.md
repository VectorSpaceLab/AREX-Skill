# Custom components for PyTorch Forecasting 1.8.0

This guide is for contributors who need to implement or revise a custom metric, a v1 model, a v1 package wrapper, or an experimental v2 model/package/data-module component.

## 1) Choose the right surface

### Stable v1 path
Use the v1 stack when your component should work with `TimeSeriesDataSet`, `BaseModel`, and the `from_dataset()` factory pattern.

Typical surfaces:

- `TimeSeriesDataSet`
- `BaseModel`
- `BaseModelWithCovariates`
- `AutoRegressiveBaseModel`
- `AutoRegressiveBaseModelWithCovariates`
- `_BasePtForecaster` package wrapper

### Experimental v2 path
Use the v2 stack only when the task explicitly targets the beta API.

Typical surfaces:

- `BaseModel` from `pytorch_forecasting.models.base._base_model_v2`
- `Base_pkg`
- `TimeSeries`
- `EncoderDecoderTimeSeriesDataModule`
- `TslibDataModule`

## 2) Custom metric guidance

### Metric base choice

- `MultiHorizonMetric`: point-style or generic horizon-wise metric.
- `DistributionLoss`: predictive distribution losses.
- `MultivariateDistributionLoss`: multivariate distribution losses.
- `MultiLoss`: combine multiple metrics for multi-target setups.

### Contract to keep

- `loss(self, y_pred, target) -> Tensor` should return the unreduced per-timestep loss.
- Let the base class handle masking, weighting, packing, and reduction.
- Use `self.to_prediction(y_pred)` inside the loss unless the metric explicitly needs raw outputs.
- For distribution losses, also implement `map_x_to_distribution()` and `rescale_parameters()`.
- For custom quantile behavior, implement `to_quantiles()`.

### Minimal metric skeleton

```python
from __future__ import annotations

import torch
from pytorch_forecasting.metrics import MultiHorizonMetric


class AsymmetricMAE(MultiHorizonMetric):
    """Mean absolute error with different under/over-forecast penalties."""

    def __init__(
        self,
        underforecast_weight: float = 2.0,
        overforecast_weight: float = 1.0,
        reduction: str = "mean",
        **kwargs,
    ):
        super().__init__(reduction=reduction, **kwargs)
        self.underforecast_weight = underforecast_weight
        self.overforecast_weight = overforecast_weight

    def loss(self, y_pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        prediction = self.to_prediction(y_pred)
        error = prediction - target
        under = torch.as_tensor(self.underforecast_weight, dtype=error.dtype, device=error.device)
        over = torch.as_tensor(self.overforecast_weight, dtype=error.dtype, device=error.device)
        weights = torch.where(error < 0, under, over)
        return error.abs() * weights
```

### Metric wrapper when you need test discovery
If the metric should be discovered by the metrics registry, add a package wrapper class that inherits `_BasePtMetric` and provides:

- `metric_type`
- `info:metric_name`
- `requires:data_type`
- optional `python_dependencies`

A compact wrapper looks like this:

```python
from pytorch_forecasting.metrics.base_metrics._base_object import _BasePtMetric


class AsymmetricMAE_pkg(_BasePtMetric):
    _tags = {
        "metric_type": "point",
        "info:metric_name": "AsymmetricMAE",
        "requires:data_type": "point_forecast",
    }

    @classmethod
    def get_cls(cls):
        from pytorch_forecasting.metrics.point import AsymmetricMAE
        return AsymmetricMAE
```

## 3) v1 custom model guidance

### Preferred model pattern
For a new v1 model, implement:

- `__init__`
- `_pkg()`
- `from_dataset()`
- `forward()`

Use one of the base classes according to the data shape:

- `BaseModel`: no covariates.
- `BaseModelWithCovariates`: covariates, but not autoregressive.
- `AutoRegressiveBaseModel`: autoregressive, no covariates.
- `AutoRegressiveBaseModelWithCovariates`: autoregressive with covariates.

### Input shape expectations
`TimeSeriesDataSet` batches normally expose a dict with keys such as:

- `encoder_cont`
- `decoder_cont`
- `encoder_cat`
- `decoder_cat`
- `encoder_lengths`
- `decoder_lengths`
- `target_scale`
- `encoder_target`
- `decoder_target`

Do not assume `encoder_cont` is always one-dimensional. If the dataset has multiple continuous features, `x["encoder_cont"]` is typically 3D.

### Forward contract
Return a network-output dict that contains at least `prediction`.
For v1, use `self.to_network_output(prediction=prediction)`.
If the model emits normalized outputs, rescale them with `self.transform_output(..., target_scale=x["target_scale"])` before wrapping the result.

### `from_dataset()` rules
Use `from_dataset()` to derive dataset-dependent sizes and to validate compatibility.
Common checks:

- fixed encoder/decoder lengths, if the architecture requires them
- allowed covariates or known-variable assumptions
- number of targets for multi-target models
- quantile count / output dimension alignment for probabilistic heads

Example pattern:

```python
from pytorch_forecasting.data.timeseries import TimeSeriesDataSet
from pytorch_forecasting.models.base import BaseModel


class MyModel(BaseModel):
    def __init__(self, input_size: int, output_size: int, hidden_size: int = 16, **kwargs):
        self.save_hyperparameters()
        super().__init__(**kwargs)
        self.network = ...

    @classmethod
    def _pkg(cls):
        from pytorch_forecasting.models.my_model._my_model_pkg import MyModel_pkg
        return MyModel_pkg

    @classmethod
    def from_dataset(cls, dataset: TimeSeriesDataSet, **kwargs):
        new_kwargs = {
            "input_size": dataset.max_encoder_length,
            "output_size": dataset.max_prediction_length,
        }
        new_kwargs.update(kwargs)
        return super().from_dataset(dataset, **new_kwargs)

    def forward(self, x):
        prediction = self.network(x["encoder_cont"].squeeze(-1))
        prediction = self.transform_output(prediction, target_scale=x["target_scale"])
        return self.to_network_output(prediction=prediction)
```

### Covariate-aware v1 models
If the architecture uses covariates, derive from `BaseModelWithCovariates` and expect the model to receive all encoder/decoder feature channels.
Useful ingredients:

- `x_reals`
- `x_categoricals`
- `embedding_sizes`
- `embedding_labels`
- `static_categoricals`
- `static_reals`
- `time_varying_categoricals_encoder`
- `time_varying_categoricals_decoder`
- `time_varying_reals_encoder`
- `time_varying_reals_decoder`
- `embedding_paddings`
- `categorical_groups`

### Multi-target v1 models
If the dataset has multiple targets, expect `target_scale` and `y` to be lists. Many models will need:

- a flattened or concatenated network head
- `MultiLoss` for training
- output reshaping back into one tensor per target

### Autoregressive v1 models
If the model predicts one step at a time, use the autoregressive base classes and split logic between `encode()` and `decode()`.
Keep target lag handling explicit and validate minimum encoder length early.

## 4) v1 package wrapper (`_pkg`) guidance

A v1 package wrapper is a private class that links the model to registry metadata and test fixtures.

### Naming
- File name: private file ending in `_pkg.py`
- Class name: `MyModel_pkg`

### Base class
In v1, inherit from `_BasePtForecaster`.

### `_tags` to keep accurate
Common tags include:

- `info:name`
- `info:compute`
- `info:pred_type`
- `info:y_type`
- `authors`
- `capability:exogenous`
- `capability:multivariate`
- `capability:pred_int`
- `capability:flexible_history_length`
- `capability:cold_start`
- `python_dependencies`
- `tests:skip_by_name` when a specific estimator/loss combination is known to fail

### Test fixture expectations
`get_base_test_params()` should return at least two parameter dictionaries, with the first entry covering defaults.
`_get_test_dataloaders_from()` should return small CPU-friendly train/val/test loaders.

A good fixture set varies one or two meaningful axes:

- default vs smaller hidden size
- covariates on/off
- fixed vs flexible lengths
- point vs quantile vs distribution loss
- optional dependency path vs default path

### Registry impact
The package wrapper is what discoverability, estimator tests, and tag filtering use. If the wrapper name or `info:name` is wrong, registry lookups and package linkage tests will fail even if the model code itself is correct.

## 5) Experimental v2 model / package / data-module guidance

### v2 model
Use the v2 `BaseModel` only for the beta API.
The forward method should return a dict containing `prediction`.
The package class can then use `predict()` modes such as `prediction`, `quantiles`, and `raw`.

### v2 package
Use `Base_pkg` for the orchestrator layer.
It owns:

- `model_cfg`
- `trainer_cfg`
- `datamodule_cfg`
- checkpoint save/load behavior
- `fit()` / `predict()` orchestration

A v2 package should implement:

- `get_cls()`
- `get_datamodule_cls()`
- `get_test_train_params()`

### v2 data module
Use a custom data module only if existing encoder-decoder or tslib data modules cannot produce the tensors your model expects.
Implement:

- `_prepare_metadata()`
- `metadata`
- `_preprocess_data()`
- `setup()`

Keep metadata focused on what the model needs to build layers and shapes, not a verbatim copy of all raw dataset fields.

### v2 dataset contract
The v2 data-module dataset should return the exact tensor dictionary the model expects. If the model expects `history_cont`, `future_cont`, `history_mask`, etc., the dataset must emit those keys consistently and the collate function must preserve them.

## 6) Registration and tagging checklist

When you add a new component, check the relevant registry surface:

- model import/export path
- package wrapper import/export path
- metric wrapper import/export path, if applicable
- tag values for test discovery
- optional dependency guards on top-level imports

Keep optional libraries out of top-level imports. If a component only needs `cpflows`, `optuna`, or another soft dependency in a specific method, import it inside that method.

## 7) Fast self-review checklist

- `from_dataset()` derives all dataset-dependent sizes.
- `forward()` returns the correct shape for the selected loss.
- Point predictions are 2D after `to_prediction`; raw outputs remain 3D when expected.
- Quantile heads match the number of quantiles.
- Distribution heads predict the correct number of parameters.
- Package wrapper class name and `info:name` match the model class.
- `python_dependencies` is present only when needed.
- No top-level optional imports.
- No broad dev extras were required for a basic smoke run.
