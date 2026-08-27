# Custom component troubleshooting

Use this when a custom metric, v1 model, v1 package wrapper, experimental v2 package/data-module component, or focused test fails.

## 1) v1 `BaseModel` tensor-dict issues

### `KeyError: "encoder_cont"` or missing expected input key
Likely causes:

- The `TimeSeriesDataSet` was created without continuous variables.
- The target is categorical and the model should use categorical tensors instead.
- A v2 data-module tensor contract was accidentally used in a v1 model.

Fixes:

- For numeric single-target v1 smoke tests, include the target in `time_varying_unknown_reals`.
- For categorical targets, configure `target_normalizer=NaNLabelEncoder()` and use the categorical tensors intentionally.
- Keep v1 models aligned to `TimeSeriesDataSet` keys such as `encoder_cont`, `decoder_cont`, `encoder_cat`, `decoder_cat`, `encoder_lengths`, `decoder_lengths`, and `target_scale`.

### Size mismatch after `.squeeze(-1)`
Likely causes:

- The dataset has multiple continuous features, so `encoder_cont` is not a single channel.
- The model assumes no covariates, but `TimeSeriesDataSet` includes known or unknown covariates.

Fixes:

- Select explicit feature positions instead of squeezing blindly.
- For covariate-aware models, inherit from `BaseModelWithCovariates` and use `x_reals` / `x_categoricals` to map tensor channels back to variable names.
- Validate unsupported covariates in `from_dataset()` and fail early with a clear message.

### Raw predictions are 2D when tests expect 3D
Likely causes:

- The head returns `(batch, prediction_length)` instead of `(batch, prediction_length, output_dim)`.
- A point metric head forgot the trailing singleton dimension.

Fixes:

- For point forecasts, use a final output shape of `(batch, prediction_length, 1)` when returning raw network output.
- For quantile forecasts, set output dim to `len(loss.quantiles)`.
- For distribution losses, set output dim to the number of distribution parameters.

### Predictions have the wrong scale
Likely causes:

- `transform_output()` was skipped.
- The wrong `target_scale` object was passed for multi-target data.

Fixes:

- In v1, call `self.transform_output(prediction, target_scale=x["target_scale"])` before `self.to_network_output(prediction=prediction)`.
- For multi-target models, treat `target_scale` as a list and return one prediction tensor per target when the loss expects it.

### Forward returns the wrong object type
Likely causes:

- A v1 model returns a plain tensor.
- A v2 model copied v1 `to_network_output()` style.

Fixes:

- v1: return `self.to_network_output(prediction=prediction)`.
- v2: return a dict such as `{"prediction": prediction}`.

## 2) `.from_dataset()` mistakes

### Constructor arguments duplicate dataset settings
Likely cause: the model asks users to pass encoder/prediction lengths manually.

Fix: derive dataset-dependent fields in `from_dataset()`, for example `dataset.max_encoder_length`, `dataset.max_prediction_length`, target count, embedding sizes, and covariate names.

### Model silently accepts incompatible datasets
Likely causes:

- No validation for fixed-length-only architectures.
- No validation for unsupported covariates.
- No validation for multi-target support.

Fix: add explicit checks in `from_dataset()` before calling `super().from_dataset()`.
Raise `ValueError` or use assertions with messages that name the unsupported condition.

### `allowed_encoder_known_variable_names` is ignored
Likely cause: a covariate-aware model overrides `from_dataset()` but does not pass the argument through.

Fix: include the argument in the signature and pass it to `super().from_dataset()` when the selected base class supports it.

### Multi-target losses fail
Likely causes:

- The model returns one tensor while the loss expects a list.
- `target_scale`, `encoder_target`, or `decoder_target` is a list but the model treats it as a tensor.
- `MultiLoss` was not used for multiple targets.

Fix: reshape the network output into one tensor per target and use `MultiLoss` when combining target-specific metrics.

## 3) Package wrapper and registry failures

### `test_pkg_linkage` fails for v1
Common signals:

- `MyModel does not have a pkg attribute`
- package name does not match model class name
- package class is not `MyModel_pkg`

Fixes:

- Add `@classmethod def _pkg(cls): ... return MyModel_pkg` to the model.
- Use an absolute import inside `_pkg()`.
- Name the package wrapper class exactly `MyModel_pkg`.
- Set `_tags["info:name"]` to `"MyModel"`.

### v2 package linkage fails
Common signals:

- package class name is not accepted for the v2 naming convention
- `get_cls()` imports the wrong model
- `get_datamodule_cls()` returns a class that emits incompatible keys

Fixes:

- Use `MyModel_pkg_v2` or the accepted class-name-derived v2 variant.
- Return the actual v2 model class in `get_cls()`.
- Return a compatible data module class in `get_datamodule_cls()`.
- Ensure `get_test_train_params()` produces small valid `model_cfg` and `datamodule_cfg` combinations.

### Registry cannot find the class
Likely causes:

- The module is not importable from the package namespace.
- The wrapper inherits the wrong base object.
- Top-level optional imports fail during registry crawling.

Fixes:

- Export model/package or metric/package classes through the relevant package `__init__` files.
- v1 forecaster wrappers should inherit `_BasePtForecaster`.
- v2 wrappers should inherit `Base_pkg`.
- Metric wrappers should inherit `_BasePtMetric`.
- Move optional imports into methods and declare `python_dependencies` tags.

## 4) Optional dependency failures

### `ModuleNotFoundError: cpflows`
Likely cause: a component or test selected MQF2/distribution functionality without the optional MQF2 extra.

Fixes:

- Install the MQF2 optional dependency only if this path is in scope.
- Otherwise use core metrics such as `SMAPE` or `QuantileLoss` for smoke tests.
- If a model truly requires `cpflows`, set `python_dependencies` so focused tests can skip when unavailable.

### `ModuleNotFoundError: optuna` or plotting import errors
Likely cause: a component imported tuning or plotting dependencies at module import time.

Fixes:

- Do not top-level import tuning or plotting libraries for ordinary model/metric definitions.
- Import soft dependencies inside the specific method that needs them.
- Avoid choosing tuning/plotting tests for a core custom-component smoke run.

## 5) Estimator and metric test failures

### `test_integration` fails before training starts
Likely causes:

- `_get_test_dataloaders_from()` returns missing keys.
- `from_dataset()` rejects the fixture dataset.
- default parameters create a model that is too large or shape-incompatible.

Fixes:

- Make `get_base_test_params()` low-compute.
- Ensure the first parameter set covers default initialization.
- Return train/val/test dataloaders with matching `TimeSeriesDataSet` settings.

### `test_integration` trains but prediction check fails
Likely causes:

- `BaseModel.predict(mode="raw")` receives an output dict without `prediction`.
- raw prediction does not have three dimensions.
- `to_prediction()` or `to_quantiles()` cannot process the head output.

Fixes:

- Return `prediction` consistently.
- Keep raw output shape `(batch, prediction_length, output_dim)`.
- Implement custom `to_prediction()` / `to_quantiles()` only when the loss needs special post-processing.

### Metric `test_metric_update_and_compute` fails
Likely causes:

- The metric `loss()` already reduced over batch/time.
- Weighted or packed targets are not supported because base-class handling was bypassed.
- The loss returns NaN/Inf due to zero denominators or invalid logs.

Fixes:

- Return unreduced losses from `loss()`.
- Let `MultiHorizonMetric.update()` handle masking and weights.
- Clamp denominators and validate parameters in `__init__()`.

### Metric `test_to_prediction` or `test_to_quantiles` fails
Likely causes:

- A point metric receives a 3D output with last dimension larger than one and no quantile semantics.
- A quantile metric output dimension does not match its quantile list.
- Distribution metric parameters are not mapped to a valid torch distribution.

Fixes:

- For point metrics, emit a singleton third dimension or override `to_prediction()` carefully.
- For quantile metrics, keep the final dimension aligned to the quantile list.
- For distribution metrics, implement `map_x_to_distribution()` and `rescale_parameters()` together.

## 6) v2 package/data-module failures

### `fit()` says `model_cfg` or `datamodule_cfg` is missing
Likely cause: `Base_pkg` needs configs to build the data module and model from scratch.

Fix: instantiate the package with explicit `model_cfg`, `trainer_cfg`, and `datamodule_cfg` dictionaries unless loading from a checkpoint.

### v2 `predict_modes` fails
Likely causes:

- v2 model `forward()` returns the wrong key.
- `loss.to_prediction()` or `loss.to_quantiles()` cannot handle the raw head.
- data module returns different tensor keys for fit and predict stages.

Fixes:

- Return `{"prediction": tensor}` from the v2 model.
- Keep prediction output 3D in `raw` and `quantiles` modes; point `prediction` mode should reduce to 2D.
- Ensure `setup(stage="fit")` and `setup(stage="predict")` build compatible dataloaders.

### Custom v2 data module emits inconsistent batches
Likely causes:

- `collate_fn` drops optional keys.
- metadata reports shapes different from the actual batch tensors.
- train/val/test/predict windows use different feature sets.

Fixes:

- Build a tiny `TimeSeries` with one known feature, one unknown target, and one static feature.
- Inspect one batch from each dataloader stage.
- Align `_prepare_metadata()`, `_preprocess_data()`, `__getitem__()`, and `collate_fn` around one explicit tensor schema.

## 7) Last-resort narrowing

If a broad test run fails with many unrelated estimators, do not debug the whole suite first. Narrow to:

1. import / registry check
2. package-linkage test
3. tiny manual CPU smoke
4. one estimator or metric integration test with `-k YourComponentName`
5. only then broader tests
