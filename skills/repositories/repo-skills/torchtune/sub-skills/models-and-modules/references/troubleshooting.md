# Troubleshooting Models And Modules

Use this matrix before running expensive training, generation, or conversion jobs.

## Failure Matrix

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `_component_` imports from a path containing `._model_builders`, `._component_builders`, or another underscore module fail after an upgrade | Config uses private implementation dotpaths | Replace with public exports such as `torchtune.models.llama3.llama3_8b` or `torchtune.modules.peft.LoRALinear`. Use `scripts/inspect_model_builders.py` to list active public exports. |
| `ImportError` mentions optional packages such as low-precision or quantization support | Environment is missing optional dependencies needed by torchtune import, QLoRA, or quantized modules | Install the documented optional dependency set for the selected workflow, or switch configs from `qlora_*`/`quantize_base: true` to regular LoRA until dependencies are available. |
| Download or checkpoint loading fails for Meta Llama, Llama 4, or other gated models | Model license/access was not accepted or token was not provided to the download step | Request model access, provide a token through the CLI/environment, and keep credentials out of YAML committed to projects. |
| Tokenizer loads but generated text is garbled or dataset tokenization fails | Tokenizer family or file layout does not match the model builder | Pair Llama 3.x with `llama3_tokenizer`, Qwen with matching vocab/merges files, Phi/Gemma/Mistral with their family tokenizers, and multimodal rows with the family transform. |
| Special token IDs are missing or wrong | `special_tokens_path` points at a JSON mapping not compatible with the underlying tokenizer vocabulary | Use the special-token file shipped with the model, or verify the IDs are supported before overriding. Special-token JSON does not add new vocabulary entries by itself. |
| LoRA config errors on target modules | `lora_attn_modules` names do not match the family builder | Start with tested names such as `q_proj` and `v_proj`, then consult the family builder signature/tests for `k_proj`, `output_proj`, MLP, or multimodal fusion support. |
| Adapter checkpoint load has missing adapter keys | Loading a base checkpoint into a LoRA model with strict semantics | Use non-strict loading where appropriate and validate that missing keys are adapter-only via `validate_missing_and_unexpected_for_lora`. |
| Adapter checkpoint load has unexpected full-base keys | Trying to load full model state as adapter-only state, or adapter-only state into a base model | Extract adapter-only keys with `get_adapter_state_dict`, or merge adapters with `get_merged_lora_ckpt` before loading into a base model for inference/export. |
| QLoRA construction fails or quantized weights are wrong dtype | `quantize_base` dependencies/config are absent or incompatible | Verify low-precision dependencies, avoid extra quantization kwargs when `quantize_base` is false, and test with tiny tensors before full checkpoint loading. |
| State-dict conversion produces shape/key mismatches | Wrong conversion helper for the family, wrong head counts, tied-embedding setting, or checkpoint source format | Match conversion helper to checkpoint provenance; pass `num_heads`, `num_kv_heads`, `dim`, `head_dim`, and `tie_word_embeddings` values that match the model. |
| Tiny model experiments pass but real checkpoint loading OOMs | A builder was instantiated with full production dimensions or checkpoint tensors were loaded eagerly | Use config/signature inspection for planning, memory-map/load on CPU where supported by the workflow, and run only approved full-size jobs. |
| Exported checkpoint cannot be used by downstream tools | Adapter was not merged, wrong PEFT conversion path, or export module variant mismatch | Decide between adapter-only, merged base, and PEFT adapter formats. Use conversion utilities and route deployment/quantization details to `../inference-evaluation-quantization/SKILL.md`. |

## Tokenizer/Model Family Mismatch Case

Before training, compare these fields:

- Model builder family and size, such as `torchtune.models.qwen2_5.qwen2_5_7b_instruct`.
- Tokenizer builder family, such as `torchtune.models.qwen2_5.qwen2_5_tokenizer`.
- Required tokenizer artifacts: Qwen vocab/merges, SentencePiece `tokenizer.model`, Hugging Face `tokenizer.json`, or family special tokens.
- `max_seq_len` on model and tokenizer/model transform.
- Chat template or special-token behavior expected by the instruct/base checkpoint.

If these do not match, fix the config before touching dataset rows or recipe parameters.

## Private Dotpath Repair

Bad config pattern:

```yaml
model:
  _component_: torchtune.models.llama3._model_builders.llama3_8b
```

Public replacement:

```yaml
model:
  _component_: torchtune.models.llama3.llama3_8b
```

Use the same rule for tokenizers, transforms, and modules. Private source files may be useful for understanding implementation details, but public runtime configs should use package exports.

## Gated Downloads And Local Artifacts

- Do not put access tokens in configs. Use CLI flags, environment variables, or secret managers outside reusable skill content.
- Confirm model access before debugging tokenizer or state-dict errors; a partial download can mimic model/tokenizer mismatch.
- Some registry configs intentionally ignore original checkpoint shards for certain downloads; inspect with `tune cat` or `tune cp` before changing patterns.

## Conversion Debugging Checklist

1. Identify source format: Meta, Hugging Face, torchtune, adapter-only, or PEFT adapter.
2. Choose the family-specific converter when available; use generic converters only when the family follows the generic key layout.
3. Confirm model dimensions and attention head parameters before converting Q/K/V projections.
4. Check tied embeddings and output projection behavior before saving.
5. Run a small key-shape sample first when possible; do not load or save multi-shard checkpoints as a blind first step.

## Export Variant Notes

Export-oriented module variants can differ from training modules for deployment compatibility. Unless the task is explicitly about export/deployment, stay with public training modules and conversion utilities. When the task moves to generation, evaluation, post-training quantization, or deployment packaging, use `../inference-evaluation-quantization/SKILL.md`.
