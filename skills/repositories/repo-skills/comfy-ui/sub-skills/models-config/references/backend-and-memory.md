# Backend and Memory Flags

ComfyUI's backend behavior is controlled by torch availability, device flags, precision flags, and VRAM/cache settings. Treat these as launch-time choices; for server binding, ports, TLS, and API usage, use `../../server-api/SKILL.md`.

## Device Selection

| Goal | Flags | Guidance |
| --- | --- | --- |
| Run without a GPU | `--cpu` | Slow, but useful for diagnosis or machines without a supported accelerator. Do not combine with GPU-only assumptions. |
| Select visible CUDA devices | `--cuda-device 0` or `--cuda-device 0,1` | Restricts this process to listed CUDA device ids. |
| Choose default visible GPU | `--default-device 0` | Keeps other devices visible but selects a default. |
| Use DirectML | `--directml` or `--directml N` | Windows-oriented fallback; may be slower and less compatible than native CUDA/ROCm/XPU/MPS stacks. |
| Use Intel oneAPI selector | `--oneapi-device-selector <selector>` | For oneAPI/XPU environments where a selector string is required. |
| Use Apple Silicon | no special ComfyUI flag in normal cases | Requires PyTorch with MPS support; ComfyUI detects MPS through torch. |
| Use AMD ROCm | no special ComfyUI flag in normal Linux ROCm cases | Requires a ROCm-compatible PyTorch install. ComfyUI sees AMD GPUs through torch CUDA APIs. |

Avoid claiming a machine has CUDA just because a workflow is GPU-heavy. Ask for the user's installed torch/backend stack or phrase recommendations as conditional.

## VRAM Modes

The VRAM flags are mutually exclusive:

| Flag | Effect | When to use |
| --- | --- | --- |
| `--gpu-only` | Store and run everything on GPU. | Only for very high VRAM systems where CPU offload is unwanted. |
| `--highvram` | Keep models in GPU memory after use. | High VRAM and repeated model reuse; can cause out-of-memory if overused. |
| `--lowvram` | Reduces GPU pressure; with older/non-dynamic modes it can move text encoders to CPU. | Limited VRAM when dynamic VRAM alone is not enough. |
| `--novram` | More aggressive memory saving than `--lowvram`. | Very constrained GPUs; expect slower runs. |
| `--cpu` | Run everything on CPU. | Last resort or hardware diagnosis. |

Dynamic VRAM is normally used unless disabled by mode or flag. Prefer these before heavy-handed changes:

- `--vram-headroom GB`: keep extra VRAM free above the default dynamic target.
- `--reserve-vram GB`: reserve VRAM for the OS or other applications.
- `--cache-none`: reduce RAM/VRAM cache at the cost of re-executing nodes.
- `--disable-smart-memory`: force more aggressive offload to regular RAM; useful only for troubleshooting specific memory behavior.

Dynamic VRAM controls:

- `--disable-dynamic-vram`: use estimate-based loading instead of dynamic VRAM.
- `--enable-dynamic-vram`: force dynamic VRAM on systems where it is not default.
- `--async-offload [NUM_STREAMS]` and `--disable-async-offload`: tune asynchronous weight offload; enabled by default on many NVIDIA setups.
- `--fast-disk`: prefer disk-backed dynamic loading/offload over unpinned RAM on fast storage.

## Cache and RAM Flags

| Flag | Use |
| --- | --- |
| `--cache-ram [ACTIVE_GB] [INACTIVE_GB]` | RAM pressure caching; default caching mode with optional headroom thresholds. |
| `--cache-classic` | Old aggressive caching; can improve speed but use more memory. |
| `--cache-lru N` | Keep at most N node results; may use more RAM/VRAM depending on graph. |
| `--cache-none` | Minimal caching; re-executes every node each run. |
| `--high-ram` | Alias-like behavior that enables classic caching for high-RAM/pagefile-preferred systems. |

## Precision Flags

Precision flags can reduce memory or improve compatibility, but wrong choices may break quality or execution.

UNet/diffusion model:

- `--force-fp32`, `--force-fp16`: global pressure toward fp32/fp16.
- `--fp32-unet`, `--fp64-unet`, `--bf16-unet`, `--fp16-unet`: explicit UNet dtype.
- `--fp8_e4m3fn-unet`, `--fp8_e5m2-unet`, `--fp8_e8m0fnu-unet`: store UNet weights in fp8 variants where backend/model support exists.

VAE:

- `--fp16-vae`: lower memory but can cause black images on some models/backends.
- `--fp32-vae`: safer when VAE artifacts or black images appear.
- `--bf16-vae`: useful on backends with good bf16 support.
- `--cpu-vae`: offload VAE to CPU to save GPU VRAM.

Text encoder:

- `--fp8_e4m3fn-text-enc`, `--fp8_e5m2-text-enc`, `--fp16-text-enc`, `--fp32-text-enc`, `--bf16-text-enc`.

Attention/performance:

- `--use-pytorch-cross-attention`, `--use-split-cross-attention`, `--use-quad-cross-attention`, `--use-sage-attention`, `--use-flash-attention` are mutually exclusive attention choices.
- `--disable-xformers` disables xformers.
- `--force-upcast-attention` can help black image issues; `--dont-upcast-attention` is mainly for debugging.
- `--enable-triton-backend` enables Triton backend use in ComfyUI acceleration code when installed and compatible.
- `--fast` enables experimental optimizations; warn that it may crash or affect quality.

## Practical Recommendations

Limited VRAM without assuming CUDA:

1. Start with default dynamic VRAM.
2. If other apps need memory, add `--vram-headroom 1` or another small value.
3. If out-of-memory persists, try `--lowvram`; then `--novram` for more aggressive offload.
4. If VAE causes OOM or black images, try `--cpu-vae` or `--fp32-vae` depending on the symptom.
5. Use `--cache-none` when cached node results are the main memory pressure.
6. Only use CUDA-specific flags when the user confirms a CUDA torch install and NVIDIA GPU.

High VRAM repeated workflows:

1. Consider `--highvram` when repeated model reuse matters and VRAM is ample.
2. Avoid `--gpu-only` unless the graph and all models comfortably fit.
3. Keep dynamic VRAM enabled unless a specific regression requires disabling it.

CPU-only diagnosis:

1. Use `--cpu` and expect slow execution.
2. Do not recommend fp8 or CUDA attention features for CPU-only runs.
3. If an import says a backend package is missing or torch was compiled without a backend, fix the torch/backend install separately from model paths.
