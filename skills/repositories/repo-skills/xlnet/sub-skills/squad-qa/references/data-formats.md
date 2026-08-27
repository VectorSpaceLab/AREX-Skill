# SQuAD data, cache, and output formats

## Input JSON contract

`run_squad.py` expects the standard SQuAD object shape:

```json
{
  "version": "v2.0",
  "data": [
    {
      "title": "Article title",
      "paragraphs": [
        {
          "context": "Paragraph text containing answer spans.",
          "qas": [
            {
              "id": "question-id",
              "question": "Question text?",
              "answers": [
                {"text": "answer text", "answer_start": 10}
              ],
              "is_impossible": false
            }
          ]
        }
      ]
    }
  ]
}
```

### Training JSON requirements

When `read_squad_examples(..., is_training=True)` reads `--train_file`:

- Every QA must have `id`, `question`, `answers`, and `is_impossible`.
- Answerable examples must have exactly one answer in `answers`.
- Unanswerable SQuAD 2.0 examples should use `"is_impossible": true` and an empty `answers` list.
- Answerable examples should use `"is_impossible": false` and one answer containing `text` and `answer_start` character offset.
- Raw SQuAD 1.1 train files usually omit `is_impossible`; add `"is_impossible": false` to each QA before preprocessing or training.

If a training answerable QA has zero or multiple answers, the script raises `ValueError("For training, each question should have exactly 1 answer.")`.

### Prediction JSON requirements

When `read_squad_examples(..., is_training=False)` reads `--predict_file`:

- `id`, `question`, and `context` are required.
- `answers` are used later by the evaluator if labels are present; for blind test prediction, labels may be absent depending on the task wrapper.
- `is_impossible` is not read during example construction in prediction mode, but SQuAD 2.0 evaluation uses empty answers to determine no-answer questions.

For SQuAD 1.1 dev evaluation, every question has at least one answer. For SQuAD 2.0 dev evaluation, unanswerable questions should have empty `answers`.

## Model artifact contract

| Artifact | Used by | Required for |
| --- | --- | --- |
| `spiece.model` | SentencePiece tokenizer | preprocessing, training, prediction |
| `xlnet_config.json` | XLNet model config | training and prediction |
| `xlnet_model.ckpt*` pretrained checkpoint files | `--init_checkpoint` | training initialization |
| Fine-tuned checkpoint under `--model_dir` | Estimator checkpoint loading | prediction-only and resumed prediction |

`--init_checkpoint` is for initializing training. In `PREDICT` mode the model function logs that `init_checkpoint` is not being used; prediction uses the latest checkpoint from `--model_dir`.

## Directory roles

| Path flag | Role | Typical contents |
| --- | --- | --- |
| `--output_dir` | Feature cache and TFRecord directory. Used for training TFRecords and eval cache. | `*.train.tf_record`, `*.eval.tf_record`, `*.eval.features.pkl` |
| `--model_dir` | Estimator model directory. | checkpoints, event files, graph metadata |
| `--predict_dir` | Final prediction outputs. | `predictions.json`, `nbest_predictions.json`, `null_odds.json` |
| `--train_file` | Raw SQuAD training JSON. | `train-v1.1.json` after compatibility edit or `train-v2.0.json` |
| `--predict_file` | Raw SQuAD dev/test JSON. | `dev-v1.1.json`, `dev-v2.0.json`, or test JSON |

Keep these directories separate. A common failure is using `--model_dir` as `--output_dir`, which mixes long-lived checkpoints with disposable feature cache.

## Training TFRecord naming

Preprocessing writes one training TFRecord per process:

```text
<output_dir>/<spiece_basename>.<proc_id>.slen-<max_seq_length>.qlen-<max_query_length>.train.tf_record
```

Example with `spiece.model`, `proc_id=3`, `max_seq_length=512`, and `max_query_length=64`:

```text
proc_data/squad/spiece.model.3.slen-512.qlen-64.train.tf_record
```

Training reads all matching shards with this glob:

```text
<output_dir>/<spiece_basename>.*.slen-<max_seq_length>.qlen-<max_query_length>.train.tf_record
```

That is why parallel preprocessing can safely write to the same `--output_dir` as long as every process uses the same `--num_proc` and a different `--proc_id`.

## Eval cache naming

Prediction creates or reuses one eval TFRecord and one feature pickle:

```text
<output_dir>/<spiece_basename>.slen-<max_seq_length>.qlen-<max_query_length>.eval.tf_record
<output_dir>/<spiece_basename>.slen-<max_seq_length>.qlen-<max_query_length>.eval.features.pkl
```

If those files already exist and `--overwrite_data=False`, prediction reuses them. Use `--overwrite_data=True` or delete the eval cache after changing `--predict_file`, SentencePiece model, sequence length, query length, or doc stride.

## Feature fields written to TFRecords

Training and eval TFRecords include common fields:

| Field | Meaning |
| --- | --- |
| `unique_ids` | Feature id used to join model outputs back to examples. |
| `input_ids` | SentencePiece token ids with XLNet special tokens. |
| `input_mask` | Mask for real vs padding positions. |
| `p_mask` | Mask for invalid answer positions such as question tokens, padding, SEP, and CLS. |
| `segment_ids` | Segment ids for paragraph/question/special tokens. |
| `cls_index` | Position of CLS token used by the answerability head. |

Training features additionally include:

| Field | Meaning |
| --- | --- |
| `start_positions` | Gold start token index. |
| `end_positions` | Gold end token index. |
| `is_impossible` | Float label for no-answer regression loss. |

## Prediction outputs

`run_squad.py` writes these files to `--predict_dir`:

| File | Schema | Purpose |
| --- | --- | --- |
| `predictions.json` | `{question_id: "best answer text"}` | Final best non-null answer text per question. |
| `nbest_predictions.json` | `{question_id: [{text, probability, start_log_prob, end_log_prob}, ...]}` | N-best spans for inspection and debugging. |
| `null_odds.json` | `{question_id: score}` | No-answer score (`cls_logits`) used by threshold search. |

Prediction always stores the best non-null span in `predictions.json`; the SQuAD 2.0 threshold search uses `null_odds.json` to compute best exact/F1 threshold metrics.

## SQuAD 1.1 compatibility note

The CLI can be used for SQuAD 1.1, but the training reader was written in a SQuAD 2.0 style and indexes `qa["is_impossible"]` during training. Before preprocessing SQuAD 1.1 train data, normalize each QA to include:

```json
"is_impossible": false
```

Do not add empty answers to answerable SQuAD 1.1 QAs; preserve the original single answer and `answer_start`.
