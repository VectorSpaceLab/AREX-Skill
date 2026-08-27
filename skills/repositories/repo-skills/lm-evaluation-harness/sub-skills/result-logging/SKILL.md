---
name: result-logging
description: "Understand, validate, summarize, compare, and safely route
  lm-evaluation-harness result artifacts, sample logs, cache files, and optional
  external logging integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Result Logging

Use this sub-skill when the user needs help interpreting saved `lm-eval` outputs, validating result JSON, comparing finished runs, preparing logging arguments, or converting local result files into tables.

## Route Here For

- Reading aggregated `results_*.json` files and optional per-task `samples_*.jsonl` logs.
- Explaining result schema fields such as `results`, `groups`, `configs`, `versions`, `n-shot`, `higher_is_better`, `n-samples`, `samples`, `config`, `task_hashes`, tokenizer metadata, and environment metadata.
- Debugging why metrics, sample logs, task hashes, stderr values, cache files, or service uploads are missing.
- Preparing `--output_path`, `--log_samples`, `--predict_only`, `--wandb_args`, `--trackio_args`, and `--hf_hub_log_args` without exposing credentials.
- Summarizing or comparing already-saved local JSON results with bundled scripts.
- Planning Zeno visualization prerequisites without assuming a network service or API key is available.

## Do Not Use For

- Constructing and running new evaluations; route to `../evaluation-runs/`.
- Choosing or configuring model backends; route to `../model-backends/`.
- Defining task metrics or YAML task behavior; route to `../task-authoring/`.
- Running network uploads to W&B, Trackio Spaces, Hugging Face Hub, or Zeno unless the user explicitly asks and provides safe credential handling.

## Fast Paths

- Result schema: read `references/result-schema.md`.
- Logging workflows, table generation, result comparison, service arguments, cache notes, and Zeno prerequisites: read `references/result-workflows.md`.
- Failure diagnosis: read `references/troubleshooting.md`.
- Local table from one or more result JSON files:
  ```bash
  python scripts/summarize_results.py path/to/results.json
  ```
- Local metric comparison between two saved runs:
  ```bash
  python scripts/compare_results.py run_a.json run_b.json --metric acc
  ```

## Safety Defaults

- Treat result files as local artifacts; do not publish, upload, or create repos unless the user explicitly asks.
- Never print tokens from `HF_TOKEN`, W&B, Trackio, Zeno, or config files.
- Prefer local JSON validation and summaries before diagnosing backend or task behavior.
- If `predict_only` is used, expect predictions/sample logs but no aggregate metrics.
- If `log_samples` is requested, require an `output_path`; sample logs are not useful if they are never written.
