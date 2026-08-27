# Summarizers and Result Interpretation

## Where OpenCompass Writes Results

A completed or reused run normally has these directories under its timestamped `work_dir`:

- `predictions/<model_abbr>/<dataset_abbr>.json` or split files such as `<dataset_abbr>_0.json`: raw model outputs and prompt metadata.
- `results/<model_abbr>/<dataset_abbr>.json`: evaluator output for one model/dataset pair, often numeric metrics plus optional `details`.
- `summary/summary_<timestamp>.txt`: tabulate, CSV, markdown, and raw-result sections in one file.
- `summary/summary_<timestamp>.csv` and `summary/summary_<timestamp>.md`: table-only exports.
- `case_analysis/all/` and `case_analysis/bad/`: outputs from case analysis helpers when run separately.

`opencompass --mode eval --reuse ...` expects existing predictions, while `--mode viz --reuse ...` expects existing results unless `--read-from-station` is used. Route command construction to `evaluation-workflows`; this reference focuses on reading the produced files.

## Summary Table Columns

The default summarizer formats rows as:

| column | Meaning | Diagnostic use |
| ----- | ----- | ----- |
| `dataset` | Dataset abbreviation or a synthetic summary group name. | Must match dataset `abbr`, `summarizer.dataset_abbrs`, or `summary_groups.name`. |
| `version` | Short prompt/config hash for real datasets; `-` for aggregate groups. | Use it to check whether scores are comparable across runs. |
| `metric` | Numeric metric selected for display, such as `accuracy`, `exact_match`, `rouge1`, `score`, or aggregate metrics. | If wrong or missing, inspect result JSON keys and metric whitelist/blacklist behavior. |
| `mode` | Inference mode inferred from the dataset inferencer: `gen`, `ppl`, `ll`, `unknown`, or `mixed` for groups. | Mixed groups are valid but need explanation because subsets used different inference modes. |
| model columns | Scores per model abbreviation or `summarizer_abbr`. | A `-` means the metric was not found for that model/dataset row. |

Scores are formatted with two decimals in the table. Inspect `results/<model>/<dataset>.json` when exact precision, raw metric keys, errors, or details matter.

## What `-` Means

A `-` is a placeholder, not a numeric zero. Common causes:

- The dataset abbreviation was requested in `summarizer.dataset_abbrs` but no parsed metric exists.
- A specific `(dataset, metric)` display request names a metric absent from that dataset's result JSON.
- A model has no result file for that dataset under `results/<model_abbr>/`.
- A result JSON contains `error` or only non-numeric/detail fields, so the default summarizer skips it.
- A summary group is missing one or more required subsets for that model.

Do not average `-` cells manually; repair the missing result, metric name, or group definition first.

## `dataset_abbrs` Display Order

`summarizer.dataset_abbrs` controls display order. Items may be strings or dataset/metric pairs:

```python
summarizer = dict(
    dataset_abbrs=[
        'race',
        'race-high',
        ('mmlu-humanities', 'accuracy'),
    ],
)
```

If `dataset_abbrs` is omitted, OpenCompass displays discovered dataset metrics in config order and then any extra group metrics. If it is present, rows that do not resolve to existing dataset/metric pairs appear as `-` unless the summarizer is explicitly told to skip all-slash rows.

## `summary_groups` Aggregation

`summary_groups` computes synthetic rows from subset rows. A typical group is:

```python
summarizer = dict(
    summary_groups=[
        dict(name='race', subsets=['race-high', 'race-middle']),
    ],
)
```

Key semantics:

- `name` is the synthetic row name.
- `subsets` may contain dataset abbreviations or `(dataset_abbr, metric)` pairs, but not a mixture of both forms in the same group.
- If any subset metric is missing for a model, that model's group row is not numerically aggregated; raw results record an error such as missing metrics.
- With no explicit aggregate mode, the default metric is usually `naive_average`; weighted groups use `weighted_average`; other supported flags include `sum`, `standard_deviation`, and `harmonic_mean` in the default summarizer.
- If all subset modes match, the group `mode` matches them; otherwise the group `mode` is `mixed`.
- `weights` are keyed by subset name in weighted groups. Check spelling because missing keys can raise or produce unintended weighting.

For the synthetic case “aggregate metric is missing despite subset results,” check all of these in order: exact subset abbreviations, numeric metric keys, per-model completeness, whether a requested display metric exists, and whether subset modes/versions are intentionally mixed.

## Metric Interpretation

OpenCompass chooses evaluator strategies in dataset `eval_cfg`. Common objective mappings include:

- Multiple choice or classification: `ACCEvaluator`, often with `first_capital_postprocess`, `first_option_postprocess`, or similar extraction.
- QA or reading comprehension: `EMEvaluator`, F1/exact-match evaluators, or dataset-specific postprocessors.
- Translation and generation: BLEU, ROUGE, or dataset-specific scoring.
- Code: HumanEval/MBPP-style execution pass rates such as `humaneval_pass@1` or pass@k variants.
- Toxicity or scoring-type tasks: metric names such as `avg_toxicity_score` from specialized evaluators.
- LLM-as-judge: usually `accuracy` after judge-output postprocessing, unless the dataset-specific summarizer reports another score.

The default summarizer ignores known bookkeeping fields such as `bp`, `sys_len`, `ref_len`, and `type`, and orders preferred metric names before less common numeric keys. If a result JSON has several numeric metrics, tell the user which metric the summary selected and whether another metric is more appropriate for the task.

## Result Reuse, Viz Mode, and Result Station

Use `--reuse` when reading a previous timestamped run directory. In `eval` mode, OpenCompass evaluates existing predictions; in `viz` mode, it summarizes existing results. The CLI rejects `eval`/`viz` without reuse or result-station read because there is no active inference stage to create new inputs.

The result station stores combined result, prediction, and config records by dataset and model. Important behavior:

- `--read-from-station` copies matching station results into the current run's local `results/`/`predictions/` structure and records existing combinations.
- `--station-overwrite` controls whether station writes replace existing station files.
- In `viz` mode, missing local files may be skipped while station reads provide available rows.
- Subjective station filenames include judge-model naming, often with `judged-by--<judge_abbr>` in local result paths.

When diagnosing station behavior, distinguish “not found at station,” “found but not overwritten,” and “local summary did not request/display the row.”

## Case and Multi-Model Analysis

`case_analyzer.py` reconstructs examples from prediction files, applies dataset and prediction postprocessors where configured, and writes all cases plus bad cases. For generation tasks, it currently treats all cases as bad cases for inspection rather than as a correctness judgment.

`viz_multi_model.py` loads multiple configs and timestamped work directories, builds `MultiModelSummarizer`, merges tables, and optionally shows one group. Use it as a reference pattern for comparing runs, but do not make runtime skill instructions depend on a source checkout path.

## Repeat Analysis

OpenCompass native repeat analysis inspects prediction text for abnormal repetition, length outliers, periodic token patterns, and gzip-compression signals. It can run after visualization when configured through the CLI's repeat-analysis flag, or via native tooling in a fully installed environment.

For lightweight review, this sub-skill bundles `scripts/analyze_repeat_results.py`. It reads JSON, JSONL, or CSV fixtures and reports repeated n-grams, excessive repeated-line ratios, duplicate predictions, and long-text outliers without importing OpenCompass.
