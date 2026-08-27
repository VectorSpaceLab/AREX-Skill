# New Model Support

Use this reference when a user asks why an Axolotl model family fails to load, whether a new architecture needs custom support, or which code/config touchpoints matter before opening a patch. Keep normal training recipes in sibling sub-skills.

## First Classification

Ask these questions before editing source:

1. Does the model load with standard `AutoConfig`, tokenizer, and the chosen auto model class?
2. Is it text-only `ForCausalLM`, multimodal `ForConditionalGeneration`/image-text-to-text, MoE, SSM/hybrid, or a pre-quantized checkpoint?
3. Does it require `trust_remote_code`, a custom tokenizer/processor, or an optional package?
4. Does the failure happen in config validation, tokenizer loading, processor loading, model loading, adapter injection, forward/loss, sample packing, attention backend, or checkpoint save/merge?
5. Is the user trying to train with LoRA/QLoRA, full fine-tune, QAT/PTQ, or inference/merge only?

Do not jump straight to monkeypatches when a YAML field fixes the issue.

## Safe Validation Order

Use progressively more expensive checks:

1. Static YAML review with this sub-skill’s `scripts/check_model_config.py`.
2. `axolotl preprocess config.yaml` to catch schema, tokenizer, processor, and dataset issues.
3. `axolotl preprocess config.yaml --debug` to inspect rendered tokens, labels, chat template, and masking.
4. A tiny `axolotl train config.yaml` only when the user has the runtime stack and explicitly wants training validation.
5. Direct model-forward comparison only for advanced loss debugging in a controlled environment.

The Axolotl agent docs describe direct-forward comparison using `load_cfg`, `normalize_config`, `prepare_plugins`, `load_tokenizer`, and `ModelLoader`, but future agents should only run that when the user agrees to model loading/downloads and has the hardware/runtime ready.

## Loader Touchpoints

When source changes are actually needed, inspect these Axolotl areas by responsibility:

| Symptom | Likely touchpoint | What to verify |
| --- | --- | --- |
| Config class missing | config/model-loading utilities | Whether `base_model_config`, `cls_model_config`, `trust_remote_code`, or pre-config patches are enough. |
| Tokenizer fails | tokenizer loader | `tokenizer_config`, tokenizer class, `tokenizer_use_fast`, Mistral-common/Kimi-style special cases, special token handling. |
| Processor fails | processor loader | `processor_type`, `processor_config`, `processor_kwargs`, `trust_remote_code`, Mistral/Voxtral-specific processor logic. |
| Wrong auto model class | model loader multimodal mapping | Whether `is_multimodal` is derived and the loader uses image-text/conditional-generation class. |
| Adapter injection fails | adapter loader / PEFT config | Unsupported layer type, `lora_target_modules`, `lora_target_parameters`, ClippableLinear-like wrappers, plugin adapter support. |
| Attention backend crash | patch manager / attention monkeypatches | `attn_implementation`, backend availability, head dim limits, model support flags. |
| Packing loss spike | trainer loss path / model-specific masking | Whether the model uses new `create_causal_mask` behavior and needs attention-mask removal with packed sequences. |
| Loss logging inflated | trainer init / forward signature | Whether `model_accepts_loss_kwargs` or `num_items_in_batch` normalization is wrong. |
| Missing multimodal inputs | trainer compute loss / collator | Extra inputs such as token type IDs, pixel/audio values, or processor output fields. |
| Expert kernels no-op | model loader / expert interface | Whether the model exposes Transformers `ExpertsInterface` for `experts_implementation`. |

## Common Model-Support Patterns

### Multimodal wrappers

Many current VLMs load as `ForConditionalGeneration` rather than `ForCausalLM`. This matters for:

- CCE patches, which may patch causal-LM classes but miss conditional-generation classes.
- LoRA/PEFT, because vision towers may include custom linear wrappers.
- Trainer inputs, because image/audio models may require extra fields even for text-only data.
- Sample packing, because multimodal configs usually set `sample_packing: false`.

Start with YAML: `processor_type`, `chat_template`, `skip_prepare_dataset`, `remove_unused_columns`, `sample_packing`, `freeze_mm_modules`, and language-backbone LoRA targets.

### New masking systems and sample packing

Some newer Transformers models detect packed sequences from `position_ids` only when `attention_mask` is absent. If loss jumps toward random-token loss with packing enabled, compare packed vs non-packed and inspect whether Axolotl removes attention masks for that model family.

Older Llama/Mistral/Qwen2-style models generally use Axolotl multipack attention patches; newer Gemma-style masking may need model-specific handling.

### Attention head-dim and backend limits

A model can support Flash Attention generally but still fail for specific layers with large head dimensions. Gemma 4 examples use `flex_attention`, `sdpa`, or hybrid FA2/SDPA handling because global layers exceed FA kernel limits. Do not assume `attn_implementation: flash_attention_2` is always best.

### MoE and expert parameters

MoE support can involve three distinct concerns:

- Adapter targeting: routed expert tensors may need `lora_target_parameters`.
- Expert quantization: `quantize_moe_experts` has CUDA and adapter/low-bit requirements.
- Expert implementation: `experts_implementation: scattermoe` requires model support for the interface.

Validate each independently.

### Remote code

`trust_remote_code: true` may be necessary for unsupported hub models, but it is a security decision and disables LoRA kernel compatibility. Prefer native support or pinned/reviewed code where possible.

## Source Change Planning

When a source change is required, keep it narrow and add tests. Candidate files by change type:

- Config schema or validation: `utils/schemas/` and schema validation tests.
- Model/tokenizer/processor loading: loader modules and loader tests.
- Attention or model patches: patch manager and model-specific monkeypatch tests.
- PEFT/adapter compatibility: adapter loader and LoRA/MoE tests.
- Trainer loss or packed-sequence behavior: trainer tests plus one model-specific regression if feasible.
- Examples: add a minimal YAML under the matching model family after behavior is validated.

Do not add public runtime skill content that tells future agents to import or run source-repo test files directly. If a safe helper is needed, bundle it under the generated skill `scripts/` directory.

## Acceptance Criteria for a New-Model Fix

A credible new-model support plan should include:

- A minimal config YAML showing `base_model`, tokenizer/processor fields, adapter choice, attention backend, and dataset type.
- The exact failing phase and error message before the fix.
- A reason why YAML-only changes are insufficient.
- The model-loader/processor/adapter/trainer/patch-manager touchpoints to update.
- A test plan that avoids full training where possible: schema validation, tokenizer/processor smoke, adapter injection with tiny model/mock, or monkeypatch unit test.
- Known exclusions, such as optional packages not installed, gated model access, or GPU-only kernels.

## Hard Cases to Use During Review

- Qwen/Gemma multimodal QLoRA config: VLM wrapper with `processor_type: AutoProcessor`, `adapter: qlora`, `load_in_4bit: true`, language-backbone LoRA regex, missing `chat_template`, and an accidental `sample_packing: true`. The agent should flag missing/mismatched multimodal fields before training.
- Unsupported hybrid/MoE model: remote-code model where tokenizer loads but adapter injection fails on expert parameters. The agent should decide whether to use `lora_target_parameters`, disable LoRA kernels, add a plugin adapter, or plan a PEFT/model-specific patch with tests.
