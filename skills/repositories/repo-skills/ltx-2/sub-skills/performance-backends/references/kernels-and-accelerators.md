# Kernels and accelerators

This reference bundles the useful backend facts that affect performance choices.

## `ltx-kernels` overview

`ltx-kernels` provides four compiled CUDA extensions and one CuTe DSL VAE surface:

- `all2all_cpp`: multi-GPU head exchange for sequence parallelism.
- `ops_cpp`: fused element ops for blockwise quantization.
- `blockwise_cpp`: FP8 blockwise GEMM.
- `nvfp4_cpp`: Blackwell-only NVFP4 quantize + block-scaled GEMM.
- `ltx_kernels.vae`: CuTe DSL neighborhood-attention kernels for the diffusion VAE.

The package is optional in the repo workspace and is not built by a normal workspace sync.

## Build prerequisites

- Linux.
- PyTorch with CUDA.
- A CUDA toolkit with `nvcc`.
- A C++ compiler.
- `TORCH_CUDA_ARCH_LIST` should be set to the intended target architectures on build hosts to avoid unnecessary compilation.
- For `ltx_kernels.vae`, `nvidia-cutlass-dsl` must be available.

## Architecture guidance

### `all2all_cpp`

- Used by sequence parallelism.
- Needed for multi-GPU SP runs.
- Assumes CUDA IPC / NCCL-capable single-node multi-GPU execution.
- Exposes `send_recv_heads`, `gather_heads`, and `allgather` for head/token exchange.

### `ops_cpp`

- Provides fused RMSNorm/RoPE helpers and FP6 pack/unpack operations used by blockwise quantization.
- It is a compiled dependency of the blockwise Python surface.

### `blockwise_cpp`

- Supports FP8 blockwise GEMM.
- SM89 is the baseline path.
- SM90 adds the Hopper deep GEMM path when that architecture is targeted.
- Blockwise kernels are not a general fallback on Ampere.
- The Python surface includes `BlockwiseFP8Linear`, `BlockwiseFP6Linear`, and functional quantize/dequantize helpers.

### `nvfp4_cpp`

- Blackwell-only.
- Uses FP4 E2M1 data with FP8 E4M3 block scales and FP32 per-tensor decode scales.
- Requires SM >= 10.0 and the `nvfp4_cpp` extension.
- `nvfp4-prequant` expects packed uint8 weights, block scales, `weight_scale_2`, and usually calibrated `input_scale` values in the checkpoint.
- Do not suggest this path on A100, Hopper, or Ada.
- On non-Blackwell GPUs, recommend FP8 or offload instead.

### `ltx_kernels.vae`

The diffusion VAE exposes two JIT CuTe DSL kernels:

- `na_attn_dsl`: neighborhood attention for deterministic stages.
- `block_fna_dsl`: fused stage-5 DiffusionNABlock.

These kernels require datacenter Blackwell with Tensor Memory and tcgen05 support. Consumer Blackwell, Hopper, and Ada are not valid verification targets.

## NATTEN and FlashAttention

- NATTEN is the preferred production backend for DiffVAE on non-B200 CUDA hosts.
- The documented NATTEN extra pins a NATTEN wheel matched to the torch/CUDA stack used by this repo line.
- `combined_compile` requires NATTEN.
- If NATTEN is absent, chunked modes can fall back to Triton or eager SDPA.
- FlashAttention is optional and architecture-sensitive; automatic attention selection prefers FA3 on Hopper when installed, FA4 on datacenter Blackwell when installed, and PyTorch SDPA otherwise.
- Do not treat FlashAttention as a universal requirement.

## DiffVAE backend selection

`DiffVAEMode` resolves into one of four major paths:

- `chunked_eager`: chunked decode with eager-friendly fallback semantics.
- `chunked_compile`: compile the chunked path when NATTEN is present.
- `combined_compile`: full-volume compile path; requires NATTEN.
- `blackwell_dsl`: Blackwell-only fused path.

## Compile and capture guidance

- `torch.compile` can help repeated inference.
- `reduce-overhead` and capture-like modes expect weights to stay resident.
- Dynamic shapes are supported, but the sequence dimension must stay within the safe compile envelope.
- Unsafe dynamic-shape guard skipping can produce illegal memory access when the sequence length grows beyond the cached range.

## Readiness cues

When a user asks about one of these items, the first question is usually:

1. Is CUDA working at all?
2. Is the path optional or required for the requested goal?
3. Does the machine meet the architecture gate?
4. Is there a safe fallback that preserves the user's goal?

If the answer to any of those is no, surface the fallback rather than pushing the user toward a build.
