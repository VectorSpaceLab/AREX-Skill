---
name: runtime-and-installation
description: "Install, validate, select backends, and troubleshoot Jittor
  runtime, compiler, cache, profiling, and performance behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Runtime and installation

Use this sub-skill when the task is to install Jittor, validate an import or first JIT compile, select CPU/GPU/distributed runtime flags, diagnose cache/compiler/backend failures, or run a bounded performance/profiling check.

Do **not** use this sub-skill for deep Tensor/Var/autograd API usage, neural-network layer or optimizer recipes, dataset/model downloads, or custom C++ operator authoring; route those to the matching Jittor sub-skill.

## Default operating stance

- CPU JIT import and a tiny CPU operation are the required baseline.
- CUDA, ROCm, MPI/NCCL, ACL/vendor accelerators, and MKL/DNNL acceleration are optional. Only claim an optional backend after a backend-specific smoke passes.
- A visible GPU is not enough to claim CUDA. Require `jt.has_cuda` and a tiny synchronized op after setting `jt.flags.use_cuda = 1`.
- First import or first op may compile runtime code and fetch optional CPU acceleration assets. Do not time that first compile as model performance.
- Prefer scoped flags (`with jt.flag_scope(...):`) for temporary backend/debug changes.

## Read or run map

- Read [runtime flags and backends](references/runtime-flags-and-backends.md) to choose pip, Docker, or manual installation; set compiler/CUDA/MPI flags; and separate required CPU JIT from optional hardware.
- Read [profiling and debugging](references/profiling-debugging.md) to localize lazy-execution errors, profile synchronized code, inspect memory, and avoid misleading timings.
- Read [troubleshooting](references/troubleshooting.md) for symptom-driven fixes covering unsupported platforms, compiler issues, cache corruption, CUDA/nvcc, MKL/DNNL downloads, NaN/Inf, OOM, MPI deadlock, and timing mistakes.
- Run [jittor_perf_probe.py](scripts/jittor_perf_probe.py) for a safe CPU-first timing smoke. Use `--use-cuda` only after CUDA is intentionally configured.

## Minimum validation flow

1. Install with a supported Python and a working C++ compiler, then run a CPU import/JIT smoke:

   ```bash
   python - <<'PY'
   import jittor as jt
   x = jt.float32([1, 2, 3])
   y = (x * x).sum()
   print({
       "version": jt.__version__,
       "sum_squares": float(y.data),
       "has_cuda": bool(jt.has_cuda),
       "use_cuda": int(jt.flags.use_cuda),
       "cc_type": jt.flags.cc_type,
   })
   PY
   ```

2. Prefer bundled support checks over original repo tests for routine validation:

   ```bash
   python ../../scripts/check_jittor_env.py
   python ../../scripts/jittor_cache_doctor.py
   ```

3. For CUDA, first prove availability and then enable it:

   ```bash
   python - <<'PY'
   import jittor as jt
   if not jt.has_cuda:
       raise SystemExit("CUDA is not available to Jittor; validate CPU or configure CUDA first.")
   jt.flags.use_cuda = 1
   x = jt.float32([1, 2, 3])
   print(float((x * x).sum().data))
   PY
   ```

4. For performance timing, run from this sub-skill directory:

   ```bash
   python scripts/jittor_perf_probe.py --warmup 1 --rerun 5
   ```
