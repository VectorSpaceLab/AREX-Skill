---
name: data-model-customization
description: "Customize ms-swift datasets, registries, plugins, models, and
  templates safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data and Model Customization

Use this sub-skill when the task is to prepare or validate custom data, map columns, inspect ms-swift registries, register datasets/models/templates through an external plugin, or reason about model/template selection before training or inference.

## Read First

- [Data formats](references/data-formats.md): standard `messages` rows, `--columns`, SFT/RLHF/multimodal/agent fields, and preprocessor selection.
- [Registry and plugins](references/registry-and-plugins.md): `--custom_dataset_info`, `--external_plugins`, `register_dataset`, `register_model`, `register_template`, and safe plugin structure.
- [Template reference](references/template-reference.md): `get_processor`, `get_template`, template/model selection, agent templates, loss scaling, and offline skeleton checks.
- [Troubleshooting](references/troubleshooting.md): row drops, malformed messages, media problems, template mismatch, plugin side effects, and local/offline loading.

## Bundled Checks

- `scripts/validate_dataset_rows.py`: validate JSONL/JSON/CSV rows for common ms-swift keys before passing them to `swift sft`, `swift pt`, or `swift rlhf`.
- `scripts/inspect_registries.py`: list installed `DATASET_MAPPING`, `MODEL_MAPPING`, and `TEMPLATE_MAPPING` entries without model downloads.
- `scripts/inspect_template_encoding.py`: print a safe template-encoding plan by default; optionally attempt an installed ms-swift processor/template encode without downloading weights.

## Routing Boundaries

- Stay here for `--dataset`, `--columns`, `--custom_dataset_info`, `--external_plugins`, preprocessors, registry inspection, and model/template registration plans.
- Route full `swift sft`, `swift pt`, and dataset packing/training execution to the training sub-skill.
- Route inference engine behavior, deployment servers, and client requests to inference/deployment coverage.
- Route RLHF/GRPO algorithm execution, reward models, rollout workers, Ray, and Megatron execution to advanced distributed/RLHF coverage.
- Route export and evaluation execution to export/evaluation coverage.

## Quick Patterns

- Prefer direct data files first: `swift sft --dataset train.jsonl --columns prompt=query answer=response ...`.
- Use `--custom_dataset_info dataset_info.json` when stable aliases, subsets, splits, or reusable column mappings are needed.
- Use `--external_plugins plugin.py` only when code must call `register_dataset`, `register_model`, or `register_template`.
- Inspect support with `python scripts/inspect_registries.py --models --templates --contains qwen2_5` before overriding `--model_type` or `--template`.
- Validate rows with `python scripts/validate_dataset_rows.py data.jsonl --columns raw_prompt=query raw_answer=response --check-media exists` before long runs.
