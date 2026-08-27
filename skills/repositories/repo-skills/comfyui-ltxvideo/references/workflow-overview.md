# Workflow Overview

This overview distills the repository README and workflow JSON families into reusable routes. It intentionally avoids links to original source workflow files; use the sub-skill references and bundled scripts instead.

## How to choose a workflow family

| Task family | Typical user phrasing | Owning sub-skill | Core nodes/signals |
| --- | --- | --- | --- |
| Text-to-video (T2V) | "generate LTX-2 video from a prompt", "single-stage distilled" | `core-generation` | empty video latent, text conditioning, sampler/sigmas/noise, VAE decode |
| Image-to-video (I2V) | "animate this image", "first-frame conditioning" | `core-generation` + `prompt-conditioning` | `LTXVImgToVideoConditionOnly`, guide/image conditioning index `0`, prompt conditioning |
| Two-stage upsampled video | "higher resolution", "two-stage", "spatial/temporal upscaler" | `core-generation` | latent upscaler models, second denoise pass, tiled VAE decode |
| Video-to-video/detailer | "refine a source video", "extend/detail a clip" | `core-generation` | input video components, `LTXVLoopingSampler`, latent reuse, tiled/spatio-temporal decode |
| Prompt/Gemma setup | "Gemma text encoder", "Gemma API", "enhance prompt", "save conditioning" | `prompt-conditioning` | Gemma model folder, API key/model id, prompt enhancer, safetensors conditioning |
| IC-LoRA control | "depth/edge/pose control", "motion track", "union control", "ingredients" | `specialized-workflows` | IC-LoRA loader, video guide nodes, reference image/video, guide strength/downscale |
| HDR output | "linear HDR", "LogC3", "EXR export" | `specialized-workflows` | HDR IC-LoRA, VAE decode output, `LTXVHDRDecodePostprocess`, OpenEXR preflight |
| DubIt / speech rephrasing | "dub this video", "same speaker", "audio reference tokens" | `specialized-workflows` | AV latents, audio VAE decode, `LTXVSetAudioRefTokens`, frozen audio stage |
| Text-to-audio (T2A) | "audio only", "no video output", "generate audio from text" | `specialized-workflows` + `prompt-conditioning` | `LTXVAudioOnlyModel`, dummy video latent, audio latent, audio VAE decode |
| Inpaint/outpaint/masks | "mask a video", "outpaint", "green inpaint composite" | `specialized-workflows` | `LTXVPreprocessMasks`, `LTXVDilateVideoMask`, `LTXVInpaintPreprocess`, Laplacian blend |
| Expert control | "STG", "APG", "Q8", "attention bank", "flow edit", "PAG", "FETA" | `advanced-control` | STG/APG guiders, Q8 patcher, tricks nodes, model patch utilities |

## Native workflow families used as evidence

The repository contains workflow JSON families for older LTX-2.0, LTX-2.3, and LTX-2.5 model generations. Use these as recipe classes, not as runtime dependencies.

### LTX-2.0 families

- T2V full and distilled workflows with checkpoint, LoRA, text conditioning, sampler, and video save.
- I2V full and distilled workflows that add a source image and first-frame conditioning.
- V2V/detailer workflow using `LTXVLoopingSampler` and spatio-temporal tiled decode.
- Early IC-LoRA all-control workflows that show the reference/control pattern.

### LTX-2.3 families

- T2V/I2V single-stage distilled/full workflows.
- T2V/I2V two-stage distilled workflow with spatial/temporal latent upsamplers.
- IC-LoRA union control, motion track, HDR, DubIt, pixel spatial upscaler, ingredients, inpaint, outpaint, and V2V IC-LoRA families.
- T2A single-stage distilled workflow using audio/video latent split/concat and audio-only model patching.

### LTX-2.5 families

- Newer workflow exports for T2V/I2V, two-stage, V2V IC-LoRA, T2A, union control, motion track, inpaint/outpaint, and ingredients.
- Some exported node identifiers are UUID-like rather than semantic node class names. Treat these as modern workflow snapshots; use `../scripts/summarize_workflow_json.py` and the [node catalog](node-catalog.md) to map the semantic nodes that still belong to this custom-node package.

## Cross-sub-skill workflow composition

Most real tasks need more than one sub-skill:

1. **Prompt first.** If the graph starts from raw text, choose local Gemma, API Gemma, or prompt enhancement with `prompt-conditioning`.
2. **Core graph second.** Choose latent size, sampler, sigmas, tiling/looping, upsampling, and decode with `core-generation`.
3. **Specialty controls third.** Add IC-LoRA, T2A, HDR, masks, sparse tracks, DubIt, or pixel upscaling with `specialized-workflows`.
4. **Expert patching last.** Add STG/APG/Q8/tricks only if the user explicitly needs expert model-control behavior or an existing workflow already uses those nodes.

## Static checks versus native execution

Use static checks for planning and diagnosis:

- Node package import/mapping checks through `../scripts/inspect_custom_node_package.py`.
- Workflow JSON summary through `../scripts/summarize_workflow_json.py`.
- Conditioning, sparse-track, HDR EXR, and Q8 preflight scripts in sub-skills.

Run native ComfyUI generation only after the user confirms:

- the required LTX/Gemma/LoRA/audio/upscaler models are already downloaded or download is authorized;
- CUDA and VRAM are sufficient;
- output paths and large media writes are acceptable;
- API calls or external services, if any, are authorized.
