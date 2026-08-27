---
name: evaluation
description: "Configure and run LLM Foundry offline and in-training ICL
  evaluation, custom tasks, Eval Gauntlet aggregation, API-wrapper evaluation,
  and result interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# evaluation

Use this sub-skill when the user wants to evaluate an LLM Foundry model with in-context-learning (ICL) tasks, add ICL evaluation hooks to training, build custom JSONL eval datasets, aggregate Eval Gauntlet scores, evaluate API-wrapper models, or interpret evaluation output.

## Route

- **In scope:** the public `llmfoundry eval YAML_PATH [overrides...]` CLI; offline eval YAMLs; `EvalConfig` required and optional fields; ICL task schemas; custom task JSONL validation; Eval Gauntlet categories and composite-score math; OpenAI/FMAPI API-wrapper evaluation; result tables and metric names.
- **Route to `../training-finetuning/`:** full training-loop YAML design, optimizer/scheduler/checkpointing choices, or training runtime debugging beyond the eval hook keys listed here.
- **Route to `../inference-conversion/`:** standalone Hugging Face generation/chat scripts, checkpoint export, ONNX/FasterTransformer conversion, and non-eval inference serving.
- **Route to `../package-apis-configuration/`:** model registry internals, creating new registry entries, MPT/HF model class configuration internals, and package extension mechanics.

## Start here

1. Identify the eval mode: offline installed CLI, in-training ICL hooks, custom task/schema work, Eval Gauntlet aggregation, or API-wrapper eval.
2. Read [references/workflows.md](references/workflows.md) for the matching workflow and minimal YAML shapes.
3. For custom or modified task configs, read [references/task-schemas.md](references/task-schemas.md) before running anything.
4. Run the bundled static linter before launching models:

   ```bash
   python scripts/llmfoundry_eval_config_lint.py path/to/eval.yaml
   ```

   The linter parses YAML and optional local task/Gauntlet files, checks required fields and likely metric/task mismatches, and never loads models or downloads data.
5. Launch offline evaluation only after the config, local data paths, credentials, and model/cache situation are known:

   ```bash
   llmfoundry eval path/to/eval.yaml key=value another.nested.key=value
   ```

## Operating rules

- Canonical offline `EvalConfig` requires `models`, `max_seq_len`, and `device_eval_batch_size`. Use a `models:` list with per-model `model_name`, `model`, optional `load_path`, and `tokenizer` blocks.
- Important optional eval fields include `icl_tasks`, `eval_gauntlet`, `loggers`, `callbacks`, `fsdp_config`, `precision`, `seed`, `eval_subset_num_batches`, and `icl_subset_num_batches`. If someone says “subsets”, map that request to the explicit subset fields; do not invent a generic `subsets` key unless their installed version documents it.
- `device_eval_batch_size` must be an integer for ICL tasks. Lower it first for OOMs; MC/schema tasks expand each logical example into one row per choice/context option.
- Supported task families for this sub-skill are `generation_task_with_answers`, `language_modeling`, `multiple_choice`, and `schema`; their JSONL row contracts and metrics are in [references/task-schemas.md](references/task-schemas.md).
- `metric_names` in ICL task YAMLs normally use class-style names such as `InContextLearningMultipleChoiceAccuracy`, not lower-case registry aliases.
- Use `has_categories: true` only when every task row has a `category` field. Category subtasks are partitioned and then averaged in result tables.
- Eval Gauntlet only aggregates benchmarks whose `(label, num_fewshot)` exactly match completed ICL evaluators. A missing benchmark removes that category from composite scores.
- API-wrapper eval requires credentials or a configured custom endpoint. Never ask users to place secrets in YAML; use environment variables or platform secret mechanisms.
- Full Eval Gauntlet and large model evals can download models/datasets and consume substantial GPU/API budget. Prefer a tiny custom task or `icl_subset_num_batches` smoke before full runs.

## Bundled references and script

- [references/task-schemas.md](references/task-schemas.md) — `EvalConfig`, ICL task rows, delimiters, categories, metrics, installed signatures.
- [references/workflows.md](references/workflows.md) — offline CLI, overrides, in-training hooks, API-wrapper eval, custom task assembly, result interpretation.
- [references/eval-gauntlet.md](references/eval-gauntlet.md) — categories, random baselines, weighting/rescale/subtract math, averages, custom Gauntlet configs.
- [references/troubleshooting.md](references/troubleshooting.md) — malformed rows, metric mismatches, path/cache/credential/max length/OOM/subset failures.
- [scripts/llmfoundry_eval_config_lint.py](scripts/llmfoundry_eval_config_lint.py) — safe static linter for eval YAML and local task/Gauntlet files.
