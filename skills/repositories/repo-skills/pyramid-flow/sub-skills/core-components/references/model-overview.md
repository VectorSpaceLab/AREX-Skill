# Core Components Model Overview

Pyramid-Flow combines a pyramidal flow-matching DiT, text encoders, a causal video VAE, custom diffusion schedulers, and distributed utilities. This sub-skill focuses on those reusable components, not user-facing launchers or dataset/training command construction.

## Component graph

```text
prompt(s) / precomputed text features
        |
        v
FluxTextEncoderWithMask or SD3TextEncoderWithMask
        |
        v
PyramidDiTForVideoGeneration
  |-- DiT body selected by model_name/model_variant
  |     |-- pyramid_flux  -> Flux-style transformer checkpoint subtree
  |     `-- pyramid_mmdit -> SD3/MMDiT-style transformer checkpoint subtree
  |-- PyramidFlowMatchEulerDiscreteScheduler
  |-- CausalVideoVAE for raw pixel <-> latent conversion
  `-- trainer_misc sequence/distributed helpers when launched multi-process
        |
        v
latent sequence -> CausalVideoVAE.decode(...) -> PIL frames/video export
```

## Repository model families

| Family | Where it appears | Typical use | Core-component notes |
| --- | --- | --- | --- |
| `pyramid_flux` | README's latest miniFLUX recommendation and Flux modules. | Newer public checkpoints including miniFLUX video/image variants. | Constructor selects the Flux transformer/text encoder path and uses Flux-specific image latent shift/scale. README recommends `model_dtype='bf16'`. |
| `pyramid_mmdit` | Original SD3-style implementation and MMDiT modules. | SD3-based 384p/768p video checkpoints. | Constructor selects the MMDiT transformer/text encoder path and uses MMDiT-specific image latent shift/scale. |
| Causal Video VAE | `video_vae/`, README inference snippets, VAE docs, precompute/training flows. | Convert raw frames to latents, decode generated latents, reconstruct images/videos, support VAE training. | Spatial downsample scale is 8. Long videos use temporal chunking; large spatial inputs may enable VAE tiling. |
| Flow scheduler | `diffusion_schedulers/scheduling_flow_matching.py` and DiT wrapper. | Per-stage reverse process for pyramid-flow inference/training. | Stage index must match configured stages. Generation repeatedly calls `set_timesteps(..., stage_index=i)` then `step(...)`. |
| Cosine DDPM scheduler | `diffusion_schedulers/scheduling_cosine_ddpm.py`. | Lightweight cosine diffusion utility. | CPU-safe and independent of checkpoints. |
| Distributed helpers | `trainer_misc/` and `utils.py` for context parallel in VAE code. | Multi-GPU inference/training, FSDP training loops, context/sequence parallel latent exchange. | Most helper accessors assert unless the relevant process group was initialized. |

## Wrapper responsibilities

`PyramidDiTForVideoGeneration` is the main glue object. It owns:

1. **Checkpoint subtree routing**: joins the user-supplied `model_path` with `model_variant` to load the DiT body; optionally joins `model_path` with `causal_video_vae` for VAE weights.
2. **Architecture selection**: `model_name='pyramid_flux'` or `model_name='pyramid_mmdit'` selects the transformer and text encoder implementation.
3. **Latent scaling**: image and video frames use separate shift/scale constants before diffusion and inverse scaling before decode.
4. **Pyramid stages**: defaults to three spatial stages `[1, 2, 4]` and passes stage count/ranges into the flow scheduler.
5. **Autoregressive video units**: `frame_per_unit`, `max_temporal_length`, and `sample_ratios` define training/inference stage layout.
6. **Device/offload behavior**: model properties read DiT device/dtype; sequential CPU offload uses Accelerate and forces compatible generation settings.

Use the generation-inference sub-skill for prompt recipes and launch commands. Use this reference to reason about which constructor parameters and tensor shapes those launch commands are feeding.

## VAE responsibilities

`CausalVideoVAE` is a diffusers-style `ModelMixin`/`ConfigMixin` class. Its core contract is:

- Encode normalized videos/images into a diagonal Gaussian latent distribution.
- Decode latents into reconstructed videos/images.
- Support tiled spatial processing for large images/videos.
- Support chunked temporal processing for long videos.
- Return diffusers-style output objects by default.

`CausalVideoVAELossWrapper` is a higher-level wrapper around a pretrained VAE plus optional LPIPS/discriminator loss. Use it when a task mentions:

- VAE checkpoint loading with keys under `vae.` or discriminator keys under `loss.discriminator`.
- Training loss with `disc_start`, `kl_weight`, perceptual weight, discriminator weight, or LPIPS checkpoint.
- User-facing `reconstruct()`, `encode_latent()`, and `decode_latent()` helpers that produce PIL images.

For pure encode/decode API inspection, `CausalVideoVAE` is the direct object. For VAE training/reconstruction workflows, route to training-workflows after using this reference for shapes and method signatures.

## Scheduler stage model

The flow scheduler builds dictionaries keyed by stage index:

- `timesteps_per_stage[i]`
- `sigmas_per_stage[i]`
- `start_sigmas[i]`
- `end_sigmas[i]`
- `ori_start_sigmas[i]`

For the default `stages=3`, valid stage indexes are `0`, `1`, and `2`. The DiT wrapper calls `set_timesteps()` separately for each stage before iterating over `scheduler.timesteps` and calling `step()`.

When debugging scheduler errors, check these first:

1. `len(num_inference_steps)` matches `len(model.stages)` if a list is supplied.
2. `stage_index` is in range for the scheduler's configured `stages`.
3. `stage_range` length is `stages + 1` and monotonically covers `[0, 1]`.
4. The `timestep` passed to `step()` is a value from `scheduler.timesteps`, not an integer loop index.
5. `model_output` and `sample` have exactly matching shape and compatible dtype/device.

## Shape conventions

| Tensor | Common shape | Owner | Notes |
| --- | --- | --- | --- |
| Raw video/image batch for VAE | `[B, 3, T, H, W]` | `CausalVideoVAE.encode`, wrapper `get_vae_latent`, VAE loss wrapper | A 4D image `[B, 3, H, W]` may be converted to one-frame video in the wrapper. Normalize pixel values consistently with the calling workflow. |
| VAE latent | `[B, 4, T_latent, H/8, W/8]` for default config | `CausalVideoVAE.decode`, DiT wrapper | Spatial dimensions should correspond to a source height/width divisible by 8. |
| Pyramid latent list | list from low resolution to high resolution | DiT wrapper `get_pyramid_latent()` | Built by repeated 2D interpolation of VAE latents for each stage. |
| Scheduler sample/model output | same tensor shape, often latent-like 5D tensors | `PyramidFlowMatchEulerDiscreteScheduler.step()` | The scheduler is shape-agnostic as long as tensor shapes broadcast exactly. |
| Text embeddings | prompt embeddings, attention mask, pooled embeddings | text encoder modules and DiT wrapper | In multi-GPU sequence parallel generation, embeddings are broadcast within sequence-parallel groups. |

The VAE implementation may produce decoded spatial sizes rounded to the nearest downsample-compatible grid if inputs are not divisible by 8. Treat non-divisible height/width as invalid for workflow planning and precheck before encode/decode.

## Distributed helper model

There are two distributed-helper areas:

- `trainer_misc` for DiT inference/training sequence parallel, DDP initialization, optimizer/scheduler helpers, FSDP training loop, and VAE DDP training loop export.
- Top-level `utils.py` for context-parallel helpers used by `video_vae` internals.

For `trainer_misc`:

1. `init_distributed_mode(args)` inspects environment variables from OpenMPI or torchrun-style launchers.
2. If no distributed variables exist, the helper sets `args.distributed=False` and returns; rank/world-size helpers fall back to single-process defaults.
3. `init_sequence_parallel_group(args)` requires DDP already initialized and reads `args.sp_group_size` and `args.sp_proc_num`.
4. Accessors such as `get_sequence_parallel_group()` assert if initialization did not happen; always guard with `is_sequence_parallel_initialized()` in reusable code.
5. `all_to_all` and broadcast calls require initialized process groups and should not be called in single-process smoke tests.

## Backend and artifact boundaries

- Imports, scheduler math, and tiny VAE shape checks are CPU-safe.
- Full text-to-video, image-to-video, feature extraction, and training require CUDA for truthful execution.
- End-to-end generation also requires downloaded model checkpoints matching `model_name` and `model_variant`.
- Full training requires datasets and, for VAE loss training, LPIPS checkpoint handling.
- MPS is mentioned by public docs but was not verified in this production run.

## Quick decision guide

| User asks... | Use this sub-skill? | Next step |
| --- | --- | --- |
| "What arguments does `PyramidDiTForVideoGeneration.generate()` accept?" | Yes | Use `api-reference.md` signatures and generation semantics. |
| "Why does `stage_index=3` fail?" | Yes | Use scheduler stage model and troubleshooting. |
| "How do I run Gradio or torchrun generation?" | No | Route to `generation-inference`; return here only for API semantics. |
| "How do I precompute VAE latents?" | No | Route to `data-preparation`; return here for VAE latent shape details. |
| "How do I launch VAE/DiT training?" | No | Route to `training-workflows`; return here for distributed helper semantics and model shapes. |
| "Can I inspect components without downloading checkpoints?" | Yes | Run `scripts/smoke_core_components.py` for imports/schedulers/tiny VAE only. |
