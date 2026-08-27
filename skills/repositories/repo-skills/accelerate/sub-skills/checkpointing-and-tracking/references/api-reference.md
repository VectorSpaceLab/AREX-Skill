# Checkpointing and Tracking API Reference

## Accelerator Checkpointing and Export

| API | Use | Key parameters / behavior |
| --- | --- | --- |
| `Accelerator.save_state(output_dir=None, safe_serialization=True, **save_model_func_kwargs)` | Save full training state for resume. | With automatic checkpoint naming, ignores `output_dir` and writes under `<project_dir>/checkpoints/checkpoint_<iteration>`. Increments `project_configuration.iteration`. |
| `Accelerator.load_state(input_dir=None, load_kwargs=None, **load_model_func_kwargs)` | Load full training state. | If `input_dir=None`, requires automatic checkpoint naming and loads the latest checkpoint. Accepts `map_location="cpu"` or `"on_device"` through `load_model_func_kwargs`. |
| `Accelerator.register_for_checkpointing(*objects)` | Include custom stateful objects in `save_state`/`load_state`. | Every object must have `state_dict` and `load_state_dict`; invalid entries raise `ValueError`. |
| `Accelerator.register_save_state_pre_hook(hook)` | Run custom logic before state save. | Hook signature: `(models, weights, output_dir) -> None`; returns removable handle. |
| `Accelerator.register_load_state_pre_hook(hook)` | Run custom logic before state load. | Hook signature: `(models, input_dir) -> None`; returns removable handle. |
| `Accelerator.save(obj, f, safe_serialization=False)` | Distributed-safe object save. | Saves once per machine by default; respects `save_on_each_node`. |
| `Accelerator.save_model(model, save_directory, max_shard_size="10GB", safe_serialization=True)` | Save model weights as an artifact. | Handles wrapped models and sharded safetensors. Raises for meta-device parameters. |
| `Accelerator.get_state_dict(model, unwrap=True)` | Produce backend-aware model state dict. | Default unwraps the prepared model before `state_dict()`. |
| `Accelerator.unwrap_model(model, keep_fp32_wrapper=True, keep_torch_compile=True)` | Recover original module from wrappers. | Useful for custom library save methods. |
| `Accelerator.wait_for_everyone()` | Barrier before/after distributed save work. | No-op in single process; prevents race conditions in distributed file operations. |
| `Accelerator.free_memory(*objects)` / `Accelerator.clear(*objects)` | Release Accelerate references and reset step. | Reassign returned values to original variables. |

## ProjectConfiguration

`accelerate.utils.ProjectConfiguration` fields relevant to this sub-skill:

- `project_dir`: root directory for checkpoints and project outputs.
- `logging_dir`: directory for trackers that require local log storage; defaults to `project_dir` when unset.
- `automatic_checkpoint_naming`: when true, `save_state()` writes numbered folders under `project_dir/checkpoints`.
- `total_limit`: maximum checkpoint folders to keep when automatic naming is enabled.
- `iteration`: initial checkpoint number; set this when continuing a run whose earlier checkpoint numbers already exist.
- `save_on_each_node`: save once per node instead of once on the global main process.

## Low-Level Checkpointing Functions

These functions are public but usually called by `Accelerator.save_state()` and `Accelerator.load_state()` rather than user code:

| API | Purpose |
| --- | --- |
| `accelerate.checkpointing.save_accelerator_state(...)` | Writes model, optimizer, scheduler, dataloader, scaler, and RNG files to an output directory. |
| `accelerate.checkpointing.load_accelerator_state(...)` | Loads those files and returns override attributes such as saved step. |
| `accelerate.checkpointing.save_custom_state(obj, path, index=0, save_on_each_node=False)` | Writes `custom_checkpoint_<index>.pkl`. |
| `accelerate.checkpointing.load_custom_state(obj, path, index=0)` | Loads a registered object's state with CPU map location and `weights_only=False`. |

File naming includes `model.safetensors` or `pytorch_model.bin`, `optimizer.bin`, `scheduler.bin`, `random_states_<process>.pkl`, `scaler.pt`, optional dataloader state files, and `custom_checkpoint_<index>.pkl` for registered objects.

## Tracking APIs

| API | Use | Notes |
| --- | --- | --- |
| `Accelerator(log_with=...)` | Select tracker(s). | Accepts a string, `LoggerType`, list, custom `GeneralTracker` instance, or `"all"`. |
| `Accelerator.init_trackers(project_name, config=None, init_kwargs=None)` | Start trackers and log initial config. | `init_kwargs` is nested by tracker name, e.g. `{ "wandb": {"tags": [...]}}`. |
| `Accelerator.log(values, step=None, log_kwargs=None)` | Log metrics to active trackers. | Runs on main process through Accelerate's decorator. |
| `Accelerator.get_tracker(name, unwrap=False)` | Retrieve a tracker by `.name`. | `unwrap=True` returns the underlying service object. |
| `Accelerator.end_training()` | Finish trackers and destroy process group. | Should be called after tracking runs. |
| `accelerate.tracking.get_available_trackers()` | Discover installed supported trackers. | Returns `LoggerType` values for available optional packages. |

## Tracker Classes

All tracker classes inherit `GeneralTracker` and implement `name`, `requires_logging_directory`, `tracker`, `store_init_configuration()`, `log()`, and optional richer methods such as `log_images()`, `log_table()`, `log_artifact()`, or `finish()`.

| Class | `.name` | Notes |
| --- | --- | --- |
| `TensorBoardTracker` | `tensorboard` | Requires a logging directory; logs scalars/text/nested scalar groups and images. |
| `WandBTracker` | `wandb` | `main_process_only=False` at class level, with methods decorated to run correctly through PartialState. Supports image/table helpers. |
| `TrackioTracker` | `trackio` | Trackio integration. |
| `CometMLTracker` | `comet_ml` | Comet ML integration. |
| `AimTracker` | `aim` | Requires a logging directory; supports images. |
| `MLflowTracker` | `mlflow` | Supports metrics, figures, artifacts, and local directories. |
| `ClearMLTracker` | `clearml` | Supports images and tables. |
| `DVCLiveTracker` | `dvclive` | DVCLive integration. |
| `SwanLabTracker` | `swanlab` | SwanLab integration; supports images. |

`GeneralTracker.main_process_only` defaults to `True`. Use the `accelerate.tracking.on_main_process` decorator on custom tracker methods when only the main process should execute them.

## Logging APIs

| API | Use | Notes |
| --- | --- | --- |
| `accelerate.logging.get_logger(name, log_level=None)` | Rank-aware Python logger adapter. | Uses `ACCELERATE_LOG_LEVEL` if `log_level` is omitted. |
| `logger.info(..., main_process_only=True)` | Default main-process log. | Works for standard logging levels. |
| `logger.info(..., main_process_only=False)` | Log from all processes. | Messages include `[RANK <index>]`. |
| `logger.info(..., in_order=True)` | Log rank-by-rank. | Ignores `main_process_only`; every rank must reach the call. |
| `logger.warning_once(...)` | Emit duplicate warning args once. | Cache is argument-based. |

The logging adapter requires Accelerate state to be initialized with `Accelerator()` or `PartialState()` before logging.

## Profiling APIs

| API | Use | Key fields |
| --- | --- | --- |
| `ProfileKwargs(...)` | Configure PyTorch profiler through Accelerate. | `activities`, `schedule_option`, `on_trace_ready`, `record_shapes`, `profile_memory`, `with_stack`, `with_flops`, `with_modules`, `output_trace_dir`. |
| `Accelerator(kwargs_handlers=[profile_kwargs])` | Attach default profiler config. | The `profile()` context uses this unless overridden. |
| `accelerator.profile(profile_handler=None)` | Context manager returning a PyTorch profiler object. | Use `prof.key_averages().table(...)`; call `prof.step()` for scheduled profiling. |

## State, RNG, and Memory Utilities

| API | Use |
| --- | --- |
| `accelerate.state.PartialState` | Lightweight shared state for process index, main-process checks, device, and barriers. Used by trackers/loggers. |
| `accelerate.state.AcceleratorState` | Full Accelerator process/distributed state. |
| `accelerate.utils.set_seed(seed, device_specific=False, deterministic=False)` | Seed Python, NumPy, Torch, and available accelerator backends. |
| `accelerate.utils.synchronize_rng_state(rng_type, generator=None)` | Broadcast one RNG state from process 0. |
| `accelerate.utils.synchronize_rng_states(rng_types, generator=None)` | Broadcast multiple RNG states. |
| `accelerate.utils.clear_device_cache(garbage_collection=False)` | Empty backend device cache where supported; optionally run GC. |
| `accelerate.utils.release_memory(*objects)` | Set objects to `None`, collect garbage, clear cache, and return replacement `None`s. |
| `accelerate.utils.find_executable_batch_size(...)` | Retry a function with smaller batch sizes on recognized OOM errors. |
