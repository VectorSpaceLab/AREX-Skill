---
name: "configuration-and-extension"
description: "Guides MMGeneration config authoring, dataset layout, registry
  extension, and runtime customization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Configuration and Extension

Use this sub-skill when you need to read, edit, or extend MMGeneration configs rather than run a full training or evaluation job.

## Typical triggers

- "How do I change this config?"
- "How do I register a custom loss or hook?"
- "What dataset layout does this config expect?"
- "How do I print the resolved config?"
- "How do I add a new generator or optimizer?"

## Include here

- Config inheritance, `_base_`, `_delete_`, and `custom_imports`
- `--cfg-options` overrides and config printing
- Dataset layout and pipeline keys
- Registry patterns for models, modules, losses, optimizers, and hooks
- Runtime customizations: LR schedules, momentum schedules, checkpoint/log/eval hooks
- Safe config-only validation before training or evaluation

## Exclude here

- Actually launching training jobs -> `training-and-distribution`
- Running metrics or sampling jobs -> `evaluation-and-metrics` or `inference-and-sampling`
- Latent editing and TorchServe packaging -> `applications-and-deployment`

## Read these files first

- `references/configuration.md`
- `references/troubleshooting.md`
- `../../references/api-reference.md`
- `../../references/data-formats.md`
- `../../references/cli-reference.md`

## Bundled helper

- `scripts/print_config.py` — print the fully resolved config and verify `--cfg-options` overrides.

## What good guidance looks like

A future agent should be able to:

1. Inspect a config file and see the final merged result.
2. Decide whether a dataset or pipeline shape matches the intended workflow.
3. Add a custom module or hook with the correct registry/import pattern.
4. Understand when `custom_imports`, `_delete_`, or `data_info` is required.
5. Distinguish config-only validation from a real training or evaluation run.

## Common failure modes

- A custom class is written but never imported into the registry namespace.
- A nested override does not match the original config structure.
- Paired/unpaired dataset keys do not match the pipeline expectations.
- A loss expects a different output key than the model actually emits.
- A runtime hook or optimizer is described in config but not imported or registered.

For symptom-by-symptom recovery, read `references/troubleshooting.md`.
