# Model catalog

Public entry points are `BaseModel` registry keys. Engine names are internal implementation details.

## Variant templates

- Base: `<model_key>`
- LoRA: `<model_key>_lora`
- INT8: `<model_key>_int8`
- LoRA + INT8: `<model_key>_lora_int8`
- LoRA + K-bit: `<model_key>_lora_kbit`

Only use the suffixes that actually appear in the family row below.

## Supported families

| Family | Registry keys | Notes |
| --- | --- | --- |
| BLOOM | `bloom`, `bloom_lora`, `bloom_int8`, `bloom_lora_int8` | Causal LM family with standard LoRA and INT8 variants. |
| Cerebras 1.3B | `cerebras`, `cerebras_lora`, `cerebras_int8`, `cerebras_lora_int8` | Same public pattern as BLOOM. |
| DistilGPT-2 | `distilgpt2`, `distilgpt2_lora` | Small causal LM; sampling-oriented defaults. |
| Falcon 7B | `falcon`, `falcon_lora`, `falcon_int8`, `falcon_lora_int8`, `falcon_lora_kbit` | Remote-code family; K-bit variant is available. |
| Galactica 6.7B | `galactica`, `galactica_lora`, `galactica_int8`, `galactica_lora_int8` | Uses custom tokenizer settings. |
| GPT-J 6B | `gptj`, `gptj_lora`, `gptj_int8`, `gptj_lora_int8` | Causal LM family with CPU-adam finetune defaults. |
| GPT-2 | `gpt2`, `gpt2_lora`, `gpt2_int8`, `gpt2_lora_int8` | Classic GPT-2 family; the default LoRA target is `c_attn`. |
| GPT-OSS 20B | `gpt_oss_20b`, `gpt_oss_20b_lora`, `gpt_oss_20b_int8`, `gpt_oss_20b_lora_int8`, `gpt_oss_20b_lora_kbit` | Harmony-format remote-code family with custom chat formatting. |
| GPT-OSS 120B | `gpt_oss_120b`, `gpt_oss_120b_lora`, `gpt_oss_120b_int8`, `gpt_oss_120b_lora_int8`, `gpt_oss_120b_lora_kbit` | Same notes as GPT-OSS 20B. |
| LLaMA | `llama`, `llama_lora`, `llama_int8`, `llama_lora_int8`, `llama_lora_kbit` | Custom tokenizer/model loaders; K-bit variant exists. |
| LLaMA 2 | `llama2`, `llama2_lora`, `llama2_int8`, `llama2_lora_int8`, `llama2_lora_kbit` | Remote-code family with K-bit support. |
| Mamba | `mamba` | Base only; no LoRA or quantized public variants. |
| Mistral 7B | `mistral_7b` | Base only. |
| Ministral 3.14B | `ministral_3_14b`, `ministral_3_14b_lora`, `ministral_3_14b_int8`, `ministral_3_14b_lora_int8`, `ministral_3_14b_lora_kbit` | Remote-code family with higher default generation length. |
| MiniMaxM2 | `minimax_m2`, `minimax_m2_lora`, `minimax_m2_int8`, `minimax_m2_lora_int8`, `minimax_m2_lora_kbit` | Remote-code family; K-bit variant exists. |
| OPT 1.3B | `opt`, `opt_lora`, `opt_int8`, `opt_lora_int8` | Standard decoder family. |
| Qwen3 0.6B | `qwen3_0_6b`, `qwen3_0_6b_lora`, `qwen3_0_6b_int8`, `qwen3_0_6b_lora_int8`, `qwen3_0_6b_lora_kbit` | Remote-code family with K-bit support. |
| Generic wrapper | `generic`, `generic_lora`, `generic_int8`, `generic_lora_int8`, `generic_lora_kbit` | Use for arbitrary Hugging Face-compatible checkpoints or local directories. The direct constructors are the normal entry point. |
| Stable Diffusion | `stable_diffusion` | Registered placeholder only; instantiation raises `NotImplementedError`. |

## Generic wrappers

Use these constructors when the checkpoint is not already covered by a family-specific wrapper:

- `GenericModel(model_name)`
- `GenericInt8Model(model_name)`
- `GenericLoraModel(model_name, target_modules=...)`
- `GenericLoraInt8Model(model_name, target_modules=...)`
- `GenericLoraKbitModel(model_name, target_modules=...)`

`model_name` may be a Hugging Face repo ID or a local checkpoint directory. If you need the exact family-backed round-trip behavior, prefer one of the registry-backed model keys above.

## Bundled `x/...` hub entries

These are the only public hub paths currently mapped by the model hub helper.

| Hub path | What it resolves to |
| --- | --- |
| `x/gpt2` | bundled GPT-2 checkpoint |
| `x/gpt2_lora` | bundled GPT-2 LoRA checkpoint |
| `x/distilgpt2` | bundled DistilGPT-2 checkpoint |
| `x/distilgpt2_lora` | bundled DistilGPT-2 LoRA checkpoint |
| `x/llama_lora` | bundled LLaMA LoRA checkpoint |
| `x/distilgpt2_lora_finetuned_alpaca` | bundled fine-tuned DistilGPT-2 LoRA checkpoint |
| `x/llama_lora_finetuned_alpaca` | bundled fine-tuned LLaMA LoRA checkpoint |
| `x/llama_lora_int4` | bundled LLaMA LoRA INT4 checkpoint |

## Quick notes

- `gpt_oss_*`, `minimax_m2`, `qwen3_0_6b`, `falcon`, `llama2`, and `ministral_3_14b` rely on model-specific loaders or remote-code settings.
- Large-model presets often use `max_new_tokens=512` and often prefer contrastive-search-style defaults.
- The `generic` registry key exists so load-time routing can reconstruct generic checkpoints, but the usual forward constructor is `GenericModel(...)`.
- `stable_diffusion` is reserved for future work and is not a usable inference target.
