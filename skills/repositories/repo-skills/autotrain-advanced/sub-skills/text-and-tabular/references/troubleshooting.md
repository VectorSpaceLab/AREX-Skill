# Text and tabular troubleshooting

## Column mapping failures

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `X not in train data` | `data.column_mapping` or CLI column flag points to a missing column | Inspect the file columns and rerun the validator with the intended mapping. |
| Validation split fails while train passes | Train and validation files have different schemas | Run the validator on both files and align column names/types. |
| Token classification list parsing warnings | Token/tag values are strings but not parseable list literals | Store tokens and tags as JSON/Python-list strings or native list values in JSONL. |
| Extractive QA answer parsing warnings | Answer values are strings but not dict-like | Store answers as dictionaries with text/span information or parseable dict strings. |

## Task alias problems

- `st:*` and `sentence-transformers:*` are sentence-transformer task aliases; use the subtype (`pair`, `pair_class`, `pair_score`, `triplet`, or `qa`) to decide columns.
- `text-binary-classification` and `text-classification` resolve to the same text classification family.
- `text-single-column-regression` and `text-regression` resolve to the text regression family.
- `ext-qa` and `extractive-qa` resolve to extractive QA.

## Local vs Hub data

- Local paths are safest with local backends.
- Hosted backends need data accessible to the backend; push or use a Hub dataset when required.
- If YAML contains `${HF_TOKEN}` or `${HF_USERNAME}`, set those variables before parser validation if the config expects them to resolve.

## Model and runtime issues

- Start with a small public model and tiny local sample when debugging flags or columns.
- Training commands can download tokenizer/model weights; do not use them as cheap verification probes.
- If a trainer fails after data munging, keep the prepared data artifact and debug model/backend separately.

## Minimal recovery checklist

```bash
python skills/disco/autotrain-advanced/scripts/check_install.py
python skills/disco/autotrain-advanced/scripts/inspect_cli.py <task-command> --help
python skills/disco/autotrain-advanced/scripts/validate_config.py path/to/config.yml
python skills/disco/autotrain-advanced/sub-skills/text-and-tabular/scripts/validate_text_data.py --task <task> ... train.csv
```
