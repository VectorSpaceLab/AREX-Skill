# Runtime Utilities and Visualization Troubleshooting

Use this symptom map when MMEngine logging, visualizers, optional backends, distributed utilities, device detection, or testing helpers behave unexpectedly.

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `MMLogger.get_instance` ignores new `log_file` or `log_level` kwargs | A logger with the same `name` already exists through `ManagerMixin`. | Reuse the existing configuration, choose a new instance name, or reset only in controlled test teardown. |
| Duplicate or missing log lines | Multiple logger instances/handlers, rank filtering, or nonzero distributed ranks emitting only errors. | Use one stable `MMLogger` instance name, inspect rank with `get_dist_info`, and avoid manually adding handlers unless needed. |
| Warning appears only once | MMEngine logger filters duplicate warning messages. | Log distinct warning text for distinct problems or use a separate logger if repeated diagnostics are required. |
| `print_log(..., logger='current')` does not use the expected logger | The current logger is the latest manager-created logger, or none was created before the call. | Create the intended `MMLogger.get_instance(...)` first or pass the logger object/name explicitly. |
| `MessageHub.update_scalar` asserts about `resumed` | The same key was previously created with a different `resumed` flag. | Pick a resume policy per key and keep it consistent for all updates. |
| `MessageHub.get_scalar` raises `KeyError` | The scalar key has never been updated in that hub. | Call `update_scalar(s)` before reading or use `get_info(..., default=...)` for runtime metadata. |
| Visualizer produces no local files | `save_dir` is `None`, no backend is configured, or write methods are skipped on non-main rank. | Configure `vis_backends=[dict(type='LocalVisBackend')]`, set a writable `save_dir`, and check `get_dist_info()`. |
| Local visual output appears under an unexpected nested directory | `Visualizer(save_dir=...)` passes `save_dir/vis_data` to backends, and `LocalVisBackend` adds files such as `vis_image/` and `scalars.json`. | Look under the `vis_data` child directory or instantiate `LocalVisBackend` directly when exact paths matter. |
| `LocalVisBackend.add_image` raises an assertion | Image dtype is not `np.uint8`. | Convert or clip image arrays to RGB `uint8` before logging: `image.astype('uint8')` only after ensuring values are in `0..255`. |
| Saved image colors look swapped | MMEngine treats input arrays as RGB and converts to BGR for OpenCV PNG writing. | Feed RGB arrays to visualizer APIs; convert BGR camera/OpenCV inputs to RGB before `add_image`. |
| `Visualizer.add_datasample` does nothing | Base MMEngine `Visualizer.add_datasample` is a placeholder. | Use a downstream library visualizer subclass for task-specific samples, or call generic drawing methods plus `add_image`. |
| Optional backend import fails | Service package such as `wandb`, `mlflow`, `clearml`, `aim`, `dvclive`, or `neptune` is not installed. | Fall back to `LocalVisBackend` or TensorBoard, or install/configure the requested service outside this skill. |
| Optional service backend hangs or prompts for login | Backend initializes lazily on first `add_*` or `experiment` access and needs credentials/network or offline configuration. | Prefer local fallback for automated checks; if service logging is required, set explicit offline/local credentials and init kwargs. |
| TensorBoard backend import fails | TensorBoard support is unavailable in the current PyTorch environment. | Install TensorBoard support or use `LocalVisBackend` for scalar/image files. |
| `init_dist` fails with missing env vars | The process was not launched with PyTorch, MPI, or Slurm environment variables. | Do not call `init_dist` in single-process scripts; use Runner/torch launch or keep code guarded by `get_dist_info`. |
| `get_dist_info()` returns `(0, 1)` unexpectedly | `torch.distributed` is not initialized. | Confirm the program was launched as distributed and that `init_dist` or Runner distributed setup ran before the check. |
| Function decorated with `master_only` returns `None` | Current rank is not main process. | Treat `None` as expected on nonzero ranks and only consume returned values on rank 0. |
| `collect_results` returns `None` | In distributed mode, only rank 0 receives the collected result. | Branch on `rank == 0` before using the collected list. |
| `collect_results(..., device='gpu', tmpdir=...)` asserts | GPU/NPU collection does not accept `tmpdir`. | Use `tmpdir=None` for GPU/NPU collection or switch to `device='cpu'` for filesystem-backed collection. |
| CPU result collection cannot find shared files | The chosen temporary directory is not visible to every rank or is cleaned too early. | Use a shared, disposable directory for all ranks or leave `tmpdir=None` and let MMEngine coordinate. |
| `get_device()` returns an unexpected accelerator or `cpu` | MMEngine uses availability probes and a fixed priority order; optional backend packages may or may not be importable. | Treat `get_device()` as diagnostic and allow explicit user device overrides. |
| `collect_env()` reports optional package warnings or missing packages | Environment collection probes optional dependencies. | Report only relevant missing packages; do not fail a local workflow solely because an optional service is absent. |
| `Timer.since_start()` raises `TimerError` | The timer is not running. | Create with `Timer(start=True)` or call `start()` before measuring. |
| Progress output corrupts JSON/log streams | Progress bars write carriage returns to stdout by default. | Send progress to a separate file-like object or disable progress output in machine-readable commands. |
| `check_python_script` has surprising side effects | It runs the target script in the current process with patched `sys.argv`. | Use it only for trusted scripts and prefer subprocesses for isolation. |
| Tests leak logger/visualizer state | ManagerMixin global instance dictionaries persist between tests. | In test teardown, close/logging shutdown and clear relevant `_instance_dict` values only for test isolation. |

## Safe Fallback Recipe

When a visualization request mentions a service backend but the environment lacks packages or credentials, use this policy:

1. Preserve the user's desired metric/image/config names and step values.
2. Configure `LocalVisBackend` with a user-approved disposable `save_dir`.
3. If TensorBoard is installed and acceptable, add `TensorboardVisBackend` as a second local backend.
4. Record service backend requirements as optional follow-up work instead of blocking local artifact generation.
5. Never create credentials, start network uploads, or mutate service state without explicit user instruction.

## Distributed-Safe Output Recipe

For utilities that may run under both single-process and distributed launches:

1. Start with `rank, world_size = get_dist_info()`.
2. Emit user-visible logs and file writes only when `rank == 0` or through `MMLogger`/`Visualizer` methods that already apply rank rules.
3. Use `collect_results` for ordered result gathering and consume the return only on rank 0.
4. Keep temporary collection paths shared and disposable, and use `device='cpu'` unless a GPU/NPU collective is required.
5. Make non-distributed behavior explicit in tests: expect rank 0, world size 1, and immediate local returns.
