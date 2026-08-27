# Text and tabular workflows

## Command families

| CLI command | Config aliases | Route notes |
| --- | --- | --- |
| `text-classification` | `text-classification`, `text_classification`, binary/multi-class aliases | Text column plus label/target column. |
| `text-regression` | `text-regression`, `text_regression`, `text-single-column-regression` | Text column plus numeric target. |
| `token-classification` | `token-classification`, `token_classification` | Token/tag list data. |
| `seq2seq` | `seq2seq` | Source text to target text. |
| `sentence-transformers` | `st:pair`, `st:pair_class`, `st:pair_score`, `st:triplet`, `st:qa`, `sentence-transformers:*` | Trainer subtype controls column requirements. |
| `tabular` | `tabular` | Structured data with id/target columns and classification/regression mode. |
| `extractive-qa` | `extractive-qa`, `ext-qa`, `ext_qa`, `extractive_question_answering` | Context/question/answer rows. |

## Safe command inspection

```bash
python skills/disco/autotrain-advanced/scripts/inspect_cli.py text-classification --help
python skills/disco/autotrain-advanced/scripts/inspect_cli.py sentence-transformers --help
python skills/disco/autotrain-advanced/scripts/inspect_cli.py tabular --help
python skills/disco/autotrain-advanced/scripts/inspect_cli.py extractive-qa --help
```

## Config validation flow

```bash
python skills/disco/autotrain-advanced/scripts/validate_config.py path/to/text_or_tabular.yml
```

Then verify:

- `task` resolves to the expected family.
- `base_model` is the intended model id/path.
- `data.path`, `train_split`, and `valid_split` are valid for local or Hub data.
- `data.column_mapping` points to existing columns.
- `backend` is compatible with the user's auth and compute budget.

## Local data validation

Use the bundled schema validator before training local CSV/JSONL files:

```bash
python skills/disco/autotrain-advanced/sub-skills/text-and-tabular/scripts/validate_text_data.py \
  --task seq2seq \
  --text-column source \
  --target-column target \
  train.jsonl
```

For validation splits, run the same command on the validation file or use `--valid-path`.

## Launch pattern

Once config/data checks pass, a typical launch is either:

```bash
autotrain --config path/to/config.yml
```

or the task-specific CLI:

```bash
autotrain text-classification --train --project-name my-run --data-path data.csv --model distilbert-base-uncased --text-column text --target-column label --backend local
```

Always inspect the active command help before relying on a remembered flag name.

## Hub and local data

- Local backends can save prepared datasets locally.
- Non-local backends generally need data/model artifacts accessible to the backend, commonly through the Hugging Face Hub.
- If `hub.username` or `hub.token` uses `${ENV_VAR}` syntax in YAML, set the environment variable before parsing or running.
