# Handler API reference

## Core handler families

| Symbol(s) | Purpose | Notes |
| --- | --- | --- |
| `Checkpoint` | Save and restore stateful objects during training or evaluation. | Works with any object exposing `state_dict` / `load_state_dict`; pair it with `DiskSaver` for filesystem checkpoints or a custom save handler for other storage. |
| `DiskSaver` | Write checkpoints to a directory on disk. | Supports atomic writes, directory creation, rank-aware saving, and `require_empty` checks. |
| `ModelCheckpoint` | High-level checkpoint handler for disk-only saving. | Convenience wrapper around `Checkpoint` with filename retention and score-based selection. |
| `EarlyStopping` | Stop a trainer after a score stops improving. | Attach to an evaluator and pass the trainer to terminate. |
| `TerminateOnNan` | Stop when the output becomes NaN or infinite. | Useful for catching unstable losses early. |
| `TimeLimit` | Stop after a fixed wall-clock budget. | Handy for bounded training runs or demo jobs. |
| `Timer` | Measure elapsed or average batch/epoch time. | Attach it to engine events with `start`, `pause`, `resume`, and `step`. |
| `EMAHandler` | Maintain an exponential moving average of parameters. | Common in vision and diffusion-style training loops. |
| `ProgressBar` | Human-readable progress display on top of an engine. | Uses `tqdm`; can show metric names and iteration statistics. |
| `BasicTimeProfiler` / `HandlersTimeProfiler` | Measure event, dataflow, and handler timings. | `BasicTimeProfiler.write_results(...)` needs `pandas`. |

## Logger integrations

| Symbol(s) | Purpose | Optional dependency |
| --- | --- | --- |
| `TensorboardLogger` / `setup_tb_logging` | Log training metrics, optimizer parameters, and evaluator metrics to TensorBoard. | `tensorboard` or `tensorboardX` |
| `WandBLogger` / `setup_wandb_logging` | Send metrics and artifacts to Weights & Biases. | `wandb` |
| `MLflowLogger` / `setup_mlflow_logging` | Track experiments with MLflow. | `mlflow` |
| `NeptuneLogger` / `setup_neptune_logging` | Track experiments with Neptune. | `neptune-client` |
| `ClearMLLogger` / `setup_clearml_logging` | Track experiments with ClearML. | `clearml` |
| `PolyaxonLogger` / `setup_plx_logging` | Track experiments with Polyaxon. | `polyaxon` |
| `VisdomLogger` / `setup_visdom_logging` | Legacy Visdom dashboards and plots. | `visdom` |
| `FBResearchLogger` / `setup_trains_logging` | Legacy alias for older experiment tracking workflows. | Historical compatibility surface |
| `logger_utils.global_step_from_engine` | Share a global step source across trainer and evaluator loggers. | Useful when the evaluator logs at `Events.COMPLETED`. |

## Scheduler and parameter-update helpers

| Symbol(s) | Purpose | Notes |
| --- | --- | --- |
| `BaseParamScheduler` | Base class for parameter scheduling. | Handles state dicts and event-index bookkeeping. |
| `ParamScheduler` | Scheduler bound to an optimizer or param-group-like object. | The common base for learning-rate and state parameter schedules. |
| `LRScheduler` | Wrap a PyTorch LR scheduler as an Ignite handler. | Bridges standard PyTorch schedulers into engine events. |
| `PiecewiseLinear` | Linear interpolation between named milestones. | Good for short warmups or hand-authored schedules. |
| `LinearCyclicalScheduler` / `CosineAnnealingScheduler` | Cyclic parameter schedules. | `cycle_size` should usually match the number of iterations per epoch when attached to iteration events. |
| `create_lr_scheduler_with_warmup` | Build a warmup + scheduler composition. | Useful for transformer-style warmup or staged schedules. |
| `BatchSizeScheduler` | Change batch size during a run. | Useful when memory use or curriculum strategy changes over time. |
| `ReduceLROnPlateauScheduler` | Wrap PyTorch ReduceLROnPlateau logic for Ignite. | Usually driven by evaluator metrics. |
| `StateParamScheduler` family | Schedule engine state parameters instead of optimizer params. | Includes step, exponential, lambda, and multi-step variants. |
| `FastaiLRFinder` | LR-finder helper and plotter. | `plot`/preview paths need `matplotlib`. |

## Common handler boundaries

- `Checkpoint` and `ModelCheckpoint` own persistence, not the training loop.
- `EarlyStopping` and `TerminateOnNan` are control-flow handlers; attach them to the evaluator or trainer event that should stop the run.
- Logger helpers live here when they wrap `BaseLogger` subclasses, but detailed training-loop structure still belongs in `sub-skills/engine/`.
- `Timer` and the profilers are instrumentation helpers; use them when you need timings rather than model quality metrics.
- Parameter schedulers are ordinary handlers, so attach them to the engine event cadence that matches the update frequency you want.
