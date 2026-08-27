# Troubleshooting: runtime, install, and backend issues

Read this when Jittor will not import, compiles slowly, selects the wrong backend, or behaves unpredictably during the first JIT run.

## 1. Unsupported platform, Python, or compiler

**Symptoms**
- Installation aborts early.
- Import fails before any JIT compile.
- The compiler probe cannot find `g++`, `clang++`, or a usable `cc_path`.

**Likely causes**
- The host is not Linux or macOS.
- Python is too old for the package metadata.
- The C++ compiler or OpenMP pieces are missing.

**Next step**
- Re-check the runtime facts with `scripts/check_jittor_env.py`.
- Use a supported Python and a working compiler before trying to reason about model code.
- If you need a clean baseline, install from a supported wheel or from this checkout with `pip install -e .` inside a proper Python environment.

## 2. First import takes a long time

**Symptoms**
- The first `import jittor` or first tensor operation takes much longer than later runs.
- A cache path under `~/.cache/jittor` appears and fills with runtime artifacts.

**Likely causes**
- Jittor is compiling runtime support objects on first use.
- Optional CPU acceleration support is being fetched or built.

**Next step**
- Wait for the first compile to finish once.
- Do not benchmark the first import as if it were steady-state execution.
- If the optional CPU acceleration path is not desired, keep the baseline CPU smoke minimal and revisit backend tuning later.

## 3. CUDA is visible on the host, but Jittor still reports no CUDA

**Symptoms**
- `nvidia-smi` sees a GPU, but `jt.has_cuda` is false.
- CUDA examples fail or Jittor tries to fetch a CUDA toolkit.

**Likely causes**
- `nvcc` is not installed or not on PATH.
- The runtime intentionally set `nvcc_path` to empty to avoid auto-enabling CUDA.
- The host only exposes a driver, not a full toolkit.

**Next step**
- Treat CUDA as unverified unless the CUDA-specific smoke passes.
- If you need CUDA, configure the toolkit explicitly and rerun the backend smoke from `runtime-and-installation/scripts/jittor_perf_probe.py --use-cuda` or a dedicated CUDA test.
- If CUDA is optional, stay with the CPU baseline and record the accelerator as unverified.

## 4. Cache corruption or stale compiled artifacts

**Symptoms**
- Repeated compile failures after a system upgrade or driver change.
- Mysterious JIT errors disappear after deleting cache.

**Likely causes**
- Cached kernels or downloaded assets no longer match the current compiler or driver.

**Next step**
- Use `jittor_cache_doctor.py` to inspect the cache layout.
- If deletion is truly needed, use `python -m jittor_utils.clean_cache <category>` only after you are sure the cache should be cleared.
- For a full reset, prefer clearing only the affected category first, not everything.

## 5. Optional MKL/DNNL fetch fails

**Symptoms**
- Import succeeds, but Jittor emits messages about downloading or using an optional CPU acceleration package.
- The fetch fails because of network or mirror problems.

**Likely causes**
- The optional CPU acceleration asset is unavailable.
- Network access is restricted.

**Next step**
- Stay on the CPU baseline for API validation.
- Do not convert an optional fetch failure into a core failure unless your workflow truly depends on that acceleration path.

## 6. NaN, Inf, or misleading error locations

**Symptoms**
- Training blows up with NaN or Inf.
- Stack traces point to a later operation rather than the real source.

**Likely causes**
- Lazy execution delayed the real error site.
- Numerical instability in the model or input data.

**Next step**
- Use `jt.flag_scope(lazy_execution=0)` or `jt.flags.lazy_execution = 0` to localize the failure.
- Combine `trace_py_var=3` and `JT_CHECK_NAN=1` when you need stronger localization.
- If the code is performance sensitive, turn the debug flags off again after diagnosis.

## 7. OOM or runaway memory growth

**Symptoms**
- The process dies or memory keeps increasing between iterations.

**Likely causes**
- The graph is being retained too long.
- The batch or model is too large for the selected backend.

**Next step**
- Inspect memory with the profiling references and make sure synchronized values are not held longer than necessary.
- Clear graphs when appropriate, and check for accidental global references.
- If you are on a GPU path, do not assume CPU-only fallback proves the GPU path is healthy.

## 8. MPI or distributed jobs hang

**Symptoms**
- A multi-process job stalls after launch.
- One rank waits forever during synchronization.

**Likely causes**
- MPI toolchain mismatch.
- Different ranks call Jittor APIs in an inconsistent order.

**Next step**
- Validate the single-process CPU baseline first.
- Confirm the MPI toolchain is installed and visible before attempting distributed routes.
- Use the MPI-specific docs and tests only when the host actually provides MPI tooling.

## 9. Performance timing looks wrong

**Symptoms**
- Reported latency fluctuates wildly.
- The first iteration is much slower than later ones.

**Likely causes**
- No warmup.
- No synchronization around the timed section.
- The first JIT compile was included in the measurement.

**Next step**
- Run the bounded probe in `runtime-and-installation/scripts/jittor_perf_probe.py`.
- Warm up first, then synchronize before and after the timed loop.
- Compare like-for-like backend settings only.

## When to stop and ask for more help

Stop if the issue requires:
- a different host compiler or Python runtime,
- explicit CUDA, ROCm, MPI, or vendor accelerator hardware,
- network access for downloads you are not allowed to perform,
- or a change to a user-owned environment that may be destructive.

In those cases, keep the baseline CPU workflow documented and mark the optional backend as unverified rather than guessing.