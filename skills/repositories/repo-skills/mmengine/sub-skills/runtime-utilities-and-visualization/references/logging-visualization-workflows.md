# Logging and Visualization Workflows

This reference covers MMEngine runtime logging, message hubs, visualizers, and visual backends. Keep service-backed logging optional and default to local outputs when credentials or packages are unavailable.

## Choose the Runtime Utility

| Need | Use | Key inputs | Output behavior |
| --- | --- | --- | --- |
| Emit a quick message | `mmengine.logging.print_log(msg, logger=..., level=...)` | message, logger name/object/`current`, log level | Prints through an MMEngine/current logger or standard logging target. |
| Reusable formatted logger | `MMLogger.get_instance(name, log_file=None, log_level='INFO', ...)` | non-empty instance name, optional file path, level, distributed flag | Returns the same global instance for the same name; can write terminal and file logs. |
| Share scalar histories | `MessageHub.get_instance(name)` | scalar names, numeric values, counts, resume flags | Stores `HistoryBuffer` values for smoothing/resume and runtime metadata. |
| Save local visual artifacts | `Visualizer(..., vis_backends=[dict(type='LocalVisBackend')], save_dir=...)` | RGB `uint8` images, scalar dicts, config objects, step | Writes under `save_dir/vis_data/` using backend-specific filenames. |
| Use TensorBoard | `TensorboardVisBackend` | save dir, scalar/image/config calls | Requires TensorBoard support; writes event files locally. |
| Use tracking service | `WandbVisBackend`, `MLflowVisBackend`, `ClearMLVisBackend`, `AimVisBackend`, `DVCLiveVisBackend`, `NeptuneVisBackend` | backend config, package installation, service credentials or local mode | Initializes lazily on first `add_*` or `experiment` access; may contact external services depending on backend config. |

## Logging Workflow

1. Pick a stable logger instance name, usually one per experiment or application component.
2. Create the logger once with `MMLogger.get_instance(name='experiment', log_file='run.log', log_level='INFO')`.
3. Reuse the instance with `MMLogger.get_instance('experiment')` or route `print_log(..., logger='current')` after creating the intended logger.
4. In distributed code, let MMEngine rank filtering handle terminal noise: rank 0 logs normal messages, nonzero ranks emit errors to stream, and file naming changes when multi-rank file logging is enabled.
5. If adding custom file handlers, pass `file_handler_cfg=dict(type='TimedRotatingFileHandler', ...)` or another supported `logging.handlers` class name.

`MMLogger` inherits `ManagerMixin`, so `get_instance` returns the previously created object for a repeated name. If you pass new constructor kwargs for an existing name, MMEngine warns and keeps the original instance.

## MessageHub Workflow

Use `MessageHub` for runtime values that multiple components need to exchange without direct references.

- `MessageHub.get_instance('name')` creates or retrieves a named hub.
- `MessageHub.get_current_instance()` creates a default `mmengine` hub if none exists, then returns the latest hub.
- `update_scalar(key, value, count=1, resumed=True)` records numeric history; `value` may be Python numeric, scalar NumPy value, or scalar torch tensor.
- `update_scalars({'loss': dict(value=0.1, count=4), 'lr': 0.001})` batch-updates history buffers.
- `update_info(key, value, resumed=True)` stores current runtime metadata and overwrites previous values.
- Keep `resumed` consistent for each key; changing it later raises an assertion.

Use `get_scalar(key)` when the key must exist and `get_info(key, default=None)` for optional runtime metadata.

## Local Visualizer Workflow

A safe local visualizer needs no credentials and should be the default fallback:

```python
from mmengine.visualization import Visualizer

visualizer = Visualizer(
    name='local-runtime-check',
    vis_backends=[dict(type='LocalVisBackend')],
    save_dir='work-dir')
visualizer.add_scalar('loss', 0.1, step=1)
visualizer.add_scalars({'accuracy': 0.9}, step=1)
visualizer.add_image('sample', rgb_uint8_image, step=1)
visualizer.close()
```

Important path behavior: `Visualizer(..., save_dir='work-dir')` passes `work-dir/vis_data` to backends. `LocalVisBackend` then creates image/config/scalar files below that backend directory, commonly including `vis_image/` and `scalars.json`.

## Image and Data Sample Rules

- `LocalVisBackend.add_image` asserts `image.dtype == np.uint8` and treats image arrays as RGB, converting to BGR only for local PNG writing.
- TensorBoard also expects HWC image arrays for `add_image`.
- `Visualizer.add_datasample` in base MMEngine is an abstract no-op placeholder; downstream OpenMMLab libraries usually subclass `Visualizer` to implement task-specific drawing.
- Use `set_image`, drawing methods, and `get_image` for generic overlays; use downstream visualizers for detection/segmentation/data-sample semantics.
- Many visualizer write methods are decorated with `master_only`, so they execute only on rank 0 after distributed initialization.

## Backend Selection

| Backend | Safe default? | Typical config | Notes |
| --- | --- | --- | --- |
| `LocalVisBackend` | Yes | `dict(type='LocalVisBackend')` | Writes images, scalars, and configs to local disk; best fallback. |
| `TensorboardVisBackend` | Usually | `dict(type='TensorboardVisBackend')` | Requires TensorBoard support in the environment; no service credentials. |
| `WandbVisBackend` | Optional | `dict(type='WandbVisBackend', init_kwargs={...})` | Imports `wandb` lazily and may need login/offline settings. |
| `MLflowVisBackend` | Optional | `dict(type='MLflowVisBackend', tracking_uri=...)` | Requires `mlflow`; tracking URI determines local vs remote behavior. |
| `ClearMLVisBackend` | Optional | `dict(type='ClearMLVisBackend', init_kwargs={...})` | Requires ClearML package and configured credentials for remote use. |
| `AimVisBackend` | Optional | `dict(type='AimVisBackend', repo=...)` | Requires Aim; can be local depending on repo config. |
| `DVCLiveVisBackend` | Optional | `dict(type='DVCLiveVisBackend')` | Requires DVCLive; suited for DVC-managed projects. |
| `NeptuneVisBackend` | Optional | `dict(type='NeptuneVisBackend', init_kwargs={...})` | Requires Neptune package and credentials for remote use. |

When a service backend fails to import or authenticate, switch to `LocalVisBackend` or TensorBoard unless the user explicitly needs that service.

## Runner Cross-Link

Runner hook placement belongs to `../runner-and-training/SKILL.md`. This sub-skill explains the underlying visualizer and logger behavior; use the Runner sub-skill to configure `default_hooks.logger`, visualization hooks, log intervals, and training-output directories.
