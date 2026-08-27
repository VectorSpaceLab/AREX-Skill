# Model Taxonomy and Configs

InvokeAI model management separates model identity from loading and inference. Model records are Pydantic config objects identified by a discriminator built from `type`, `format`, `base`, and sometimes `variant`.

## Core Enums

### Base Model Architecture

Use `BaseModelType` to describe the architecture or provider family a model belongs to:

| Value | Meaning |
| --- | --- |
| `any` | Fallback for models not tied to a diffusion architecture, such as standalone CLIP, T5, Qwen, or text LLM encoders. |
| `sd-1`, `sd-2`, `sd-3` | Stable Diffusion 1.x, 2.x, and 3.5 families. |
| `sdxl`, `sdxl-refiner` | Stable Diffusion XL base and refiner. |
| `flux`, `flux2` | FLUX.1 and FLUX.2 model families. |
| `cogview4` | CogView 4. |
| `z-image` | Z-Image, including Turbo/Base variants. |
| `qwen-image` | Qwen Image and Qwen Image Edit. |
| `anima` | Anima, using Cosmos Predict2 DiT plus LLM adapter patterns. |
| `external` | Hosted external provider model. |
| `unknown` | Unknown architecture fallback. |

### Model Type

Use `ModelType` to describe what the model record represents:

| Value | Use |
| --- | --- |
| `main` | Main/pipeline model. |
| `vae` | VAE model or submodel. |
| `lora`, `control_lora` | LoRA or FLUX ControlLoRA patch. |
| `controlnet`, `t2i_adapter`, `ip_adapter` | Control adapters. |
| `embedding` | Textual inversion embedding. |
| `clip_vision`, `clip_embed`, `siglip` | Vision or CLIP embedding models. |
| `t5_encoder`, `qwen3_encoder`, `qwen_vl_encoder`, `text_llm`, `llava_onevision` | Text/multimodal encoder families. |
| `spandrel_image_to_image`, `flux_redux` | Specialty image-to-image/redux models. |
| `external_image_generator` | Hosted external image generation model. |
| `onnx`, `unknown` | ONNX or unknown fallback. |

### Model Format

Use `ModelFormat` to describe storage or quantization format:

| Value | Use |
| --- | --- |
| `diffusers` | Diffusers directory-style model. |
| `checkpoint` | Single checkpoint-style model file. |
| `lycoris`, `omi` | LoRA formats. |
| `onnx`, `olive`, `invokeai` | ONNX/Olive/InvokeAI-specific formats. |
| `embedding_file`, `embedding_folder` | Textual inversion forms. |
| `t5_encoder`, `qwen3_encoder`, `qwen_vl_encoder` | Encoder-specific directory/config formats. |
| `bnb_quantized_int8b`, `bnb_quantized_nf4b` | bitsandbytes quantized formats. |
| `gguf_quantized` | GGUF/GGML quantized weights. |
| `external_api` | Hosted external provider record. |
| `unknown` | Unknown fallback. |

## Variants

- `ModelVariantType`: `normal`, `inpaint`, `depth`.
- `FluxVariantType`: `schnell`, `dev`, `dev_fill`.
- `Flux2VariantType`: `klein_4b`, `klein_4b_base`, `klein_9b`, `klein_9b_base`.
- `ZImageVariantType`: `turbo`, `zbase`.
- `QwenImageVariantType`: `generate`, `edit`.
- `Qwen3VariantType`: `qwen3_4b`, `qwen3_8b`, `qwen3_06b`.
- `ClipVariantType`: `large`, `gigantic`.
- `SchedulerPredictionType`: `epsilon`, `v_prediction`, `sample`.
- `ModelRepoVariant`: default empty string, `fp16`, `fp32`, `onnx`, `openvino`, `flax`.

## Config Object Contract

Every concrete config subclass must provide:

- Common record fields: `key`, `hash`, `path`, `file_size`, `name`, `description`, `source`, `source_type`, optional source metadata, and optional cover image URL.
- Literal discriminator fields: `type`, `format`, `base`, and `variant` when needed.
- `from_model_on_disk()` identification logic that returns a config or raises a non-match error.
- A unique tag assembled from `type.format.base.variant` where `variant` is included only when needed.

The factory validates raw dicts through the discriminated union, so stale fields can change the target class. If a user is changing class-defining fields, preserve only fields that are valid for the target class and use class-change-aware update paths.

## Identification Flow

1. Validate that the supplied path looks like a model: known file extension, root config file, or model-like weights within a shallow directory search.
2. Build common fields from path, source, hash, size, and optional overrides.
3. Try all registered config subclasses except the unknown fallback.
4. Record both successful matches and non-match/errors in classification details.
5. Prefer main models over LoRAs and CLIP embed matches when a file could match multiple configs.
6. Apply default settings for main, control adapter, ControlLoRA, and LoRA records after the best match is selected.
7. If no match is found and unknown fallback is allowed, return an unknown config instead of failing hard.

## Supported Families to Check

- Main models: SD1, SD2, SD3, SDXL, SDXL refiner, FLUX, FLUX.2, CogView4, Qwen Image, Z-Image, Anima.
- Main formats: diffusers directories, checkpoint files, GGUF quantized files for FLUX/FLUX.2/Qwen Image/Z-Image, and NF4 bitsandbytes FLUX.
- VAE families: SD1, SD2, SDXL, FLUX, FLUX.2, Qwen Image, Anima, with checkpoint or diffusers variants depending on family.
- Control adapters: ControlNet checkpoint/diffusers, T2I adapter, IP adapter, FLUX ControlLoRA.
- Text and multimodal: T5, Qwen3, Qwen VL, TextLLM, LLaVA OneVision, CLIP Vision, CLIP Embed, SigLIP.
- Patch models: LoRA LyCORIS, OMI, and diffusers-style LoRA across SD, SDXL, FLUX, FLUX.2, Z-Image, Qwen Image, and Anima where supported.
- External models: records use `base=external`, `type=external_image_generator`, `format=external_api`; they are not probed from disk.

## Diagnostic Heuristics

- If a known file gets `unknown`, inspect safe metadata first, then state-dict key prefixes/shapes only if the file format is safe or the user accepts pickle risk.
- If a model has the right family but wrong type, inspect stale `type`, `format`, `base`, `variant`, and `config_path` overrides.
- If a diffusers directory has many nested files, first confirm the actual model root containing `model_index.json` or `config.json` rather than passing a parent library/cache directory.
- If a main model appears as LoRA, remember main-model matches are intentionally prioritized when merged LoRA keys make the state dict ambiguous.
- If an external model cannot be probed, diagnose it through provider id, provider model id, capabilities, default settings, and provider configuration rather than disk metadata.