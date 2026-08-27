# Core Workflow Recipes

This reference distills the core ComfyUI-LTXVideo recipe families into reusable graph-planning guidance. It does not require the original checkout or example files. For installation, CUDA, and full model inventory, see the root [model/backend requirements](../../../references/model-and-backend-requirements.md).

## Public model-folder expectations

Use standard ComfyUI model directories. Do not hard-code local machine paths; ask the user for their ComfyUI root or inspect their ComfyUI model folder if needed.

| Asset family | ComfyUI folder | Core use |
| --- | --- | --- |
| LTX-2.3 or LTX-2.0 checkpoint | `models/checkpoints` | Loaded by standard checkpoint loaders or `LowVRAMCheckpointLoader`; provides model/CLIP/VAE outputs. |
| Gemma/text encoder assets | `models/text_encoders/...` | Needed before prompt conditioning can feed core samplers; detailed setup belongs to prompt-conditioning. |
| Latent upscaler models | `models/latent_upscale_models` | Required by current two-stage LTX-2.3 recipe families. |
| Distilled LoRA or workflow LoRA | `models/loras` | Often used in distilled/two-stage flows; IC-LoRA usage routes to specialized-workflows. |
| Audio VAE/checkpoint-style AV assets | `models/checkpoints` unless the user's ComfyUI node expects another configured folder | Some LTX-2.3 AV workflows keep audio/video latent utilities in the graph even for video output. Audio-only tasks route elsewhere. |

If ComfyUI says a model is missing, fix the folder and filename first; do not rewrite the workflow around the error unless the asset is intentionally omitted.

## Common graph skeleton

A core video workflow normally has these phases:

1. **Load model assets.** Use standard ComfyUI checkpoint/LoRA/upscaler loaders or the low-VRAM loaders from this package. For prompt encoder and Gemma/API conditioning, route to prompt-conditioning.
2. **Build conditioning.** Positive and negative conditioning must be present. Core samplers expect a guider object that can expose raw positive/negative conditionings.
3. **Prepare video latent.** Use an empty LTX video latent for T2V, encode first-frame conditioning for I2V, or convert/load existing video into latents for V2V/detailing.
4. **Denoise.** Choose base, in-context, extend, tiled, or looping sampler depending on length/resolution/reuse requirements.
5. **Separate/select/upsample latents if needed.** Two-stage flows upsample latent outputs before a second denoise pass. Long flows select/append/transition latent chunks.
6. **Decode.** Use standard VAE decode for small outputs, tiled VAE decode for large frames, and spatio-temporal tiled VAE decode for long videos.
7. **Save/export through ComfyUI.** This skill does not own final media save node policy; keep output format decisions consistent with the user's ComfyUI setup.

## LTX-2.3 T2V/I2V single-stage pattern

Use this when the user wants one clip at the target resolution without a latent upsample stage.

Typical wiring:

1. Load the LTX-2.3 checkpoint. If memory spikes during loading, replace standard loaders with `LowVRAMCheckpointLoader` and chain later loaders through `dependencies`.
2. Build positive/negative text conditioning and a guider. Prompt details belong to prompt-conditioning, but core generation requires both positive and negative sides to reach the sampler.
3. Create an empty video latent with the target width, height, frame count, and batch size.
4. For T2V, leave image conditioning absent. For I2V, attach `LTXVImgToVideoConditionOnly` to apply the first image to the latent, or pass `optional_cond_images` with index `0` into `LTXVBaseSampler`.
5. Select sampler, sigmas/scheduler, noise seed, and guider. Distilled examples commonly use a short denoise schedule and an LTX-compatible sampler; preserve the user's chosen schedule unless diagnosing a schedule-specific error.
6. Run one denoise pass. If the graph includes AV latent split/concat nodes because the checkpoint is joint audio/video, keep the video latent branch intact even when the user's visible output is video.
7. Decode with `LTXVTiledVAEDecode` when frame size is large or VAE decode OOMs; otherwise standard decode may be sufficient.

Core parameter cues:

- Width/height should follow the node increment and model expectations. The base sampler exposes defaults around a widescreen 768×512/960×544 style and step sizes of 32.
- `num_frames` is a pixel-frame count; LTX examples often use values of the form `1 + 8*k` such as 97 or 121.
- First-frame I2V conditioning strength near `0.7` to `1.0` is common. Lower it if the image over-constrains motion; raise it if the first frame drifts.

## LTX-2.3 T2V/I2V two-stage pattern

Use this when the user asks for an upsampled/final quality output or when a recipe names a latent upscaler stage.

Typical wiring:

1. Run the stage-one single-stage pattern at the draft resolution/length.
2. Load the required latent upscaler model from `models/latent_upscale_models`. Current two-stage LTX-2.3 recipe families also expect the appropriate LTX checkpoint and often a distilled LoRA in `models/loras`.
3. Apply the latent upsampler to the stage-one latent. Preserve temporal/spatial scale assumptions from the upscaler model; do not substitute a pixel upscaler for a latent upscaler.
4. Re-apply I2V first-frame conditioning when the graph calls for it, often with higher strength in stage two to keep the upsampled result anchored.
5. Run a second sampler/denoise pass with the upsampled latent as initialization.
6. Decode the final latent, usually with tiled VAE decode because stage-two latents target a larger image.

Troubleshooting cue: if the graph fails before the second sampler with a missing `LATENT_UPSCALE_MODEL`, check `models/latent_upscale_models` and the loader filename before changing sampler settings.

## LTX-2.0 V2V/detailer and long-video pattern

Use this when the user has an existing video or latent sequence and wants refinement/detailing rather than pure generation.

Typical wiring:

1. Load/scale the input video through ComfyUI video/component nodes, then encode or prepare latents matching the target LTX VAE scale.
2. Load the LTX-2.0-compatible checkpoint and any workflow LoRA needed for detail refinement.
3. Build prompt conditioning and a guider. V2V graphs may use an empty or weak prompt when the input video carries most of the structure.
4. Feed latents to `LTXVLoopingSampler` when the clip is long or high-resolution. It processes temporal chunks and optional spatial tiles rather than denoising the full sequence at once.
5. Use `LTXVSpatioTemporalTiledVAEDecode` for memory-bounded decode of long latent sequences.

Parameter cues:

- `temporal_tile_size` and `temporal_overlap` are expressed in pixel frames in the looping node UI, then converted through the VAE time scale internally.
- Use overlap rather than hard cuts for V2V/detailer continuity. A common starting point is overlap around one-quarter to one-third of the temporal tile size.
- Use `adain_factor` lightly, such as `0.1` to `0.3`, if long chunks accumulate saturation or color drift.

## Choosing among core samplers

| Situation | Sampler family | Reason |
| --- | --- | --- |
| Prompt-only clip | `LTXVBaseSampler` | Creates empty latents and denoises in one pass. |
| First-image animation | `LTXVBaseSampler` with optional image index `0` or `LTXVImgToVideoConditionOnly` before denoise | Encodes the first image into the latent and applies a noise mask. |
| Existing guiding latents | `LTXVInContextSampler` | Uses guiding latents from the beginning of the new clip. |
| Append frames after an existing latent/video | `LTXVExtendSampler` | Selects the tail overlap, creates new latent length, and blends/concatenates output. |
| One high-resolution clip | `LTXVTiledSampler` | Divides latent spatial dimensions and blends tile overlaps. |
| Long/high-res video | `LTXVLoopingSampler` | Combines temporal chunks, optional spatial tiling, keyframes, per-tile prompts, and normalization. |

## Output and decode expectations

- Video latent tensors are 5D. If an operation expects a video latent, a nested audio/video latent or pure audio latent may fail; route audio-only workflows to specialized-workflows.
- VAE decoded frame count is `1 + (latent_frames - 1) * time_scale`. If the decoded output has one frame too many or a duplicated tail, check the decode node's `last_frame_fix` option.
- For large outputs, match tiled sampler and tiled decode strategy: tiled sampling reduces denoise memory; tiled decode reduces VAE memory. They solve different OOM points.
