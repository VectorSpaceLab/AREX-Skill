# Cross-cutting troubleshooting

Use this page when the right Jittor sub-skill is not yet obvious. It routes common failures to the owning workflow and summarizes the fastest recovery path.

## Symptom to route map

| Symptom | Likely owner | First recovery step |
| --- | --- | --- |
| Import fails, compiler is missing, or the host platform looks unsupported | `runtime-and-installation` | Run `scripts/check_jittor_env.py` and confirm Python, compiler, and `jittor` importability. |
| CUDA is visible on the machine, but Jittor reports no CUDA | `runtime-and-installation` | Treat CUDA as unverified until `jt.has_cuda` and a CUDA smoke pass. |
| A tensor, gradient, or `Module` behaves strangely | `core-api-and-autograd` | Inspect shapes and dtypes, then rerun with lazy execution disabled. |
| A training loop does not converge or a scheduler/state restore looks wrong | `nn-training-workflows` | Check `execute`, `train/eval`, loss reduction, and optimizer parameter ownership. |
| A dataset, transform, or model-zoo load fails | `datasets-models-and-io` | Confirm data layout, download policy, and whether pretrained weights need a network connection. |
| A `jt.code`, console, or utility-CLI task fails | `custom-op-console-and-tools` | Check compiler availability, the helper CLI, and the exact source or console flags. |

## Cross-cutting failure patterns

### 1. First JIT compile is slow

This is normal. Jittor compiles runtime pieces on first use, and some optional CPU acceleration assets may be fetched or built. Do not benchmark the first compile as if it were steady state.

### 2. A visible GPU is not enough

If the host has NVIDIA hardware but Jittor does not report CUDA support, the root cause is usually missing `nvcc`, missing toolchain pieces, or a deliberately CPU-only environment. Optional backends are separate checks.

### 3. A lot of warnings do not mean a broken install

Jittor can emit informational logs while it detects compilers, cache locations, or optional assets. Look for the actual exit code and the tiny CPU smoke before assuming the package is broken.

### 4. Cache problems often look like compile problems

If a stale cache or driver change is involved, the error may disappear after a targeted cache reset. Inspect the cache first with `scripts/jittor_cache_doctor.py`.

## When to stop

Stop and ask for a different environment or backend when the task truly requires:

- a different compiler than the host provides,
- a GPU/accelerator backend that the host cannot expose,
- a network download you are not authorized to perform,
- or destructive cleanup of a user-owned environment.

If the issue belongs to one workflow, prefer the owning sub-skill's troubleshooting page instead of expanding this cross-cutting page further.