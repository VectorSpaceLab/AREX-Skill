# FLA install and backend setup reference

This reference is self-contained for runtime setup decisions. It distills the package metadata, install matrix, environment-variable contract, backend dispatch code, and safe inspection results for Flash Linear Attention.

## Package and import contract

| Item | Contract |
| --- | --- |
| Import package | `fla` |
| Main distribution | `flash-linear-attention` |
| Core distribution | `fla-core` |
| Python | `>=3.10`; Python `>=3.11` is preferred for current Triton stacks and avoids a known Triton parser failure on older Python. |
| Base dependencies | `transformers>=4.45.0`, `einops` |
| Backend dependencies | `torch` and the correct `triton` flavor live in backend extras, not base dependencies. |
| Version evidence | The inspected source exports `fla.__version__ = "0.5.2"`; do not hard-code this for future checkouts. |

FLA ships as two PyPI packages:

- `fla-core`: shared `fla` namespace package containing `fla.ops`, `fla.modules`, and `fla.utils`. Use this only when the task needs kernel/module APIs and not layer/model APIs.
- `flash-linear-attention`: layer/model package containing `fla.layers` and `fla.models`; it depends on the matching `fla-core` version and forwards backend extras to `fla-core`.

A bare install is intentionally not enough for runtime use:

```bash
pip install flash-linear-attention
```

Do not treat that as a valid FLA runtime because it omits `torch` and `triton`. Pick exactly one backend extra from the matrix below.

## Backend install matrix

Use a fresh environment for backend switches or Triton nightly experiments. Pip does not prioritize one configured index over another, so ROCm / XPU / CPU use a two-step install that first pins `torch` from the matching PyTorch index.

| Backend | Extra | Torch/Triton source | Install commands |
| --- | --- | --- | --- |
| CUDA | `[cuda]` | CUDA-capable `torch` plus PyPI `triton>=3.3` | `pip install "flash-linear-attention[cuda]"` |
| ROCm | `[rocm]` | PyTorch ROCm index; `torch` pulls `pytorch-triton-rocm` / `triton-rocm` | `pip install --index-url https://download.pytorch.org/whl/rocm7.2 torch`<br>`pip install "flash-linear-attention[rocm]"` |
| Intel XPU | `[xpu]` | PyTorch XPU index; `torch` pulls `pytorch-triton-xpu` | `pip install --index-url https://download.pytorch.org/whl/xpu torch`<br>`pip install "flash-linear-attention[xpu]"` |
| Ascend NPU | `[npu]` | Ascend stack with `torch_npu` and `triton-ascend` | Source CANN 9.0.0 first, then:<br>`pip install torch==2.7.1 torch_npu==2.7.1 torchvision==0.22.1`<br>`pip install triton-ascend==3.2.1 --extra-index-url=https://triton-ascend.osinfra.cn/pypi/simple`<br>`pip install "flash-linear-attention[npu]"` |
| CPU/import-only | `[cpu]` | PyTorch CPU index plus PyPI `triton>=3.3` | `pip install --index-url https://download.pytorch.org/whl/cpu torch`<br>`pip install "flash-linear-attention[cpu]"` |

For PyTorch nightly, replace the backend wheel path with `whl/nightly/<backend>` and add `--pre`. Keep `torch` and Triton nightly aligned; mismatched nightlies are a common source of H100 compiler errors.

## Editable or source installs

For development against a local checkout or a source tree supplied by the user:

```bash
# CUDA development install
pip install -e ".[cuda,test]"

# Non-CUDA development install: first install backend torch from the matching index,
# then use the matching editable extra, for example:
pip install --index-url https://download.pytorch.org/whl/rocm7.2 torch
pip install -e ".[rocm,test]"
```

When the user already has a verified backend-specific `torch` and Triton stack, the matching editable extra should leave it satisfied instead of reinstalling broad dependencies.

For pre-release `torch` / `triton-nightly` stacks, use a resolver-bypass install only after the backend stack is already verified:

```bash
pip install transformers einops
pip uninstall -y fla-core flash-linear-attention
pip install -U --no-deps <local-wheel-or-source-package>
```

## Optional extras and optional packages

| Extra / package | Purpose | Setup note |
| --- | --- | --- |
| `tilelang` / package `tilelang` | Optional TileLang backend for selected operators. | Install with `pip install "flash-linear-attention[tilelang]"` or install `tilelang` into the same environment. A usable `nvcc` compiler is also required. |
| `conv1d` / package `causal-conv1d` | CUDA short-convolution backend for Mamba-family short convolutions. | Install with `pip install "flash-linear-attention[conv1d]"`. Without it, FLA can fall back to Triton for short convolution. |
| package `flash_kda` | Optional FlashKDA CUTLASS inference backend for `chunk_kda`. | Not a base dependency. The backend only handles specific inference shapes/dtypes and falls back otherwise. |
| NPU packages | `torch_npu`, `triton-ascend`, CANN runtime. | Use the pinned NPU stack above; upstream `triton` is not the NPU backend. |
| `benchmark` extra | Benchmark plotting/data helpers. | Only needed for benchmark workflows, not imports or smoke checks. |
| `test` extra | `pytest` / `pytest-xdist`. | Needed for native tests, not for this sub-skill's safe checker. |

## Environment variables that affect setup or backend selection

Set these before starting Python. Some values are read at import time and may be cached.

| Variable | Default | Valid values | What it controls |
| --- | --- | --- | --- |
| `FLA_CONV_BACKEND` | `cuda` in the env reference; individual constructors may default to `triton` | `cuda`, `triton` | ShortConvolution, Mamba, Mamba2, and log-linear Mamba2 convolution backend. If `cuda` is selected but `causal-conv1d` is unavailable, the code warns and falls back to Triton. |
| `FLA_DISABLE_BACKEND_DISPATCH` | unset / `0` | `0`, `1` | Master switch. `1` bypasses all optional dispatch backends and forces default implementations. |
| `FLA_TILELANG` | unset | `0`, `1` | Enables/disables TileLang backends when package and compiler probes pass. Some TileLang backends require explicit opt-in; common backends may default on for Hopper with newer Triton when needed. |
| `FLA_FLASH_KDA` | unset / enabled | `0`, `1` | Enables/disables FlashKDA dispatch when `flash_kda` is installed and verifier constraints pass. |
| `FLA_INTRACARD_CP` | unset / disabled | `0`, `1` | Opts into intra-card context-parallel dispatch for shared delta-rule prefill paths. Requires inference mode and variable-length inputs. |
| `FLA_INTRACARD_MAX_SPLITS` | `32` | integer `>=1` | Caps intra-card CP sub-sequence splitting depth. |
| `FLA_TRIL_PRECISION` | `ieee` | `ieee`, `tf32`, `tf32x3` | Precision for `solve_tril`; `tf32x3` is NVIDIA-only and intended for Ampere or newer. Invalid values assert during import/use. |
| `FLA_USE_FAST_OPS` | `0` | `0`, `1` | Uses faster but less accurate Triton math intrinsics in shared op helpers. Do not enable when diagnosing correctness. |
| `FLA_USE_TMA` | `0` | `0`, `1` | Enables TMA on Hopper/Blackwell when Triton supports tensor descriptors. Disable if setup/compiler issues occur. |
| `FLA_USE_COMPILE` | `1` | `1`, `0`, `true`, `false`, `yes`, `no` | Controls `torch.compile` for the RWKV7 fused addcmul path; auto-disabled on Python older than 3.11. |
| `FLA_CACHE_MODE` | `disabled` | `disabled`, `strict`, `fuzzy`, `full`, `default`, `always` | Controls pre-tuned kernel-config lookup versus Triton autotune fallback. |
| `FLA_CACHE_RESULTS` | `1` | `0`, `1` | Passes cache behavior into `triton.autotune` when the Triton version supports it. |
| `FLA_CONFIG_DIR` | unset | path | Overrides where FLA reads kernel config JSON files. Use only when intentionally testing custom configs. |
| `FLA_GPU_NAME` | unset | string | Overrides detected GPU name for config-cache selection. |
| `FLA_DISABLE_TENSOR_CACHE` | `0` | `0`, `1` | Bypasses the in-process tensor-cache decorator. Useful for cache/debug isolation. |
| `FLA_CI_ENV` | `0` | `0`, `1` | Loosens some native test assertions. It is not a production accuracy flag. |
| `FLA_BENCH_OP_WARMUP_ITERS`, `FLA_BENCH_WARMUP_MS`, `FLA_BENCH_REP_MS`, `FLA_BENCH_COOLDOWN_SEC` | benchmark-specific | integers | Affect bundled benchmark scripts only; they do not change library runtime behavior. |

## Optional backend dispatch model

FLA's dispatch system is lazy and verifier-based:

1. Public functions opt into dispatch by operation name.
2. On first call, FLA imports the operation's backend registry.
3. Registered backends are tried by priority.
4. A backend is used only when its required package is importable, its environment gate is enabled, and its verifier accepts the current call.
5. If no optional backend accepts the call, FLA runs the default implementation.

This means an optional backend package can be installed but still unused. Common reasons are an environment variable set to `0`, missing `nvcc` for TileLang, training mode for inference-only backends, unsupported dtype/shape, no variable-length inputs for intra-card CP, or `FLA_DISABLE_BACKEND_DISPATCH=1`.

## Safe runtime smoke checks

Run the bundled checker from the sub-skill directory or copy it into the target environment:

```bash
python scripts/check_fla_runtime.py --show-env-vars
```

Expected output includes:

- Python/platform summary.
- Distribution/module versions for `fla`, `flash-linear-attention`, `fla-core`, `torch`, `triton`, `transformers`, and `einops` when installed.
- Public export counts for `fla`, `fla.ops`, `fla.layers`, `fla.models`, and `fla.modules` when importable.
- CUDA availability and device name when `torch.cuda` is available.
- Optional package presence for `tilelang`, `flash_kda`, `causal_conv1d`, `torch_npu`, and `triton_ascend`.

For a CUDA setup, require an actual tiny CUDA allocation:

```bash
python scripts/check_fla_runtime.py --require-cuda
```

A CPU import check does not prove GPU kernels. Do not proceed to GPU-specific correctness, model, or benchmark work until the relevant accelerator check passes or the user accepts a narrowed scope.
