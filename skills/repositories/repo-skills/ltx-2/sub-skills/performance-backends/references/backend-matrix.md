# Backend matrix

This sub-skill separates the **verified CUDA baseline** from optional or accelerator-specific paths.

## Verified baseline for this draft

- CUDA smoke succeeded with `torch 2.13.0+cu132` on an A100 host.
- `ltx-kernels` optional compiled backends were **not** built or installed in the verified baseline.
- Treat any claim about Blackwell-only kernels, NATTEN, or FlashAttention as **unverified** until the local machine checks them.

## Capability matrix

| Capability | Minimum backend | CPU substitute | Verified on baseline? | Notes |
|---|---|---:|---:|---|
| CLI parsing, `--help`, config inspection | CPU | Full | Yes | Safe on any machine with Python and the package installed. |
| Import/signature inspection | CPU | Full | Yes | Useful for debugging flag/shape semantics without running generation. |
| Single-GPU real generation/training | CUDA | None | Partial | CUDA runtime was validated, but no generation or training run was executed in the baseline. |
| Memory relief via `--offload {cpu,disk}` | CUDA | Partial | Partial | Helps peak VRAM; slower than resident weights. `disk` is the slowest fallback. |
| Memory relief via `--quantization fp8-cast` | CUDA + PyTorch float8 storage | Partial | Partial | Best default for BF16 checkpoints when memory is tight. It stores selected weights as FP8 and upcasts during inference; no `ltx-kernels` build. |
| Memory relief via `--quantization fp8-scaled-mm` | CUDA + native FP8 + prequant checkpoint | Partial | Partial | Requires a checkpoint already stored in FP8 with `.weight_scale` metadata. Best on Hopper+. |
| `--quantization nvfp4-cast` / `nvfp4-prequant` | Blackwell CUDA only | None | No | Blackwell-only path. Use FP8/offload on A100, Hopper, or Ada. |
| `--compile` / `torch.compile` | CUDA | Partial | Partial | Effective only when the model layout and backend satisfy the compile contract. `reduce-overhead` and `capture` need resident weights. |
| DiffVAE `DiffVAEMode` chunked paths | CUDA | Partial | Partial | `chunked_eager` can fall back to Triton/eager if NATTEN is missing. |
| DiffVAE `combined_compile` | CUDA + `natten` | None | No | Requires NATTEN. Without it, the mode should raise and the user should pick a fallback. |
| DiffVAE `blackwell_dsl` | Datacenter Blackwell + `ltx-kernels` + `nvidia-cutlass-dsl` | None | No | Datacenter Blackwell only. Consumer Blackwell, Hopper, and Ada cannot verify it. |
| Sequence parallelism (SP) | Linux + multi-GPU CUDA + `ltx-kernels` built | None | No | SP all2all is mandatory and needs compiled kernels. |
| Tiled data parallelism (TDP) | Linux + multi-GPU CUDA | None | No | Upscale-only approximation. Not a memory workaround. |
| Distributed VAE decode | Linux + multi-GPU CUDA | Partial | No | Useful for latency; requires compatible VAE backend choice. |
| Distributed Gemma | Linux + multi-GPU CUDA | Partial | No | Accelerator choice depends on prompt count and builder path. |

## Flag and environment guide

### Memory and layout flags

- `--offload {none,cpu,disk}`: lower peak VRAM by moving weights out of GPU memory. `cpu` holds streamed weights in system RAM; `disk` is slower but reduces RAM pressure.
- Block streaming: RAM streaming preloads blocks into pinned CPU buffers; disk streaming reads blocks on demand when only a small number of CPU slots is allowed.
- `--quantization fp8-cast`: BF16 checkpoint, downcast on load, upcast during inference.
- `--quantization fp8-scaled-mm`: prequantized FP8 checkpoint, native FP8 matmul.
- `--quantization nvfp4-cast` / `nvfp4-prequant`: Blackwell-only NVFP4 flow.
- `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`: useful allocator setting when memory fragmentation becomes a problem.
- `--compile [KEY=VALUE ...]`: enable `torch.compile` with optional config overrides.

### `torch.compile` guide

- Default compile is opt-in and off by default.
- `mode=reduce-overhead`, `mode=max-autotune`, and `capture=true` are for GPU-resident weights or streaming paths that report resident-weight semantics.
- `inductor_config` and `dynamo_config` replace defaults wholesale; re-include defaults you still need.
- Avoid `unsafe_skip_cache_dynamic_shape_guards` unless the token envelope is fixed. Reusing a kernel compiled at a smaller sequence length can cause illegal memory access or silent corruption.
- DiffVAE decode compile latency changes at the int32 address threshold: `T * (H_px/4) * (W_px/4) * 512 <= 2,147,483,647`. Crossing it can force int64 addressing and much slower cold compile.

### DiffVAE mode guide

- `chunked_eager`: lowest compile cost; works as the fallback path when NATTEN is missing.
- `chunked_compile`: compile the chunked path when NATTEN is present; falls back to the chunked eager recipe when it is not.
- `combined_compile`: fastest warm non-B200 path, but requires NATTEN.
- `blackwell_dsl`: fused Blackwell-only path; use only on datacenter Blackwell hardware.

## Readiness interpretation

Use the bundled readiness checker to decide which bucket a machine belongs in:

- **CPU-only or broken CUDA**: safe for parser/help inspection only.
- **CUDA baseline**: enough for flag planning, CPU-substitute troubleshooting, and single-GPU advice.
- **CUDA + optional accelerator stack**: only then should you talk about `ltx-kernels`, NATTEN, FlashAttention, NVFP4, or Blackwell DSL as active options.

If the user asks for a backend that is not in the verified set, present it as a conditional path and name the missing gate explicitly.
