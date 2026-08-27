# Model Catalog

This catalog focuses on public import paths for configs and custom code. Use `_component_` values from package exports, not private files. Many builders instantiate large modules, so inspect signatures or configs before calling them.

## Public Dotpath Rules

- Prefer `torchtune.models.<family>.<builder>` for built-in models, tokenizers, model transforms, and family conversion helpers exported from the family package.
- Prefer `torchtune.modules.*`, `torchtune.modules.peft.*`, `torchtune.modules.loss.*`, and `torchtune.generation.*` for reusable building blocks.
- Avoid underscore implementation modules in configs. They are useful as source evidence but are not stable public config targets.
- Recipes are not an importable package. For training configs that mention a model builder, launch with `tune run` and registry or file configs; use `../cli-and-config/SKILL.md` for command syntax.

## Text Model Families

| Family | Base builders | Adapter builders | Tokenizer or transform notes |
| --- | --- | --- | --- |
| Llama 4 | `torchtune.models.llama4.llama4_scout_17b_16e`, `llama4_maverick_17b_128e`, `llama4_decoder` | `lora_llama4_scout_17b_16e`, `lora_llama4_decoder`, `lora_llama4_vision_encoder`, `lora_llama4_vision_projection_head` | Multimodal; gated model access is expected. Use `llama4_transform` or `Llama4Tokenizer` with matching special tokens. |
| Llama 3.3 | `torchtune.models.llama3_3.llama3_3_70b` | `lora_llama3_3_70b`, `qlora_llama3_3_70b` | Reuses Llama 3 tokenizer conventions. Gated Hugging Face access is common. |
| Llama 3.2 text | `torchtune.models.llama3_2.llama3_2_1b`, `llama3_2_3b`, `llama3_2` | `lora_llama3_2_1b`, `lora_llama3_2_3b`, `qlora_llama3_2_1b`, `qlora_llama3_2_3b`, `lora_llama3_2` | Reuses `torchtune.models.llama3.llama3_tokenizer`; 1B/3B builders expose `tie_word_embeddings`. |
| Llama 3 / 3.1 | `torchtune.models.llama3.llama3_8b`, `llama3_70b`, `llama3`; `torchtune.models.llama3_1.llama3_1_8b`, `llama3_1_70b`, `llama3_1_405b`, `llama3_1` | `lora_llama3_*`, `qlora_llama3_*`, `lora_llama3_1_*`, `qlora_llama3_1_*` | Use `torchtune.models.llama3.llama3_tokenizer`; Llama 3.1 exposes scaled RoPE utilities. |
| Llama 2 | `torchtune.models.llama2.llama2_7b`, `llama2_13b`, `llama2_70b`, `llama2`, `llama2_reward_7b`, `llama2_classifier` | `lora_llama2_*`, `qlora_llama2_*`, `lora_llama2`, `lora_llama2_classifier`, reward variants | Use `llama2_tokenizer` with Llama 2 tokenizer files and optional chat template. |
| Qwen 2 | `torchtune.models.qwen2.qwen2_0_5b`, `qwen2_1_5b`, `qwen2_7b`, `qwen2` | `lora_qwen2_0_5b`, `lora_qwen2_1_5b`, `lora_qwen2_7b`, `lora_qwen2` | `qwen2_tokenizer(path, merges_file=None, special_tokens_path=None, max_seq_len=None, prompt_template=None, truncation_type="right", **kwargs)`. |
| Qwen 2.5 | `torchtune.models.qwen2_5.qwen2_5_0_5b`, `1_5b_base`, `1_5b_instruct`, `3b`, `7b_base`, `7b_instruct`, `14b_base`, `14b_instruct`, `32b_base`, `32b_instruct`, `72b_base`, `72b_instruct` | Matching `lora_qwen2_5_*` builders | `qwen2_5_tokenizer(path, merges_file, special_tokens_path=None, max_seq_len=None, prompt_template=None, truncation_type="right", **kwargs)`. |
| Qwen 3 | `torchtune.models.qwen3.qwen3_0_6b_base`, `0_6b_instruct`, `1_7b_base`, `1_7b_instruct`, `4b_base`, `4b_instruct`, `8b_base`, `8b_instruct`, `14b_base`, `14b_instruct`, `32b` | Matching `lora_qwen3_*` builders | `qwen3_tokenizer(path, merges_file, special_tokens_path=None, max_seq_len=None, prompt_template=None, truncation_type="right", **kwargs)`. |
| Gemma / Gemma 2 | `torchtune.models.gemma.gemma_2b`, `gemma_7b`, `gemma`; `torchtune.models.gemma2.gemma2_2b`, `gemma2_9b`, `gemma2_27b`, `gemma2` | `lora_gemma_*`, `qlora_gemma_*`, `lora_gemma2_*`, `qlora_gemma2_*` | Use `gemma_tokenizer`; Gemma 2 adds sliding window and capping parameters. |
| Mistral | `torchtune.models.mistral.mistral_7b`, `mistral`, `mistral_reward_7b`, `mistral_classifier` | `lora_mistral_7b`, `qlora_mistral_7b`, `lora_mistral`, reward/classifier variants | Use `mistral_tokenizer` with Mistral tokenizer files and optional chat template. |
| Phi 3 / Phi 4 | `torchtune.models.phi3.phi3_mini`, `phi3`; `torchtune.models.phi4.phi4_14b` | `lora_phi3_mini`, `qlora_phi3_mini`, `lora_phi3`, `lora_phi4_14b`, `qlora_phi4_14b` | Phi 3 exposes `phi3_mini_tokenizer`; Phi 4 exposes `phi4_tokenizer(vocab_path=None, merges_path=None, special_tokens_path=None, ...)`. |
| SmolLM2 | `torchtune.models.smol.smollm2_135m`, `smollm2_360m`, `smollm2_1_7b`, `smollm2` | No family LoRA wrapper exported in the inspected public package | Use generic modules or custom adapter code only after checking target layer names. |

## Multimodal And Encoder Families

| Family | Public builders | Notes |
| --- | --- | --- |
| Llama 3.2 Vision | `torchtune.models.llama3_2_vision.llama3_2_vision_11b`, `llama3_2_vision_90b`, `llama3_2_vision_decoder`, `llama3_2_vision_encoder`, `llama3_2_vision_transform` | `Llama3VisionTransform` replaces a text tokenizer in multimodal datasets and returns image encoder inputs plus tokens. LoRA builders can target decoder, encoder, and fusion separately. |
| Llama 4 multimodal | `llama4_scout_17b_16e`, `llama4_maverick_17b_128e`, `llama4_decoder`, `llama4_vision_encoder`, `llama4_vision_projection_head`, `llama4_transform` | Includes MoE-style decoder settings, vision encoder/projection builders, and gated downloads. |
| CLIP | `torchtune.models.clip.clip_text_vit_large_patch14`, `clip_text_encoder`, `clip_vision_encoder`, `clip_mlp`, `clip_tokenizer`, `CLIPImageTransform` | Useful as a vision/text encoder or multimodal component; tokenizer default max length is 77. |
| T5 | `torchtune.models.t5.t5_v1_1_xxl_encoder`, `t5_encoder`, `t5_tokenizer` | Encoder-only usage in torchtune components; `t5_tokenizer(path, max_seq_len=512, truncate=True)`. |
| FLUX autoencoder | `torchtune.models.flux.flux_1_autoencoder` | Autoencoder component for image-model workflows; do not confuse with decoder-only LLM builders. |

## Tokenizer And Transform Checklist

- Match tokenizer family to the model family. A Llama 3.x model should normally use `torchtune.models.llama3.llama3_tokenizer`, while Qwen 2/2.5/3 use their family tokenizers and BPE merge files.
- Ensure downloaded artifacts include the expected tokenizer file names such as `tokenizer.model`, `tokenizer.json`, `merges.txt`, or family-specific special-token JSON files.
- Set `max_seq_len` on tokenizer or model transform consistently with recipe, model `max_seq_len`, packing, and memory constraints.
- For multimodal models, pass the model transform where a dataset builder expects `model_transform` or tokenizer-like behavior; route row/message shape details to `../data-and-datasets/SKILL.md`.
- If special tokens are overridden, verify the token IDs are actually supported by the tokenizer file; special-token JSON does not modify the underlying vocabulary.

## Config Fragments

Text model and tokenizer fragments use public builders:

```yaml
model:
  _component_: torchtune.models.llama3_2.llama3_2_1b
  tie_word_embeddings: true

tokenizer:
  _component_: torchtune.models.llama3.llama3_tokenizer
  path: ${checkpoint_dir}/original/tokenizer.model
  max_seq_len: 2048
```

Qwen builders usually need both vocab and merges/tokenizer files:

```yaml
tokenizer:
  _component_: torchtune.models.qwen2_5.qwen2_5_tokenizer
  path: ${checkpoint_dir}/vocab.json
  merges_file: ${checkpoint_dir}/merges.txt
  max_seq_len: 4096
```

Multimodal model transforms replace text-only tokenizers in multimodal dataset configs:

```yaml
tokenizer:
  _component_: torchtune.models.llama3_2_vision.llama3_2_vision_transform
  path: ${checkpoint_dir}/original/tokenizer.model
  image_size: 560
  max_seq_len: 8192
```

## Custom Component Builders

Use a local builder function when a config would otherwise expose too many constructor details:

```python
from torch import nn
from torchtune.modules import TransformerDecoder

class CustomDecoder(TransformerDecoder):
    pass

def custom_decoder(num_layers: int, max_seq_len: int, vocab_size: int) -> nn.Module:
    # Build submodules here and return the configured model.
    ...
```

Config-friendly builders should have explicit arguments, avoid side effects at import time, and return ready-to-train modules. Launch custom configs or custom recipes through `tune run` from a project directory where the local builder is importable.
