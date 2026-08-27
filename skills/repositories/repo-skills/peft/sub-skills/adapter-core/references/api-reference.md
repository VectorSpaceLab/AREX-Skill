# Adapter Core API Reference

This reference covers PEFT adapter primitives that are shared across methods. Method-specific arguments belong in the method sub-skill; for example, LoRA-specific rank, dropout, DoRA, rsLoRA, and quantization details belong in `lora-and-quantization`.

## Installation And Import Surface

Generic install choices:

```bash
pip install peft
# or, for contributors working from a local source tree:
pip install -e .
```

Typical imports:

```python
from peft import LoraConfig, PeftConfig, PeftModel, TaskType, get_peft_model
from peft import get_layer_status, get_model_status, inject_adapter_in_model
```

Verified package facts for this generated skill:

- Package version observed during skill generation: `peft 0.19.2.dev0`.
- Python support: Python `>=3.10`.
- No PEFT console entry points are required for core adapter workflows.
- Common optional ecosystem imports for full workflows are `torch`, `transformers`, and `accelerate`.

## Enums And Base Configs

`TaskType` identifies the task wrapper PEFT should use for common Transformers workflows. Common values include:

- `TaskType.CAUSAL_LM`
- `TaskType.SEQ_2_SEQ_LM`
- `TaskType.SEQ_CLS`
- `TaskType.TOKEN_CLS`
- `TaskType.QUESTION_ANS`
- `TaskType.FEATURE_EXTRACTION`

`PeftType` identifies the adapter method, such as `PeftType.LORA`, `PeftType.IA3`, `PeftType.PREFIX_TUNING`, or other registered PEFT methods.

`PeftConfig` is the base config class. It stores fields such as `task_type`, `peft_type`, `auto_mapping`, `peft_version`, `base_model_name_or_path`, `revision`, and `inference_mode`. Most user workflows instantiate a method-specific config, for example `LoraConfig`, and then use `PeftConfig.from_pretrained(...)` only when loading an existing adapter directory or model id.

Important validation behavior:

- Invalid `task_type` values raise a `ValueError` listing valid `TaskType` values.
- Method configs set their own `peft_type` during construction.
- Configs often normalize list-style `target_modules` to a set after initialization or loading.
- Regex `target_modules` strings cannot be combined with layer-index filters such as `layers_to_transform` or `layers_pattern` for methods that expose those filters.

## Wrapping Models

`get_peft_model(model, peft_config, adapter_name="default", mixed=False, autocast_adapter_dtype=True, revision=None, low_cpu_mem_usage=False)` returns a `PeftModel` or compatible mixed adapter wrapper.

Use it when:

- You want PEFT lifecycle helpers such as `add_adapter`, `load_adapter`, `set_adapter`, `disable_adapter`, `delete_adapter`, `save_pretrained`, and trainable/status helpers.
- You are starting training from a base model plus a new config.
- You need task-aware behavior for common Transformers tasks.

Avoid using `get_peft_model` to load already-trained adapter weights into a base model. Use the save/load sub-skill for checkpoint loading patterns.

`PeftModel(model, peft_config, adapter_name="default", autocast_adapter_dtype=True, low_cpu_mem_usage=False)` is the wrapper class behind standard PEFT models. Direct construction is uncommon; prefer `get_peft_model` unless you are implementing advanced integration code.

## Adapter Lifecycle Helpers

Common `PeftModel` methods:

- `add_adapter(adapter_name, peft_config, low_cpu_mem_usage=False)`: attach another adapter config to the same base model.
- `load_adapter(...)`: load adapter weights into an existing `PeftModel`; use the save/load sub-skill for full checkpoint workflows.
- `set_adapter(adapter_name, inference_mode=False)`: activate one adapter by name. Some base tuners support a list of adapter names; use `model.base_model.set_adapter([...])` when stacking compatible low-level tuners rather than relying on `PeftModel.set_adapter` for all methods.
- `disable_adapter()`: context manager that temporarily disables adapters and runs the base model path.
- `delete_adapter(adapter_name)`: remove an adapter from the model.
- `print_trainable_parameters()`: print trainable parameter count and percentage.

Use unique adapter names that do not conflict with PEFT prefixes in state dict keys. The default adapter name is `"default"`.

## Status Helpers

Use status helpers when adapter state is ambiguous after loading, adding, merging, disabling, deleting, or stacking adapters.

`model.get_layer_status()` returns per-target-layer records with fields such as layer name, module type, enabled state, active adapters, merged adapters, available adapters, and whether adapter weights are trainable.

`model.get_model_status()` summarizes the whole model, including base model type, adapter model type, configured adapters, active adapters, merged adapters, whether adapters are enabled, trainable parameter counts, and aggregate trainable percentage.

Module-level helpers also exist:

```python
from peft import get_layer_status, get_model_status

layer_status = get_layer_status(model_or_submodule)
model_status = get_model_status(model_or_submodule)
```

The module-level forms are useful for integrations that attach PEFT tuners to submodules rather than wrapping the whole object as a `PeftModel`.

## Target Module Selection

Many adapter methods insert trainable layers by matching module names. `target_modules` can be:

- A list or set of module-name suffixes, such as `["q_proj", "v_proj"]` or `["encoder.block.0.layer.0.SelfAttention.q"]`.
- A regex string, such as `r".*\.mlp\.fc\d"`.
- A method-supported shorthand such as `"all-linear"` for methods that support it.
- `None` when the method can infer default targets from a recognized Transformers architecture.
- An empty list for methods/workflows that intentionally use `target_parameters` instead of module replacement.

For custom models, inspect `model.named_modules()` and pass explicit target names. Do not rely on Transformers architecture defaults unless the model exposes a supported architecture config.

Use `modules_to_save` for extra modules that should remain trainable and be included in adapter checkpoints, such as task heads, custom classifier heads, resized embeddings, batch norm layers needed for reproducibility, or non-adapter layers that the task updates.

## Custom Models And Unsupported Modules

PEFT supports many `torch.nn.Module` models, not only Transformers classes, when the adapter method supports the targeted module type. For custom models:

1. Print or inspect `dict(model.named_modules()).keys()`.
2. Choose explicit `target_modules` suffixes or regex patterns that match only intended layers.
3. Add non-adapter heads to `modules_to_save` when they must train and save with the adapter.
4. Call `get_peft_model` and verify trainable counts/status before training.
5. If PEFT warns that a targeted module type is unrecognized, confirm whether the method supports a custom replacement module or whether a different target layer should be selected.

Some adapter methods support custom module mappings for advanced cases. Custom replacement modules should accept `base_layer` and `adapter_name` positional arguments and tolerate method-specific keyword arguments.

## Low-Level Injection API

`inject_adapter_in_model(peft_config, model, adapter_name="default", low_cpu_mem_usage=False, state_dict=None)` injects adapter layers into a plain model and returns that model instead of a `PeftModel` wrapper.

Use it when:

- You need PEFT layers in a non-Transformers or integration-owned module.
- You do not need `PeftModel` methods such as `disable_adapter`, merging helpers, or task wrappers.
- You are integrating with another library that already owns model wrapping.

Limits:

- Prompt-learning adapters are not supported by low-level injection.
- You must manage training, saving, activation, and state dict handling explicitly with functional helpers.
- Injecting from a `state_dict` can infer target modules for module-targeting adapters, but workflows based on `target_parameters` still require an accurate config.

Related functional helpers include `get_peft_model_state_dict`, `set_peft_model_state_dict`, `set_adapter`, and `delete_adapter` for non-`PeftModel` integrations.
