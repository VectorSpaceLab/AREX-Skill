# Kernels and Backends

Use this reference for Protenix kernel flags, optional acceleration dependencies, and conservative fallback choices.

## Quick Isolation Defaults

When debugging imports, shapes, CPU execution, or uncertain GPU compatibility, start with the most portable settings:

```bash
export LAYERNORM_TYPE=torch
protenix pred ... --trimul_kernel torch --triatt_kernel torch --enable_tf32 false
```

For programmatic configs, use:

```python
cfg.triangle_multiplicative = "torch"
cfg.triangle_attention = "torch"
cfg.enable_tf32 = False
cfg.enable_efficient_fusion = False
cfg.enable_diffusion_shared_vars_cache = False
```

This favors correctness and diagnosability over speed. Re-enable optimized kernels only after the doctor script confirms package imports and CUDA visibility.

## Layer Norm Selection

Protenix triangular layers choose the layer norm implementation at import time:

- If `LAYERNORM_TYPE` is unset, the default is `fast_layernorm`.
- If `LAYERNORM_TYPE=torch`, native PyTorch layer norm is used.
- The fast layer norm path imports or JIT-builds `fast_layer_norm_cuda_v2` from Protenix's bundled CUDA extension sources.

Safe guidance:

- Set `LAYERNORM_TYPE=torch` before importing `protenix.model.*` for config inspection, CPU debugging, and generic tensor-shape tests.
- Use the fast layer norm default only when proving CUDA extension behavior or matching the optimized runtime path.
- If an import already happened in the current Python process, restart the process after changing `LAYERNORM_TYPE`.

## Triangle Multiplicative Kernel

Config value: `triangle_multiplicative`; CLI flag: `--trimul_kernel`.

Allowed values:

| Value | Meaning | Fallback behavior |
| --- | --- | --- |
| `cuequivariance` | NVIDIA cuEquivariance triangular multiplicative update. | Source falls back to torch only when `c_hidden != c_z`; import/runtime failures still need dependency repair or selecting `torch`. |
| `torch` | Native PyTorch implementation. | Most portable and first-choice fallback for unsupported GPU, ABI, or optional dependency issues. |

cuEquivariance notes:

- The kernel function imports `cuequivariance_torch.primitives.triangle.triangle_multiplicative_update` at call time.
- Current source comments state hidden dimensions must be multiples of 32 and that the common supported case has `c_hidden == c_z`.
- Kernel precision follows tensor dtype; TF32 is controlled by PyTorch's global CUDA matmul setting.
- Environment variables such as `CUEQ_TRITON_TUNING`, `CUEQ_TRITON_IGNORE_EXISTING_CACHE`, and `CUEQ_TRITON_CACHE_DIR` affect cuEquivariance tuning/cache behavior. Avoid changing them unless the user is explicitly tuning kernels.

## Triangle Attention Kernel

Config value: `triangle_attention`; CLI flag: `--triatt_kernel`.

Allowed values:

| Value | Meaning | Safe use |
| --- | --- | --- |
| `cuequivariance` | cuEquivariance triangle attention path used by Protenix defaults. | Fast path when cuEquivariance imports and target GPU/ABI are supported. |
| `triattention` | Protenix custom Triton tri-attention module. | Requires Triton support; the package includes a PyTorch fallback wrapper for Triton import/runtime import failures in the tri-attention package. |
| `deepspeed` | DeepSpeed DS4Sci Evoformer attention. | Requires DeepSpeed DS4Sci stack and may require `CUTLASS_PATH`; verify imports before use. |
| `torch` | Native PyTorch implementation. | Most portable fallback; first choice for isolation. |

DeepSpeed notes:

- DS4Sci Evoformer attention is CUTLASS-based and may compile at first use.
- `CUTLASS_PATH` matters only for the DeepSpeed triangle attention path.
- Before selecting `deepspeed`, verify `deepspeed` imports and that the DS4Sci Evoformer attention module is available in the installed DeepSpeed package.

Triton notes:

- Protenix tests accept Triton major version `3`; the verified inspection environment had Triton `3.3.1` and PyTorch `2.7.1`.
- The repo contains compatibility tests for GPUs where Triton kernels may fail with messages such as `Not Supported` or missing kernel support.
- If a Triton failure appears on consumer NVIDIA GPUs or unsupported architectures, use `--triatt_kernel torch` and `--trimul_kernel torch` before investigating source-level kernel changes.

## TF32, Cache, Fusion, and Dtype

Key flags:

| Config / flag | Inference default | Training base default | Notes |
| --- | ---: | ---: | --- |
| `enable_tf32` / `--enable_tf32` | `True` | `False` | Model initialization sets `torch.backends.cuda.matmul.allow_tf32` from this value. |
| `enable_efficient_fusion` / `--enable_fusion` | `True` | `False` | Enables efficient fusion paths in diffusion/transformer modules. Disable during fallback triage. |
| `enable_diffusion_shared_vars_cache` / `--enable_cache` | `True` | `False` | Shared-variable caching improves inference memory/speed tradeoffs; disable for deterministic isolation. |
| `dtype` / `--dtype` | `bf16` in common inference docs | `bf16` | `fp32` can simplify numerical debugging but increases memory. |

Source comments warn that full-precision backward with `triangle_attention="cuequivariance"` can require TF32 in some confidence-head settings. Treat this as a training/backward-path constraint, not a reason to enable TF32 for every diagnostic run.

## CLI and Training Mapping

CLI inference options map to internal config values:

- `--trimul_kernel` → `configs.triangle_multiplicative`
- `--triatt_kernel` → `configs.triangle_attention`
- `--enable_cache` → `configs.enable_diffusion_shared_vars_cache`
- `--enable_fusion` → `configs.enable_efficient_fusion`
- `--enable_tf32` → `configs.enable_tf32`
- `--use_tfg_guidance` → `configs.sample_diffusion.guidance.enable`

Training reads environment defaults before parsing:

```bash
export TRIANGLE_ATTENTION=torch
export TRIANGLE_MULTIPLICATIVE=torch
```

Then CLI dotted overrides can still apply through `parse_configs` if the key exists.

## Conservative Fallback Ladder

Use this order when a backend fails:

1. Run `python scripts/protenix_runtime_doctor.py --json` and inspect `torch.cuda`, optional imports, CLI availability, and `LAYERNORM_TYPE`.
2. Restart the Python process with `LAYERNORM_TYPE=torch` if model imports or fast layer norm builds are involved.
3. Set both triangle kernels to `torch` using config values or CLI flags.
4. Disable TF32/cache/fusion if the symptom is numerical instability, shape mutation, or an opaque fused-kernel error.
5. Re-enable one acceleration path at a time: first TF32/cache/fusion, then cuEquivariance or Triton, then DeepSpeed only if needed.
6. If a failure mentions ABI, missing symbols, `no kernel image`, unsupported GPU architecture, or `Not Supported`, do not patch model math first; align PyTorch/CUDA/Triton/cuEquivariance/DeepSpeed versions or stay on torch kernels.

## Native Evidence to Reference During Code Review

When reviewing a Protenix change, check these implementation areas in the installed package or source checkout:

- Config defaults: `configs.configs_base`, `configs.configs_inference`, `configs.configs_model_type`.
- CLI-to-config mapping: `runner.batch_inference`.
- Training environment defaults: `runner.train`.
- Model TF32 application: `protenix.model.protenix.Protenix`.
- Layer norm selection: `protenix.model.triangular.layers` and `protenix.model.layer_norm`.
- Triangle multiplication: `protenix.model.triangular.triangular`.
- TriAttention fallback: `protenix.model.tri_attention`.
- Fused/dropout/Triton compatibility tests: Protenix's test modules for Triton compatibility and fused dropout/add behavior.
