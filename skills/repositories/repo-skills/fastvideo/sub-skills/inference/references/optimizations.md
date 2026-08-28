# Optimization reference

## Attention selection

Set `FASTVIDEO_ATTENTION_BACKEND` before constructing the generator. Common
values are `TORCH_SDPA`, `FLASH_ATTN`, `VIDEO_SPARSE_ATTN`, `SAGE_ATTN`,
`SAGE_ATTN_THREE`, `ATTN_QAT_INFER`, `VMOBA_ATTN`, `SLA_ATTN`, and
`SAGE_SLA_ATTN`. Availability is model-, GPU-, and extension-specific.
Reinstantiate after changing the variable.

VSA, BSA, V-MoBA, SLA, Sage, and Flash paths may require compiled packages.
TurboDiffusion requires SLA and guidance scale 1.0. Full STA is an archived
workflow and is not an active-main default. On unsupported hardware, use a
supported dense fallback such as SDPA only if the model supports it.

## Quantization and compile

Pass a quantization config instance where the API requires one, for example a
config obtained from `get_quantization_config("FP8")()`. FP8 hardware benefits
from sm89+ but older devices may use a slower fallback. NVFP4/Attn-QAT and FA4
are architecture-gated and require the documented matching CUDA/toolkit and
kernel versions; `use_fsdp_inference=True` is incompatible with pointer-based
FP4 paths.

`enable_torch_compile=True` compiles eligible DiT components, not every encoder
or VAE. The first generation includes graph-build overhead. Warm up with the
same shapes and discard it; measure a later generation. Do not use
`mode="reduce-overhead"`/CUDA-graph assumptions unless the selected runtime
explicitly supports the custom attention path.

## Memory controls

`dit_cpu_offload`, `dit_layerwise_offload`, text/image encoder offload,
`vae_cpu_offload`, pinning, FSDP inference, lower frames/resolution, and fewer
steps trade memory against latency. Start with model defaults, then change one
control at a time and record the resulting output and timing.
