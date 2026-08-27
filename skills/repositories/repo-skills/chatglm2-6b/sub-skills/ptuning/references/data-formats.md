# P-Tuning Data Formats

## ADGEN-style summarization

The documented example uses JSON records with `content` as the prompt and
`summary` as the target:

```json
{"content":"类型#上衣*版型#宽松","summary":"这件上衣版型宽松。"}
```

The command must pass `--prompt_column content --response_column summary`.
The repository's sample launcher expects JSON files for `--train_file` and
`--validation_file`; the parser accepts `.json`/`.csv` extensions, while the
examples use JSON arrays/records.

## Multi-turn chat data

Chat training uses records such as:

```json
{"prompt":"第一问","response":"第一答","history":[]}
{"prompt":"第二问","response":"第二答","history":[["第一问","第一答"]]}
```

Pass `--prompt_column prompt --response_column response --history_column
history`. Every history item must be a two-element query/response pair. The
preprocessor calls the ChatGLM tokenizer's `build_prompt`, then truncates to
`max_source_length`; long history is therefore not free context.

## Length and padding

Key data arguments from `arguments.py`:

- `max_source_length` defaults to 1024.
- `max_target_length` defaults to 128.
- `val_max_target_length` defaults to `max_target_length`.
- `max_train_samples`, `max_eval_samples`, and `max_predict_samples` limit
  subsets for debugging.
- `ignore_pad_token_for_loss` defaults to true; padded labels become `-100`.
- `preprocessing_num_workers` controls dataset mapping workers.

Training creates a sequence of source ids, target ids, EOS, and padding. If
inputs or targets are empty, the preprocessing function skips that record.
Validate field names and non-empty strings before launching a long run.

## Checkpoint output

P-Tuning v2 uses `--pre_seq_len` and optionally `--prefix_projection`; the
trainer saves only trainable prefix parameters when `save_changed` is enabled.
Full fine-tuning saves the full model. Keep output directories distinct so a
prefix checkpoint is not mistaken for a full checkpoint.
