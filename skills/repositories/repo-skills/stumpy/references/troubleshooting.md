# STUMPY Cross-cutting Troubleshooting

Use this for install/import/backend/data issues before entering a workflow-specific sub-skill.

## Import or version problems

**Symptoms:** `ModuleNotFoundError: stumpy`, unexpected `stumpy.__version__`, or old signatures.  
**Recovery:**

```bash
python -m pip install -U stumpy
python - <<'PY'
from importlib.metadata import version
import stumpy
print(version('stumpy'))
print(stumpy.__file__)
PY
```

Use distribution metadata (`importlib.metadata.version('stumpy')`) when editable/source installs report an unusual module `__version__` string.

## Numba first-call latency

**Symptom:** a tiny first call seems slow.  
**Likely cause:** Numba compiles kernels the first time a function is called in a process.  
**Recovery:** run a tiny warm-up before benchmarking; do not time the first call as steady-state performance.

## Numeric dtype and shape issues

**Symptoms:** `TypeError`, invalid output, or confusing profile shape.  
**Recovery:**

- Convert arrays to `np.float64`.
- Validate `m >= 3` and `m <= len(series)` for 1-D profiles.
- For multidimensional profiles, ensure `T.shape == (dimensions, time)`, not `(time, dimensions)`.
- Cast profile distance columns to float before `np.isfinite`, `argmin`, or `argmax`.

## Missing optional dependencies

- Dask workflows need `dask` and `distributed`.
- Ray workflows need `ray` and are optional/experimental; prefer Dask unless Ray is requested.
- Pandas/polars inputs need their respective packages.
- Plotting/tutorial reproduction may need packages beyond STUMPY; the bundled skill scripts avoid plotting and remote datasets.

Use:

```bash
python scripts/stumpy_check_env.py --check dask
```

## CUDA/GPU failures

**Symptoms:** `CudaSupportError`, driver-not-found functions, GPU APIs show generic `(*args, **kwargs)` signatures, or `numba.cuda.is_available()` is false.  
**Recovery:**

1. Run `python scripts/stumpy_check_env.py --check cuda`.
2. Require `numba.cuda.is_available()` in the target runtime before using `gpu_*` APIs.
3. If `nvidia-smi` sees devices but Numba cannot, check container GPU passthrough, driver/runtime compatibility, Numba CUDA support, and environment libraries.
4. Fall back to CPU or Dask unless the user explicitly requires GPU execution.

## Join-type mistakes

- Self-join: one series, `ignore_trivial=True`.
- AB-join: two series, `ignore_trivial=False`.

A common failure is passing two identical arrays as an AB-join and expecting self-join exclusion behavior.

## Distance-model mismatch

If motifs or matches look wrong, check whether the workflow mixed normalized and non-normalized APIs. Normalized workflows compare shape after z-normalization. Non-normalized workflows preserve amplitude and offset differences.

## Workflow-specific references

- Exact 1-D profile errors: `sub-skills/matrix-profile-basics/references/troubleshooting.md`.
- Multidimensional shape/subspace errors: `sub-skills/multidimensional-profiles/references/troubleshooting.md`.
- Motif/match/segmentation errors: `sub-skills/motifs-anomalies-segmentation/references/troubleshooting.md`.
- Approximate/streaming/pan errors: `sub-skills/approximate-streaming-pan/references/troubleshooting.md`.
- Dask/Ray/CUDA errors: `sub-skills/distributed-gpu-acceleration/references/backend-troubleshooting.md`.
