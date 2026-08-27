# Result Workflows

This reference covers safe, local-first result handling after an evaluation has run. Use `../evaluation-runs/` when the user still needs to construct or execute the evaluation itself.

## Save Results and Samples

For result files that can be inspected later, ensure the run has an output path:

```bash
lm-eval run --model hf --model_args pretrained=gpt2 --tasks hellaswag --output_path ./results/gpt2
```

To save model inputs/outputs per sample, add sample logging:

```bash
lm-eval run --model hf --model_args pretrained=gpt2 --tasks hellaswag --output_path ./results/gpt2 --log_samples
```

Important behavior:

- `--log_samples` requires `--output_path` because the sample JSONL files must be written somewhere.
- `--predict_only` implies sample logging and skips metric computation; expect predictions rather than normal aggregate metric tables.
- Aggregated results are JSON files; per-sample logs are task-specific JSONL files.
- The tracker stores task hashes only when sample hashes are available.

## Read Local Results Safely

Use the bundled scripts for local post-run analysis. They do not import `lm_eval`, do not run models, and do not contact external services.

Create a compact Markdown table from result JSON:

```bash
python scripts/summarize_results.py results/model/results_2026.json
```

Include groups and write to a file:

```bash
python scripts/summarize_results.py results/model/results_2026.json --include-groups --output summary.md
```

Compare two saved result files on a metric family, including nested keys like `acc,none`:

```bash
python scripts/compare_results.py baseline.json candidate.json --metric acc
```

Use `--metric exact_match,strict-match` when the filter name matters. Use `--alpha` to mark approximate significance when both runs include stderr fields.

## Generate Tables

The repository's table scripts show the intended table shape: task, version, filter, few-shot count, metric, value, and stderr. The bundled `summarize_results.py` adapts that idea without depending on `pytablewriter` or a repository checkout.

When building tables manually:

1. Load the aggregated result JSON.
2. Iterate `results` for task metrics and optionally `groups` for group metrics.
3. Split metric keys on the first comma into `metric` and `filter`; default the filter to an empty value when missing.
4. Skip `alias`, `name`, `sample_len`, `sample_count`, and keys ending in `_stderr` as primary rows.
5. Pair each metric with a matching `<metric>_stderr,<filter>` or `<metric>_stderr` key when available.
6. Preserve raw values unless the user explicitly wants percentages.

## Compare Runs

The repository comparator evaluates two backends and performs a z-test for `acc,none`. For post-run analysis, prefer comparing already-saved result JSON:

- Join by task names present in both files.
- Match metrics by exact key, or by metric family plus filter.
- Record `higher_is_better` direction when available; if missing, report raw deltas without declaring a winner.
- If both stderr values exist, compute `z = (candidate - baseline) / sqrt(stderr_a^2 + stderr_b^2)` and a two-tailed normal approximation p-value.
- If stderr is missing or non-numeric, report deltas only.

Nested metric keys are normal. `acc,none`, `acc_norm,none`, and `exact_match,strict-match` are separate metric/filter pairs.

## W&B Logging Args

`--wandb_args` and `--wandb_config_args` are forwarded to the W&B logger. The logger flattens numeric metrics as `task/metric`, strips trailing `,none` from metric names for logging, writes result tables, and stores the full result JSON as an artifact.

Safe preparation pattern:

```bash
lm-eval run ... --output_path ./results/run --wandb_args project=my-evals name=run-001
```

Safety notes:

- Do not put API keys in command text, result files, or skill content.
- Assume W&B requires its normal local login or environment configuration.
- `wandb>=0.13.6` is expected by the logger.

## Trackio Logging Args

Trackio logging uses `--trackio_args` and defaults the project to `lm-eval-harness` if no project is supplied. Aggregate metrics are flattened as `task/metric`. Sample logs are converted to Trace objects with prompt/response messages and metric metadata.

Safe preparation pattern:

```bash
lm-eval run ... --output_path ./results/run --log_samples --trackio_args project=my-evals name=run-001
```

Trackio is optional. If it is not installed, the logger raises an import error suggesting `pip install trackio` or the package extra that includes Trackio support.

## Hugging Face Hub Logging Args

`--hf_hub_log_args` configures optional result/sample pushes through the evaluation tracker. Useful keys include:

| Key | Purpose |
| --- | --- |
| `hub_results_org` | Hub organization; defaults to token owner if omitted during push. |
| `details_repo_name` | Dataset repo for detailed/sample outputs. |
| `results_repo_name` | Dataset repo for aggregate results. |
| `push_results_to_hub` | Push aggregated results. |
| `push_samples_to_hub` | Push sample JSONL outputs; requires sample logging. |
| `public_repo` | Make created dataset repos public instead of private. |
| `leaderboard_url` | Add leaderboard URL metadata. |
| `point_of_contact` | Add contact metadata. |
| `gated` | Gate the details dataset. |

Safety notes:

- Hub pushes require a token through normal Hugging Face credential channels; do not ask users to paste tokens into logs.
- If push flags are true and no token is available, the tracker raises a token error.
- If `hub_repo_name` is used, it maps both details and results to the same repo and is deprecated in favor of `details_repo_name`/`results_repo_name`.

## Zeno Visualization Prerequisites

The repository Zeno script is reference-only for this skill because it depends on an external service, `zeno_client`, and `ZENO_API_KEY`. It expects a directory whose subdirectories are model names, with each model directory containing aggregated `results_*.json` and per-task `samples_*.jsonl` files.

Before attempting Zeno upload, check:

- The user explicitly wants an external upload.
- `ZENO_API_KEY` is configured outside the prompt transcript.
- Sample logs exist for the tasks being visualized.
- All compared model directories share at least one common task.
- `model_args` values are sanitized before being used as names or labels.

If any prerequisite is missing, keep the workflow local and summarize or compare the JSON files instead.
