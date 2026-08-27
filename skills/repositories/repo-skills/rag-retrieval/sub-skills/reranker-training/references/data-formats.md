# Reranker Training Data Formats

RAG-Retrieval reranker training supports two dataset loaders: `PointwiseRankerDataset` and `GroupedRankerDataset`. Choose the dataset type first, then choose a compatible `loss_type` in the training config.

## Pointwise JSONL

Each line is one query-document pair:

```json
{"query": "...", "content": "...", "label": 1}
```

Required fields:

- `query`: string query text; the loader strips surrounding whitespace.
- `content`: string document text; this becomes the candidate passage paired with the query.
- label field: defaults to `label`, or any field named by `train_label_key` / `val_label_key`.

Pointwise label behavior:

- Labels may already be continuous scores in `[0, 1]`.
- Discrete labels such as `0`, `1`, `2` are scaled to `[0, 1]` by `(label - min_label) / (max_label - min_label)`.
- Set `max_label` and `min_label` to cover the actual discrete range. For `0/1/2` relevance labels, use `min_label: 0` and `max_label: 2`, producing `0.0`, `0.5`, and `1.0`.
- `max_label` must be greater than `min_label`; `min_label` must be non-negative.
- A label outside `[min_label, max_label]` raises an error in the dataset loader.

Compatible losses:

- `pointwise_bce`: binary or soft-label cross entropy over one logit. Use for labels scaled to `[0, 1]`.
- `pointwise_mse`: sigmoid score regression to the scaled label. Use when teacher scores or continuous relevance values should be matched directly.

## Grouped JSONL

Each line is one query plus a list of hits:

```json
{"query": "...", "hits": [{"content": "...", "label": 1}, {"content": "...", "label": 0}]}
```

Required fields:

- `query`: string query text.
- `hits`: list of candidate documents for that query.
- each hit requires `content` and should contain the configured label field.
- label field defaults to `label`, or the value of `train_label_key` / `val_label_key`.

Grouped loader behavior:

- `train_group_size` must be at least `2`.
- A query with fewer hits than `train_group_size` is skipped entirely.
- Hits are shuffled before groups are formed.
- Full groups are sliced in chunks of `train_group_size`.
- A short final group is padded by randomly sampling earlier hits so it reaches `train_group_size`.
- Any group whose labels are all identical is skipped because pairwise/listwise ranking loss has no useful preference signal.
- Grouped labels are not scaled by `max_label` / `min_label`; they are passed as numeric relevance values.

Compatible losses:

- `pairwise_ranknet`: works with grouped labels where at least two labels differ. It forms label-difference pairs within each group and weights by absolute label difference.
- `listwise_ce`: use only for grouped data where positives are represented as non-zero labels and negatives as `0`. The README describes the strict one-positive case; the implementation softmaxes over all non-zero labels, so multiple positive non-zero labels become a soft target distribution rather than a single-positive CE target.

## Validation Expectations

Before training, validate both config and data:

```bash
python skills/rag-retrieval/sub-skills/reranker-training/scripts/validate_reranker_training_config.py \
  --config <training-config.yaml> \
  --data <train-data.jsonl>
```

Expect the validator to catch:

- missing `query`, `content`, `hits`, or configured label fields.
- non-numeric labels.
- pointwise labels outside `[min_label, max_label]`.
- grouped records with too few hits for `train_group_size`.
- grouped candidate groups that will be skipped because every label is identical.
- `listwise_ce` groups without exactly one positive label, reported as a warning because the implementation can still softmax multiple non-zero labels.
- data shape inconsistent with `train_dataset_type`.

## Choosing Between Pointwise And Grouped

Use pointwise when every query-document pair has an independent score, binary relevance label, multi-level relevance label, or teacher-generated score.

Use grouped when ranking within a query matters and each record can provide enough candidate documents per query to fill `train_group_size` with at least two distinct labels. If grouped data is sparse, pointwise training is often more reliable because grouped data can silently lose many records through skip rules.
