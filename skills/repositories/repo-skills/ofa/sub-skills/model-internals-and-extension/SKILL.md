---
name: model-internals-and-extension
description: "Guides OFA task, model, and criterion registration plus prompt
  tuning, adapters, bitfit, and encouraging-loss extensions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# model-internals-and-extension

Use this sub-skill when a user wants to inspect OFA internals, add a new task or criterion, or reason about prompt tuning and other extension flags.

## Trigger phrases

- "How is OFA registered?"
- "Add a new task / criterion / model"
- "What does `ofa_module` do?"
- "How do prompt tuning, adapters, or bitfit work?"
- "How do I use encouraging loss?"

## What this sub-skill owns

- OFA task/model/criterion registration,
- architecture names and shared model configuration,
- classification-head and generator wiring,
- prompt tuning, adapters, and bitfit guidance,
- encouraging-loss usage and extension planning.

## What it excludes

- end-to-end caption/VQA/RefCOCO/OCR/ImageNet commands -> `vision-language-tasks`,
- Gigaword / GLUE -> `language-tasks`,
- MMSpeech data prep or stage commands -> `mmspeech`,
- generic launch or environment setup -> `setup-and-command-building`.

## Read these files

- [references/api-reference.md](references/api-reference.md) for the main OFA classes, registries, and architecture fields.
- [references/criteria-and-tuning.md](references/criteria-and-tuning.md) for prompt tuning, adapters, bitfit, and encouraging loss.
- [references/troubleshooting.md](references/troubleshooting.md) for registry and checkpoint mismatch failures.
- [scripts/inspect_ofa_registration.py](scripts/inspect_ofa_registration.py) to print the live task/model/criterion registry.

## Typical workflow

1. Inspect the registry to confirm the task or criterion already exists.
2. Read the API reference before adding a new extension point.
3. Decide whether the change belongs in prompt tuning, adapters, bitfit, or a new criterion.
4. Check the troubleshooting notes for checkpoint and shell-command pitfalls.

## Notes

- The repo uses Fairseq-style registration and architecture decorators.
- Prompt tuning and adapter-style changes are usually command flags, not a separate package.
- A registry check is much safer than assuming the model was imported correctly.
