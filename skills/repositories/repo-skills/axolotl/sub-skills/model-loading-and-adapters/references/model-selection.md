# Model Selection, Tokenizers, Processors, and Attention

Use this reference when choosing Axolotl model-loading fields or diagnosing model-family-specific config failures. Axolotl is config-driven: future agents should edit YAML and validate with Axolotl commands instead of changing code unless they are explicitly adding model support.

## Loading Surface

Start from these fields:

| Need | Axolotl fields | Guidance |
| --- | --- | --- |
| Base weights | `base_model`, optional `base_model_config` | `base_model` is the model repo or local model path. Use `base_model_config` only when config files live somewhere else. |
| Tokenizer override | `tokenizer_config`, `tokenizer_type`, `tokenizer_use_fast`, `tokenizer_legacy`, `tokenizer_use_mistral_common` | Leave unset unless the model family requires a different tokenizer or a known slow/legacy tokenizer path. |
| Processor for multimodal | `processor_type`, optional `processor_kwargs` | Use `processor_type: AutoProcessor` for most VLMs. Mistral/Voxtral families may use Mistral-common/Voxtral-specific processors. |
| Remote modeling code | `trust_remote_code` | Set only when the model requires reviewed remote code. It affects tokenizer/model/processor loading and is incompatible with LoRA kernel optimizations. |
| Model class override | `model_type`, `cls_model_config` | Prefer auto loading; use explicit classes only for known model support needs. |
| Revision | `revision_of_model` | Pins model/tokenizer/processor revision consistently. |

When a user says “tokenizer mismatch,” inspect `base_model`, `tokenizer_config`, `chat_template`, `special_tokens`, `tokens`, `eot_tokens`, and any adapter setting that requires `lora_modules_to_save` after token additions.

## Text vs Multimodal Decision

For text-only SFT/pretraining, Axolotl usually loads `AutoModelForCausalLM` and `AutoTokenizer`. For multimodal models, the loader selects a multimodal auto class and Axolotl may need a processor.

Multimodal starter fields:

```yaml
processor_type: AutoProcessor
skip_prepare_dataset: true
remove_unused_columns: false
sample_packing: false
chat_template: qwen2_vl  # or gemma4, gemma3, qwen3_5, pixtral, llama4, etc.
```

Add `freeze_mm_modules: true` when training text-only or language-model-only adapters on a model with vision/audio encoders. Multimodal examples commonly keep LoRA targets constrained to `model.language_model...` or `language_model.model...` paths so adapters do not land on frozen vision/audio modules.

Do not promise feature parity for multimodal. Axolotl docs call multimodal support beta/limited, and multimodal preprocessing has special handling for image/audio tokens.

## Chat Template Choice

`chat_template` is both a tokenizer/rendering decision and a dataset prompt-strategy decision. If set at the top level, Axolotl propagates it to compatible `datasets` entries such as `type: chat_template`.

Common model-template pairings from Axolotl examples/docs:

| Family | Typical `chat_template` | Notes |
| --- | --- | --- |
| Gemma 4 | `gemma4` | All Gemma 4 variants load as multimodal wrappers; use `freeze_mm_modules: true` when appropriate. |
| Gemma 3 | `gemma3` | 1B can be text-only; larger variants may be vision-capable. |
| Gemma 3n | `gemma3n` | Vision/audio variants need processor and no sample packing. |
| Qwen2/2.5/3 VL | `qwen2_vl` | VLM configs require processor and multimodal dataset handling. |
| Qwen3.5 | `qwen3_5` | Includes text, MoE, and vision examples. |
| Llama 3.2 Vision | `llama3_2_vision` | Multimodal wrapper path. |
| Llama 4 | `llama4` | Multimodal/MoE-aware config choices may matter. |
| Pixtral | `pixtral` | Processor required. |

If `axolotl inference` or preprocessing says there is no chat template, add a model-appropriate `chat_template` or confirm the tokenizer already carries one.

## Attention Backend Selection

Use canonical `attn_implementation` names; short aliases such as `flash`, `flex`, and `sdp` are rejected. Legacy booleans such as `flash_attention: true` still map to canonical values with deprecation warnings, but future configs should use the canonical field.

| Value | Use when | Watch for |
| --- | --- | --- |
| `flash_attention_2` | Common fast CUDA path with sample packing support | Needs compatible flash-attn install/GPU; head-dim limits can matter. |
| `flash_attention_3` | Hopper FA3 path | Requires appropriate CUDA/FA3 install. |
| `flex_attention` | Variable head dims, some Gemma 4 configs, torch compile workflows | Torch/Triton constraints; large head dims can be slow or OOM. |
| `sdpa` | Safe PyTorch fallback | Axolotl warns for sample packing because it does not handle cross-sample decontamination. |
| `eager` | Debug fallback | Slow; no packing support. |
| `xformers` | Turing/older GPU fallback or xFormers setup | Requires xFormers. |
| `sage` | SageAttention experiments, LoRA/QLoRA recommended | Full fine-tuning is discouraged in Axolotl docs/tests. |
| `fp8` | torchao FP8 attention on SM90+ | Strict PyTorch/torchao/GPU requirements and no KV cache. |

`gemma4_hybrid_attn_impl: true` requires `attn_implementation: flash_attention_2`; Axolotl then runs compatible Gemma 4 sliding-window layers under FA2 and global layers under SDPA.

## Architecture Notes

### Gemma 4

- All variants load as multimodal wrappers, even text-oriented variants.
- For text-only or language-model-only LoRA, use `freeze_mm_modules: true` and restrict LoRA with a regex targeting `model.language_model.layers...`.
- Do not use `lora_target_linear: true` on multimodal Gemma 4; it can target vision/audio modules.
- Gradient checkpointing needs `use_reentrant: false`; Axolotl auto-adjusts Gemma 4 in normalized config.
- DDP may need unused-parameter handling unless activation offloading changes the constraint.
- Gemma 4 has attention head-dim constraints: configs use `flex_attention`, `sdpa`, or `gemma4_hybrid_attn_impl` depending on model/run.
- MoE variants can combine `quantize_moe_experts`, `lora_target_parameters`, and ScatterMoE kernels.

### Gemma 3 / Gemma 3n

- Gemma 3 1B can be treated as text-only; larger variants can be multimodal.
- Vision configs use processor, `skip_prepare_dataset: true`, `remove_unused_columns: false`, `sample_packing: false`, and `chat_template: gemma3`.
- Gemma 3n vision/audio examples use `chat_template: gemma3n`; docs call out extra optional deps for some modalities.

### Qwen 3.5 / Qwen MoE / Qwen VL

- Qwen3.5 uses hybrid attention/linear-attention patterns in newer examples.
- MoE routed expert parameters are 3D tensors; use `lora_target_parameters` for routed experts rather than only `lora_target_modules`.
- Shared experts can be targeted through `lora_target_modules` because they are linear modules.
- Vision configs use `processor_type: AutoProcessor`, `sample_packing: false`, and `chat_template: qwen3_5` or `qwen2_vl` depending on the model family.

### Mistral / Pixtral / Voxtral

- Mistral-derived models may require left padding under Flash Attention when not packing.
- Some Mistral vision/audio families need Mistral-common extras or tokenizer/processor choices; keep this as an environment prerequisite rather than a runtime skill dependency.
- Voxtral audio examples use `processor_type: VoxtralProcessor` and often `tokenizer_use_mistral_common` patterns.
- Pixtral uses processor + `chat_template: pixtral` with multimodal dataset handling.

### Llama / Mllama / Llama 4

- Standard Llama text configs are the safest baseline for LoRA/QLoRA and QAT examples.
- Llama vision/multimodal wrappers need processor/chat template choices.
- Llama 4 has model-specific patch paths in Axolotl for linearized experts and multimodal/MoE handling.

## Validation Order

1. Run `python scripts/check_model_config.py config.yaml` from this sub-skill for static warnings.
2. Run `axolotl preprocess config.yaml` in the user’s Axolotl environment for schema, tokenizer, processor, and dataset validation.
3. Use `axolotl preprocess config.yaml --debug` when chat templates, labels, image/audio features, or sample packing need inspection.
4. Only then run `axolotl train config.yaml` if the task actually asks for training and hardware/runtime prerequisites are ready.

Do not use this skill’s static helper as proof that a model loads; it intentionally avoids imports/downloads/model loading.
