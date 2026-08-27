# RACE Data Formats

This reference describes the data shape consumed by XLNet's RACE multiple-choice workflow.

## Directory layout

Point `--data_dir` at the unpacked RACE root:

```text
RACE_DIR/
  train/
    middle/
      <json files>
    high/
      <json files>
  dev/
    middle/
      <json files>
    high/
      <json files>
  test/
    middle/
      <json files>
    high/
      <json files>
```

The loader lists every file under `RACE_DIR/<split>/<level>/` and parses it as JSON; it does not depend on a specific filename extension. Missing `middle` or `high` directories produce file-listing errors unless the corresponding level is filtered out.

## Per-file JSON schema

Each source file represents one article with multiple questions:

```json
{
  "article": "Passage text...",
  "questions": ["Question with _ placeholder?", "Another question?"],
  "options": [["A option", "B option", "C option", "D option"], ["...", "...", "...", "..."]],
  "answers": ["A", "C"]
}
```

Required fields:

| Field | Type | Contract |
| --- | --- | --- |
| `article` | string | Passage/context text shared by all questions in the file. |
| `questions` | list of strings | One question per answer. A blank placeholder is represented by `_` when the option should be substituted into the question. |
| `options` | list of 4-string lists | Four answer candidates per question. The outer list length must match `questions` and `answers`. |
| `answers` | list of `"A"`, `"B"`, `"C"`, or `"D"` | Correct candidate labels. The loader maps them to integer labels 0..3. |

Optional metadata fields may be present and are ignored by the XLNet RACE loader.

## Example construction semantics

For every question in a JSON article file, the loader creates one RACE example with four candidate sequences:

1. Tokenize the article as the context.
2. For each of the four options:
   - if the question contains `_`, replace `_` with the option text;
   - otherwise concatenate `question + " " + option`.
3. Tokenize that question-answer string.
4. Truncate the question-answer token list to `max_qa_length` by keeping the rightmost tokens.
5. Truncate the context so `context + SEP + question-answer + SEP + CLS` fits into `max_seq_length` for each candidate.
6. Flatten all four candidate feature arrays into one example.

Resulting TFRecord feature shapes per RACE example:

| Feature | Shape | Notes |
| --- | --- | --- |
| `input_ids` | `[max_seq_length * 4]` | Four candidate sequences are flattened. |
| `input_mask` | `[max_seq_length * 4]` | Padding mask; padded positions are `1`, real tokens are `0` in this codebase. |
| `segment_ids` | `[max_seq_length * 4]` | Context, question-answer, CLS, SEP, and PAD segment ids. |
| `label_ids` | scalar | 0..3 candidate label. |
| `is_real_example` | scalar | 0 only for padding examples added before evaluation. |

## Split and level filters

- `--eval_split=dev` reads `RACE_DIR/dev/...`; `--eval_split=test` reads `RACE_DIR/test/...`.
- `--high_only=True` skips the `middle` level for any split loaded by the run.
- `--middle_only=True` skips the `high` level for any split loaded by the run.
- Do not set both filters. The loader applies both skip checks and can leave no real examples.
- The filters affect training and evaluation. For full-RACE training followed by high-only or middle-only evaluation, run a separate eval-only command against the trained `model_dir`.

## TFRecord cache names

The workflow writes preprocessed TFRecords under `--output_dir` and reuses them unless `--overwrite_data=True`.

| Mode | File name pattern |
| --- | --- |
| Training | `<spiece basename>.len-<max_seq_length>.train.tf_record` |
| Evaluation | `<spiece basename>.len-<max_seq_length>.<eval_split>.tf_record` |
| High-only eval | `high.<spiece basename>.len-<max_seq_length>.<eval_split>.tf_record` |
| Middle-only eval | `middle.<spiece basename>.len-<max_seq_length>.<eval_split>.tf_record` |

Training cache names do not include the high/middle filter. When doing high-only or middle-only training, use a dedicated `output_dir` or force regeneration with `--overwrite_data=True` so an existing full-RACE training cache is not silently reused.

## Length and memory implications

- The documented RACE recipes use `max_seq_length=512` and `max_qa_length=128` because passages are long and questions may require reasoning across the passage.
- One RACE example contains four candidates, so memory scales approximately with `batch_size * 4 * max_seq_length` candidate-token slots.
- Reducing `max_seq_length` and `max_qa_length` can make local debugging feasible, but expect lower accuracy and more context truncation.
