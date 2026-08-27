# Losses, Optimizers, Scalers, And Interpolation

## Criterion Registry

The `pytorch_criterion_dict` training registry includes:

- `MSE`
- `SmoothL1Loss`
- `PoissonNLLLoss`
- `RMSE`
- `MAPE`
- `DilateLoss`
- `L1`
- `PenalizedMSELoss`
- `CrossEntropyLoss`
- `NegativeLogLikelihood`
- `BCELossLogits`
- `FocalLoss`
- `QuantileLoss`
- `BinaryCrossEntropy`
- `GaussianLoss`
- `MASELoss`

Additional custom losses in `flood_forecast.custom.custom_opt`, such as `InfoNCELoss`, `NSELoss`, and `MaskedMSELoss`, are used by multimodal/physics workflows but are not registered in `pytorch_criterion_dict` for ordinary JSON trainer lookup in this snapshot.

## Optimizer Registry

The supported optimizer names in the trainer registry are:

- `Adam`
- `SGD`
- `BertAdam`

## Scalers

The package can build these scikit-learn scalers:

- `StandardScaler`
- `RobustScaler`
- `MinMaxScaler`
- `MaxAbsScaler`

### Important scaler note

When a JSON config writes `scaler_params["feature_range"]` as a list, the trainer converts it to a tuple before constructing the scaler. That avoids the common sklearn JSON mismatch.

## Interpolation Helpers

The interpolation registry includes:

- `back_forward`
- `back_forward_generic`
- `forward_back_generic`

## Loss Selection Notes

### `GaussianLoss`

Use for models that emit a mean and standard deviation or a Gaussian tuple.

### `CrossEntropyLoss`

Use with classification loaders; labels are converted from one-hot to class indices in the training loop.

### `MASELoss`

Requires a baseline method and the source history tensor.

### `QuantileLoss`, `FocalLoss`, `NSELoss`, `MaskedMSELoss`

Useful for probabilistic, classification, hydrology, or sparse-supervision workflows respectively.

### `InfoNCELoss`

Used by contrastive pretraining for catchment embeddings.

## Multi-Criterion Training

`training_params["criterion"]` can be a list when the model should optimize multiple objectives at once. `criterion_params` can be a list of per-criterion kwargs.

## Validation Hint

If loss setup fails even before the first batch, inspect the config keys against the registry names exactly. The registry is string-based; misspellings are not auto-corrected.
