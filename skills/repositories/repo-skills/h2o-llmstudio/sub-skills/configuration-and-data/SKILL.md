---
name: "configuration-and-data"
description: "Build, inspect, validate, and round-trip experiment configs and
  datasets for all supported H2O LLM Studio problem types."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# configuration-and-data

Use this sub-skill when you need to load, inspect, validate, or round-trip H2O LLM Studio experiment configs and dataset files.

## Owns

- YAML experiment configs and nested dataclass sections.
- Problem type selection and per-problem defaults.
- Dataset connectors, local CSV / Parquet file rules, and import-time column mapping.
- Prompt, answer, system, parent-id, and DPO rejection columns.
- Conversation chains and default seeded datasets.
- Config checks that happen before training.

## Does not own

- Training execution, CLI launches, or GPU setup. Use `training-and-experiments`.
- Model, loss, metric, and plot internals. Use `modeling-and-evaluation`.
- GUI navigation or app startup. Use `app-and-ui`.

## Supported problem types

- Causal language modeling
- Causal classification modeling
- Causal regression modeling
- Sequence-to-sequence modeling
- DPO modeling

## Read first

- `references/configuration-reference.md`
- `references/data-formats.md`
- `references/problem-types.md`
- `references/troubleshooting.md`

## Skill-owned scripts

- `scripts/inspect_config.py` — load a YAML config, report the resolved problem type, and verify a canonical round-trip.
- `scripts/validate_dataset.py` — load the config, validate the referenced dataset files, and inspect chain and label rules.

## Typical workflow

1. Confirm the intended problem type.
2. Load the YAML config and compare it with the expected schema.
3. Validate the train and validation datasets, including required columns.
4. Check the config round-trip before handing the experiment off to training.

## Cross-links

- If the task needs training or checkpoint debugging, switch to `training-and-experiments`.
- If the task is about loss curves, metrics, or predictions, switch to `modeling-and-evaluation`.
- If the task is about import dialogs, dataset pages, or app screens, switch to `app-and-ui`.
