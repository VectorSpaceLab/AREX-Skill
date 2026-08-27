---
name: save-load-merge
description: "Save, load, inspect, merge, hotswap, mix, and convert PEFT
  adapters and checkpoints for local or Hub workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Save, Load, and Merge

Use this sub-skill when the task is about PEFT checkpoint files, `save_pretrained`, `from_pretrained`, `AutoPeftModel*`, adapter state dicts, Hub loading, `merge_and_unload`, `PeftMixedModel`, hotswapping adapters, weighted adapter merging, conversion helpers, or deployment packaging.

## Route Here For

- Inspecting or repairing adapter folders containing `adapter_config.json` plus `adapter_model.safetensors` or `adapter_model.bin`.
- Loading adapters with `PeftModel.from_pretrained`, `PeftConfig.from_pretrained`, `AutoPeftModel*`, or `load_adapter`.
- Saving adapter-only checkpoints with `save_pretrained`, including non-default adapter subdirectories and embedding-layer save decisions.
- Loading multiple adapters, activating one or several adapters, using `PeftMixedModel`, or hotswapping LoRA weights in place.
- Merging adapters into base weights with `merge_and_unload` or creating weighted LoRA/(IA)³ adapters with `add_weighted_adapter`.
- Converting compatible non-LoRA adapters or Transformers-loaded PEFT weights into LoRA-style artifacts.
- Diagnosing bad loaded outputs, missing base models, random new-token embeddings, version mismatches, slow loads, and merge limitations.

## Route Elsewhere

- Initial adapter wrapping with `get_peft_model`, `PeftConfig`, target module selection, and adapter lifecycle basics: use `../adapter-core/SKILL.md`.
- LoRA variant choices, quantized-base setup, DoRA, rsLoRA, QLoRA, LoftQ, QALoRA, or trainable-token configuration: use `../lora-and-quantization/SKILL.md`.
- Method-specific limits for prompt tuning, IA³, OFT/BOFT, VeRA, LoHa/LoKr, Poly, FourierFT, or other tuners: use the relevant method sub-skill.
- Trainer, Accelerate, distributed, FSDP, DeepSpeed, or training launch mechanics: use `../training-and-integrations/SKILL.md`.

## Start Fast

1. Run `python scripts/inspect_adapter_checkpoint.py <adapter-dir>` from this sub-skill directory to check local adapter files without network access.
2. Read `references/checkpoints.md` for checkpoint layout, save/load class selection, state dict helpers, Hub/local loading, and embedding save rules.
3. Read `references/merge-and-conversion.md` for `merge_and_unload`, weighted adapter merging, mixed adapters, hotswap, and conversion utilities.
4. Read `references/troubleshooting.md` when loaded results look wrong or errors mention base models, vocab/embeddings, unexpected config keys, slow adapter load, active adapters, or unsupported merges.

## Core Save/Load Pattern

```python
from peft import PeftConfig, PeftModel
from transformers import AutoModelForCausalLM

adapter_id = "org-or-path/my-adapter"
config = PeftConfig.from_pretrained(adapter_id)
base_model = AutoModelForCausalLM.from_pretrained(config.base_model_name_or_path)
model = PeftModel.from_pretrained(base_model, adapter_id)
```

Use `AutoPeftModelForCausalLM.from_pretrained(adapter_id)` when the adapter config contains enough base-model and task information and you want PEFT to infer the model class. Use the explicit `PeftConfig` + Transformers base model pattern when you need full control over dtype, quantization, `device_map`, local files, revisions, or base-model class.

## Checkpoint Rules of Thumb

- PEFT adapter checkpoints are adapter-only by default; they do not contain the full base model.
- A loadable adapter directory needs `adapter_config.json` and either `adapter_model.safetensors` or `adapter_model.bin`.
- `adapter_config.json` should identify `peft_type`; `task_type` and `base_model_name_or_path` strongly improve automatic loading and handoff quality.
- `adapter_model.safetensors` is preferred over `.bin`; both carry the adapter `state_dict`.
- Non-default adapters are saved in a subdirectory named after the adapter, while the adapter name is stripped from saved state-dict keys.
- If training added vocabulary tokens or trained task heads, ensure embeddings or heads were saved with `save_embedding_layers=True`, `modules_to_save`, or method-specific trainable-token settings.

## Merge and Deployment Decision Pattern

- Keep adapter checkpoints for continued PEFT operations: loading multiple adapters, disabling adapters, switching adapters, hotswapping, or sharing compact files.
- Use `merged_model = model.merge_and_unload()` when deployment needs a plain Transformers model and the method/settings support merging.
- Do not expect to unmerge after saving a merged full model; merging discards PEFT wrapper functionality in the returned model.
- Use `model.add_weighted_adapter(...)` to create a new adapter from compatible loaded adapters before selecting it with `set_adapter`.
- Use `PeftMixedModel` only for inference-time composition of compatible adapter types; mixed adapter models are not a portable saved mixed checkpoint.
- Use hotswap for replacing compatible LoRA weights in place, especially to avoid recompilation after `torch.compile`.

## Bundled Materials

- `references/checkpoints.md`: concrete file layout, save/load workflows, state dict helpers, Hub/local loading, AutoPeftModel choices, and embedding persistence.
- `references/merge-and-conversion.md`: merge/unload, weighted merges, mixed adapters, hotswap constraints, and conversion helpers.
- `references/troubleshooting.md`: focused diagnosis for bad outputs, missing bases, random embeddings, version drift, slow loading, adapter activation, and merge failures.
- `scripts/inspect_adapter_checkpoint.py`: no-network local adapter directory inspector with class hints and tiny fixture generation.
