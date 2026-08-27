# Handler troubleshooting

## Install and optional dependency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` from `tqdm`, `tensorboard`, or `tensorboardX` | Progress bar or TensorBoard logging package is missing. | Install the helper package that matches the route you are using. |
| `ModuleNotFoundError` from `matplotlib` | LR-finder plots or schedule previews need plotting support. | Install `matplotlib` before calling the plotting helpers. |
| `ModuleNotFoundError` from `pandas` | Time profiler CSV output needs pandas. | Install `pandas` before calling `BasicTimeProfiler.write_results(...)` or `HandlersTimeProfiler.write_results(...)`. |
| Logger class import fails for `wandb`, `mlflow`, `clearml`, `neptune-client`, `polyaxon`, or `visdom` | The matching experiment-tracking package is not installed. | Install only the logger package you need and configure its service credentials or environment variables. |

## Checkpointing and file-system issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Directory path ... is not found` | A `DiskSaver` directory was not created and `create_dir=False` was used. | Create a fresh directory or pass `create_dir=True`. |
| `Files ... are already present in the directory` | `DiskSaver` default `require_empty=True` found existing `.pt` files. | Use a fresh directory or set `require_empty=False` when you intentionally want to reuse a path. |
| Only one checkpoint appears even though the handler runs repeatedly | `n_saved=1` retains only the best or latest retained file. | Increase `n_saved` or accept the single-file retention behavior. |
| Checkpoints never appear on non-zero ranks | The save handler is rank-aware. | Save on the desired rank or use the default rank-0 behavior intentionally. |
| A checkpointing job hangs on XLA or with `ZeroRedundancyOptimizer` | The save path is not executed on all participating processes. | Let every process enter the checkpoint handler, especially on XLA or when zero-redundancy optimizers are involved. |

## Early stopping and score problems

- `score_function` must be callable and should return a numeric score, usually from `engine.state.metrics`.
- Attach `EarlyStopping` to the evaluator's `Events.COMPLETED`, not to the trainer's training loop.
- `patience` must be a positive integer.
- If the wrong metric is used, the run may never stop or may stop too early. Check that `mode` matches the metric direction.
- `threshold_mode` controls whether the improvement threshold is absolute or relative. Use `abs` for a simple cut-off and `rel` for percentage-based improvements.

## Timer and profiler mistakes

- `Timer(average=True)` only reports a meaningful average when `step()` is called on the same cadence as the unit you care about.
- When attaching `Timer` to an engine, use `step=Events.ITERATION_COMPLETED` for average batch timing.
- `BasicTimeProfiler` expects a bounded run. If the data stream has no length, provide `epoch_length`.
- `BasicTimeProfiler.write_results(...)` and `HandlersTimeProfiler.write_results(...)` require `pandas`.

## Logger and progress issues

- `setup_tb_logging(...)` uses a training engine and evaluator metrics; make sure the evaluator has already attached the metrics you want to log.
- `ProgressBar` can become noisy if you attach too many metric names. Keep the display small and relevant.
- `logger_utils.global_step_from_engine(...)` is the safest way to align evaluator logging with trainer steps.
- External loggers often need local files, service accounts, API keys, or project names. Confirm those settings before debugging the Ignite side.

## Scheduler issues

- `cycle_size` for cyclic schedulers must be larger than 1.
- Attach iteration-based schedulers to `Events.ITERATION_STARTED` or `Events.ITERATION_COMPLETED`.
- If the scheduler appears not to move, check whether the event it is attached to actually fires.
- `ReduceLROnPlateauScheduler` should usually be driven by a validation metric, not by training loss alone.

## When in doubt

Start with the smallest synthetic loop, verify the logger or checkpoint file on disk, and only then move on to a larger training run.
