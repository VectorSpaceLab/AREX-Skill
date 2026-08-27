# Installation and runtime overview

This is the short shared reference for Jittor setup. Read the runtime sub-skill for the detailed backend and debugging guidance.

## Public package facts

- Distribution name: `jittor`
- Core import names: `jittor`, `jittor_utils`
- Python support documented in the repo: native Unix-like use starts at Python 3.7; Windows guidance starts at Python 3.8.
- Runtime dependencies from package metadata: `numpy<2.0`, `tqdm`, `pillow`, `astunparse`, plus `pywin32` on Windows.
- A working C++ compiler is part of the normal install story because Jittor compiles runtime pieces on first use.

## Install choices

Choose one of these public paths:

1. Published package:
   - `python -m pip install jittor`
2. Local checkout:
   - `python -m pip install -e .`
3. Docker when the host is awkward or backend toolchains are missing:
   - use the CPU-only or CUDA-enabled images documented in the README.

## Minimal import check

A good baseline is a tiny CPU operation that forces one JIT compile and one synchronized value read:

```bash
python - <<'PY'
import jittor as jt
x = jt.float32([1, 2, 3])
y = (x * x).sum()
print({"version": jt.__version__, "sum_squares": float(y.data), "has_cuda": bool(jt.has_cuda)})
PY
```

## Backend policy

- CPU importability is the baseline for this repo skill.
- CUDA, ROCm, MPI/NCCL, ACL/vendor accelerators, and optional CPU acceleration are all separate capability checks.
- A visible GPU does not by itself prove Jittor CUDA support.

## Where to read next

- `references/api-map.md` for a quick module-to-workflow map.
- `sub-skills/runtime-and-installation/SKILL.md` for backend flags, compiler selection, and debugging.
- `scripts/check_jittor_env.py` for a safe environment check from any working directory.
- `scripts/jittor_cache_doctor.py` for a no-delete cache inspection pass before you consider cleanup.