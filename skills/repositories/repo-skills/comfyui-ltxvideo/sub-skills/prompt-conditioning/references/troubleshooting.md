# Prompt-Conditioning Troubleshooting

Use this page for Gemma/API prompt encoding, prompt enhancers, saved conditioning safetensors, dynamic conditioning, and multimodal guider symptoms. For global install/backend/model-placement issues, see the root [model and backend requirements](../../../references/model-and-backend-requirements.md). For sampler/decode/latent errors, route to `../core-generation/SKILL.md`.

## Local Gemma loader

| Symptom or message | Cause | Fix |
| --- | --- | --- |
| `No config.json found for the selected Gemma model (...)` | `LTXVGemmaCLIPModelLoader` resolves the model directory as the parent of selected `gemma_path`; that folder is incomplete or the wrong file was selected. | Put the complete Gemma model repository under ComfyUI `models/text_encoders/<gemma-folder>/` and select a file inside that folder. Confirm `config.json` and tokenizer files are beside the weights. |
| Tokenizer/model loading fails despite `config.json` existing | Tokenizer files or weight/index files are missing. Local loader does not download them. | Re-copy/download all Gemma files into the same model folder; restart or refresh ComfyUI model lists. |
| Prompt enhancement error: `Processor not loaded - enhancement not available` | Text encoding loaded, but image processor/chat-template files were absent or unreadable. | Add `chat_template.json`, `processor_config.json`, and `preprocessor_config.json` to the Gemma folder. If image-aware enhancement is not needed, bypass `LTXVGemmaEnhancePrompt`. |
| Prompt is truncated or conditioning is unusually slow | `max_length` too small or too large. The tokenizer pads to the selected length and truncates beyond it. | Start with default `1024`. Increase only for genuinely long prompts; decrease for fast experiments only when truncation is acceptable. |
| Projection/config assertion while loading local CLIP | Selected LTX checkpoint does not match the expected text-embedding projection layout. | Use the LTX checkpoint intended for the workflow family. Keep Gemma conditioning and model checkpoint from compatible LTX versions. |

## API text encoding

| Symptom or message | Cause | Fix |
| --- | --- | --- |
| `API key is required` | Empty `api_key`. | Provide a valid LTX Video API key or use local Gemma encoding. Do not store the key in public workflow files. |
| `Text prompt cannot be empty` | Empty or whitespace-only prompt. | Provide a positive or negative prompt string. For negative conditioning, use explicit negative terms rather than an empty text unless the workflow intentionally supports that. |
| `Model path is required` | Empty `ckpt_name`. | Select an LTX checkpoint/diffusion-model file from ComfyUI model folders. |
| `Model ID cannot be identified from the provided model file` | The safetensors checkpoint lacks required model-id metadata. | Choose an official or metadata-preserved LTX model file. A stripped/converted local checkpoint may work for local generation but not for API encoding. |
| Invalid API key message | Credential is invalid or expired. | Regenerate the key in the LTX Video console, then update the node input securely. |
| `API request failed with status ...` or wrapped request failure | Network/service/API contract issue. | Check network, credentials, and prompt payload. If all are valid, update ComfyUI-LTXVideo before assuming graph wiring is wrong. |

## Prompt enhancer downloads and memory

| Symptom | Cause | Fix |
| --- | --- | --- |
| First use stalls or downloads large files | `LTXVPromptEnhancerLoader` downloads Hugging Face LLM/captioner snapshots when absent. | Ask for permission in budget-sensitive sessions. Pre-populate ComfyUI `models/LLM` cache if downloads are not allowed. |
| Download fails and cache folder disappears | The loader removes partial download folders on failure. | Fix network/auth/model name, then retry; do not rely on the partial folder. |
| Security concern about model code | The image captioner loader uses remote-code trust. | Use only trusted model names or avoid the generic prompt enhancer. |
| OOM during enhancement | Enhancer loads both LLM and image captioner and asks ComfyUI to reserve their estimated memory. | Use local Gemma/API enhancement instead, lower other loaded models, or run enhancement before loading generation-heavy branches. |
| Image prompt assertion about number of frames/prompts | Image-caption path expects first-frame conditioning count to match prompt count. | Use one image prompt per prompt or switch to text-only enhancement. |

## Conditioning safetensors

| Symptom or message | Cause | Fix |
| --- | --- | --- |
| `Conditioning is empty` | Save node received an empty conditioning list. | Trace the encoder output; ensure positive/negative conditioning actually reaches `LTXVSaveConditioning`. |
| `No files found. Please save a conditioning first.` | ComfyUI embeddings folder has no selectable files. | Save conditioning once, or place a valid conditioning safetensors file in the embeddings folder and refresh ComfyUI. |
| `File not found: <file_name>` or `Conditioning file not found: ...` | Selected embedding no longer exists or file list is stale. | Refresh ComfyUI, correct the file name, or re-save the conditioning. |
| `Invalid file: <file_name>` | Folder lookup failed for that selection. | Use a file in ComfyUI's embeddings folder, not an arbitrary path in the node UI. |
| `No conditioning data found in file: <file_name>` | Safetensors file does not contain `conditioning_data_*` keys. | Validate with `../scripts/validate_conditioning_safetensors.py`; regenerate through `LTXVSaveConditioning` if keys are wrong. |
| Downstream dtype/device error | Saved dtype or load device is incompatible with later nodes/hardware. | Try the other save dtype (`bfloat16` vs `float16`) and load on CPU first. Move to GPU only when CUDA/VRAM are confirmed. |
| Reused conditioning validates but generation fails | Conditioning was created for a different LTX checkpoint family or modality layout. | Regenerate conditioning with the same LTX model family as the target workflow. |

## Multimodal guider and dynamic conditioning

| Symptom or message | Cause | Fix |
| --- | --- | --- |
| `Modality AUDIO already exists in parameters` or `Modality VIDEO already exists in parameters` | Chained `GuiderParameters` duplicated a modality. | Keep one node per modality. Chain `AUDIO` then `VIDEO`, or `VIDEO` then `AUDIO`, but do not repeat either. |
| `skip_blocks` causes parsing failure | String contains non-integer text. | Use comma-separated integers such as `28` or `14,17`, or leave empty. Route complex STG layer tuning to `../advanced-control/SKILL.md`. |
| `MultimodalGuider` output not affecting generation | Sampler is still connected to another guider, or positive/negative conditioning bypasses this guider. | Trace the `GUIDER` output into the sampler and confirm both positive and negative inputs are connected. |
| Audio/video stream influence is too weak or too strong | `cfg`, `stg`, `rescale`, `modality_scale`, or `cross_attn` are off for one modality. | Tune one modality at a time. Set `cfg=1.0`, `stg=0.0`, `modality_scale=1.0`, or `rescale=0.0` to disable terms for isolation tests. |
| Dynamic conditioning has no visible effect | The active graph has no denoise mask to modify, or the patched model is not the one reaching the sampler. | Put `DynamicConditioning` on the model branch before guider/sampler. Use it mainly with masked/first-frame/image-conditioning workflows. |

## Routing checklist

- If the symptom begins at model loading, file placement, or CUDA dependency level, use the root troubleshooting/model-backend references.
- If the symptom begins at prompt text, Gemma files, API credentials, conditioning safetensors, or guider parameter wiring, stay in this sub-skill.
- If the symptom begins at frame counts, latent dimensions, sampler order, tiled VAE decode, or VRAM during generation, route to `../core-generation/SKILL.md`.
- If the symptom mentions IC-LoRA, HDR, sparse tracks, DubIt, T2A latent routing, masks, inpaint/outpaint, or pixel upscaler, route to `../specialized-workflows/SKILL.md`.
- If the symptom mentions Q8 kernels, APG/STG advanced presets, attention banks, PAG/FETA, flow edit, inverse samplers, or model patching beyond normal guider parameters, route to `../advanced-control/SKILL.md`.
