---
name: configuration-and-datasets
description: "Author, inspect, and validate OpenCompass Python configs and
  dataset definitions, including built-in config selection, local CustomDataset
  JSONL/CSV use, dataset source mappings, and static config comparison."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenCompass Configuration and Datasets

Use this sub-skill when an agent needs to create or inspect OpenCompass config files, combine built-in model/dataset configs, build local JSONL/CSV datasets, register dataset source mappings, or compare config structure before launching expensive runs.

## Route by Task

- **Author an evaluation config**: follow `references/config-authoring.md` for `mmengine.config.read_base`, top-level `models`, `datasets`, optional `summarizer`, and validation commands.
- **Select built-in configs**: use `references/config-catalog.md` plus `scripts/list_opencompass_configs.py` to discover model and dataset config modules by wildcard or fuzzy token.
- **Create custom datasets**: follow `references/dataset-customization.md` for `CustomDataset`, local JSONL/CSV layout, `reader_cfg`, `infer_cfg`, `eval_cfg`, and dataset mapping registration.
- **Compare configs safely**: use `scripts/compare_config_keys.py` and the workflows in `references/config-catalog.md` to detect changed top-level keys, dataset abbreviations, model abbreviations, and reader/evaluator shape before a run.
- **Troubleshoot config loading**: use `references/troubleshooting.md` for import errors, wrong variable names, prompt/output column mismatches, `DATASET_SOURCE`, file layout, and generated config suffixes.

## Boundaries

- For model adapter constructor parameters, acceleration backends, and HF/vLLM/LMDeploy execution details, route to the `model-backends` sub-skill.
- For prompt-template internals, chat rounds, retrievers, and inferencer behavior, route to the `prompt-and-inference` sub-skill.
- For `opencompass` CLI launch modes, work directories, reuse, runners, and summarization of completed outputs, route to the `evaluation-workflows` sub-skill.

## Quick Static Validation

```bash
python -m py_compile path/to/eval_config.py
python scripts/compare_config_keys.py old_config.py new_config.py --show datasets,models
python scripts/list_opencompass_configs.py mmlu gsm8k --kind datasets
```

Use `opencompass path/to/eval_config.py --dry-run` only in an environment with OpenCompass runtime dependencies installed and any imported model/dataset modules available. Dry-run validates scheduling/config expansion; it does not prove real model inference.
