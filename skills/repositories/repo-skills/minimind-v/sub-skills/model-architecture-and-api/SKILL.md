---
name: model-architecture-and-api
description: "Routes MiniMind-V model architecture, VLM API, config, visual
  token flow, MoE, and generation-semantics questions without launching training
  or inference services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Architecture and API

Use this sub-skill when the user asks about MiniMind-V source APIs or model design.

## Route here

- `VLMConfig`, `MiniMindVLM`, `MMVisionProjector`, `MiniMindConfig`, `MiniMindForCausalLM`, `image2tensor`, `get_image_embeddings`, `count_vision_proj`, `forward`, or `generate` semantics.
- MiniMind base config knobs: hidden size, layer count, attention heads, RoPE/YaRN, vocabulary size, dense/MoE switches.
- How image placeholders become visual embeddings and why 64 `<|image_pad|>` tokens are needed.
- Multi-image `pixel_values` shape questions and `num_return_sequences` image-repeat behavior.

## Route elsewhere

- Training schedules, checkpoint/resume, or freezing strategy: `training`.
- Download/resource layout: `data-and-resources`.
- CLI inference/WebUI: `inference-and-serving`.
- Export/conversion: `model-export-and-format-conversion`.

## Operating procedure

1. Read [API reference](references/api-reference.md) for signatures, config defaults, tensor shapes, and function caveats.
2. Read [architecture notes](references/architecture-notes.md) for visual-token flow, dense/MoE variants, and generation flow.
3. Read [troubleshooting](references/troubleshooting.md) for missing vision encoder, placeholder, shape, cache, and MoE mismatch failures.
4. If live confirmation is needed, run [`inspect_minimind_vlm_api.py`](scripts/inspect_minimind_vlm_api.py) with `--repo-root` pointing at a MiniMind-V checkout. The helper imports source modules and prints signatures/defaults; it does not load weights or download resources.

## Key facts

- `VLMConfig(image_special_token='<|image_pad|>', image_ids=[12], **kwargs)` inherits MiniMind config and defaults to `image_hidden_size=768`, `image_token_len=64`.
- `MiniMindVLM(config=None, vision_model_path='./model/siglip2-base-p32-256-ve')` builds the language model, tries to attach SigLIP2, and always creates the projector.
- The vision projector is `LayerNorm -> Linear -> GELU -> Linear`, mapping SigLIP hidden features into MiniMind hidden size without token-count resampling.
- SigLIP2 P32 with fixed 256x256 inputs yields 64 patch tokens; MiniMind-V represents one image as 64 `<|image_pad|>` tokens.
- Dense and MoE variants share the VLM wrapper; `use_moe` changes the MiniMind language backbone feed-forward blocks.
