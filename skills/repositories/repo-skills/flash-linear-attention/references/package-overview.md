# Flash Linear Attention Package Overview

Use this reference to orient a task before selecting a focused sub-skill.

## Package surfaces

| Surface | Import | Use when | Focused route |
| --- | --- | --- | --- |
| Core operators | `fla.ops` | Calling or maintaining Triton/backended linear-attention kernels such as `chunk_gla`, `chunk_kda`, `chunk_retention`, `fused_recurrent_*`, or `parallel_*`. | `../sub-skills/ops-kernels-and-dispatch/SKILL.md` |
| Fused modules | `fla.modules` | Using fused norm/gate/loss/convolution/rotary utilities in model code. | `../sub-skills/layers-and-models/SKILL.md` for usage, ops route for kernel internals. |
| Layers | `fla.layers` | Replacing a PyTorch attention/token-mixing module with an FLA layer such as `GatedLinearAttention`, `KimiDeltaAttention`, or `MultiScaleRetention`. | `../sub-skills/layers-and-models/SKILL.md` |
| Models | `fla.models` | Constructing Transformers-compatible Config/Model/ForCausalLM classes and hybrid attention configs. | `../sub-skills/layers-and-models/SKILL.md` |
| KDA | `fla.ops.kda`, `fla.layers.KimiDeltaAttention`, `fla.models.KDAConfig` | Kimi Delta Attention gate modes, optional backends, context parallel, or KDA validation. | `../sub-skills/kda-and-context-parallel/SKILL.md` |
| Benchmarks | `python -m benchmarks.ops.verify` in an FLA checkout | Correctness-gated op timing, profiler handoff, and performance-loop evidence. | `../sub-skills/benchmarking-and-optimization/SKILL.md` |

## Distribution and dependency model

FLA uses the import package `fla` and two distribution names:

- `flash-linear-attention`: the main package, including layers and models, plus a dependency on the matching core package.
- `fla-core`: the core package for `fla.ops`, `fla.modules`, and `fla.utils` workflows.

The base package metadata intentionally does not install `torch` or `triton`. Choose one backend extra and matching PyTorch wheel family before expecting runtime kernels to work. Setup details and backend-specific commands live in `../sub-skills/setup-and-backends/SKILL.md`.

## High-value public workflows

- **Use FLA as a library:** install the right backend extra, import `fla.layers`/`fla.models`, construct a small config or layer, then scale to checkpoint/generation/training only after a smoke check.
- **Use FLA operators directly:** verify tensor shapes, dtype, state/varlen metadata, and dispatch gates before calling `fla.ops` kernels in custom code.
- **Maintain kernels:** keep reference tests and numerical tolerances frozen, run focused correctness tests before benchmarking, then use correctness-gated benchmark commands for performance claims.
- **Work on KDA:** use KDA-specific guidance for gate tensors, `safe_gate`, grouped value heads, optional FlashKDA/TileLang routes, and `cp_context`.
- **Benchmark responsibly:** a benchmark number is promotable only after the full correctness gate passes on the same task scope.

## Optional dependency boundaries

| Optional surface | Trigger | Notes |
| --- | --- | --- |
| CUDA | `[cuda]` extra | Main NVIDIA path with PyTorch CUDA and upstream Triton. |
| ROCm | `[rocm]` extra after PyTorch ROCm wheel | PyTorch wheel source must match ROCm; do not mix CUDA wheels. |
| XPU | `[xpu]` extra after PyTorch XPU wheel | Intel backend path; Triton flavor comes through PyTorch. |
| NPU/Ascend | `[npu]` extra | Uses `torch_npu` and `triton-ascend`, not upstream Triton. |
| CPU | `[cpu]` extra | Useful for import/config checks; not proof of accelerator kernels. |
| TileLang | `[tilelang]` extra and `FLA_TILELANG` | Optional backend for selected ops; may require compiler/toolkit probes. |
| FlashKDA | external `flash_kda` package and `FLA_FLASH_KDA` | Optional KDA inference route with strict verifier constraints. |
| Short convolution | `[conv1d]` extra | Optional `causal-conv1d` path for short-convolution layers. |
| Benchmarks/evals | `[benchmark]`, external harness packages, datasets | Can require downloads, GPUs, and long runtimes; do not use as smoke checks. |

## Maintainer policy highlights

- Follow the repository's style and contribution rules when editing a checkout: minimal diffs, tests for operator/module changes, no broad rewrites of validated kernels, and explicit approval for breaking or numerical changes.
- Mainline Triton kernels should avoid `tl.make_block_ptr` and `tl.advance`; use explicit offset-vector addressing and `tl.int64` address arithmetic.
- Public model/config/checkpoint compatibility changes are breaking unless they only restore intended behavior.
- Before opening a PR, load the repo's MR-readiness guidance and prepare a test plan plus performance evidence when relevant.
