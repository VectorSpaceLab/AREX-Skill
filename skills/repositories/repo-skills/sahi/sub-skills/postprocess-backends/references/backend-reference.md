# Backend selection and acceleration limits

SAHI postprocessing dispatch is controlled by `sahi.postprocess.backends` and used by `sahi.postprocess.combine`. Treat the configured backend and the resolved backend as two different facts.

## Backend state model

| API | Meaning | Important nuance |
| --- | --- | --- |
| `set_postprocess_backend(name)` | Sets the process-global configured backend. Valid names are `"auto"`, `"numpy"`, `"numba"`, and `"torchvision"`. | Clears the dispatch cache. Call before inference loops; it is not designed as a thread-safe per-request switch. |
| `get_postprocess_backend()` | Returns the configured backend string. | If configured as `"auto"`, it returns `"auto"`; it does not tell you which backend dispatch will use. |
| `resolve_backend()` | Converts `"auto"` to a concrete backend and caches the answer. | Returns `"numpy"`, `"numba"`, or `"torchvision"`. For a forced backend, it returns the forced name without proving the optional package can execute. |

Quick inspection:

```python
from sahi.postprocess.backends import (
    get_postprocess_backend,
    resolve_backend,
    set_postprocess_backend,
)

set_postprocess_backend("auto")
print("configured:", get_postprocess_backend())  # may be "auto"
print("resolved:", resolve_backend())            # concrete backend

set_postprocess_backend("numpy")                 # reproducible fallback
print("configured:", get_postprocess_backend())
print("resolved:", resolve_backend())
```

## Auto-detection order

When configured as `"auto"`, `resolve_backend()` uses this order:

1. `"torchvision"` if `torchvision` is importable and a torch CUDA or Apple MPS backend is available.
2. `"numba"` if `numba` is importable.
3. `"numpy"` as the always-available fallback.

Auto-detection does not mean a selected detector model is running on the same device. It only chooses the postprocessing implementation for NMS/NMM.

## Backend comparison

| Backend | Best use | Extra packages | Limits and gotchas |
| --- | --- | --- | --- |
| `numpy` | CPU-only or reproducible fallback; small to medium prediction counts; optional-backend troubleshooting. | None beyond SAHI's normal numerical stack. | Uses vectorized CPU paths and sparse/streaming fallbacks for large or degenerate inputs. It is not GPU accelerated, but it avoids optional dependency and JIT issues. |
| `numba` | Large CPU postprocessing when `numba` is installed and warmup cost is acceptable. | `numba`. | First call can spend time compiling. NMS and GreedyNMM loops are JIT-compiled; full NMM still uses shared Python merge bookkeeping after metric work. Large sparse cases may fall back through numpy-style sparse paths. |
| `torchvision` | Large postprocessing on a runtime with compatible `torch`, `torchvision`, and CUDA or Apple MPS. | `torch` and `torchvision`. | Auto-selects only when a GPU/MPS backend is visible. `nms(..., match_metric="IOU")` uses `torchvision.ops.nms`; IOS and NMM compute metric matrices with torch then use shared merge logic. Forcing `"torchvision"` does not install packages and does not guarantee acceleration; device selection can still fall back to CPU. |

## Recommended backend choices

| Situation | Choice | Reason |
| --- | --- | --- |
| You need deterministic, dependency-light behavior while debugging duplicate boxes. | `set_postprocess_backend("numpy")` | Removes optional package, JIT, and GPU availability variables. |
| `auto` resolved differently across machines. | Force `"numpy"` for baseline, then explicitly test `"numba"` or `"torchvision"`. | `auto` is environment-sensitive by design. |
| CPU has many boxes and `numba` is installed. | Try `"numba"`, then ignore the first-call timing. | JIT warmup can dominate a tiny smoke test but help larger loops. |
| CUDA/MPS is available and postprocessing dominates runtime. | Try `"torchvision"` and compare to `"numpy"`. | Only some paths are native GPU kernels; IOS/NMM include CPU-side merge logic. |
| Optional backend imports or GPU state are unreliable. | Force `"numpy"`. | The numpy backend is the safest known-good reference. |

## Minimal backend probe command

```bash
python - <<'PY'
from sahi.postprocess.backends import get_postprocess_backend, resolve_backend, set_postprocess_backend

for backend in ["auto", "numpy"]:
    set_postprocess_backend(backend)
    print(f"configured={get_postprocess_backend()} resolved={resolve_backend()}")
PY
```

For an assertion-backed probe that also exercises NMS/NMM behavior, run `../scripts/postprocess_backend_smoke.py` from this reference directory or `scripts/postprocess_backend_smoke.py` from the sub-skill root.
