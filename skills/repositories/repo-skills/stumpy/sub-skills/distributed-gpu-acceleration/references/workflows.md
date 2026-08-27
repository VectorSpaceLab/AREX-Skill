# Distributed and GPU workflows

These workflows assume the analysis owner sub-skill has already selected the algorithm, data layout, window sizes, and interpretation. This sub-skill only swaps the execution backend and verifies backend availability.

## 1. Backend-first decision tree

1. **Need distributed CPU execution and `dask.distributed` is available:** use Dask first. It is the verified distributed backend for this skill scope.
2. **User explicitly requests Ray or already owns a Ray runtime:** Ray can be used, but mark it optional/experimental and add cleanup.
3. **User explicitly requests CUDA or large single-node acceleration and `numba.cuda.is_available()` is true:** use the `gpu_*` API with a checked `device_id`.
4. **Backend is missing or unverified:** keep the owner CPU API and say exactly which acceleration backend was unavailable.

Run a safe probe from this sub-skill directory:

```bash
python scripts/check_acceleration.py --check all
```

If the user's acceptance requires CUDA, use:

```bash
python scripts/check_acceleration.py --check cuda --require-cuda
```

## 2. Dask LocalCluster smoke and lifecycle

Use this pattern for local Dask work and examples. It avoids dashboard port conflicts and closes resources deterministically.

```python
import numpy as np
import stumpy
from dask.distributed import Client, LocalCluster


def main():
    T = np.array([0.0, 1.0, 0.0, 2.0, 0.0, 1.0, 0.0, 2.0], dtype=np.float64)
    m = 3

    cluster = LocalCluster(
        n_workers=2,
        threads_per_worker=1,
        processes=False,            # set True only when process workers are needed
        dashboard_address=None,     # avoids port 8787 warnings in smoke jobs
        worker_dashboard_address=None,
    )
    try:
        with Client(cluster) as client:
            client.wait_for_workers(2)
            mp = stumpy.stumped(client, T, m=m)
            print(mp.P_.shape, mp.I_.shape)
    finally:
        cluster.close(timeout=60)


if __name__ == "__main__":
    main()
```

### Converting CPU calls to Dask calls

| CPU call shape | Dask call shape | Notes |
| --- | --- | --- |
| `stumpy.stump(T, m, ...)` | `stumpy.stumped(client, T, m, ...)` | For AB-joins, preserve `T_B` and `ignore_trivial=False`. |
| `stumpy.aamp(T, m, ...)` | `stumpy.aamped(client, T, m, ...)` | Non-normalized; preserve `p` and `k`. |
| `stumpy.mstump(T, m, ...)` | `stumpy.mstumped(client, T, m, ...)` | `T` is multidimensional with rows as dimensions; only self-join. |
| `stumpy.maamp(T, m, ...)` | `stumpy.maamped(client, T, m, ...)` | Non-normalized multidimensional self-join. |
| `stumpy.mpdist(T_A, T_B, m, ...)` | `stumpy.mpdisted(client, T_A, T_B, m, ...)` | Scalar distance; preserve `percentage` or `k`. |
| `stumpy.aampdist(T_A, T_B, m, ...)` | `stumpy.aampdisted(client, T_A, T_B, m, ...)` | Non-normalized scalar distance. |
| `stumpy.ostinato(Ts, m, ...)` | `stumpy.ostinatoed(client, Ts, m, ...)` | `Ts` is a list of time series. |
| `stumpy.aamp_ostinato(Ts, m, ...)` | `stumpy.aamp_ostinatoed(client, Ts, m, ...)` | Non-normalized consensus motif. |
| `stumpy.stimp(T, ...)` | `stumpy.stimped(client, T, ...)` | Returns an object; call `.update()` before reading the pan profile. |
| `stumpy.aamp_stimp(T, ...)` | `stumpy.aamp_stimped(client, T, ...)` | Non-normalized pan profile object. |

### Dask pan matrix profile loop

`stimped` and `aamp_stimped` return stateful objects. The accelerated part happens during `.update()` calls.

```python
import numpy as np
import stumpy
from dask.distributed import Client, LocalCluster

T = np.array([584.0, -11.0, 23.0, 79.0, 1001.0, 0.0, -19.0], dtype=np.float64)

with LocalCluster(n_workers=2, threads_per_worker=1, processes=False,
                  dashboard_address=None, worker_dashboard_address=None) as cluster:
    with Client(cluster) as client:
        pan = stumpy.stimped(client, T, min_m=3, max_m=4, step=1)
        for _ in range(len(pan.M_)):
            pan.update()
        transformed = pan.PAN_
        windows = pan.M_
```

Route window-size selection, pan interpretation, and update-count decisions back to the approximate/streaming/pan owner sub-skill.

## 3. Ray optional workflow

Ray support is optional and experimental. Use it only when requested or when an existing runtime is already Ray-based. STUMPY expects the imported `ray` module as the `client` argument.

```python
import numpy as np
import stumpy
import ray

T = np.array([584.0, -11.0, 23.0, 79.0, 1001.0, 0.0, -19.0], dtype=np.float64)

ray.init(ignore_reinit_error=True)
try:
    mp = stumpy.stumped(ray, T, m=3)
    print(mp.P_.shape)
finally:
    if ray.is_initialized():
        ray.shutdown()
```

Ray caveats:

- A missing `ray` package is not a blocking failure for this skill unless the user requires Ray.
- If `ray.is_initialized()` is false, STUMPY raises an exception before scheduling work.
- Future STUMPY versions may alter or remove Ray support; keep Dask as the default distributed route.

## 4. CUDA availability and GPU workflow

Use `numba.cuda.is_available()` as the operational gate. A host can show GPUs through `nvidia-smi` while Numba still reports unavailable; in that case do not call STUMPY GPU APIs.

```python
import numpy as np
import stumpy
from numba import cuda

T = np.array([0.0, 1.0, 0.0, 2.0, 0.0, 1.0, 0.0, 2.0], dtype=np.float64)
m = 3

if cuda.is_available():
    device_ids = [device.id for device in cuda.list_devices()]
    device_id = device_ids if device_ids else 0
    mp = stumpy.gpu_stump(T, m=m, device_id=device_id)
    print(mp.P_.shape)
else:
    # Safe fallback: use CPU or Dask and report that CUDA was unavailable.
    mp = stumpy.stump(T, m=m)
    print("CUDA unavailable; used CPU STUMP", mp.P_.shape)
```

### GPU API substitutions

| CPU owner API | GPU API | Notes |
| --- | --- | --- |
| `stump` | `gpu_stump` | 1-D normalized self-join/AB-join; supports `k` and `device_id`. |
| `aamp` | `gpu_aamp` | 1-D non-normalized self-join/AB-join; supports `p`, `k`, and `device_id`. |
| `mpdist` | `gpu_mpdist` | Scalar MPdist; `k` overrides `percentage`. |
| `aampdist` | `gpu_aampdist` | Non-normalized scalar MPdist. |
| `ostinato` | `gpu_ostinato` | Consensus motif across a list of series. |
| `aamp_ostinato` | `gpu_aamp_ostinato` | Non-normalized consensus motif. |
| `stimp` | `gpu_stimp` | Pan matrix profile object; call `.update()`. |
| `aamp_stimp` | `gpu_aamp_stimp` | Non-normalized pan matrix profile object; call `.update()`. |

There is no GPU multidimensional `mstump` replacement in this sub-skill scope. Use Dask `mstumped`/`maamped` for accelerated multidimensional profiles.

## 5. Safe fallback pattern

Use a fallback branch when acceleration is optional. Preserve the user-visible result type where possible.

```python
def compute_1d_profile(T, m, prefer_cuda=False, dask_client=None):
    import stumpy

    if prefer_cuda:
        try:
            from numba import cuda
            if cuda.is_available():
                ids = [device.id for device in cuda.list_devices()]
                return stumpy.gpu_stump(T, m=m, device_id=ids or 0), "cuda"
        except Exception as exc:
            cuda_reason = f"CUDA unavailable: {exc.__class__.__name__}: {exc}"
        else:
            cuda_reason = "CUDA unavailable: numba.cuda.is_available() is false"
    else:
        cuda_reason = "CUDA not requested"

    if dask_client is not None:
        return stumpy.stumped(dask_client, T, m=m), "dask"

    result = stumpy.stump(T, m=m)
    result._acceleration_note = cuda_reason  # optional application-side metadata
    return result, "cpu"
```

When the user requires a specific backend, do **not** silently fall back. Stop with the probe output and the troubleshooting route.

## 6. What to report after a run

For accelerated results, report:

- backend used (`dask`, `ray`, `cuda`, `cpu-fallback`),
- number of Dask workers/threads or CUDA `device_id` values,
- whether CUDA was required or optional,
- whether GPU execution was actually run, not merely imported,
- output shape/type and any owner-workflow interpretation routed elsewhere.
