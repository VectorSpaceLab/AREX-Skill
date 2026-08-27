---
name: core-generation
description: "Plan and troubleshoot core LTX-2 text/image/video generation
  workflows in ComfyUI-LTXVideo."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Core Generation

Use this sub-skill when the user asks how to build, adapt, or debug ordinary LTX-2 video generation in ComfyUI-LTXVideo: text-to-video (T2V), image-to-video (I2V), video-to-video/detailer (V2V), single-stage generation, two-stage latent upsampling, long or tiled generation, low-VRAM loading, VAE decode, latent selection/transition, and basic guide/keyframe placement.

Start with the repo-level [model and backend requirements](../../references/model-and-backend-requirements.md) before promising a run. Generation requires a working ComfyUI install, this custom node package, a CUDA-capable runtime for native generation, and user-provided LTX/Gemma/upscaler/LoRA files in the standard ComfyUI model folders. For prompt encoder setup, route to [prompt-conditioning](../prompt-conditioning/SKILL.md).

## Route here for

- T2V and I2V graph planning with `LTXVBaseSampler`, `EmptyLTXVLatentVideo`, `LTXVImgToVideoConditionOnly`, standard ComfyUI sampler/sigma/noise nodes, and VAE decode.
- V2V/detailer or continuation flows that reuse input/video latents with `LTXVInContextSampler`, `LTXVExtendSampler`, `LTXVLoopingSampler`, latent selection, or latent transitions.
- Single-stage LTX-2.3 generation and two-stage LTX-2.3 generation with latent upsampler models and a second denoise/decode pass.
- Spatially tiled sampling and tiled VAE decode with `LTXVTiledSampler`, `LTXVTiledVAEDecode`, and `LTXVSpatioTemporalTiledVAEDecode`.
- Low-VRAM model-load sequencing with `LowVRAMCheckpointLoader`, `LowVRAMAudioVAELoader`, and `LowVRAMLatentUpscaleModelLoader`.
- Workflow-specific errors involving missing core model files, wrong guider/conditioning object type, latent shape/frame mismatch, keyframe index constraints, tiling seams, and VRAM pressure.

## Do not handle here

- Gemma local/API text encoding, prompt enhancement, saved conditioning files, multimodal guider parameter semantics, or dynamic prompt details: use [prompt-conditioning](../prompt-conditioning/SKILL.md).
- IC-LoRA union control, HDR, audio-only/T2A, DubIt, sparse motion tracks, masks, inpaint, outpaint, pixel spatial upscaling, or ingredients workflows: use [specialized-workflows](../specialized-workflows/SKILL.md).
- STG/APG tuning, Q8 kernels, VAE/model patchers, PAG/FETA, attention-bank/override, flow-edit, or other experimental tricks: use [advanced-control](../advanced-control/SKILL.md).
- Installation/import failures that occur before nodes appear in ComfyUI: use repo-level [troubleshooting](../../references/troubleshooting.md).

## Operating workflow

1. **Classify the recipe.** Decide whether the user needs T2V, I2V, V2V/detailing, two-stage upsampled output, long/tiled output, or only decode/latent utilities. Use [core workflows](references/core-workflows.md) for recipe families distilled from native workflow candidates.
2. **Check public prerequisites.** Confirm the checkpoint, text encoder, optional latent upscaler, optional distilled LoRA, CUDA/VRAM expectations, and ComfyUI model-folder placement. Defer prompt encoder details to [prompt-conditioning](../prompt-conditioning/SKILL.md) but keep the folder dependency visible.
3. **Choose the latent shape first.** For video latents the internal shape is `[batch, channels, latent_frames, latent_h, latent_w]`; pixel-frame count is derived by the VAE as `1 + (latent_frames - 1) * time_scale`. Prefer output dimensions divisible by the VAE spatial scale and ComfyUI node increments.
4. **Wire conditioning deliberately.** T2V leaves image inputs absent. I2V uses `LTXVImgToVideoConditionOnly` or sampler `optional_cond_images` at index `0`. Keyframes use guide nodes and explicit indices; guide videos longer than eight frames should start on a frame index divisible by eight.
5. **Use a guider that preserves raw positive and negative conditionings.** Core samplers extract `positive` and `negative` from the guider. If the user has only prompt text, route prompt construction to [prompt-conditioning](../prompt-conditioning/SKILL.md) first; if the graph uses STG/APG-specific guiders, route expert parameter tuning to [advanced-control](../advanced-control/SKILL.md).
6. **Pick the sampler family.** `LTXVBaseSampler` is the default core T2V/I2V sampler. `LTXVInContextSampler` starts from guiding latents. `LTXVExtendSampler` appends new frames with overlap. `LTXVTiledSampler` divides one latent spatially. `LTXVLoopingSampler` combines temporal chunks and optional spatial tiles for long outputs.
7. **Decode safely.** Standard decode is fine for small outputs. Use `LTXVTiledVAEDecode` for spatial memory pressure and `LTXVSpatioTemporalTiledVAEDecode` for long videos; choose `working_device=cpu` only when the user accepts slower decode for lower GPU memory.
8. **Troubleshoot before changing semantics.** Use [troubleshooting](references/troubleshooting.md) for missing files, guider errors, frame-count mismatches, visible seams, or OOM. Do not tell the user to open original example JSONs; answer from the distilled references here.

## Core node decision table

| Need | Prefer | Key cue |
| --- | --- | --- |
| Ordinary T2V | `LTXVBaseSampler` with empty video latent/no image conditioning | User has prompt only and wants one generated clip. |
| First-frame I2V | `LTXVImgToVideoConditionOnly` before sampling, or sampler `optional_cond_images` index `0` | User provides one image to animate. |
| Keyframes in a clip | `LTXVAddGuideAdvanced` or sampler optional conditioning images/indices | Multiple images should appear at specific frames. |
| Latent-guided generation | `LTXVInContextSampler` or `LTXVAddLatentGuide` | User already has reference/guiding latents. |
| Extend a clip | `LTXVExtendSampler` | User wants more frames after an existing latent/video. |
| Spatial high resolution | `LTXVTiledSampler` and/or `LTXVTiledVAEDecode` | One clip is too large for memory or shows spatial scale needs. |
| Very long video | `LTXVLoopingSampler` | Needs temporal chunks, evolving prompts, or long-term coherence. |
| Low VRAM load order | `LowVRAM*` loaders chained by `dependencies` | Model loading peaks before generation starts. |

## Answering patterns

When answering novice workflow questions:

- Name the recipe family first, then list the minimum node families in order.
- State which model folders must already contain user-provided assets.
- Keep prompt encoder setup as a dependency and link to [prompt-conditioning](../prompt-conditioning/SKILL.md) instead of copying Gemma/API details here.
- Explain whether frame numbers are pixel frames or latent frames for the node being discussed.

When answering expert troubleshooting questions:

- Identify whether the failure happens during asset loading, sampling, latent utility wiring, or VAE decode.
- Preserve the user's sampler/scheduler choices unless the error specifically implicates those choices.
- Prefer alignment, overlap, tiling, and latent-shape fixes before changing prompt semantics.
- Mention CUDA/VRAM requirements publicly, but do not assume any private inspection environment or local checkout remains available.

## Reference map

- [Core workflows](references/core-workflows.md): T2V/I2V/V2V recipe patterns, model-folder expectations, single-stage and two-stage families.
- [Sampling and latents](references/sampling-and-latents.md): sampler inputs, latent frame math, guide/keyframe rules, selection/transition, and noise masks.
- [Tiling, looping, low VRAM](references/tiling-looping-low-vram.md): long/tiled generation, tiled VAE decode, low-VRAM loader sequencing, and parameter cues.
- [Troubleshooting](references/troubleshooting.md): workflow-specific failures and fixes.
- Root [workflow overview](../../references/workflow-overview.md) and [node catalog](../../references/node-catalog.md) provide cross-skill context when available.

## Native recipe families distilled here

- LTX-2.3 T2V/I2V single-stage: checkpoint + text conditioning + video/audio latent preparation + one denoise pass + tiled VAE decode.
- LTX-2.3 T2V/I2V two-stage: stage-one generation, latent upsampler model, second conditioning/denoise pass, then decode.
- LTX-2.0 V2V detailer: input video/components, LTX checkpoint/LoRA, text conditioning, `LTXVLoopingSampler`, and spatio-temporal tiled decode.

These native candidates require CUDA and model assets and were used as static recipe evidence only; do not run native ComfyUI workflows or download models from this skill.
