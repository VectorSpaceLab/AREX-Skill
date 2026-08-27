---
name: text-and-tabular
description: "Operate AutoTrain Advanced text, NLP, sentence-transformers,
  extractive QA, and tabular training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent-skill: autotrain-advanced
license: Apache 2.0
---

# AutoTrain text, NLP, embeddings, and tabular workflows

Use this sub-skill for non-LLM text tasks, sentence-transformers, extractive QA, and tabular workflows.

## Supported entry points

- `autotrain text-classification --help`
- `autotrain text-regression --help`
- `autotrain token-classification --help`
- `autotrain seq2seq --help`
- `autotrain sentence-transformers --help`
- `autotrain tabular --help`
- `autotrain extractive-qa --help`
- YAML aliases such as `text-classification`, `text-regression`, `token-classification`, `seq2seq`, `extractive-qa`, `sentence-transformers:pair`, `st:triplet`, and `tabular`

If the request is LLM-specific, route to `../llm-training/`; the data validator in this sub-skill still supports `--task llm` for local column checks.

## Task families

| Family | Typical data shape | Notes |
| --- | --- | --- |
| text classification/regression | text column + target/label column | Binary and multi-class classification resolve to the same text-classification trainer family. |
| token classification | token list column + tag list column | Values may be Python-list strings that AutoTrain parses with `ast.literal_eval`. |
| seq2seq | source text + target text | Use for summarization/translation-style data. |
| extractive QA | context text + question + answer dict/string | Answer values should be dict-like or parseable into dicts. |
| sentence-transformers | pair/triplet/QA rows | Trainer variants control whether target labels/scores are needed. |
| tabular | id column + one or more target columns | `task` distinguishes classification vs regression. |

## Safe validation sequence

1. Inspect the specific command help with the root `inspect_cli.py` helper.
2. Validate YAML configs with the root `validate_config.py` helper.
3. Validate local CSV/JSONL columns with `scripts/validate_text_data.py`.
4. Launch training only after model, data path, split names, backend, and Hub credentials are confirmed.

## Useful script

```bash
python skills/disco/autotrain-advanced/sub-skills/text-and-tabular/scripts/validate_text_data.py \
  --task text-classification \
  --text-column text \
  --target-column label \
  data.csv
```

The script performs local schema checks only. It does not import trainer code, upload data, or start training.

## References

- `references/workflows.md` — task/alias map and command/config patterns.
- `references/data-formats.md` — column schemas and validator examples.
- `references/troubleshooting.md` — column mapping, parser, Hub, and local dataset recovery.
