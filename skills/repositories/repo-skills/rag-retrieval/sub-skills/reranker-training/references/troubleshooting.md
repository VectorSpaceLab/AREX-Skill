# Reranker Training Troubleshooting

## Schema Mismatches

Symptoms:

- `KeyError: 'query'`, `KeyError: 'content'`, or `KeyError: 'hits'`.
- validator reports that pointwise data looks grouped, or grouped data looks pointwise.

Fix:

- For `train_dataset_type: pointwise`, each line must contain `query`, `content`, and the configured label field.
- For `train_dataset_type: grouped`, each line must contain `query` and `hits`; each hit must contain `content` and the configured label field.
- Keep validation data shape aligned with `val_dataset_type`.

## Wrong `label_key`

Symptoms:

- labels silently become `0` in the original dataset loader when the configured label key is absent.
- validator reports missing label fields.
- training loss does not move because every label is effectively negative.

Fix:

- If the JSONL uses `score`, set `train_label_key: "score"` and `val_label_key: "score"`.
- If the JSONL uses `label`, keep the default `label` keys.
- Do not mix `label` for training and `score` for validation unless the files really differ.

## Pointwise Label Scaling

Symptoms:

- `ValueError: Label is out of range.`
- user has `0/1/2` labels but left `max_label: 1`.
- labels are continuous probabilities but config uses a discrete range that excludes them.

Fix:

- For `0/1/2` labels, set `min_label: 0` and `max_label: 2`.
- For existing probabilities in `[0, 1]`, set `min_label: 0` and `max_label: 1`.
- Use `pointwise_mse` for teacher scores or regression-like labels; use `pointwise_bce` for binary or soft-label classification.

## Grouped Samples Disappear

Symptoms:

- training uses far fewer groups than expected.
- logs mention queries skipped for having fewer hits than `train_group_size`.
- validator reports many undersized records or all-identical groups.

Cause:

- Any query with fewer hits than `train_group_size` is skipped entirely.
- Any formed group with all identical labels is skipped.
- A short final group can be padded from earlier hits, but it is still skipped if labels remain identical.

Fix:

- Lower `train_group_size`.
- Add more candidate hits per query.
- Ensure each query group contains at least two different labels.
- Switch to pointwise training if candidate counts are too sparse for grouped losses.

## `train_group_size` Problems

Symptoms:

- assertion failure for grouped data.
- reshape errors in ranking losses.

Fix:

- Set `train_group_size >= 2` for grouped data.
- Use grouped data only with `pairwise_ranknet` or `listwise_ce`.
- Do not use grouped losses with pointwise data.
- Remember model input pairs per training step are `batch_size * train_group_size` for grouped data.

## Listwise Label Issues

Symptoms:

- listwise CE behaves unexpectedly.
- groups have no positive labels or multiple positives.

Fix:

- Prefer one positive label and the rest `0` for each group when using `listwise_ce`.
- Treat multiple non-zero labels as a deliberate soft target only if that is intended.
- If labels are graded relevance values and relative order matters, `pairwise_ranknet` is usually safer.

## Loss And Model Compatibility

Symptoms:

- loss is missing from model output.
- loss stays flat or errors at reshape time.

Fix:

- Use only actual code-supported losses: `pointwise_bce`, `pointwise_mse`, `pairwise_ranknet`, `listwise_ce`.
- Use pointwise losses with `train_dataset_type: pointwise`.
- Use ranking-list losses with `train_dataset_type: grouped`.
- `bert_encoder` and `llm_decoder` both support the same loss names, but LLM decoder runs need much smaller batch sizes and careful formatting.

## Unsupported `model_type`

Symptoms:

- `ValueError: Model type not currently supported`.

Fix:

- Set `model_type: "bert_encoder"` for BERT/XLM-R cross-encoder rerankers.
- Set `model_type: "llm_decoder"` for decoder-style rerankers.
- Do not invent other values without changing `train_reranker.py`.

## LLM Formatting Errors

Symptoms:

- LLM reranker sees empty or malformed inputs.
- all scores are similar.
- documents are truncated more than expected.

Fix:

- Ensure `query_format` and `document_format` each contain `{}`.
- Use a clear `seq` separator such as newline or space.
- Use a `special_token` that matches the intended scoring prompt and tokenizer behavior.
- Reduce prompt verbosity or increase `max_len` if long queries leave no document budget.
- Reuse the same formatting fields during inference with the trained LLM decoder checkpoint.

## DeepSpeed ZeRO-3 Save Caveat

Symptoms:

- training appears to run but final model saving fails or produces incomplete checkpoints.

Fix:

- Use DeepSpeed ZeRO-1 or ZeRO-2 for LLM decoder reranker training.
- Avoid ZeRO-3 for this training flow unless the save path has been separately fixed and validated.

## GPU Memory And Mixed Precision

Symptoms:

- CUDA out-of-memory errors.
- unstable fp16 loss scaling.
- slow or failed LLM decoder runs.

Fix:

- Lower `batch_size`; for grouped data this multiplies by `train_group_size`.
- Lower `train_group_size` when using grouped data.
- Increase `gradient_accumulation_steps` to preserve effective batch size.
- Use `bf16` only on hardware that supports it; otherwise try `fp16` or no mixed precision.
- Reduce `max_len` if documents are long.
- Prefer BERT encoder training or distillation when LLM decoder training is too heavy.

## `shuffle_rate` Surprises

Symptoms:

- document text appears scrambled.
- training is less stable on short factual passages.

Cause:

- When `shuffle_rate > 0`, long document text may be split into chunks and shuffled as augmentation.

Fix:

- Keep `shuffle_rate: 0.0` for first runs and for distillation data.
- Only enable shuffling deliberately as augmentation after baseline training works.
- Ensure `shuffle_rate` is between `0` and `1`.
