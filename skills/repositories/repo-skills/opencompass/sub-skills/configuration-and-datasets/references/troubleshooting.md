# Troubleshooting Configuration and Datasets

## Config Import Errors

Symptoms:

- `ModuleNotFoundError` or `ImportError` while loading a config.
- `Config.fromfile` or `opencompass --dry-run` fails before task creation.

Fixes:

- Wrap config inheritance imports in `with read_base():`.
- Import installed OpenCompass config modules using `opencompass.configs...` or relative imports only when the config lives inside the config package.
- Alias duplicate imports: `from ... import models as judge_models`.
- If importing a model config pulls optional backends, route backend installation and model parameters to `model-backends`.
- Use `python -m py_compile config.py` to separate syntax errors from runtime import errors.

## Wrong Top-Level Variable Names

Symptoms:

- CLI loads the file but finds no tasks.
- A composed config silently evaluates fewer datasets or models than expected.

Fixes:

- Define `datasets = [...]` and `models = [...]` at top level for evaluation configs.
- Built-in dataset modules usually export variables like `mmlu_datasets`, not `datasets`; import and append them explicitly.
- Built-in model modules usually export `models`; alias every imported `models` variable before combining.
- Use `scripts/compare_config_keys.py config_a.py config_b.py --show datasets,models` to inspect static top-level names and literal entries.

## Prompt and Output Column Mismatch

Symptoms:

- Key errors for prompt placeholders such as `{problem}` or `{question}`.
- Evaluator receives empty or missing references.
- Generation completes but scores are missing or invalid.

Fixes:

- Ensure every prompt placeholder is listed in `reader_cfg.input_columns` and exists in the JSONL/CSV row or dataset item.
- Ensure `reader_cfg.output_column` matches the reference column used by the evaluator.
- For `GenericLLMEvaluator`, the judge prompt often uses `{prediction}` plus original columns such as `{problem}` and `{answer}`; the evaluator `dataset_cfg.reader_cfg` must expose those fields.
- For local CSV, confirm the header names are exact; spaces and capitalization are significant.
- For local JSONL, validate every line is a JSON object with the same required fields.

Quick JSONL check:

```bash
python - <<'PY'
import json, sys
path = sys.argv[1]
with open(path, encoding='utf-8-sig') as f:
    for number, line in enumerate(f, 1):
        row = json.loads(line)
        missing = {'problem', 'answer'} - row.keys()
        if missing:
            raise SystemExit(f'line {number}: missing {sorted(missing)}')
print('ok')
PY data/local_qa.jsonl
```

## DATASET_SOURCE and Dataset Mapping

Symptoms:

- A dataset downloads from the wrong source.
- ModelScope IDs are ignored.
- Local fallback path is not used.

Fixes:

- `DATASET_SOURCE=ModelScope` is the common switch for loaders that explicitly support ModelScope.
- Check that the config `path` matches a `DATASETS_MAPPING` key when using logical OpenCompass dataset names.
- Mapping entries can contain `ms_id`, `hf_id`, and `local`; missing IDs mean that source is not available for that dataset.
- Some loaders pass `local_mode=True` to data-path resolution, which favors local paths. Inspect loader behavior if source switching is unexpected.
- For local one-off JSONL/CSV evaluations, avoid source mapping and use `CustomDataset` with an explicit path.

## Local Dataset File Layout

Symptoms:

- `Unsupported file format` from `CustomDataset`.
- `FileNotFoundError` for `path`/`file_name` combinations.
- CSV data loads with wrong columns.

Fixes:

- `CustomDataset` supports `.jsonl` and `.csv`; it does not load `.json`, `.xlsx`, or directories unless `file_name` points to a supported file.
- If `path` is a directory, provide `file_name='dev.jsonl'` or `file_name='dev.csv'`.
- JSONL must contain one JSON object per line.
- CSV must include a header row.
- Use UTF-8 or UTF-8 with BOM for local files.

## Missing Dataset Mapping

Symptoms:

- Logical path such as `opencompass/my-dataset` cannot resolve.
- A new dataset class works locally but not for other users.

Fixes:

- Add a `DATASETS_MAPPING` entry for reusable logical paths.
- Keep `path` in the dataset config equal to the mapping key.
- Include `hf_id`, `ms_id`, or `local` only when that source really exists.
- For public catalog inclusion, add dataset-index metadata in the source repository; for private skill usage, document the local file expectations instead.

## Generated Config Names and Suffixes

Symptoms:

- Multiple config files exist for one dataset and it is unclear which to import.
- A reproduced run differs after using a non-suffixed config.

Fixes:

- Treat suffixes like `_gen`, `_ppl`, `_llmjudge`, and `_cascade` as evaluation-method indicators.
- Treat trailing hashes as prompt/config version identifiers.
- Use non-hash files only when the latest/default prompt is intended.
- Preserve exact hash-suffixed imports when reproducing a known result.
- Use `scripts/list_opencompass_configs.py dataset_token --kind datasets` to see available variants.

## Static Compare Looks Incomplete

Symptoms:

- `compare_config_keys.py` reports no dataset abbrs or only top-level names.

Fixes:

- Static comparison only sees literal assignments in the parsed file. It cannot execute imports or resolve dynamically built lists.
- Use it to detect obvious changed keys and literal config entries, then run `opencompass --dry-run --debug` for full config expansion.
- If a config is mostly `read_base` imports, compare the imported source config files directly or inspect them with the catalog script.
