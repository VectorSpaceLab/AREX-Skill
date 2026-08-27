# Distributed, Device, and Utility Workflows

Use this reference for MMEngine utilities that are safe outside full Runner workflows: distributed rank helpers, device selection, environment reports, progress bars, timers, manager mixins, and testing helpers.

## Distributed Utility Rules

MMEngine distributed helpers intentionally degrade to single-process behavior when `torch.distributed` is unavailable or uninitialized.

| Need | API | Non-distributed behavior | Distributed behavior |
| --- | --- | --- | --- |
| Detect initialization | `mmengine.dist.is_distributed()` | `False` | `True` after a process group is initialized. |
| Get rank/world size | `get_dist_info()` | `(0, 1)` | Actual rank and world size for the process group. |
| Main-process check | `is_main_process()` | `True` | `True` only on rank 0. |
| Main-rank side effect | `@master_only` | Runs normally | Runs only on rank 0 and returns `None` on other ranks. |
| Synchronize | `barrier()` | No-op | Blocks until all ranks arrive. |
| Collect outputs | `collect_results(results, size, device='cpu', tmpdir=None)` | Returns `results[:size]` | Returns ordered list on rank 0 and `None` on other ranks. |

Do not call `init_dist` casually in a library helper. It expects launch-specific environment variables for `pytorch`, `mpi`, or `slurm` launchers and may set device state. Initialize distribution at an application or Runner entry point only.

## Distributed-Safe Result Collection

For helper code that should work with and without distributed launch:

```python
from mmengine.dist import collect_results, get_dist_info

rank, world_size = get_dist_info()
parts = local_predictions
collected = collect_results(parts, size=dataset_size, device='cpu')
if rank == 0:
    consume(collected)
```

Guidelines:

- Keep collected items picklable.
- Use `device='cpu'` when portability matters; it may use a temporary directory in distributed mode.
- Use `device='gpu'` or `device='npu'` only when the process group/device backend supports it, and keep `tmpdir=None` for those modes.
- Always handle `None` on non-main ranks after collection.
- When passing `tmpdir`, ensure all ranks can access the same path and the path is disposable.

## Device Utilities

`mmengine.device.get_device()` returns the first available device type from MMEngine's priority order: `npu`, `cuda`, `mlu`, `mps`, `dipu`, `musa`, then `cpu`.

Use it for coarse routing and diagnostics, not as a substitute for tensor placement validation. For user-facing code, still allow explicit device overrides such as `device='cpu'` when reproducibility or unsupported accelerators matter.

Useful device helpers include:

- `is_cuda_available()` for CUDA checks.
- `is_npu_available()`, `is_mlu_available()`, `is_mps_available()`, `is_dipu_available()`, and `is_musa_available()` for optional accelerator checks.
- `get_max_cuda_memory()` and `get_max_musa_memory()` for backend-specific peak-memory summaries after tensors have been allocated.

## Environment Collection

Use `mmengine.utils.dl_utils.collect_env()` to collect a dictionary of runtime environment facts such as platform, Python, CUDA/PyTorch details, and optional package states. This is a diagnostic helper; it may include warnings or `not found` values for optional packages and should not be treated as failure by itself.

A safe environment-report pattern:

```python
from mmengine.utils.dl_utils import collect_env

env = collect_env()
for key in ('sys.platform', 'Python', 'PyTorch', 'MMEngine'):
    print(f'{key}: {env.get(key)}')
```

Avoid embedding machine-specific environment output into public skill files or reusable documentation. Share only the keys relevant to the user's debugging session.

## ManagerMixin Behavior

`ManagerMixin` powers global named instances such as `MMLogger`, `MessageHub`, and `Visualizer`.

- Subclasses must have a non-empty string `name` argument.
- `get_instance(name, **kwargs)` creates once per name and returns the existing object thereafter.
- Passing different kwargs for an existing name warns and does not reconfigure the existing instance.
- `get_current_instance()` returns the latest created instance and raises if no instance exists, except `MessageHub.get_current_instance()` creates a default `mmengine` hub.
- `check_instance_created(name)` is useful before deciding whether to create or reuse a shared object.

When tests or notebooks create many named objects, clear class `_instance_dict` only in test teardown or controlled cleanup code; do not clear global managers in library runtime paths.

## Timers, Progress, and Randomness

Use MMEngine progress helpers for lightweight scripts and diagnostics:

- `Timer()` measures elapsed time; `since_start()` and `since_last_check()` require the timer to be running.
- `with Timer(print_tmpl='elapsed {:.3f}s'):` prints elapsed time when the block exits.
- `check_time(timer_id)` keeps named global timers and returns zero on first call.
- `ProgressBar(task_num)` prints progress to stdout or a file-like object.
- `track_progress(func, tasks)` applies a function sequentially and returns results.
- `track_parallel_progress(func, tasks, nproc=...)` uses multiprocessing; avoid it for unpicklable functions or interactive notebook state.
- `track_iter_progress(tasks)` yields items while updating a progress bar.
- `mmengine.runner.set_random_seed(seed=None, deterministic=False, diff_rank_seed=False)` sets Python, NumPy, torch, and accelerator seeds; when `seed=None`, MMEngine synchronizes a generated seed across ranks.

For quiet automation, pass a file-like object or avoid progress helpers when stdout must stay machine-readable. For full Runner `randomness=dict(...)` configuration, use `../runner-and-training/SKILL.md`.

## Testing Helpers

MMEngine exposes small helpers under `mmengine.testing` for package tests and examples:

- `assert_allclose(actual, expected, rtol=None, atol=None, equal_nan=True, msg='')` wraps torch's allclose assertions across supported versions.
- `assert_dict_contains_subset`, `assert_attrs_equal`, `assert_dict_has_keys`, and `assert_keys_equal` provide lightweight structural checks.
- `assert_is_norm_layer` and `assert_params_all_zeros` support model initialization tests.
- `check_python_script(cmd)` runs a Python script in-process with patched `sys.argv`; use it only for trusted scripts because it executes code in the current process.
- `RunnerTestCase` provides toy Runner fixtures for MMEngine's own tests; prefer distilled tiny examples in user skills rather than depending on internal test files.

## Cross-Links

- Use `../runner-and-training/SKILL.md` for configuring distributed launch through Runner, log processors, and hooks.
- Use `../models-metrics-and-inference/SKILL.md` for model analysis utilities and evaluator collection semantics.
- Use `../data-structures-and-io/SKILL.md` for filesystem backend choices and serialized data loading/dumping.
