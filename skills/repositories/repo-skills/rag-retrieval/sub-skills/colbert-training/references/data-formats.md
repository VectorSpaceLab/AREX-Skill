# ColBERT Training Data Formats

## Required JSONL Shape

ColBERT training expects one JSON object per line. Each valid row needs:

```json
{"query": "question text", "pos": ["positive passage"], "neg": ["hard negative passage"]}
```

- `query` must be a non-empty string.
- `pos` must be a non-empty list of non-empty strings.
- `neg` must be a non-empty list of non-empty strings.
- Extra fields are ignored by the dataset reader.
- Invalid JSON, blank required fields, empty lists, and non-string passages should be fixed before training.

The bundled helper validates this shape without loading tokenizers or models:

```bash
python sub-skills/colbert-training/scripts/validate_colbert_training_args.py --data train.jsonl --neg-nums 15
```

## Positive Expansion

`ColBERTDTripletataset` expands each JSONL row into one training sample per positive passage. A row with one `query`, three `pos` passages, and ten `neg` passages becomes three training items sharing the same query and negative pool.

This means the effective number of query-positive pairs can be larger than the number of JSONL lines. Estimate training steps from expanded positives, not raw line count:

```text
expanded_examples = sum(len(row["pos"]) for row in jsonl_rows)
steps_per_epoch = ceil(expanded_examples / batch_size)
optimizer_steps ~= steps_per_epoch * epochs / gradient_accumulation_steps
```

## Negative Sampling and `neg_nums`

For every expanded query-positive pair, the dataset selects `neg_nums` hard negatives from that row’s `neg` list.

- If `len(neg) >= neg_nums`, it randomly samples `neg_nums` negatives without replacement.
- If `len(neg) < neg_nums`, it repeats the row’s negatives enough times, then randomly samples `neg_nums` from the repeated pool.
- If `neg` is empty, the source dataset will fail because it cannot resample from an empty list.

Resampling keeps training runnable with small negative lists, but it weakens the effective hard-negative diversity. If many rows have fewer negatives than `neg_nums`, warn the user and suggest lowering `neg_nums` or mining more negatives.

## Token Length Fields

Training tokenizes query and passages separately:

- `query_max_len` defaults to `128`.
- `passage_max_len` defaults to `512`.
- Queries, positives, and negatives use padding to max length and truncation.
- Positive and negative passages share `passage_max_len`.

Long documents can be truncated silently, so validate length choices against the user’s corpus. For passage-heavy corpora, prefer chunking passages upstream instead of simply increasing `passage_max_len` until memory fails.

## Validation Expectations

Before a full launch, check:

- Every line is valid JSON and has `query`, `pos`, and `neg` in the expected types.
- No row has empty `pos` or empty `neg`.
- `neg_nums` is positive and is not larger than most rows’ negative counts unless resampling is intentional.
- `query_max_len` and `passage_max_len` are positive integers.
- The sample count after positive expansion is large enough to justify the requested batch size and distributed launch.
