# PEFT Checkpoints and Loading

## What `save_pretrained` writes

A normal PEFT adapter save is compact because it stores adapter parameters, not full base-model weights.

Required loading files:

- `adapter_config.json`: adapter metadata and method configuration.
- `adapter_model.safetensors` or `adapter_model.bin`: adapter `state_dict`; prefer safetensors for safer deserialization.

Common optional file:

- `README.md`: model card metadata; not required for loading.

Important `adapter_config.json` fields:

- `peft_type`: method family, such as `LORA`, `IA3`, `PROMPT_TUNING`, `LOHA`, or `LOKR`.
- `task_type`: task wrapper hint, such as `CAUSAL_LM`, `SEQ_2_SEQ_LM`, `SEQ_CLS`, `TOKEN_CLS`, `QUESTION_ANS`, or `FEATURE_EXTRACTION`.
- `base_model_name_or_path`: base model identifier or path used for the adapter; required in practice for one-line automatic loading.
- `revision`: optional base model revision.
- method-specific keys: for LoRA, expect keys such as `target_modules`, `r`, `lora_alpha`, `lora_dropout`, `bias`, `modules_to_save`, `use_rslora`, and `use_dora`.

## Save patterns

Adapter-only save:

```python
model.save_pretrained("my_adapter")
```

Save a specific adapter when several are loaded:

```python
model.save_pretrained("my_adapter", selected_adapters=["domain_a"])
```

If the adapter name is not `default`, PEFT saves it below a subdirectory named after the adapter. The saved state dict strips the adapter name, so the same checkpoint can be loaded later under a different `adapter_name`.

Prefer safetensors unless a legacy consumer requires pickle-based `.bin`:

```python
model.save_pretrained("my_adapter", safe_serialization=True)
```

When vocabulary was extended, task heads were trained, or extra non-adapter modules changed, verify persistence deliberately:

```python
model.save_pretrained("my_adapter", save_embedding_layers=True)
```

Use `modules_to_save` in the original PEFT config for classifier heads or other non-adapter modules that need to remain trainable and be saved with the adapter.

## Load patterns

Explicit and controllable load:

```python
from peft import PeftConfig, PeftModel
from transformers import AutoModelForCausalLM

adapter_id = "my_adapter"
peft_config = PeftConfig.from_pretrained(adapter_id)
base_model = AutoModelForCausalLM.from_pretrained(
    peft_config.base_model_name_or_path,
    torch_dtype="auto",
    device_map="auto",
)
model = PeftModel.from_pretrained(base_model, adapter_id, adapter_name="default")
```

Automatic PEFT class load:

```python
from peft import AutoPeftModelForCausalLM

model = AutoPeftModelForCausalLM.from_pretrained("my_adapter", torch_dtype="auto", device_map="auto")
```

Use `AutoPeftModel*` when the adapter config has a reliable `task_type` and `base_model_name_or_path`. Use explicit loading when the task class, dtype, quantization config, revision, tokenizer resize, local-only behavior, or base-model construction needs to be controlled.

Task-to-class hints:

| `task_type` | Typical PEFT auto class |
| --- | --- |
| `CAUSAL_LM` | `AutoPeftModelForCausalLM` |
| `SEQ_2_SEQ_LM` | `AutoPeftModelForSeq2SeqLM` |
| `SEQ_CLS` | `AutoPeftModelForSequenceClassification` |
| `TOKEN_CLS` | `AutoPeftModelForTokenClassification` |
| `QUESTION_ANS` | `AutoPeftModelForQuestionAnswering` |
| `FEATURE_EXTRACTION` | `AutoPeftModelForFeatureExtraction` |
| missing/unknown | `AutoPeftModel` or explicit `PeftConfig` + base model |

## Hub and local loading

The same `from_pretrained` APIs accept local directories or Hub model IDs. For production or reproducible workflows:

- Pin the adapter revision when loading from the Hub.
- Pin the base model revision if `adapter_config.json` records one or if the base model changes frequently.
- Use `local_files_only=True` when the task must not use network.
- Use explicit base loading when the adapter folder has no `base_model_name_or_path` or points to a private/missing base.

## Loading additional adapters

```python
model = PeftModel.from_pretrained(base_model, "adapter_a", adapter_name="a")
model.load_adapter("adapter_b", adapter_name="b")
model.set_adapter("b")
```

For multiple active adapters of the same model, use a list when the method supports it:

```python
model.set_adapter(["a", "b"])
```

If outputs do not change, inspect `model.active_adapters`, `get_model_status()`, and `get_layer_status()` before assuming the checkpoint is bad.

## State dict helpers

Use PEFT helpers rather than manually filtering keys when moving adapter weights between objects:

```python
from peft import get_peft_model_state_dict, set_peft_model_state_dict

adapter_state = get_peft_model_state_dict(model, adapter_name="default")
load_result = set_peft_model_state_dict(model, adapter_state, adapter_name="default")
```

Checkpoint keys often differ between in-memory and saved forms. In memory, adapter names can appear inside module dictionaries, such as `.lora_A.default.weight`. In saved files, PEFT strips the adapter name. This is expected.

## Conversion to PEFT format

A converted checkpoint needs both:

- Correctly named adapter weight keys in `adapter_model.safetensors` or `adapter_model.bin`.
- A matching `adapter_config.json` with at least `peft_type` plus enough method parameters to reconstruct adapter modules.

For LoRA-style conversion, weight keys normally include PEFT wrapper prefixes such as `base_model.model...` and layer names like `lora_A.weight`, `lora_B.weight`, or DoRA magnitude-vector entries when applicable. Prompt-learning methods store prompt parameters differently and should not be forced into LoRA key patterns.
