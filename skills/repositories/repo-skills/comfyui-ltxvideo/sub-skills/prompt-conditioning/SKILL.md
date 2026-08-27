---
name: prompt-conditioning
description: "Configure Gemma/API prompt conditioning, prompt enhancement, saved
  conditioning artifacts, dynamic conditioning, and multimodal guiders for
  ComfyUI-LTXVideo workflows."
metadata:
  disco-role: operating
  repo-skill-id: comfyui-ltxvideo
  sub-skill-id: prompt-conditioning
  node-families:
    - LTXVGemmaCLIPModelLoader
    - LTXVGemmaEnhancePrompt
    - GemmaAPITextEncode
    - LTXVPromptEnhancerLoader
    - LTXVPromptEnhancer
    - LTXVLoadConditioning
    - LTXVSaveConditioning
    - DynamicConditioning
    - GuiderParameters
    - MultimodalGuider
disable-model-invocation: true
license: NOASSERTION
---

# Prompt Conditioning for ComfyUI-LTXVideo

Use this sub-skill when a task is about producing, enhancing, saving, loading, or tuning prompt conditioning for LTX-2 video/audio workflows in ComfyUI-LTXVideo.

The backend, model-folder, CUDA, and optional dependency baseline is owned by the root [model and backend requirements](../../references/model-and-backend-requirements.md). This sub-skill assumes ComfyUI-LTXVideo is installed and focuses on the conditioning side of the graph.

## Route here when

- The workflow uses local Gemma text encoding through `LTXVGemmaCLIPModelLoader`.
- The workflow uses `GemmaAPITextEncode` instead of a local CLIP/Gemma encoder.
- The user wants to enhance raw prompts with `LTXVGemmaEnhancePrompt` or `LTXVPromptEnhancer`.
- The user wants to save/reuse `CONDITIONING` as safetensors files with `LTXVSaveConditioning` and `LTXVLoadConditioning`.
- The task involves `DynamicConditioning`, `GuiderParameters`, or `MultimodalGuider` setup for text/audio/video guidance.
- The error mentions missing Gemma `config.json`, processor/tokenizer files, API key/model-id metadata, empty conditioning, missing `conditioning_data_*`, duplicate guider modality, or prompt-enhancer downloads.

## Route elsewhere

- Core model/latent/sampler/decode wiring, frame counts, tiling, looping, or low-VRAM loading: use `../core-generation/SKILL.md`.
- IC-LoRA reference images, audio-only latent routing, HDR, masks, inpaint/outpaint, sparse tracks, or DubIt recipes: use `../specialized-workflows/SKILL.md`.
- Expert STG/APG presets, Q8 patching, VAE patching, attention-bank/PAG/FETA/flow-edit tricks, or advanced sampler internals: use `../advanced-control/SKILL.md`.

## Operating graph

1. **Choose the encoding path.**
   - Local/offline path: `LTXVGemmaCLIPModelLoader` returns a `CLIP` object from a Gemma model folder under ComfyUI `models/text_encoders` and an LTX checkpoint. See [Gemma conditioning](references/gemma-conditioning.md).
   - Hosted/API path: `GemmaAPITextEncode` sends the prompt and model id to the LTX Video API and returns `CONDITIONING` directly. It requires credentials and an LTX checkpoint/diffusion-model file carrying the required metadata. See [Gemma conditioning](references/gemma-conditioning.md#api-text-encoding).
2. **Optionally enhance prompt text before encoding.**
   - Use `LTXVGemmaEnhancePrompt` when the local Gemma `CLIP` has processor files and you want Gemma-based T2V/I2V rewriting.
   - Use `LTXVPromptEnhancerLoader` + `LTXVPromptEnhancer` for a separate Hugging Face LLM/image-captioner prompt enhancer. It may download/cache models on first use. See [prompt enhancement](references/prompt-enhancement.md).
3. **Create positive and negative conditioning.**
   - API workflows usually use separate `GemmaAPITextEncode` nodes for positive and negative prompts.
   - Local Gemma workflows use the loaded `CLIP` wherever the graph expects CLIP text encoding or prompt enhancement before encoding.
4. **Reuse conditioning when appropriate.**
   - `LTXVSaveConditioning` writes a sanitized safetensors artifact under ComfyUI embeddings.
   - `LTXVLoadConditioning` reads that artifact back on CPU or GPU. Validate suspicious files with [validate_conditioning_safetensors.py](scripts/validate_conditioning_safetensors.py). See [conditioning artifacts](references/conditioning-artifacts.md).
5. **Patch or tune guidance only after conditioning exists.**
   - `DynamicConditioning` patches the `MODEL` denoise mask behavior before sampling.
   - `GuiderParameters` builds one `GUIDER_PARAMETERS` entry per modality (`VIDEO` and/or `AUDIO`), and `MultimodalGuider` combines `MODEL`, positive/negative `CONDITIONING`, parameters, and `skip_blocks` into a sampler-ready `GUIDER`. See [multimodal guiders](references/multimodal-guiders.md).
6. **Troubleshoot from the nearest symptom.**
   - Use [troubleshooting](references/troubleshooting.md) before changing graph families. Many failures are file placement, metadata, or device-selection problems rather than sampler problems.

## Quick reference

| Need | Primary node(s) | Key inputs | Output |
| --- | --- | --- | --- |
| Load local Gemma encoder | `LTXVGemmaCLIPModelLoader` | `gemma_path`, `ltxv_path`, `max_length` | `CLIP` |
| Gemma prompt rewrite | `LTXVGemmaEnhancePrompt` | `clip`, `prompt`, `system_prompt`, `max_tokens`, `bypass_i2v`, optional `image`, `seed` | enhanced prompt string |
| API prompt embedding | `GemmaAPITextEncode` | `api_key`, `prompt`, `enhance_prompt`, `ckpt_name` | `CONDITIONING` |
| Generic prompt enhancer | `LTXVPromptEnhancerLoader`, `LTXVPromptEnhancer` | Hugging Face model names, `prompt`, optional `image_prompt` | enhanced prompt string |
| Save/load conditioning | `LTXVSaveConditioning`, `LTXVLoadConditioning` | `conditioning`, `filename`, `dtype`; then `file_name`, `device` | safetensors file; `CONDITIONING` |
| Dynamic mask power | `DynamicConditioning` | `model`, `power`, `only_first_frame` | patched `MODEL` |
| Multimodal guidance | `GuiderParameters`, `MultimodalGuider` | modality CFG/STG/rescale controls, positive/negative conditioning, `skip_blocks` | `GUIDER` |

## Safety and side effects

- Do not run native ComfyUI generation just to answer prompt-conditioning questions; static graph inspection and the bundled validator are enough for file-structure checks.
- Do not put private filesystem paths, API keys, or local environment names in generated workflows or reports.
- Treat prompt enhancer and API nodes as network/credential surfaces. Ask before triggering downloads or sending user prompts to an external API.
