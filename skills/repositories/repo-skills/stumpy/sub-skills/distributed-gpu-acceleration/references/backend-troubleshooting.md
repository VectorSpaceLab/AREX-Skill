# Backend troubleshooting

Use this guide when accelerated STUMPY execution fails before the algorithm result can be interpreted. Route data-shape, window-size, matrix-profile semantics, motif/discord/segmentation meaning, and pan-profile choices to the owner sub-skills.

## 1. Missing Dask or Distributed

Symptoms:

- `ModuleNotFoundError: No module named 'dask'`
- `ModuleNotFoundError: No module named 'distributed'`
- `ImportError` from `from dask.distributed import Client, LocalCluster`

Actions:

1. Install both Dask and Distributed in the active environment. Installing only part of the stack is a common cause of failure.
2. Re-run:
   ```bash
   python scripts/check_acceleration.py --check dask
   ```
3. If installation is not allowed, fall back to the CPU API selected by the owner sub-skill.

Do not classify missing Dask as a STUMPY algorithm failure; it is a backend dependency failure.

## 2. Dask LocalCluster port and process issues

### Dashboard port conflict

Symptoms:

- Warning about port `8787` already in use.
- LocalCluster starts but logs noisy dashboard warnings.

Actions:

- For smoke jobs and automation, set `dashboard_address=None` and `worker_dashboard_address=None`.
- If a dashboard is desired, provide an explicit free port or let Dask choose one.

### Worker process spawning or import recursion

Symptoms:

- LocalCluster hangs when `processes=True`.
- Repeated script execution inside worker subprocesses.
- Platform-specific multiprocessing errors.

Actions:

- Put Dask startup under `if __name__ == "__main__":`.
- For small diagnostics, set `processes=False` to use thread workers.
- Avoid defining large non-picklable objects in local scopes that workers must receive.

### Workers start but STUMPY call fails

Symptoms:

- Worker lost/restarted messages.
- Serialization or memory errors.
- `client.wait_for_workers(...)` timeout.

Actions:

1. Reduce `n_workers` and `threads_per_worker`.
2. Close existing unmanaged clients/clusters from the same process.
3. Verify that all workers run the same Python environment and can import `stumpy`, `numpy`, and `numba`.
4. Run the tiny bundled Dask probe before retrying the larger user workflow.

## 3. Unrecognized distributed client

Symptoms:

- `NotImplementedError: Distributed client ... is unrecognized or has yet to be implemented`

Cause:

- STUMPY dispatches by client type. It accepts Dask `Client` objects and the imported `ray` module. Other objects are not recognized.

Actions:

- For Dask, pass `Client(...)`, not a `LocalCluster`, scheduler address string, or cluster object.
- For Ray, pass the `ray` module after `ray.init()`, not a custom wrapper.

Correct Dask shape:

```python
with LocalCluster(dashboard_address=None) as cluster:
    with Client(cluster) as client:
        out = stumpy.stumped(client, T, m)
```

Correct Ray shape:

```python
import ray
ray.init()
try:
    out = stumpy.stumped(ray, T, m)
finally:
    ray.shutdown()
```

## 4. Ray optional/experimental warnings

Symptoms:

- Warning text similar to `Ray support is experimental and may be removed in the future. Use at your own risk!`
- Exception that a Ray cluster could not be found.
- `ImportError` for `ray`.

Actions:

1. Treat the warning as expected; mention it in run notes if Ray was user-requested.
2. Ensure `ray.init()` completed before calling STUMPY.
3. Always call `ray.shutdown()` in cleanup.
4. If Ray is not required, switch to Dask. Dask is the default verified distributed backend for this skill scope.

## 5. CUDA driver not found or `CudaSupportError`

Symptoms:

- `numba.cuda.cudadrv.error.CudaSupportError`
- Driver-not-found messages when calling `stumpy.gpu_stump` or another `gpu_*` API.
- GPU functions inspect as `(*args, **kwargs)`.

Cause:

- STUMPY exposes top-level `gpu_*` names even when CUDA is unavailable, but they are driver-not-found placeholders. Calling them intentionally raises a CUDA driver error.

Actions:

1. Run:
   ```bash
   python scripts/check_acceleration.py --check cuda
   ```
2. If `numba.cuda.is_available()` is false and CUDA is optional, use CPU/Dask fallback and state that GPU was not verified.
3. If CUDA is required, stop and report the probe output. Do not run native GPU tests or call `gpu_*` functions until Numba CUDA availability is true.
4. Re-import STUMPY after fixing CUDA. STUMPY decides whether to lazy-load real GPU implementations at import time.

## 6. `nvidia-smi` sees GPUs but Numba CUDA is unavailable

Symptoms:

- `nvidia-smi` lists GPUs.
- `numba.cuda.is_available()` is false.
- `numba.cuda.list_devices()` may still show device-like entries or may raise a driver/runtime error.

Interpretation:

- `nvidia-smi` proves the host driver can see hardware; it does not prove that the Python process, container, scheduler job, Numba runtime, and CUDA driver libraries are usable by STUMPY.

Actions:

1. Treat `numba.cuda.is_available()` as the gate for STUMPY GPU calls.
2. Check whether the process has GPU access under the current container/job allocation.
3. Check `CUDA_VISIBLE_DEVICES`; it may hide all GPUs or remap device IDs.
4. Check CUDA driver/runtime compatibility with the installed Numba version.
5. Check library path variables if the CUDA driver library is not discoverable.
6. After changes, start a fresh Python process and re-run the CUDA probe.

Do not claim GPU verification from visible `nvidia-smi` output alone.

## 7. `device_id` selection failures

Symptoms:

- Invalid device ordinal.
- STUMPY/Numba errors after passing a device list.
- Multi-GPU jobs use an unexpected physical GPU.

Actions:

1. In the same Python process, after `cuda.is_available()` is true, collect visible IDs:
   ```python
   from numba import cuda
   device_ids = [device.id for device in cuda.list_devices()]
   ```
2. Use `device_id=0` for the first visible GPU or `device_id=device_ids` for all visible GPUs.
3. Remember that `CUDA_VISIBLE_DEVICES` remaps host GPU IDs. Inside the process, the first visible GPU is usually `0`.
4. Do not reuse IDs printed by another shell, container, user session, or scheduler allocation.
5. For debugging, try a single visible device before a list.

## 8. CPU import is not GPU verification

The following are **not** sufficient evidence of GPU execution:

- `import stumpy` succeeds.
- `hasattr(stumpy, "gpu_stump")` is true.
- `inspect.signature(stumpy.gpu_stump)` returns a callable signature or `(*args, **kwargs)`.
- `nvidia-smi` lists GPUs.
- A CPU/Dask STUMPY computation succeeds.

Acceptable minimum evidence for GPU readiness:

- `numba.cuda.is_available()` is true in the target runtime.
- `numba.cuda.list_devices()` returns the intended visible devices.
- A deliberately selected tiny GPU STUMPY call runs only when the user has requested GPU verification and hardware is available.

This sub-skill's bundled script intentionally does not run native GPU tests. It only reports CUDA availability and device count, and it fails on CUDA absence only with `--require-cuda`.

## 9. Data and algorithm errors that are not backend errors

If the backend is healthy but STUMPY raises about these topics, route elsewhere:

- integer dtype or object dtype input,
- invalid window size,
- self-join vs AB-join `ignore_trivial`,
- NaN/inf/constant subsequence semantics,
- multidimensional row/column orientation,
- motif/discord/segmentation interpretation,
- streaming/pan update count or window range.

Keep this sub-skill focused on Dask/Ray/CUDA mechanics and fallback behavior.
