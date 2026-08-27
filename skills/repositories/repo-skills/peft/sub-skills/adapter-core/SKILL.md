---
name: adapter-core
description: "Core PEFT adapter setup, configuration, target module selection,
  adapter lifecycle, model/layer status diagnostics, custom models, and
  low-level adapter injection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Adapter Core

Use this sub-skill when the task is about constructing PEFT configs, wrapping a model with adapters, managing adapters after creation, diagnosing adapter state, targeting modules in custom models, or using low-level adapter injection.

## Route Here For

- Install/import smoke checks for `peft`, `torch`, `transformers`, and `accelerate` without downloading models.
- Core API choices: `PeftConfig`, `TaskType`, `PeftType`, `get_peft_model`, `PeftModel`, and adapter names.
- Adapter lifecycle: add, load, activate, disable, delete, inspect trainable parameters, and inspect model/layer status.
- Target module selection for custom or non-Transformers `torch.nn.Module` models.
- Low-level injection with `inject_adapter_in_model` when a `PeftModel` wrapper is not desired.
- Diagnosing invalid task/PEFT types, missing target modules, unsupported module classes, or unexpected trainable status.

## Route Elsewhere

- LoRA variants, quantized loading, DoRA, rsLoRA, QLoRA-style workflows, and LoRA-specific initialization: use `../lora-and-quantization/SKILL.md`.
- Prompt tuning, prefix tuning, p-tuning, soft prompts, or prompt encoder internals: use `../prompt-and-soft-methods/SKILL.md`.
- Saving, loading checkpoints, merging adapters into base weights, or deployment packaging: use `../save-load-merge/SKILL.md`.
- Trainer, Accelerate, distributed, FSDP, DeepSpeed, or multi-GPU training integration: use `../training-and-integrations/SKILL.md`.

## Start Fast

1. Run `python scripts/check_peft_env.py` from this sub-skill directory to verify imports and local package facts.
2. Read `references/api-reference.md` for the core class/function surface and common enum values.
3. Follow `references/workflows.md` for adapter construction, custom model targeting, lifecycle management, and low-level injection.
4. Use `references/troubleshooting.md` when errors mention invalid task types, missing `target_modules`, unsupported modules, adapter status irregularities, or optional dependency imports.

## Core Decision Pattern

- Prefer `get_peft_model(base_model, peft_config, adapter_name="default")` for normal Transformers and custom PyTorch models when PEFT should return a `PeftModel` wrapper with helper methods.
- Use explicit `target_modules` for custom models unless the method and architecture have a known PEFT default mapping.
- Use `modules_to_save` for non-adapter layers that must remain trainable and be stored with the adapter, such as custom heads or task heads.
- Use `print_trainable_parameters()`, `get_model_status()`, and `get_layer_status()` before training when trainable counts, active adapters, or merged/disabled states look surprising.
- Use low-level `inject_adapter_in_model(peft_config, model, adapter_name=...)` only when the caller needs adapter layers in a plain `torch.nn.Module` and does not need `PeftModel` helper methods.

## Bundled Materials

- `references/api-reference.md`: API inventory, enum usage, config validation, lifecycle helpers, and status helpers.
- `references/workflows.md`: practical recipes for standard wrapping, custom modules, target discovery, adapter lifecycle, and low-level injection.
- `references/troubleshooting.md`: diagnosis paths for target module, enum, trainability, optional dependency, custom module, and low-level injection failures.
- `scripts/check_peft_env.py`: safe local import/config smoke check with `--help`, JSON output option, and optional CUDA facts.
