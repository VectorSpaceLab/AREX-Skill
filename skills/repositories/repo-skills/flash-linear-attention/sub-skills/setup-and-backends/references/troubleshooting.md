# FLA setup and backend troubleshooting

Use this reference before changing FLA source code. Most setup failures come from an incomplete backend extra, mixed backend wheels, optional package gates, or environment variables read too late.

## Quick triage checklist

1. Confirm the selected backend family: CUDA, ROCm, XPU, NPU, or CPU/import-only.
2. Run:

   ```bash
   python scripts/check_fla_runtime.py --show-env-vars
   ```

3. For CUDA setups that should run kernels, also run:

   ```bash
   python scripts/check_fla_runtime.py --require-cuda
   ```

4. If `torch` / `triton` imports fail, reinstall with the matching backend extra before debugging FLA code.
5. If imports pass but an optional backend is not selected, inspect package availability, the relevant `FLA_*` gate, and the backend verifier constraints.
6. If the environment was switched between backend families, prefer a fresh environment over in-place repairs.

## Symptom: bare install has no usable `torch` or `triton`

**Typical signs**

- `ModuleNotFoundError: No module named 'torch'`.
- `ModuleNotFoundError: No module named 'triton'`.
- `import fla` appears to work but `fla.ops`, kernels, or fused modules fail immediately.
- `pip show flash-linear-attention` shows the package but `check_fla_runtime.py` exits on required imports.

**Cause**

The base package intentionally omits `torch` and `triton`. Backend dependencies live in extras so the same package metadata works across CUDA, ROCm, XPU, NPU, and CPU.

**Fix**

Install one backend extra. Examples:

```bash
pip install "flash-linear-attention[cuda]"
```

For ROCm/XPU/CPU, install backend `torch` from the matching PyTorch index first, then install FLA with the matching extra:

```bash
pip install --index-url https://download.pytorch.org/whl/rocm7.2 torch
pip install "flash-linear-attention[rocm]"
```

Do not add all backend extras at once. They represent incompatible dependency variants.

## Symptom: wrong backend wheel or mixed Triton flavor

**Typical signs**

- CUDA wheels appear on a ROCm/XPU/NPU machine.
- ROCm reports missing HIP/Triton backend even though `torch` imports.
- XPU install imports `torch` but cannot use Intel backend.
- NPU install has upstream `triton` instead of `triton-ascend`.
- Kernel compilation fails before FLA-specific code paths run.

**Cause**

Pip does not give priority to one configured index over another. If `torch` and Triton are resolved in the same command from mixed indexes, the environment can silently combine the wrong backend wheels.

**Fix**

Use the two-step install for non-CUDA backends:

```bash
# ROCm
pip install --index-url https://download.pytorch.org/whl/rocm7.2 torch
pip install "flash-linear-attention[rocm]"

# XPU
pip install --index-url https://download.pytorch.org/whl/xpu torch
pip install "flash-linear-attention[xpu]"

# CPU/import-only
pip install --index-url https://download.pytorch.org/whl/cpu torch
pip install "flash-linear-attention[cpu]"
```

For NPU, use the pinned Ascend stack and CANN runtime:

```bash
pip install torch==2.7.1 torch_npu==2.7.1 torchvision==0.22.1
pip install triton-ascend==3.2.1 --extra-index-url=https://triton-ascend.osinfra.cn/pypi/simple
pip install "flash-linear-attention[npu]"
```

When the environment has already mixed incompatible packages, a fresh environment is usually faster than uninstalling one package at a time.

## Symptom: CUDA is unavailable

**Typical signs**

- `torch.cuda.is_available()` is `False`.
- `python scripts/check_fla_runtime.py --require-cuda` exits nonzero.
- `torch.version.cuda` is empty or mismatched with the expected wheel family.
- CUDA device count is zero in a container that should have GPUs.

**Cause**

FLA CUDA kernels require a CUDA-capable PyTorch runtime and visible devices. A CPU import check does not verify CUDA kernels.

**Fix**

- Confirm the machine/container exposes GPUs to PyTorch before running FLA kernels.
- Reinstall a CUDA-capable `torch` that matches the system driver policy.
- In containers, confirm GPU device passthrough and driver libraries are visible.
- Avoid treating `triton` import success as a CUDA proof; require a tiny CUDA tensor allocation.
- If CUDA is unavailable by design, narrow the task to import/configuration work or switch to CPU/import-only setup. Do not claim GPU-kernel readiness.

## Symptom: TileLang backend is missing or unexpectedly unused

**Typical signs**

- Optional backend logs say TileLang is unavailable or falling back to Triton.
- `tilelang` is installed but FLA reports no usable `nvcc` compiler.
- `FLA_TILELANG=1` does not force a backend for the current call.

**Cause**

TileLang requires both the `tilelang` Python package and a usable CUDA compiler probe. The probe accepts `CUDA_HOME`, `CUDA_PATH`, `nvcc` on `PATH`, a `nvidia-cuda-nvcc` package that actually ships `nvcc`, or a standard CUDA toolkit install. Some TileLang backends are opt-in; common backends may default on only for specific NVIDIA/Triton combinations. The backend verifier may still reject unsupported shapes/dtypes.

**Fix**

```bash
pip install "flash-linear-attention[tilelang]"
# or install tilelang into the same environment by the user's package policy
```

Then ensure one compiler source is visible before Python starts. If the goal is to avoid TileLang while debugging, set:

```bash
export FLA_TILELANG=0
```

To bypass all optional dispatch backends, set:

```bash
export FLA_DISABLE_BACKEND_DISPATCH=1
```

## Symptom: CUDA short-convolution backend falls back to Triton

**Typical signs**

- Warning says the `cuda` convolution backend was selected but `causal_conv1d_fn` is not available.
- Mamba-family layers instantiate but use the Triton short-convolution path.

**Cause**

The CUDA short-convolution path needs the optional `causal-conv1d` package. FLA can fall back to Triton when it is absent.

**Fix**

Install the optional package if the CUDA convolution backend is required:

```bash
pip install "flash-linear-attention[conv1d]"
```

Or explicitly use Triton for diagnosis:

```bash
export FLA_CONV_BACKEND=triton
```

## Symptom: FlashKDA package is missing or the backend never activates

**Typical signs**

- `flash_kda` package is not importable.
- KDA calls fall back to the Triton/default path despite `flash_kda` being installed.
- Backend verifier messages mention inference mode, dtype, head dimension, GVA, gate flags, or context parallel.

**Cause**

FlashKDA is an optional CUTLASS inference backend for `chunk_kda`, not a general KDA replacement. It requires the external `flash_kda` package and accepts only specific calls: inference mode, `bfloat16`, key and value dimensions of 128, no GVA, gate/qk/beta processing in kernel, `state_v_first=True`, `safe_gate=True`, and no context-parallel path.

**Fix**

- Install `flash_kda` according to the user's package policy if the backend is required.
- Set `FLA_FLASH_KDA=0` to disable it and force fallback while debugging.
- Do not diagnose unsupported shapes as install failures; they are expected verifier rejections.

## Symptom: intra-card context-parallel backend does not run

**Typical signs**

- Setting `FLA_INTRACARD_CP=1` has no effect for dense/non-varlen inputs.
- Calls in training mode fall back to the default path.

**Cause**

The intra-card CP backend is opt-in, has no external package, and only accepts inference-mode variable-length calls for shared delta-rule state prefill. It rejects calls without `cu_seqlens` and calls outside `torch.inference_mode()`.

**Fix**

- Set `FLA_INTRACARD_CP=1` before starting Python.
- Use `torch.inference_mode()`.
- Pass variable-length metadata for supported operations.
- Tune `FLA_INTRACARD_MAX_SPLITS` only when you understand the precision/merge-depth trade-off.

## Symptom: FLA environment variable appears ignored

**Typical signs**

- Changing `FLA_TILELANG`, `FLA_DISABLE_BACKEND_DISPATCH`, `FLA_TRIL_PRECISION`, or cache settings inside an already-running Python process has no effect.
- Invalid `FLA_TRIL_PRECISION` triggers an assertion.
- `FLA_CI_ENV=1` is used to hide production/runtime failures.

**Cause**

Many FLA environment variables are read at import time, class initialization, or cached helper evaluation. Some are intentionally narrow test/benchmark controls rather than runtime feature flags.

**Fix**

- Export variables before launching Python.
- Restart the Python process after changing backend gates or cache/config variables.
- Use exact valid values:
  - `FLA_TRIL_PRECISION`: `ieee`, `tf32`, `tf32x3`.
  - `FLA_CACHE_MODE`: `disabled`, `strict`, `fuzzy`, `full`, `default`, `always`.
  - Most booleans: `0` or `1`; `FLA_USE_COMPILE` also accepts `true` / `false` / `yes` / `no`.
- Keep `FLA_USE_FAST_OPS=0` while debugging correctness.
- Disable `FLA_USE_TMA` unless the hardware is Hopper/Blackwell and Triton supports tensor descriptors.
- Treat `FLA_CI_ENV` as a native-test behavior flag, not as a runtime accuracy or stability fix.

## FAQ issue: H100 MMA assertion

**Typical error**

```text
mma -> mma layout conversion is only supported on Ampere
```

**Cause**

A known Triton compiler issue in older stacks on H100-class GPUs.

**Fix**

Use a fresh environment with aligned PyTorch nightly and Triton nightly packages. Do not mix an old stable `torch` with a new `triton-nightly`, or vice versa. After installing the nightly stack, install FLA without letting the resolver downgrade or replace the verified stack if necessary.

## FAQ issue: `AttributeError: 'NoneType' object has no attribute 'start'`

**Cause**

A known Triton parser/runtime issue on unsupported older Python stacks.

**Fix**

Upgrade to Python `>=3.10`. Python `>=3.11` is preferred for current FLA/Triton development stacks.

## FAQ issue: H100 `LinearLayout::reshapeOuts` assertion

**Typical error**

```text
mlir::triton::LinearLayout::reshapeOuts(...) failed
```

**Cause**

Known Triton H100 compiler issue in older stacks.

**Fix**

Use the same fresh PyTorch-nightly plus Triton-nightly style recovery as the H100 MMA assertion. Keep the backend stack internally consistent.

## FAQ issue: ARM/aarch64 Triton wheels

**Typical signs**

- Official PyTorch/Triton binary wheels are unavailable for the target ARM/aarch64 environment.
- Triton imports fail or compile support is missing despite a valid Python environment.

**Cause**

ARM/aarch64 support depends on compatible PyTorch and Triton wheel availability. FLA-provided Triton builds cover specific version pairs rather than arbitrary combinations.

**Known compatible pairs from the distilled FAQ**

| Triton | PyTorch |
| --- | --- |
| `3.2.0` | `2.6.0` |
| `3.3.0` | `2.7.0` |
| `3.3.1` | `2.7.1` |

**Fix**

Align the Triton and PyTorch versions exactly for ARM/aarch64. For example:

```bash
pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128
pip install -U triton==3.3.1 --index-url https://pypi.fla-org.com/simple
```

Then install the matching FLA backend extra or use a resolver-bypass source/wheel install only after the backend stack imports.

## When to stop setup debugging

Stop and report a backend/setup block instead of continuing when:

- The selected required accelerator is unavailable and there is no accepted CPU/import-only substitute.
- The user's package policy forbids the backend index or optional package needed for the requested backend.
- Reinstalling would mutate a user-provided environment in a way that could break other work and the user has not approved it.
- The checker passes import-only but fails `--require-cuda` for a CUDA-required task.
- The issue is a deep op numerical/correctness failure after a valid setup; route to the ops/kernel sub-skill.
