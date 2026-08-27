# Troubleshooting Checkpointing and Tracking

## Checkpoint Path Missing

Symptoms:

- `ValueError: Tried to find ... but folder does not exist` from `load_state(path)`.
- `ValueError: No input_dir provided and automatic checkpoint naming is disabled.` from `load_state()`.
- An automatic load resumes the wrong checkpoint.

Fixes:

- Pass the exact checkpoint directory created by `save_state()`, not the parent run directory.
- If using automatic naming, use `ProjectConfiguration(project_dir=..., automatic_checkpoint_naming=True)` and ensure the expected folder exists under `project_dir/checkpoints/checkpoint_<n>`.
- When omitting `input_dir`, automatic naming must be enabled; Accelerate loads the numerically latest checkpoint folder.
- If checkpoint folder names were created manually, keep the numeric suffix parseable. Nonstandard folder names can break latest-checkpoint selection.

## Automatic Naming and `total_limit`

Symptoms:

- Old checkpoints disappear unexpectedly.
- `ValueError: Checkpoint directory ... already exists`.
- New saves restart at `checkpoint_0` after a resumed run.

Fixes:

- `total_limit` intentionally deletes the oldest folders when `len(existing) + 1 > total_limit`.
- Set `ProjectConfiguration(iteration=<next_number>, automatic_checkpoint_naming=True)` when restarting a script that will continue saving into an existing project directory.
- Do not write unrelated directories into `project_dir/checkpoints`; automatic retention assumes checkpoint-like numeric suffixes.
- Use explicit `output_dir` and disable automatic naming when you need full manual folder control.

## Hook Order or Missing Metadata

Symptoms:

- Custom metadata is absent from checkpoints.
- Custom load code runs but the model later overwrites the loaded state.
- Hook behavior persists after a test or one-off save.

Fixes:

- Register save and load hooks before calling `save_state()` or `load_state()`.
- Remember save hooks run before the default checkpoint writer, and load hooks run before default model loading.
- If a hook replaces default model save/load, mutate the provided `weights` or `models` list intentionally; otherwise default serialization continues after the hook.
- Keep and remove hook handles with `handle.remove()` after temporary use.
- Pair hook formats: every file written by a save hook should have a compatible load hook or a documented optional fallback.

## Custom Object Registration Fails

Symptoms:

- `ValueError` from `register_for_checkpointing()` listing invalid items.
- Runtime error because the number of `custom_checkpoint_<n>.pkl` files does not match registered objects.

Fixes:

- Register only objects with both `state_dict()` and `load_state_dict(state)`.
- Register objects in the same order before saving and before loading.
- Avoid unrelated files matching `custom_checkpoint_<number>.pkl` in the checkpoint directory.
- Do not use custom object registration to load state from a different script with a different object graph.

## Unwrapped Model Saving Problems

Symptoms:

- Saved artifact contains wrapper-specific keys.
- A downstream library cannot reload a model saved from a prepared wrapper.
- `save_model()` raises because parameters are on the meta device.

Fixes:

- For library-specific exports, call `accelerator.unwrap_model(model)` and pass `save_function=accelerator.save` if the library supports it.
- For a plain PyTorch model artifact, prefer `accelerator.save_model(model, save_directory)`.
- Use `accelerator.get_state_dict(model)` rather than `model.state_dict()` when the model may be wrapped or managed by a distributed backend.
- Do not call `save_model()` on a model with unresolved meta parameters; materialize or load weights first.
- For DeepSpeed ZeRO-3 or FSDP checkpoint strategy, use the distributed backends sub-skill because backend config controls what can be gathered and saved.

## RNG or Resume Drift

Symptoms:

- Loss after resume diverges from a continuous run.
- Dataloader resumes from the beginning instead of the mid-epoch point.
- Random augmentations differ after loading.

Fixes:

- Set initial seeds consistently with `accelerate.utils.set_seed()` before constructing randomized objects.
- Keep the same number and order of prepared models, optimizers, schedulers, dataloaders, and registered objects.
- Use stateful dataloaders when exact dataloader state matters, or combine `load_state()` with `accelerator.skip_first_batches()` in the training loop.
- Save at deterministic boundaries such as epoch end when exact mid-epoch dataloader replay is not required.
- Treat `save_state()` as same-script resume, not cross-script migration.

## Tracker Optional Dependencies and Credentials

Symptoms:

- `Accelerator(log_with="tensorboard")` raises that a logging directory is required.
- A tracker import or initialization fails for `wandb`, `comet_ml`, `mlflow`, `clearml`, `aim`, `dvclive`, `swanlab`, or `trackio`.
- Script unexpectedly starts all installed trackers.

Fixes:

- Provide `project_dir` or `ProjectConfiguration(logging_dir=...)` for trackers with `requires_logging_directory=True`, especially TensorBoard and Aim.
- Install only the optional tracker package you intend to use, and configure credentials or offline/local mode before `init_trackers()`.
- Prefer explicit `log_with="tensorboard"` or `log_with=[...]` over `log_with="all"` in reproducible training scripts.
- For tests or credential-free smoke checks, use a custom local `GeneralTracker` writing JSONL/CSV.
- Pass tracker-specific init kwargs as `init_kwargs={"tracker_name": {...}}`, not as top-level kwargs to `init_trackers()`.

## Tracker Logging Produces No Records

Symptoms:

- Metrics file exists but has no scalar values.
- Direct tracker operations work on one rank but crash on others.
- `get_tracker(name)` raises that the tracker is not available.

Fixes:

- Call `accelerator.init_trackers(project_name, config=...)` before `accelerator.log()`.
- Ensure `name` matches the tracker `.name`, for example `"comet_ml"`, not `"comet"`.
- Call `accelerator.end_training()` so trackers flush and close.
- Convert tensors to Python scalars for broad tracker compatibility: `float(loss.detach())`.
- When using `get_tracker(..., unwrap=True)`, guard service-specific calls with `if accelerator.is_main_process:` unless the service is known to handle multiprocess calls.
- If using a custom tracker, implement `start()`, `tracker`, `store_init_configuration()`, `log()`, and `finish()` as needed; include `**kwargs` if `log_kwargs` may be passed.

## Distributed Logging Hangs or Is Too Noisy

Symptoms:

- Logging call hangs in distributed runs.
- Every process prints duplicate messages.
- `RuntimeError` says Accelerate state must be initialized before using logging utility.

Fixes:

- Create `Accelerator()` or `PartialState()` before the first `get_logger(...).info(...)` call.
- Use default `main_process_only=True` for normal progress logs.
- Use `main_process_only=False` only when every rank's message is needed.
- Use `in_order=True` sparingly; every rank must execute the same ordered log call because it inserts barriers.
- Prefer `accelerator.print()` for simple main-process-only console output.

## Profiler Output Missing or Too Large

Symptoms:

- No Chrome traces are written.
- `prof.step()` schedule never emits records.
- Profiling makes training extremely slow or creates huge files.

Fixes:

- Set `ProfileKwargs(output_trace_dir="trace_dir")` or use an `on_trace_ready` callback that exports traces.
- For scheduled profiling, call `prof.step()` once per loop iteration inside `with accelerator.profile() as prof:`.
- Keep `record_shapes`, `profile_memory`, `with_stack`, and `with_modules` off unless needed; they increase overhead.
- Use short schedules such as `wait=1, warmup=1, active=2, repeat=1` for long-running jobs.
- Match `activities` to available hardware; use `activities=["cpu"]` for portable smoke tests.

## Memory Cleanup After Failed Runs

Symptoms:

- A second experiment in the same Python process uses stale Accelerator objects.
- Device memory remains high after a failed profile/checkpoint run.
- Batch-size retry keeps failing with the same allocation state.

Fixes:

- Reassign objects returned by `accelerator.clear(...)` or `accelerator.free_memory(...)`.
- Use `release_memory(...)` for non-Accelerator references.
- Call `clear_device_cache(garbage_collection=True)` after large failed experiments, not in the hot path.
- For OOM-prone training functions, wrap a function whose first argument is `batch_size` with `find_executable_batch_size()`; unrelated exceptions are re-raised.
