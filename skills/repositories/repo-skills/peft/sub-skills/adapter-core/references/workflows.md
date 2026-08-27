# Adapter Core Workflows

These workflows are safe starting points for core adapter work. They avoid model downloads unless the caller explicitly supplies an already loaded model.

## 1. Verify The Local PEFT Environment

From this sub-skill directory:

```bash
python scripts/check_peft_env.py
python scripts/check_peft_env.py --json
python scripts/check_peft_env.py --include-cuda
```

The script verifies `peft` import/version, optional ecosystem imports, `TaskType`/`PeftType`, `LoraConfig` construction, and CUDA facts only when requested. It does not download base models or adapters.

## 2. Wrap A Base Model With A New Adapter

Use this pattern after the caller already has a loaded `torch.nn.Module` or Transformers model:

```python
from peft import LoraConfig, TaskType, get_peft_model

peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,
    lora_alpha=8,
    lora_dropout=0.0,
    target_modules=["q_proj", "v_proj"],
)
peft_model = get_peft_model(base_model, peft_config, adapter_name="default")
peft_model.print_trainable_parameters()
status = peft_model.get_model_status()
```

Checklist before training:

- `task_type` matches the task wrapper when using a common Transformers task.
- `target_modules` are explicit for custom or unrecognized architectures.
- `modules_to_save` includes trainable non-adapter heads that must be saved with the adapter.
- `print_trainable_parameters()` is plausible for the expected adapter size.
- `get_model_status()` reports the intended active adapter and trainable status.

## 3. Target A Custom Non-Transformers Module

For custom `torch.nn.Module` models, discover names first:

```python
for name, module in model.named_modules():
    print(name, type(module).__name__)
```

Then target exact suffixes or a regex:

```python
from peft import LoraConfig, get_peft_model

config = LoraConfig(
    target_modules=["encoder.proj", "decoder.proj"],
    modules_to_save=["classifier"],
)
peft_model = get_peft_model(model, config)
peft_model.print_trainable_parameters()

trainable = [name for name, param in peft_model.named_parameters() if param.requires_grad]
assert any("lora" in name.lower() for name in trainable)
assert any("classifier" in name for name in trainable)
```

Use `modules_to_save` for custom heads, classification layers, or other non-adapter layers that must update and persist. If only adapter weights are trainable and the head is randomly initialized, later reloads can behave as if training failed because the head was not saved.

## 4. Diagnose Missing Target Modules

When PEFT raises that target modules were not found:

1. Print `model.named_modules()` and confirm the exact suffixes.
2. Check whether `target_modules` is a list/set of suffixes or a regex string; do not accidentally pass a regex-looking string when suffix matching was intended.
3. For recognized Transformers models, try method defaults only if the architecture is supported; otherwise pass explicit targets.
4. For `"all-linear"`, confirm the method supports the shorthand and verify that task heads are excluded or handled through `modules_to_save`.
5. For adapters that use `target_parameters`, intentionally use `target_modules=[]` when the method documents that pattern.
6. If a selected module class is unsupported, target a supported child layer or provide a method-specific custom module mapping when available.

A simple diagnostic snippet:

```python
candidate_names = [name for name, _ in model.named_modules()]
for target in ["q_proj", "v_proj", "classifier"]:
    print(target, [name for name in candidate_names if name == target or name.endswith(f".{target}")])
```

## 5. Manage Multiple Adapters

Add and switch adapters by name:

```python
model = get_peft_model(base_model, first_config, adapter_name="default")
model.add_adapter(adapter_name="domain_b", peft_config=second_config)
model.set_adapter("domain_b")
print(model.get_model_status())
model.delete_adapter("domain_b")
```

Notes:

- Use stable, unique adapter names such as `"default"`, `"domain_a"`, or `"task_head_v2"`.
- Do not put adapter names inside PEFT state dict prefixes.
- Not every PEFT method supports activating multiple adapters at once through `PeftModel.set_adapter`.
- For compatible tuners that support stacking, activate multiple adapters through the base tuner path, for example `model.base_model.set_adapter(["default", "domain_b"])`.
- After lifecycle operations, call `get_model_status()` and, when needed, `get_layer_status()`.

## 6. Temporarily Disable Adapters

Use `disable_adapter()` as a context manager to compare base-model and adapter-enabled outputs:

```python
adapter_output = model(**inputs)
with model.disable_adapter():
    base_output = model(**inputs)
```

If the disabled output still appears adapter-influenced, inspect `get_model_status()` and check whether adapters have been merged, deleted, or activated on a nested submodule rather than the top-level wrapper.

## 7. Inspect Layer-Level State

Use layer status when trainability or activation differs across layers:

```python
for layer in model.get_layer_status():
    print(layer.name, layer.enabled, layer.active_adapters, layer.merged_adapters, layer.requires_grad)
```

Use the module-level helper for integration-owned submodules:

```python
from peft import get_layer_status, get_model_status

print(get_model_status(pipe.unet))
print(get_layer_status(pipe.text_encoder))
```

Status helpers are especially useful after loading multiple adapters, merging/unmerging, deleting adapters, or mixing library-specific integration functions with PEFT APIs.

## 8. Low-Level Adapter Injection

Use `inject_adapter_in_model` when the caller needs a plain module rather than a `PeftModel` wrapper:

```python
from peft import LoraConfig, get_peft_model_state_dict, inject_adapter_in_model

config = LoraConfig(target_modules=["linear"])
model = inject_adapter_in_model(config, model, adapter_name="default")
adapter_state = get_peft_model_state_dict(model)
```

For large adapter loading or many adapters, `low_cpu_mem_usage=True` can create empty adapter weights on the meta device before real weights are loaded with state-dict helpers.

When injecting from an adapter state dict:

```python
model = inject_adapter_in_model(config, model, state_dict=adapter_state)
```

PEFT can infer module targets from a state dict for module-targeting adapters. It cannot infer intent reliably for `target_parameters`-based adapters, so those still need an accurate config.

Low-level injection trade-off: the returned model is not a `PeftModel`, so do not expect `PeftModel` lifecycle methods such as wrapper-level `disable_adapter` or checkpoint helpers. Use functional helpers or the integration library's adapter APIs instead.

## 9. Decide Between Core APIs

- Need wrapper helpers and common training ergonomics: `get_peft_model`.
- Need to inspect or load adapter config metadata: `PeftConfig.from_pretrained` or method-specific config `from_pretrained`.
- Need a plain module with injected layers: `inject_adapter_in_model`.
- Need to check trainability and active/merged state: `get_model_status`, `get_layer_status`, and `print_trainable_parameters`.
- Need method-specific LoRA/quantization tuning: route to `lora-and-quantization`.
- Need save/load/merge instructions: route to `save-load-merge`.
