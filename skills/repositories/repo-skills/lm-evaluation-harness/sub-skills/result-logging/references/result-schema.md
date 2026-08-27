# Result Schema

`lm-evaluation-harness` result artifacts are dictionaries returned by `simple_evaluate()`/`evaluate()` and optionally persisted by the evaluation tracker. Keys are conditional, so agents should validate what is present instead of assuming every field exists.

## Aggregated Result JSON

The saved aggregated file is usually named `results_<timestamp>.json`. If `--output_path` is a directory, the tracker writes it under a sanitized model-name subdirectory. If `--output_path` is a `.json` filename, the tracker writes a timestamped sibling file using that stem.

Common top-level keys:

| Key | Meaning | Notes |
| --- | --- | --- |
| `results` | Per-task metrics | Main table source; values are task metric dictionaries. |
| `groups` | Group-level metrics | Present only for grouped tasks with aggregation. |
| `group_subtasks` | Group/task to subtask mapping | Useful for explaining group metrics. |
| `configs` | Effective task configs | Includes task output type and metric list when available. |
| `versions` | Task versions | Values can be string, number, `null`, or absent. |
| `n-shot` | Few-shot counts per task | Display with metrics when summarizing. |
| `higher_is_better` | Metric direction per task | Use for comparison tables and ranking. |
| `n-samples` | Original/effective sample counts | Shows dataset size and `--limit` effects. |
| `samples` | In-memory sample results | Only present in returned objects when sample logging is enabled; persisted sample logs are usually JSONL files instead. |
| `config` | Run/model configuration | Contains model, model args, batch/device/cache/seed fields. |
| `git_hash`, `upper_git_hash` | Source revision metadata | May be missing outside Git checkouts. |
| `date` | Evaluation start timestamp | Numeric timestamp in returned results. |
| `pretty_env_info`, `transformers_version`, `lm_eval_version` | Environment metadata | Torch/transformers can be reported as unavailable. |
| tokenizer fields | Tokenizer/eot/max-length metadata | Added when model exposes tokenizer attributes. |
| `model_source`, `model_name`, `model_name_sanitized` | Model identity | Used for output directory naming. |
| chat/instruction fields | Prompt-format reproducibility | Includes chat template/system instruction and hashes when used. |
| `task_hashes` | Reproducibility hash per task | Populated only when sample hashes are available. |
| `total_evaluation_time_seconds` | Wall-clock runtime string | Added by the tracker when saving. |

## Task Metric Dictionaries

Each `results[task]` or `groups[group]` value contains fixed display keys plus dynamic metric keys.

Fixed/common keys:

- `alias`: Display label for the task/group.
- `name`: Task name when present.
- `sample_len`: Number of evaluated docs when present.
- `sample_count`: Group-only per-metric sample counts when present.

Dynamic metric keys generally use `metric,filter` form, for example:

- `acc,none`
- `acc_norm,none`
- `exact_match,strict-match`
- `word_perplexity,none`
- `acc_stderr,none`

`*_stderr,<filter>` fields are standard errors for the matching metric/filter pair. When making tables, skip display-only strings like `alias`, skip `*_stderr` as primary metrics, and join each metric to its stderr if present.

## Per-Sample JSONL Logs

When sample logging is enabled and an output path is set, the tracker writes one JSON object per line to files usually named `samples_<task>_<timestamp>.jsonl` beside the aggregated results file.

Important sample fields:

| Field | Meaning |
| --- | --- |
| `doc_id` | Zero-based index in the evaluation split. |
| `doc` | Original dataset document. |
| `target` | Gold target, serialized as a string by the tracker. |
| `arguments` | Model request inputs as nested `gen_args_N` / `arg_N` dictionaries. |
| `resps` | Raw model responses after JSON-safe sanitation. |
| `filtered_resps` | Responses after task filters. |
| `filter` | Filter name such as `none` or `strict-match`. |
| `metrics` | Metric names computed for this sample. |
| `doc_hash`, `prompt_hash`, `target_hash` | Reproducibility hashes. |

Samples may also include dynamic per-sample metric values such as `acc`, `acc_norm`, or `exact_match`. Do not assume a single response shape: generation tasks, multiple-choice tasks, and loglikelihood tasks serialize responses differently.

## Cache Files Are Separate

There are two distinct cache concepts:

- `--use_cache` points to a SQLite response-cache path prefix for model responses.
- `--cache_requests` controls cached task request construction under the harness cache directory, or a directory selected by `LM_HARNESS_CACHE_PATH`.

Neither cache is the aggregated result JSON. Cache staleness can explain surprising repeat behavior, but result validation should start with the saved result and sample files.
