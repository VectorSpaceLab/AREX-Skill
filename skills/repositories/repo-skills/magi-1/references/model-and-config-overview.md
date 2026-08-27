# Model and config overview

This reference summarizes the MAGI-1 model families and the configuration choices future agents most often need before routing into the inference or ComfyUI sub-skills.

## What MAGI-1 generates

MAGI-1 is an autoregressive video generation model. Instead of denoising an entire video at once, it predicts video chunks and can condition later chunks on earlier clean or partially denoised chunks. The public inference surfaces support:

- Text-to-video (`t2v`): prompt-only generation.
- Image-to-video (`i2v`): one image is converted into prefix video context.
- Video-to-video / continuation (`v2v`): a prefix video is decoded, resized, and used as context for continuation.

The repository also includes ComfyUI nodes for the same broad task family and a Dify DSL for prompt enhancement.

## Released families in the repository examples

| Family | Example configs | Process layout in examples | Hardware notes from README |
| --- | --- | --- | --- |
| MAGI-1 4.5B base | `4.5B_base_config.json` | `pp_size: 1`, `cp_size: 1` | A single GPU with at least 24 GB memory is sufficient. |
| MAGI-1 4.5B distill | `4.5B_distill_config.json` | `pp_size: 1`, `cp_size: 1` | Same single-GPU family, fewer guidance paths than base. |
| MAGI-1 4.5B distill+fp8 quant | `4.5B_distill_quant_config.json` | `pp_size: 1`, `cp_size: 1` | README notes `window_size: 1` can help fit GPUs with at least 12 GB memory. |
| MAGI-1 24B base | `24B_base_config.json` | `pp_size: 1`, `cp_size: 8` | H100/H800 x8 recommended. |
| MAGI-1 24B distill | `24B_distill_config.json` | `pp_size: 1`, `cp_size: 8` | H100/H800 x8 recommended. |
| MAGI-1 24B distill+fp8 quant | `24B_distill_quant_config.json` | `pp_size: 1`, `cp_size: 8` | H100/H800 x4 or RTX 4090 x8 noted for quantized 24B. |

The README also names MAGI-1.1 24B and MAGI-1.1 24B distill+fp8 quant weights in the model zoo. When using those weights, start from the closest release config only if the architecture and checkpoint layout match the downloaded release notes.

## Config sections

Every example config has three top-level objects:

- `model_config`: architecture fields that must match the checkpoint. Do not edit these for routine inference.
- `runtime_config`: paths, seed, frame count, resolution, diffusion step count, FPS, chunk/window settings, CFG settings, and checkpoint locations.
- `engine_config`: distributed backend, pipeline/context parallelism, distill/fp8 flags, KV offload, CUDA graph, and schedule controls.

For field-level details, route to [../sub-skills/inference/references/configuration.md](../sub-skills/inference/references/configuration.md).

## Safe selection rules

- For a single-GPU user, start with a 4.5B config unless they explicitly have a supported multi-GPU setup.
- For a ComfyUI user, start with the 4.5B family because the vanilla ComfyUI `MagiProcess` node sets a single-process/single-GPU environment internally.
- For maximum quality on a multi-GPU Hopper host, choose 24B base or distill with matching weights and `torchrun` process count.
- For constrained memory, prefer distill+fp8 quant and reduce `window_size`, frame count, and resolution before editing architecture fields.
- For any distill or fp8 quant config, `runtime_config.cfg_number` must be `1`; for base configs, it must be `3`.
- Keep `engine_config.pp_size * engine_config.cp_size` equal to the number of launched ranks.
- Treat `load`, `t5_pretrained`, and `vae_pretrained` as local asset paths that must be rewritten after downloading weights.

## Useful environment defaults from examples

The example launch scripts set prompt-padding, memory, and cache controls that should usually be retained:

```text
PAD_HQ=1
PAD_DURATION=1
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
OFFLOAD_T5_CACHE=true
OFFLOAD_VAE_CACHE=true
```

The 24B multi-GPU script additionally sets:

```text
CUDA_DEVICE_MAX_CONNECTIONS=1
NCCL_ALGO=^NVLS
```

These settings reduce common runtime friction but do not replace correct checkpoint paths, process counts, and compatible CUDA attention wheels.
