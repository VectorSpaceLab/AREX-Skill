# Results and status

VLMEvalKit writes one model-level output root per model and one eval-id run directory per invocation. Use this reference to locate predictions, evaluation files, checkpoints, run summaries, and failure evidence.

## Output layout

Default shape:

```text
<work-dir>/
  <model-name>/
    <latest symlinks to selected files>
    logs/
      <eval-id>_<time>.log
    <eval-id>/
      status.json
      status.json.lock
      <model-name>_<dataset>.xlsx|tsv|json
      <model-name>_<dataset>_<judge-or-metric>.csv|json|xlsx
      <model-name>_<dataset>_checkpoint.pkl
      <model-name>_<dataset>_PREV.pkl
      <model-name>_<dataset>_structs.pkl
      <rank><world-size>_<dataset-or-result-stem>.pkl
      eval_logs/
        <model-name>_<dataset>_eval.log
```

Notes:

- `run.py` creates eval ids like `TYYYYMMDD-HHMMSS`.
- Local mode writes `logs/` under `<work-dir>/logs` and run files under `<work-dir>/<model>/<eval-id>/`.
- API mode writes model-specific `logs/` and `eval_logs/` under the model/run output tree.
- After evaluation, rank 0 creates relative symlinks in `<work-dir>/<model>/` for latest prediction/evaluation files and, in local mode, `status.json`.
- Temporary files ending in `_checkpoint.pkl`, `_PREV.pkl`, and `_structs.pkl` are intentionally excluded from latest symlinks.

## Prediction and evaluation file formats

| Purpose | Default | Environment override | Notes |
| --- | --- | --- | --- |
| Predictions | `.xlsx` | `PRED_FORMAT=tsv` or `PRED_FORMAT=json` | Use TSV for long responses to avoid spreadsheet cell truncation. |
| Evaluation metrics | `.csv` | `EVAL_FORMAT=json` | Some older/evaluator-specific paths may still produce `.xlsx` auxiliary files. |
| Checkpoints | `.pkl` | none | Used for partial/resume behavior and removed after successful consolidation in many paths. |

Prediction files contain at least `index` and `prediction`. They may include extra columns such as `thinking` when `SPLIT_THINK` is enabled or `extra_records` when a model returns structured records.

## `status.json` fields

Typical top-level fields:

```json
{
  "schema_version": "1.0",
  "eval_id": "T20260101-120000",
  "created_at": "...",
  "updated_at": "...",
  "commit": "...",
  "argv": ["run.py", "--data", "..."],
  "api_mode": false,
  "world_size": 1,
  "pred_format": "xlsx",
  "eval_format": "csv",
  "mode": "all",
  "reuse": false,
  "reuse_aux": "all",
  "model_name": "MODEL",
  "datasets": {}
}
```

Per-dataset entries under `datasets` may include:

| Field | Meaning |
| --- | --- |
| `status` | One of `pending`, `infer`, `eval`, or `done`. Status only moves forward. |
| `prediction_file` | Prediction path, usually relative to the run directory. |
| `judge_model` | Judge selected by `run.py` or overridden by CLI flags. |
| `source_run` | Eval id reused by `--reuse`, when found. |
| `reuse_aux` | Auxiliary reuse policy recorded for the dataset. |
| `skip_reason` | Reason evaluation was skipped, such as inference-only mode, official-submission-only, no ground truth, or missing reusable prediction. |
| `error_message` | Exception text captured for failed model/dataset combinations or evaluator subprocesses. |
| `primary_metric` | Metric key(s) selected by the dataset reporter. |
| `metrics` | Flattened metric dictionary from the evaluator result. |
| `updated_at` | Last dataset-status update time. |

`status.json` is the fastest first stop for deciding whether to rerun inference, run eval-only reuse, inspect prediction rows, or debug an evaluator.

## Checkpoints and temporary files

| File pattern | Producer | Use |
| --- | --- | --- |
| `<model>_<dataset>_checkpoint.pkl` | API/local checkpointing paths | Partial API/local inference results. Failed API rows are dropped from reuse when retrying. |
| `<model>_<dataset>_PREV.pkl` | `infer_data_job*` wrappers | Previous prediction rows copied before retrying incomplete work. |
| `<model>_<dataset>_<nframe>frame_<pack>_checkpoint.pkl` | Video API path | Video checkpoint keyed by video settings. |
| `<model>_<dataset>_<nframe>frame_<pack>_structs.pkl` | Video prompt construction | Cached video prompt structures. |
| `<rank><world-size>_<dataset>.pkl` | Image/multi-turn distributed local mode | Per-rank partial inference output before rank 0 merges. |
| `<rank><world-size>_<result-stem>.pkl` | Video distributed local mode | Per-rank partial video inference output before rank 0 merges. |

Do not delete checkpoint or PREV files while a run is active. For manual recovery, copy the entire eval-id directory first, then use `vlmutil merge_pkl` or a rerun with `--reuse-aux infer`.

## Summaries printed by `run.py`

At the end of each model run, rank 0 calls the status reporter and prints a run summary with columns similar to:

- `benchmark`
- `infer_fail_rate`
- `judge_fail_rate`
- `primary_metric`
- `primary_metric_value`
- `skip_reason`
- `eval_error`

If no rows are shown, check whether `status.json` exists, contains dataset entries, and has prediction files that can be loaded.

## Bundled summary script

The bundled script parses `status.json` directly and can count failed predictions from common prediction-file formats without importing `vlmeval`.

```bash
# Resolve latest child run under a model root, then print metric comparison.
python sub-skills/evaluation/scripts/summarize_runs.py --work-dir outputs/GPT4o

# Print detailed per-dataset status for a specific run.
python sub-skills/evaluation/scripts/summarize_runs.py \
  --work-dir outputs/GPT4o/T20260101-120000 \
  --verbose

# Compare selected datasets across multiple model roots or run dirs.
python sub-skills/evaluation/scripts/summarize_runs.py \
  --work-dir outputs/GPT4o \
  --work-dir outputs/OtherModel \
  --data MMBench_DEV_EN MMStar
```

Expected output: a CSV block followed by a readable table. Empty output usually means no dataset rows or no selected primary metrics matched the filter.

## Bundled API failure scan

```bash
python sub-skills/evaluation/scripts/scan_api_failures.py \
  --model-root outputs/GPT4o \
  --datasets MMBench_DEV_EN MMStar
```

The scanner reports:

- Missing expected prediction files when `--show-missing` and `--datasets` are provided.
- Prediction rows containing the standard API failure text.
- Evaluation auxiliary files containing common failure markers in `log`, `res`, or score columns.
- A nonzero exit code only when `--fail-on-detected` is supplied and failures or missing files are detected.

Use this before deciding between `--keep-failed`, a retry with `--reuse-aux infer`, or deeper provider troubleshooting.

## Interpreting common skip reasons

| Skip reason | Meaning | Next action |
| --- | --- | --- |
| `mode_infer` | The command intentionally stopped after inference. | Run `--mode eval --reuse`. |
| `No infer result found` | Eval-only mode did not find a reusable prediction file. | Check model/work-dir names and prior eval ids. |
| `Incomplete infer result` | A prediction file exists but not all dataset indices have completed non-failed predictions. | Retry without `--keep-failed` or inspect failures. |
| `invalid_dataset` | Dataset construction returned invalid/none. | Check dataset name, config JSON, cache/download prerequisites. |
| `official_submission_only_*` | The dataset needs external official evaluation. | Use generated submission file outside VLMEvalKit if authorized. |
| `test_split_without_ground_truth` | Inference is supported but local evaluation is not. | Treat predictions as submission artifacts. |
| `mmbench_evaluation_requires_official_server` | Local file lacks official MMBench answers. | Use an official/authorized data source or skip local evaluation. |
| `evaluate_returned_none` | Dataset evaluator returned no result object. | Inspect evaluator docs and generated prediction file. |

## Safe cleanup and archiving

- Keep `status.json`, logs, prediction files, and evaluation files together; they cross-reference one another.
- Archive full eval-id directories rather than only latest symlinks.
- Delete temporary checkpoint files only after confirming predictions and metrics are complete or after copying the run for forensic inspection.
- When comparing runs, prefer specific eval-id directories over mutable latest symlinks.
