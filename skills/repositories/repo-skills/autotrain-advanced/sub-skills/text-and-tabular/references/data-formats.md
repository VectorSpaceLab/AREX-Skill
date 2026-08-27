# Text and tabular data formats

Use these schemas to check local data before handing it to AutoTrain.

## Text classification and text regression

Required columns:

- `text_column` — input text, often `text`.
- `target_column` / label column — class label or numeric value, often `label` or `target`.

Validator example:

```bash
python skills/disco/autotrain-advanced/sub-skills/text-and-tabular/scripts/validate_text_data.py \
  --task text-classification --text-column text --target-column label train.csv
```

## Token classification

Required columns:

- `text_column` — token sequence. Values may be lists or strings parseable by `ast.literal_eval`.
- `target_column` — tag sequence. Values should align with tokens and may also be parseable list strings.

Validator example:

```bash
python skills/disco/autotrain-advanced/sub-skills/text-and-tabular/scripts/validate_text_data.py \
  --task token-classification --text-column tokens --target-column tags train.jsonl
```

## Seq2seq

Required columns:

- `text_column` — source/input text.
- `target_column` — output/target text.

## Extractive QA

Required columns:

- `text_column` — context passage.
- `question_column` — question.
- `answer_column` — answer dictionary or a string parseable into a dictionary.

Typical answer shape:

```json
{"text": ["answer span"], "answer_start": [42]}
```

## Sentence-transformers

Trainer subtype controls requirements:

| Trainer | Required columns |
| --- | --- |
| `pair` | `sentence1_column`, `sentence2_column` |
| `pair_class` | `sentence1_column`, `sentence2_column`, `target_column` |
| `pair_score` | `sentence1_column`, `sentence2_column`, `target_column` |
| `triplet` | `sentence1_column`, `sentence2_column`, `sentence3_column` |
| `qa` | `sentence1_column`, `sentence2_column` |

Defaults are usually `sentence1`, `sentence2`, `sentence3`, and `target`.

## Tabular

Required columns:

- `id_column` — id column, often `id` or `autotrain_id` after app munging.
- `target_columns` — one or more target columns.
- Feature columns are all remaining non-target columns.
- `task` should distinguish classification and regression in the tabular parameter object or app task key.

Validator example:

```bash
python skills/disco/autotrain-advanced/sub-skills/text-and-tabular/scripts/validate_text_data.py \
  --task tabular --id-column id --target-columns label train.csv
```

## LLM local data helper

The validator also supports `--task llm` because LLM local CSV/JSONL column checks are text-like. See `../llm-training/` for LLM-specific trainer semantics.
