---
name: distributed-gpu-acceleration
description: "Use STUMPY Dask/Ray distributed clients and optional CUDA GPU APIs
  safely, with backend checks, client lifecycle guidance, device selection, and
  fallback routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# STUMPY distributed and GPU acceleration

Use this sub-skill when a STUMPY task asks for Dask, Ray, CUDA, GPU-STUMP, multi-GPU execution, backend diagnostics, or conversion of an existing STUMPY workflow to an accelerated variant.

Do **not** use this sub-skill to decide which matrix-profile algorithm is appropriate, interpret motifs/discords/segments, choose multidimensional subspaces, or design streaming/pan analysis. Route those decisions to the owner sub-skills first, then return here only for acceleration mechanics.

## Fast routing

- **Dask distributed, verified in the prepared environment:** use a `dask.distributed.Client` as the first argument to `stumped`, `aamped`, `mstumped`, `maamped`, `mpdisted`, `aampdisted`, `ostinatoed`, `aamp_ostinatoed`, `stimped`, or `aamp_stimped`.
- **Ray distributed, optional/experimental:** pass the imported `ray` module after `ray.init()`. Expect an experimental-support warning and always `ray.shutdown()` in cleanup.
- **CUDA GPU, optional/unverified unless `numba.cuda.is_available()` is true in the target runtime:** use `gpu_stump`, `gpu_aamp`, `gpu_mpdist`, `gpu_aampdist`, `gpu_ostinato`, `gpu_aamp_ostinato`, `gpu_stimp`, or `gpu_aamp_stimp` with `device_id=0` or a list of visible device IDs.
- **Safe fallback:** if Dask/Ray/CUDA prerequisites are absent, fall back to the equivalent CPU owner API (`stump`, `aamp`, `mstump`, `maamp`, `mpdist`, `ostinato`, `stimp`, `aamp_stimp`) and state that acceleration was not verified.

## Operating rules

1. Run the bundled backend probe before claiming acceleration support:
   ```bash
   python scripts/check_acceleration.py --check all
   ```
   Add `--require-cuda` only when the user explicitly requires CUDA execution.
2. Own the client lifecycle. Prefer context managers for Dask `LocalCluster`/`Client`; use `try/finally` for Ray `init()`/`shutdown()`.
3. Preserve algorithm parameters from the owner workflow. Acceleration normally inserts `client` first for distributed APIs or `device_id` for GPU APIs; it does not change window size, normalization, `ignore_trivial`, `percentage`, `k`, `include`, or `discords` decisions.
4. Never claim GPU verification from `import stumpy` or from CPU-only signatures. In a CUDA-unavailable runtime, STUMPY exposes GPU names as driver-not-found placeholders that may inspect as `(*args, **kwargs)` and raise a CUDA driver error when called.
5. Avoid unmanaged global Dask clients in reusable code. Use `dashboard_address=None` for smoke checks to avoid dashboard port conflicts unless the user needs the dashboard.

## Reference map

- `references/api-reference.md` — accelerated API signatures, return shapes, normalized/non-normalized routing, `client`, and `device_id` notes.
- `references/workflows.md` — Dask LocalCluster, Ray, CUDA, multi-GPU, and fallback workflow templates.
- `references/backend-troubleshooting.md` — dependency, LocalCluster, Ray, CUDA driver/Numba, `nvidia-smi`, and device-selection failures.
- `scripts/check_acceleration.py` — deterministic backend smoke script with tiny synthetic Dask data and non-failing CUDA availability reporting.
