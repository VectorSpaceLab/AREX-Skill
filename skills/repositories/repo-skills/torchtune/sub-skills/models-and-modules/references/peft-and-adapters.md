# PEFT And Adapters

torchtune exposes LoRA, QLoRA, DoRA, and QAT-LoRA through public family builders and reusable PEFT modules. Prefer family `lora_*` and `qlora_*` builders in configs; use low-level modules only when building a custom model.

## Choosing Adapter Builders

| Task | Use |
| --- | --- |
| Standard LoRA fine-tuning | Family builders such as `torchtune.models.llama3.lora_llama3_8b`, `torchtune.models.qwen2_5.lora_qwen2_5_7b_instruct`, or `torchtune.models.mistral.lora_mistral_7b`. |
| QLoRA fine-tuning | Family `qlora_*` builder when exported, or family `lora_*` with `quantize_base: true` only after optional low-precision dependencies are present. |
| DoRA | Family `lora_*` builders with `use_dora: true` when supported, or low-level `DoRALinear` in custom components. |
| QAT-LoRA | `torchtune.modules.peft.QATLoRALinear` in custom modules or QAT-aware recipes/configs. |
| Multimodal LoRA | Family vision builders that expose decoder, encoder, and fusion trainability separately, such as Llama 3.2 Vision and Llama 4 builders. |
| Adapter-only save/export | `get_adapter_state_dict`, `get_merged_lora_ckpt`, and PEFT conversion utilities. |

## Common Config Pattern

A family LoRA config should use public model builders and explicit target modules:

```yaml
model:
  _component_: torchtune.models.llama3_2.lora_llama3_2_1b
  lora_attn_modules: [q_proj, v_proj]
  apply_lora_to_mlp: false
  apply_lora_to_output: false
  lora_rank: 8
  lora_alpha: 16
  lora_dropout: 0.0
  quantize_base: false
```

Switch to QLoRA only when the runtime has the low-precision dependencies needed by `quantize_base`:

```yaml
model:
  _component_: torchtune.models.llama3_2.qlora_llama3_2_1b
  lora_attn_modules: [q_proj, v_proj]
  apply_lora_to_mlp: true
  apply_lora_to_output: false
  lora_rank: 16
  lora_alpha: 32
```

For a custom component, use low-level PEFT modules directly:

```python
from torchtune.modules.peft import LoRALinear

adapter = LoRALinear(
    in_dim=4096,
    out_dim=4096,
    rank=8,
    alpha=16,
    dropout=0.0,
    quantize_base=False,
)
```

## Target Module Names

`lora_attn_modules` names are logical projection names used by family builders. Common decoder families use combinations of:

- `q_proj`, `k_proj`, `v_proj`, `output_proj` for attention projections.
- `apply_lora_to_mlp: true` to include feed-forward projections when the family builder supports it.
- `apply_lora_to_output: true` to include final output projection when supported.
- Multimodal models may expose additional controls such as `decoder_trainable`, `encoder_trainable`, and `fusion_trainable` with values like `frozen`, `lora`, or trainable booleans depending on the builder.

Use the family builder signature and tests as the source of truth. If a config fails because a target name is unknown, check the active family builder rather than guessing private layer names.

## Adapter Utilities

| API | Use |
| --- | --- |
| `get_adapter_params(model)` | Return adapter parameters from modules implementing adapter metadata. Use before freezing base weights. |
| `set_trainable_params(model, adapter_params)` | Mark only adapter parameters trainable after collecting them. |
| `get_adapter_state_dict(state_dict, device="cpu")` | Extract adapter-only keys from a model state dict for saving or export. |
| `get_merged_lora_ckpt(state_dict, rank, alpha, use_distributed_barriers=False)` | Merge LoRA weights into base weights in a state dict for inference/export; keep rank/alpha consistent with training. |
| `disable_adapter(model)` | Context manager that temporarily disables adapter contribution for comparisons or reference logits. |
| `validate_missing_and_unexpected_for_lora(...)` | Validate strict/non-strict load results when moving between base and adapter-equipped models. |
| `get_lora_module_names(lora_attn_modules, apply_lora_to_mlp, apply_lora_to_output)` | Derive expected logical LoRA module names for validation. |

## Adapter State Dict Guidance

- Base checkpoints and adapter checkpoints intentionally have different key sets. Loading a base state dict into a LoRA model is usually non-strict and should leave only adapter keys missing.
- Adapter-only state dicts should contain LoRA/DoRA adapter keys, not full base weights. Use `get_adapter_state_dict` for save/export logic.
- Merging adapters into base weights changes the state dict for inference/export. Keep an unmerged adapter checkpoint if future continued fine-tuning is needed.
- QLoRA state dicts can contain quantized base representations and adapter weights; do not assume they are interchangeable with fp16/bf16 base-only checkpoints without the conversion/merge step used by the relevant workflow.
- For PEFT interoperability, use `torchtune.models.convert_weights.tune_to_peft_adapter_config` and `tune_to_peft_adapter_weights` after confirming the family conversion assumptions.

## Low Precision And QLoRA Notes

- `quantize_base=True` enables quantized base-weight behavior in LoRA/DoRA modules and requires optional low-precision support in the environment.
- If quantization kwargs are passed while `quantize_base=False`, PEFT module tests show this is treated as an error condition rather than a no-op.
- QLoRA builders are convenience wrappers around LoRA builders with quantized base weights. They still need the same target-module choices, tokenizer/checkpoint compatibility, and adapter-state handling.
- Use tiny tensors or family unit tests for adapter shape experiments; do not instantiate a full 7B+ model only to check target names.

## Difficult Case: Add Adapters To A Config

When asked to add LoRA adapters to an existing full fine-tune config:

1. Change `model._component_` to the same family's public `lora_*` builder, not a private builder.
2. Add `lora_attn_modules`, usually starting with `[q_proj, v_proj]` unless the family docs/tests show a different target set.
3. Decide `apply_lora_to_mlp` and `apply_lora_to_output` based on memory and task needs.
4. Add rank/alpha/dropout fields and keep `quantize_base: false` unless the user explicitly wants QLoRA and dependencies are installed.
5. Ensure optimizer parameter selection comes from trainable adapter params in the recipe/config; route launch details to `../post-training-recipes/SKILL.md`.
6. Plan adapter checkpoint handling: adapter-only save for continued LoRA work, merged checkpoint for inference/export, PEFT conversion only when needed.

## Difficult Case: Multimodal Adapter Scope

For Llama 3.2 Vision or Llama 4, do not assume text-only LoRA controls all trainable parameters. Check builder fields for decoder, encoder, and fusion trainability. A common safe split is decoder frozen/base plus LoRA/fusion adapters for task-specific multimodal SFT, but user goals and memory constraints should drive the choice.
