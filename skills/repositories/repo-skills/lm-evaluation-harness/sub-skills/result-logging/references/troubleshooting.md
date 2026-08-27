# Result Logging Troubleshooting

Use this checklist before blaming a model backend or task implementation. Most result issues are caused by missing output settings, conditional schema fields, optional dependencies, or stale cache files.

## No Result File Was Written

Likely causes:

- `--output_path` was omitted.
- The run failed before final result saving.
- The user searched the wrong directory: directory output writes under a sanitized model-name subdirectory; `.json` output writes a timestamped sibling file.

Checks:

- Ask for the exact `--output_path` value and list result files below it.
- Look for `results_*.json` and `samples_*.jsonl` separately.
- Inspect stderr/stdout for `Saving results aggregated` or warnings such as `Could not save results aggregated`.

## `--log_samples` Errors or Missing Samples

`--log_samples` needs `--output_path`. Without an output path, the run cannot persist sample JSONL files.

Other causes:

- `predict_only` was used, so aggregate metrics are intentionally skipped while predictions/samples are saved.
- A task produced no examples after `--limit`, `--samples`, or split selection.
- The user is inspecting an in-memory result object instead of the output directory.
- Sample files are per task, so a multi-task run creates multiple `samples_<task>_*.jsonl` files.

Validation steps:

1. Confirm `output_path` and `log_samples` in the saved `config` or CLI command.
2. Check for task-specific JSONL files beside the aggregate result JSON.
3. Read the first JSONL line and verify fields such as `doc_id`, `arguments`, `filtered_resps`, `target`, and hash fields.
4. If `task_hashes` is empty, confirm sample hashes exist in the sample logs.

## Metrics Are Missing

Expected when:

- `--predict_only` is used.
- The run failed before metric aggregation.
- The inspected object is a sample JSONL row rather than an aggregate result JSON.

Unexpected cases:

- The task config has a different metric key than the user expects.
- The metric uses a filter suffix, for example `exact_match,strict-match` instead of `exact_match,none`.
- Group metrics live under `groups`, not `results`.

Use `summarize_results.py` to list all discovered metric/filter keys before writing custom comparisons.

## Stderr Is Missing or `N/A`

Standard error fields are optional. Some metrics or aggregations do not produce stderr, and some result writers keep `N/A` as a string. Comparison tools should report deltas without significance when stderr is absent or non-numeric.

## Malformed Result JSON

Symptoms:

- `json.JSONDecodeError` while loading aggregated results.
- Empty file or truncated JSON after interrupted runs.
- The user passed a sample JSONL file to a result JSON summarizer.

Checks:

- Aggregated results should be one JSON object, not newline-delimited JSON.
- Sample logs should be `.jsonl`, one object per line.
- Confirm the top-level aggregate file has a `results` object.
- If the file is truncated, rerun or recover from a complete copied artifact rather than editing guessed values into the JSON.

## Cache Staleness

Result files are not caches. However, stale caches can make repeat runs look surprising.

- `--use_cache` uses a SQLite response-cache path prefix.
- `--cache_requests` caches constructed task requests under the harness cache path.
- `LM_HARNESS_CACHE_PATH` can redirect request caches.

If prompts, task YAML, filters, or generation settings changed, consider using a fresh cache path or `--cache_requests refresh` for the next run. Do not delete user caches without explicit permission.

## W&B Problems

Likely causes:

- `wandb` is not installed or is older than the expected version.
- The user is not logged in through normal W&B credential channels.
- `--wandb_args` contains malformed `key=value` arguments.
- The run uses a step value that conflicts with existing W&B config unless config updates allow changes.

Safety guidance:

- Do not request or print API keys.
- Keep a local `--output_path` even when using W&B so results are recoverable if service logging fails.
- Explain that W&B strips trailing `,none` from metric names when logging flattened summaries.

## Trackio Problems

Likely causes:

- `trackio` is not installed.
- The logger cannot convert an unusual sample shape into a Trace.
- A remote Space target is configured but credentials/network are unavailable.

Safety guidance:

- Treat Trackio as optional; local JSON results remain the source of truth.
- Use `--log_samples` when the user expects Trackio traces.
- If sample trace conversion fails for some rows, aggregate metric logging may still succeed.

## Hugging Face Hub Push Problems

Likely causes:

- Push flags are true but no Hugging Face token is configured.
- `push_samples_to_hub=True` but samples were not logged.
- The organization or repo name is wrong.
- The user expected public repos but `public_repo` was false.
- Gating or card updates failed after file upload.

Safety guidance:

- Never include tokens in CLI snippets.
- Prefer `details_repo_name` and `results_repo_name` over deprecated `hub_repo_name`.
- Keep local outputs and verify them before diagnosing Hub upload behavior.

## Zeno Problems

Likely causes:

- `zeno_client` is not installed.
- `ZENO_API_KEY` is missing.
- No model subdirectories exist under the data path.
- Compared model folders do not share any task.
- Sample JSONL files are absent because `--log_samples` was not used.
- A task output type has a response shape the visualization script does not expect.

Safety guidance:

- Do not attempt Zeno upload unless the user explicitly approves external service use.
- Validate local files first with the bundled summarizer/comparator.
- Sanitize `model_args` before using it in service labels or generated names.
