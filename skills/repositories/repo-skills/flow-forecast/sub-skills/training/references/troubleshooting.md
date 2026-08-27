# Training Troubleshooting

## Registry Errors

### `Error the model ... was not found in the model dict`

- **Likely cause:** `model_name` is misspelled or not supported by the registry.
- **Fix:** compare the name against `references/model-overview.md`.

### Optimizer or criterion key errors

- **Likely cause:** `training_params["optimizer"]` or `training_params["criterion"]` is not one of the supported string keys.
- **Fix:** use the exact registry names from `references/losses-and-optimizers.md`.

## WandB Problems

### `bool object has no attribute 'get'`

- **Likely cause:** `wandb` was set to `True` instead of a dictionary or `False`.
- **Fix:** set `wandb` to `False` or use a mapping with `project`, `name`, and `tags`.

### WandB / protobuf import failures

- **Likely cause:** the environment has an incompatible WandB / protobuf pair.
- **Fix:** reinstall a compatible combination in the private inspection environment, or disable WandB for the smoke run.

### `module 'wandb.util' has no attribute 'generate_id'`

- **Likely cause:** W&B logging is enabled and the installed W&B package is newer than the utility API expected by this snapshot.
- **Fix:** use `wandb: false` unless logging is required, or install a compatible W&B/protobuf pair explicitly.
- **Verification note:** native configs that enable W&B may fail on this optional path even when the model, loader, and training loop work with W&B disabled.

## Validation Failures

### `Error validation loss is zero there is a problem with the validator.`

- **Likely cause:** the validation loader or output labels are not aligned with the model output.
- **Fix:** inspect the loader class, the decoder path, and the target column shape.

### `Error infinite or NaN loss detected. Try normalizing data or performing interpolation`

- **Likely cause:** the data is unscaled, has large magnitude variation, or still contains gaps.
- **Fix:** scale the data, add interpolation, and rerun the data-preparation validation script.

### Post-fit evaluation fails in SHAP with `tensor() got an unexpected keyword argument 'names'`

- **Likely cause:** `trainer.train_function` reaches `evaluate_model`, which may call `deep_explain_model_summary_plot`; the current PyTorch/runtime may reject that named-tensor call.
- **Fix:** treat SHAP as optional. For bounded smoke, instantiate `PyTorchForecast` and call `train_transformer_style` directly, then run inference separately. For a production run that needs SHAP, patch the explanation helper or use a compatible runtime.

## Loader / Config Mismatch

### `GeneralClassificationLoader` or `VariableSequenceLength` behaves differently than expected

- **Likely cause:** those loaders do not follow the forecasting evaluation path.
- **Fix:** check the loader-specific notes in the model-config reference and avoid forecasting-only assumptions.

### `TemporalLoader` fails on missing temporal features

- **Likely cause:** `temporal_feats` or `label_len` is missing from the config.
- **Fix:** add the explicit temporal columns and confirm that the datetime features were created before loading.

### `n_target_lags` or `n_exog_lags` exceeds `forecast_history`

- **Likely cause:** the NARX lag window is larger than the available history window.
- **Fix:** lower the lag counts or increase the history length.

## Scaler And JSON Problems

### Scaler construction fails on `feature_range`

- **Likely cause:** `scaler_params["feature_range"]` is still a JSON list.
- **Fix:** let the trainer convert it, or write it as a tuple-like structure in the generated config tooling.

## Transfer Learning Problems

### Excluded layers or frozen layers do not behave as expected

- **Likely cause:** the checkpoint keys no longer match the current model layout.
- **Fix:** inspect the model state dict and trim the transfer-learning settings.

## DA-RNN Problems

### The DA-RNN path cannot find TensorBoard

- **Likely cause:** `tensorboard` is missing or mismatched.
- **Fix:** install a compatible TensorBoard package or disable TensorBoard logging.

### `TrainData` object has no attribute `feats`

- **Likely cause:** the preprocessing helper returned `TrainData(features, targets)`, but the DA-RNN trainer expects `TrainData(feats, targs)` from `flood_forecast.da_rnn.custom_types`.
- **Fix:** adapt the object explicitly: `train_data = DaTrainData(raw.features, raw.targets)`.
- **Verification note:** the repo-native DA-RNN preprocessing tests expose this mismatch in this snapshot, so treat DA-RNN training as a caveated workflow until the adapter or source patch is applied.

## When To Stop And Ask

Ask the user for more information when the config depends on a private checkpoint, a custom model constructor, a required accelerator backend, or a cloud bucket that is not available in the inspection environment.
