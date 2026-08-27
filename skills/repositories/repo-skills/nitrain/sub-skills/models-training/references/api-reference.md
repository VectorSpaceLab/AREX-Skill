# API reference

## Purpose

Read this for the verified model-discovery and trainer signatures.

## Architecture discovery

### `nitrain.fetch_architecture(name, dim=None)`

- Returns a callable from `antspynet.architectures`.
- With `dim=2` or `dim=3`, it looks for `create_{name}_model_2d` or
  `create_{name}_model_3d`.
- Without `dim`, it looks for `create_{name}_model`.
- Raises `ValueError` when the architecture function does not exist.

### `nitrain.list_architectures()`

- Returns a list of `[name, dim]` pairs.
- Non-dimensional models use an empty string for `dim`.

### `nitrain.models.fetch_pretrained.fetch_pretrained(name, cache_dir=None)`

- Returns the antspynet pretrained network handle.
- May download weights or use a local cache depending on the model name.
- In this snapshot, `nitrain.fetch_pretrained` at the package root is a module
  object; import the callable from the submodule path above.

## Trainer APIs

### `nitrain.Trainer(model, task=None, optimizer=None, loss=None, metrics=None, **kwargs)`

- Accepts Keras, torch, or monai-backed torch models.
- `task='regression'` defaults to Adam + MSE + `['mse']`.
- `task='classification'` or `task='segmentation'` defaults to Adam plus
  binary or categorical cross-entropy depending on `model.output_shape[-1]`.
- `task=None` requires both `optimizer` and `loss`.
- Keras models are compiled automatically.

Methods:
- `fit(loader, epochs, validation=None, **kwargs)`
- `evaluate(loader)`
- `predict(loader)`
- `summary()`
- `save(path)`

### `nitrain.trainers.TorchTrainer(model, optimizer, loss, metrics, device='cpu', **kwargs)`

- A separate torch-only trainer wrapper.
- Uses the shared `torch_model_fit()` and `torch_model_evaluate()` helpers.
- The verified smoke path is CPU-only.

## Framework inference

- `infer_framework(model)` is the internal detector used by `Trainer`.
- It checks the model type string for `keras`, `torch`, or `monai`.

## Notes that matter

- `Trainer.evaluate()` and `Trainer.predict()` are only implemented for Keras in
  the inspected source.
- `Trainer.save()` is also Keras-only in this snapshot.
- `TorchTrainer` requires a model that already produces outputs compatible with
  the chosen loss and metrics.
