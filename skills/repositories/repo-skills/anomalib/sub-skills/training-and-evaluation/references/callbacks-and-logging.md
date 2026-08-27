# Callbacks and logging

This reference covers callback ordering, automatic checkpoint behavior, and the supported experiment loggers for the training-and-evaluation surface.

## Callback stack

Anomalib combines callbacks from three places:

1. `AnomalibModule.configure_callbacks()`
2. callbacks injected by `Engine`
3. callbacks passed explicitly to `Engine(callbacks=[...])`

The model-level callback bundle usually includes the pre-processor, post-processor, evaluator, and visualizer when those components inherit from Lightning `Callback`.

Engine-inserted callbacks are added automatically when the trainer is built:

- default `ModelCheckpoint` when `barebones=False` and no checkpoint callback is already present
- `TimerCallback`
- `MaxStepsProgressCallback`

This means that callback order matters when you override or duplicate the same callback class.

## Automatic checkpointing

Default behavior:

- if the trainer is not barebones and no checkpoint callback is already present, Engine inserts a `ModelCheckpoint`
- the default checkpoint lands under `weights/lightning/model.ckpt`
- `Engine.best_model_path` points at the selected checkpoint path

Barebones behavior:

- the default auto-inserted checkpoint callback is skipped
- this is the expected fast-path behavior for smoke tests and overhead checks
- if you add your own checkpoint callback, do so explicitly and document why

Useful rule of thumb:

- use barebones when you want speed and do not need the default checkpoint artifact
- use normal mode when you want the usual best-model path and Lightning logging behavior

## `get_callbacks(config)`

The public `get_callbacks(config)` helper is for config-driven wiring.

It currently adds:

- `LoadModelCallback` when `trainer.ckpt_path` is present
- an NNCF callback when `optimization.nncf.apply` is true

Notes:

- it expects a config object, not CLI parsing logic
- NNCF is imported dynamically and is optional
- if you do not need compression, keep NNCF out of the minimum environment

## Specialized callbacks

### `GraphLogger`

Graph logging depends on the logger backend:

- TensorBoard and Comet log the graph at the end of training
- W&B watches the model at train start
- W&B graph logging may not work for models without backward passes, such as training-free models

### `TimerCallback`

Tracks:

- training time
- testing time
- testing throughput

### `MaxStepsProgressCallback`

Patches the Rich progress bar when `max_steps` is used without a useful `max_epochs` value.

This is mostly a user-experience fix for step-based training.

### `TilerConfigurationCallback`

Only use this when the model supports tiling.

- it expects a model with a `tiler` attribute
- otherwise it raises `ValueError`

## Logging backends

### Console logging

`anomalib.loggers.configure_logger()` sets a Rich-based console logger and aligns Lightning's logging format.

Use it when you want consistent terminal output during debugging.

### TensorBoard

`AnomalibTensorBoardLogger` is the safest default experiment logger.

Important detail:

- `add_image(...)` requires `global_step`

### Comet

`AnomalibCometLogger` also requires `global_step` for image logging.

### Weights & Biases

`AnomalibWandbLogger` caches images and flushes them on `save()`.

It is useful, but it is still an optional dependency and should remain out of the minimum environment unless needed.

### MLflow

`AnomalibMLFlowLogger` logs figures and arrays through different experiment methods.

Be explicit about the artifact name when you want predictable output files.

## Optional dependency behavior

The `anomalib.loggers` package conditionally imports optional backends.

If the backend package is missing, the module prints an install hint instead of breaking the whole training surface.

Practical guidance:

- use `logger=False` when you want the lightest possible environment
- use TensorBoard if you want a small, local default
- add Comet, W&B, or MLflow only when you need their hosted tracking features

## Good callback habits

- Keep logging and checkpointing decisions explicit.
- Do not register the same callback class both in the model and in `Engine(callbacks=...)` unless you are intentionally overriding behavior.
- When a callback seems ignored, check the order: model callbacks first, then Engine-inserted callbacks, then explicit trainer callbacks.
