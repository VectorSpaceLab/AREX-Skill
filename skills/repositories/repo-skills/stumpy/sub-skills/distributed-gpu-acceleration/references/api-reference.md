# Distributed and GPU API reference

This reference covers acceleration mechanics only. For choosing, interpreting, or validating the underlying time-series analysis, use the owner workflow sub-skill first and then map the selected CPU API to the accelerated form below.

## Backend support contract

- **Dask distributed:** required acceleration backend for this skill scope. A Dask `Client` object is accepted by STUMPY because its class name starts with `Client`.
- **Ray distributed:** optional and experimental. STUMPY accepts the imported `ray` module, not a Dask-like client object, and emits an experimental-support warning. Ray must be initialized before calling STUMPY.
- **CUDA GPU:** optional. STUMPY enables top-level GPU implementations only when `numba.cuda.is_available()` is true during import. If CUDA is unavailable, top-level `gpu_*` names are placeholders that raise a CUDA driver-not-found error when called; inspection may show `(*args, **kwargs)`.

## Distributed API map

All distributed functions place the distributed backend as the **first positional argument**. Keep the same data, window, normalization, and interpretation choices that the CPU workflow selected.

| Accelerated API | CPU owner equivalent | Signature | Main result |
| --- | --- | --- | --- |
| `stumpy.stumped` | `stumpy.stump` | `stumped(client, T_A, m, T_B=None, ignore_trivial=True, normalize=True, p=2.0, k=1, T_A_subseq_isconstant=None, T_B_subseq_isconstant=None)` | 1-D matrix profile array. Default `k=1` columns are profile, nearest index, left index, right index; named attributes include `.P_`, `.I_`, `.left_I_`, `.right_I_`. |
| `stumpy.aamped` | `stumpy.aamp` | `aamped(client, T_A, m, T_B=None, ignore_trivial=True, p=2.0, k=1)` | Non-normalized 1-D matrix profile with the same top-k column layout as `stumped`. |
| `stumpy.mstumped` | `stumpy.mstump` | `mstumped(client, T, m, include=None, discords=False, p=2.0, normalize=True, T_subseq_isconstant=None)` | Multidimensional profile `(P, I)` exposed as an mparray-like result; rows are motif dimensionality levels. Only self-joins are supported. |
| `stumpy.maamped` | `stumpy.maamp` | `maamped(client, T, m, include=None, discords=False, p=2.0)` | Non-normalized multidimensional profile `(P, I)`; rows are motif dimensionality levels. Only self-joins are supported. |
| `stumpy.mpdisted` | `stumpy.mpdist` | `mpdisted(client, T_A, T_B, m, percentage=0.05, k=None, normalize=True, p=2.0, T_A_subseq_isconstant=None, T_B_subseq_isconstant=None)` | Scalar MPdist between two series. `k` overrides `percentage`. |
| `stumpy.aampdisted` | `stumpy.aampdist` | `aampdisted(client, T_A, T_B, m, percentage=0.05, k=None, p=2.0)` | Non-normalized scalar MPdist between two series. |
| `stumpy.ostinatoed` | `stumpy.ostinato` | `ostinatoed(client, Ts, m, normalize=True, p=2.0, Ts_subseq_isconstant=None)` | Consensus motif tuple `(central_radius, central_Ts_idx, central_subseq_idx)`. |
| `stumpy.aamp_ostinatoed` | `stumpy.aamp_ostinato` | `aamp_ostinatoed(client, Ts, m, p=2.0)` | Non-normalized consensus motif tuple `(central_radius, central_Ts_idx, central_subseq_idx)`. |
| `stumpy.stimped` | `stumpy.stimp` | `stimped(client, T, min_m=3, max_m=None, step=1, normalize=True, p=2.0, T_subseq_isconstant_func=None)` | Pan matrix profile object. Call `.update()` repeatedly; read `.PAN_` and `.M_`. |
| `stumpy.aamp_stimped` | `stumpy.aamp_stimp` | `aamp_stimped(client, T, min_m=3, max_m=None, step=1, p=2.0)` | Non-normalized pan matrix profile object. Call `.update()` repeatedly; read `.PAN_` and `.M_`. |

### Normalization routing

- `stumped(..., normalize=False)` routes to `aamped`; prefer calling `aamped` directly when the user explicitly wants non-normalized distances.
- `mstumped(..., normalize=False)` routes to `maamped`.
- `mpdisted(..., normalize=False)` routes to `aampdisted`.
- `ostinatoed(..., normalize=False)` routes to `aamp_ostinatoed`.
- `stimped(..., normalize=False)` routes to `aamp_stimped`.
- The non-normalized APIs use the Minkowski `p` parameter; normalized APIs ignore `p` while `normalize=True`.

### Client requirements

- **Dask:** pass an active `dask.distributed.Client` instance. A `LocalCluster` can be created in the same process for small jobs, or the client can connect to an external scheduler. Close both client and cluster when done.
- **Ray:** pass the imported `ray` module after `ray.init()`. STUMPY checks `ray.is_initialized()` and warns that Ray support is experimental.
- **Unrecognized clients:** STUMPY raises `NotImplementedError` for objects that are neither Dask `Client` instances nor the imported `ray` module.

## CUDA GPU API map

Only call these APIs after `numba.cuda.is_available()` is true in the same runtime where STUMPY is imported. `device_id` may be a single integer or a list of visible integer device IDs.

| GPU API | CPU owner equivalent | Source signature | Main result |
| --- | --- | --- | --- |
| `stumpy.gpu_stump` | `stumpy.stump` | `gpu_stump(T_A, m, T_B=None, ignore_trivial=True, device_id=0, normalize=True, p=2.0, k=1, T_A_subseq_isconstant=None, T_B_subseq_isconstant=None)` | 1-D matrix profile array with the same top-k layout and named attributes as `stump`/`stumped`. |
| `stumpy.gpu_aamp` | `stumpy.aamp` | `gpu_aamp(T_A, m, T_B=None, ignore_trivial=True, device_id=0, p=2.0, k=1)` | Non-normalized 1-D matrix profile. |
| `stumpy.gpu_mpdist` | `stumpy.mpdist` | `gpu_mpdist(T_A, T_B, m, percentage=0.05, k=None, device_id=0, normalize=True, p=2.0, T_A_subseq_isconstant=None, T_B_subseq_isconstant=None)` | Scalar MPdist using GPU matrix profiles. |
| `stumpy.gpu_aampdist` | `stumpy.aampdist` | `gpu_aampdist(T_A, T_B, m, percentage=0.05, k=None, device_id=0, p=2.0)` | Non-normalized scalar MPdist using GPU matrix profiles. |
| `stumpy.gpu_ostinato` | `stumpy.ostinato` | `gpu_ostinato(Ts, m, device_id=0, normalize=True, p=2.0, Ts_subseq_isconstant=None)` | Consensus motif tuple `(central_radius, central_Ts_idx, central_subseq_idx)`. |
| `stumpy.gpu_aamp_ostinato` | `stumpy.aamp_ostinato` | `gpu_aamp_ostinato(Ts, m, device_id=0, p=2.0)` | Non-normalized consensus motif tuple. |
| `stumpy.gpu_stimp` | `stumpy.stimp` | `gpu_stimp(T, min_m=3, max_m=None, step=1, device_id=0, normalize=True, p=2.0, T_subseq_isconstant_func=None)` | Pan matrix profile object. Call `.update()` repeatedly; read `.PAN_` and `.M_`. |
| `stumpy.gpu_aamp_stimp` | `stumpy.aamp_stimp` | `gpu_aamp_stimp(T, min_m=3, max_m=None, step=1, device_id=0, p=2.0)` | Non-normalized pan matrix profile object. Call `.update()` repeatedly; read `.PAN_` and `.M_`. |

### `device_id` rules

- Default `device_id=0` uses the first CUDA device visible to Numba.
- Multi-GPU functions accept `device_id=[0, 1, ...]`. Build this list with `numba.cuda.list_devices()` only after CUDA availability is confirmed.
- `CUDA_VISIBLE_DEVICES` remaps IDs inside the process. If only one physical GPU is exposed, its visible ID is usually `0` even if the host labels it differently.
- Do not pass device IDs gathered from a different shell, container, scheduler job, or environment activation.

## API evidence summary

This reference was distilled from the public quick-start examples, the public API inventory, the distributed/GPU implementation modules, and distributed/GPU tests. The runtime instructions above are self-contained and do not require reading those sources.
