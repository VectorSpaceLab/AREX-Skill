# Troubleshooting

Use these checks when FlashRAG config or data preparation fails before retrieval/indexing or pipeline execution.

## Missing runtime dependencies

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'yaml'` | PyYAML is missing. | Install FlashRAG runtime dependencies or install PyYAML before constructing `Config`. The bundled validator can still check YAML file presence without PyYAML. |
| `ModuleNotFoundError: No module named 'numpy'` | NumPy is missing. | Required by seed setup and dataset utilities; install runtime dependencies before real `Config`/`Dataset` usage. |
| `ModuleNotFoundError: No module named 'torch'` | Torch is missing. | `Config._set_seed()` imports Torch directly; install a compatible Torch build or avoid real `Config` construction in shape-only validation. |
| `ModuleNotFoundError: No module named 'datasets'` | Hugging Face datasets is missing. | Needed for parquet data loading, not simple JSONL validation. |
| Import succeeds for `flashrag` but deeper modules fail | Top-level package is available, optional/runtime dependencies are not. | Validate inputs with the bundled script, then prepare the runtime environment before running FlashRAG APIs. |

## Config creates output directories unexpectedly

By default, `Config` creates a timestamped run directory under `save_dir` and writes the effective `config.yaml`. This happens during construction, before a pipeline is run.

Fix for dry checks:

```yaml
disable_save: true
```

Also review `save_dir` and `save_note`; the effective directory includes `dataset_name`, timestamp, and `save_note`.

## Config priority surprises

Expected priority is `config_dict` > YAML file > defaults. If a value is not what you expect:

1. Check whether a dict override was passed by the caller.
2. Check whether the YAML file defines the same key.
3. Check whether a default value exists in `basic_config`.
4. For nested maps such as `model2path`, remember FlashRAG shallow-merges the section instead of replacing the entire map when both old and new values are dicts.

For a no-side-effect priority test, include `disable_save: true` in the highest-priority layer.

## Split normalization

`split` must exist in the effective config.

- `split: null` becomes `['train', 'dev', 'test']`.
- `split: test` becomes `['test']`.
- `split: [test, dev]` stays a list.

If code later expects a string, it is likely using pre-normalized assumptions. Treat `config['split']` as a list after `Config` construction.

## Missing required config keys

A minimal custom config that does not inherit defaults can fail with missing keys such as `split`, `gpu_id`, `dataset_name`, `data_dir`, `model2path`, `model2pooling`, `method2index`, `retrieval_method`, `generator_model`, `metric_setting`, `seed`, `save_dir`, or `save_note`.

Prefer starting from YAML/defaults and overriding only necessary keys. If writing a shape-only custom config for documentation or tests, include `disable_save: true` and the environment keys shown in `configuration.md`.

## Invalid JSONL

Common failures:

- Blank lines in strict validation mode.
- Trailing commas or comments, which are not valid JSON.
- A line containing a JSON array instead of one JSON object.
- Wrong extension assumptions: FlashRAG's `.json` loader reads one object per line, similar to JSONL.

Fix by rewriting as one JSON object per line. Use the validator with `--eval-jsonl` or `--corpus-jsonl` to get line numbers and field-specific messages.

## Corpus rows missing `id` or `contents`

Retrieval corpus rows should include:

```json
{"id": 0, "title": "Optional title", "contents": "Text used for retrieval"}
```

`contents` must be a non-empty string. `id` should be unique across the corpus. Route index-building questions to `retrieval-and-indexing` after the corpus passes this shape check.

## Evaluation rows missing `question` or `golden_answers`

Evaluation rows should include:

```json
{"id": "test_0", "question": "...", "golden_answers": ["..."]}
```

`question` must be a non-empty string. `golden_answers` should be a non-empty list of strings for normal QA evaluation. Missing `id` is tolerated by `Item`, but it weakens traceability and should be fixed for reusable fixtures.

## Mixed corpus/evaluation files

If a row has both `question` and `contents`, or both `golden_answers` and corpus-only fields, decide which role the file serves and split it into separate files. This avoids accidentally passing corpus documents into a QA pipeline or evaluation questions into an index builder.

## Fast isolation commands

```bash
python skills/flashrag/sub-skills/data-and-config/scripts/validate_flashrag_inputs.py --config my_config.yaml --show-effective-summary
python skills/flashrag/sub-skills/data-and-config/scripts/validate_flashrag_inputs.py --eval-jsonl dataset/nq/test.jsonl
python skills/flashrag/sub-skills/data-and-config/scripts/validate_flashrag_inputs.py --corpus-jsonl indexes/general_knowledge.jsonl
```

The validator intentionally avoids importing FlashRAG, Torch, NumPy, or PyYAML. It checks presence and lightweight syntax/shape, not full runtime compatibility.
