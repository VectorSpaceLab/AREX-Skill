---
name: specialized-workflows
description: "Plan specialized ComfyUI-LTXVideo IC-LoRA, audio, HDR,
  motion-track, mask, inpaint, outpaint, and upscaling workflows without
  reopening the source repository."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# specialized-workflows

Use this sub-skill when a user task involves ComfyUI-LTXVideo workflow families beyond ordinary T2V/I2V/V2V sampling:

- IC-LoRA guide workflows: union control, motion tracks, HDR, Dub-It, pixel spatial upscaler, ingredients, inpaint, outpaint, and V2V IC-LoRA variants.
- Audio/video utility workflows: text-to-audio, audio-only model patching, speaker reference audio tokens, and audio freezing across stages.
- Specialized media utilities: sparse track editor/draw tracks, HDR LogC3 decode and EXR preflight, video mask preprocessing/dilation, green inpaint composites, and Laplacian pyramid blending.

Do **not** use this sub-skill for normal sampling, prompt setup, or experimental model patches:

- Route ordinary T2V/I2V/V2V model loading, samplers, VAE decode, tiled/looping/low-VRAM generation, and latent basics to [core-generation](../core-generation/SKILL.md).
- Route Gemma/API prompt conditioning, prompt enhancement, saved conditioning, and multimodal guider setup to [prompt-conditioning](../prompt-conditioning/SKILL.md).
- Route Q8, STG/APG, attention-bank, flow-edit, PAG/FETA, and other expert tricks to [advanced-control](../advanced-control/SKILL.md).
- Read root install, model, CUDA, and optional dependency requirements in [model-and-backend-requirements](../../references/model-and-backend-requirements.md) before promising native execution.

All native ComfyUI executions for these workflows require ComfyUI, CUDA-capable GPU/VRAM, the LTX-2 model assets, the relevant Gemma/audio/LoRA/upscaler assets, and often large input/output media. In this skill, native generation is intentionally deferred; use the bundled scripts only for safe static checks.

## First-read routing

1. Identify the requested specialized family in the table below.
2. Read the linked reference before composing a graph or troubleshooting.
3. If the graph needs prompt text, conditioning tensors, sampler settings, latent sizing, VAE decode, two-stage upsampling, or low-VRAM sequencing, delegate those details to the sibling sub-skill rather than duplicating them here.

| User intent | Use | Read |
| --- | --- | --- |
| Add a control/reference clip or image through IC-LoRA | `LTXICLoRALoaderModelOnly`, `LTXAddVideoICLoRAGuide`, `LTXAddVideoICLoRAGuideAdvanced` | [IC-LoRA recipes](references/ic-lora-recipes.md) |
| Union depth/edge/pose control, ingredients, V2V IC-LoRA, creative pixel spatial upscaling | IC-LoRA loader + guide placement; possibly audio ref tokens | [IC-LoRA recipes](references/ic-lora-recipes.md), [masks/inpaint/outpaint/upscale](references/masks-inpaint-outpaint-upscale.md) |
| Motion-track control from a reference image | `LTXVSparseTrackEditor`, `LTXVDrawTracks`, motion-track IC-LoRA guide | [audio/HDR/motion](references/audio-hdr-motion.md), `scripts/validate_sparse_tracks.py` |
| HDR IC-LoRA output or EXR export | `LTXVHDRDecodePostprocess` after VAE decode | [audio/HDR/motion](references/audio-hdr-motion.md), `scripts/hdr_exr_preflight.py` |
| Dub-It/re-dubbing, audio identity preservation, or two-stage audio freeze | `LTXVSetAudioRefTokens`, AV concat, frozen audio latent | [audio/HDR/motion](references/audio-hdr-motion.md) |
| Text-to-audio with no video output | `LTXVAudioOnlyModel`, `LTXVAudioOnlyEmptyVideoLatent`, AV concat, audio VAE decode | [audio/HDR/motion](references/audio-hdr-motion.md) |
| Inpaint/outpaint masks or seamless compositing | `LTXVPreprocessMasks`, `LTXVDilateVideoMask`, `LTXVInpaintPreprocess`, `LTXVLaplacianPyramidBlend` | [masks/inpaint/outpaint/upscale](references/masks-inpaint-outpaint-upscale.md) |
| Family-specific error diagnosis | node-specific failure matrix | [troubleshooting](references/troubleshooting.md) |

## Operating rules

- Keep IC-LoRA guide operations on the **video-only latent and conditioning path** before the final AV latent concatenation. Propagate all returned outputs: positive conditioning, negative conditioning, and latent.
- Prefer `LTXICLoRALoaderModelOnly` for IC-LoRA workflows because it extracts the LoRA metadata-derived `latent_downscale_factor`; feed that value into guide nodes when available.
- Use `LTXAddVideoICLoRAGuideAdvanced` when a workflow needs per-guide self-attention strength or a spatial attention mask. Use the basic guide when no attention mask/strength isolation is needed.
- Treat motion tracks, masks, HDR EXR export, and audio reference tokens as specialized add-ons around a core sampler graph. Route sampler schedules, two-stage generation, VAE decode, and low-VRAM mechanics to [core-generation](../core-generation/SKILL.md).
- Treat Gemma/API text encoding, target dialogue prompts, negative prompts, and conditioning cache choices as [prompt-conditioning](../prompt-conditioning/SKILL.md) tasks.

## Safe bundled scripts

- `scripts/validate_sparse_tracks.py`: validate sparse track JSON emitted by the editor or authored manually. It imports only the Python standard library and writes nothing.
- `scripts/hdr_exr_preflight.py`: check whether `OPENCV_IO_ENABLE_OPENEXR=1` is set and whether optional `cv2` EXR constants are importable. It writes no EXR files.

## Verification status

Static evidence confirmed the specialized node families and representative input/output schemas. CUDA/model-backed generation, model downloads, ComfyUI workflow execution, HDR EXR file writing, and media-output quality checks are intentionally deferred to final verification or user runtime.
