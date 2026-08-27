# Adapter Core Troubleshooting

Use this guide when adapter construction, targeting, lifecycle management, or status inspection behaves unexpectedly.

## Invalid `task_type`

Symptoms:

- `ValueError: Invalid task type ...`
- A task wrapper is missing expected behavior for causal LM, seq2seq, sequence classification, token classification, question answering, or feature extraction.

Fixes:

- Prefer `TaskType` enum values, for example `TaskType.CAUSAL_LM` or `TaskType.SEQ_CLS`, instead of free-form strings.
- If passing strings, use exact enum names such as `"CAUSAL_LM"`.
- For custom non-Transformers modules, omit `task_type` unless a task-specific PEFT wrapper is required.
- For sequence classification or custom heads, verify `modules_to_save` so the head trains and persists.

## Invalid Or Unknown `peft_type`

Symptoms:

- Loading a config reports an unknown PEFT type.
- A base `PeftConfig` loads but method-specific fields are absent.

Fixes:

- Use method-specific config classes, such as `LoraConfig`, when creating new adapters.
- Use `PeftConfig.from_pretrained(...)` only when reading saved adapter metadata; then load with the appropriate save/load workflow.
- Confirm the installed PEFT version supports the adapter method used by the checkpoint.
- Contributors adding a new method must register a new `PeftType`, config mapping, tuner mapping, and public exports; that is development work, not a normal user workaround.

## Target Modules Not Found

Symptoms:

- `ValueError` says target modules were not found in the base model.
- Warnings say `target_modules` were set but no module was matched.
- Trainable parameter count is zero or far below expectation.

Fixes:

1. Print `model.named_modules()` and match against real module names.
2. Use suffix lists for exact module-name endings: `["q_proj", "v_proj"]` matches nested modules ending with those names.
3. Use regex strings only when you intentionally need regex matching.
4. Do not combine regex `target_modules` strings with layer-index filters such as `layers_to_transform` or `layers_pattern` for methods that reject that combination.
5. For custom models, pass explicit targets instead of relying on architecture defaults.
6. If using a method-supported shorthand such as `"all-linear"`, verify it expands to the intended layers and does not train a head that should instead be handled through `modules_to_save`.
7. If targeting parameters rather than modules, follow the method documentation and set `target_modules=[]` when required.

Fast inspection snippet:

```python
module_names = [name for name, _ in model.named_modules()]
print([name for name in module_names if "proj" in name or "linear" in name or "head" in name])
```

## Unsupported Target Module Class

Symptoms:

- PEFT warns that the targeted module type is not recognized.
- Adapter injection fails even though a target name matched.
- The model uses custom layers, fused layers, or unusual projections.

Fixes:

- Target a supported child module such as `nn.Linear`, convolution, embedding, or a method-supported projection layer when possible.
- For custom models, inspect both names and Python classes with `type(module).__name__`.
- If the method supports custom module mappings, provide a custom replacement module that accepts `base_layer` and `adapter_name` positional arguments plus method-specific keyword arguments.
- If the module is recurrent or composite, consider targeting an internal linear projection instead of the whole parent module.
- If the task is LoRA-specific, route to `lora-and-quantization` for method-level supported module details.

## Wrong Trainable Status

Symptoms:

- `print_trainable_parameters()` reports zero trainable parameters.
- Too many base parameters remain trainable.
- A classifier/head is not trainable or is missing after reload.
- `get_model_status()` reports irregular active adapters, disabled adapters, or unexpected trainable counts.

Fixes:

- Call `model.get_model_status()` and inspect `trainable_params`, `active_adapters`, `merged_adapters`, and `enabled`.
- Call `model.get_layer_status()` to find which targeted layers are trainable or disabled.
- Confirm the intended adapter is active with `model.set_adapter(adapter_name)`.
- If loading pretrained adapters for inference, remember that adapters may be frozen unless loaded as trainable.
- Add task heads, custom heads, resized embeddings, or batch norm layers to `modules_to_save` when they must train and be saved with the adapter.
- Check whether a previous lifecycle step merged, disabled, deleted, or replaced the adapter.
- Avoid calling `get_peft_model` repeatedly on an already adapted `PeftModel`; add adapters with `add_adapter` instead.

## Optional Import Issues

Symptoms:

- `import peft` works but a workflow fails importing `torch`, `transformers`, or `accelerate`.
- CUDA assumptions fail on a CPU-only machine.
- A script attempts to download a model when only an import check was intended.

Fixes:

- Install PEFT generically with `pip install peft`, or use `pip install -e .` for contributor source installs.
- Install workflow-specific dependencies separately; core adapter docs assume `torch` is available for actual model wrapping.
- Run `python scripts/check_peft_env.py --json` to distinguish PEFT import failures from optional dependency failures.
- Treat CUDA as optional unless the workflow explicitly requires GPU kernels or quantized backends.
- Keep smoke checks download-free; load models only when the user explicitly asks for a model-specific workflow.

## Custom Model Targeting Problems

Symptoms:

- A custom `torch.nn.Module` wraps successfully but learns nothing.
- The adapter targets too many or too few layers.
- Non-adapter classifier weights are not present in adapter saves.

Fixes:

1. Print the module tree and choose exact suffixes or a narrow regex.
2. Start with one or two obvious target layers and verify trainable counts.
3. Add non-adapter heads to `modules_to_save`.
4. Run a tiny forward/backward step and confirm adapter parameters receive gradients.
5. Use `get_layer_status()` to confirm the intended layers contain active adapter modules.
6. If target names are dynamic or generated, prefer explicit suffix lists assembled from `named_modules()` over broad regexes.

## Low-Level Injection Surprises

Symptoms:

- The returned object has no `PeftModel` methods.
- Prompt-learning adapters fail with low-level injection.
- Injecting from a state dict misses keys or targets the wrong modules.

Fixes:

- Use `get_peft_model` when you need wrapper-level lifecycle, save/load, disable, merge, or task helpers.
- Use `inject_adapter_in_model` only for plain-module integrations that can manage functional helper calls.
- Do not use low-level injection for prompt-learning methods.
- When using `state_dict`-driven target inference, still pass the correct method config type.
- For `target_parameters` workflows, do not rely on state-dict target inference; pass an accurate config.
- Use `get_peft_model_state_dict` and `set_peft_model_state_dict` for functional state handling.

## Adapter Name And Prefix Problems

Symptoms:

- Missing adapter keys while loading.
- Warnings mention the adapter name being contained in a prefix.
- Multiple adapters conflict or overwrite each other.

Fixes:

- Use simple adapter names such as `default`, `domain_a`, or `task_b`.
- Do not include PEFT state dict prefixes in adapter names.
- Use `add_adapter` for additional adapters instead of wrapping an already adapted model again.
- Inspect `get_model_status().available_adapters` and `get_model_status().active_adapters` after load/add/delete operations.

## Routing Reminders

- If the fix requires LoRA rank, DoRA, rsLoRA, QLoRA, quantization, or LoRA initializer details, route to `lora-and-quantization`.
- If the fix requires prompt encoders or virtual tokens, route to `prompt-and-soft-methods`.
- If the fix requires checkpoint loading, saving, merging, or adapter deployment format, route to `save-load-merge`.
- If the fix requires Trainer, Accelerate, distributed training, or multi-GPU setup, route to `training-and-integrations`.
