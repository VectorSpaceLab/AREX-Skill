# Checkpoint and Persistence Utilities

## On-disk formats

- `.ckpt` — legacy torch checkpoint.
- `.safetensors` — safe checkpoint format with JSON-encoded metadata in the header.
- `.tabpfn_fit` — zipped archive used for fitted estimator state.

## Low-level checkpoint helper

`Checkpoint(path)` exposes:

- `is_safetensors`
- `identity()` — a small fingerprint for cache invalidation
- `load()` — materializes the checkpoint into a dictionary

## Converting checkpoints

`save_as_safetensors(checkpoint, path)` converts a checkpoint dictionary to
SafeTensors.

## Foundation-model save/load

- `save_tabpfn_model(model, save_path)` stores the base checkpoint configuration.
- `load_model_criterion_config(...)` builds model, criterion, architecture config,
  and inference config objects from checkpoint data.

## Fitted-estimator save/load

- `save_fitted_tabpfn_model(estimator, path)` persists a fitted sklearn estimator.
- `load_fitted_tabpfn_model(path, device="cpu")` reconstructs the estimator and
  restores the fitted state.
- `TabPFNClassifier.save_fit_state` / `TabPFNRegressor.save_fit_state` are thin wrappers.
- `TabPFNClassifier.load_from_fit_state` / `TabPFNRegressor.load_from_fit_state`
  reload a saved fitted estimator.

## Path rules

- `save_fitted_tabpfn_model` requires a `.tabpfn_fit` suffix.
- The load helper validates archive contents so path traversal is not allowed.
- Fitted-state loading is for persistence only; it is not a checkpoint download API.
