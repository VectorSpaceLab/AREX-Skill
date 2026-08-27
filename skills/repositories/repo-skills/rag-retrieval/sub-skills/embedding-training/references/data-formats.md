# Embedding Training Data Formats

RAG-Retrieval embedding training reads JSONL through the bundled training snapshot or an explicitly selected checkout. Each line must be a JSON object with a `query` string. The dataset implementation infers the training schema from the keys in the expanded first record after accounting for optional `prompt_for_query`.

## Pair Data

Use pair data for in-batch negative training when no explicit hard negatives are available.

```json
{"query": "user question", "pos": ["positive passage A", "positive passage B"]}
```

Behavior:

- Each `pos` entry is expanded into one training record with the same query.
- Other records in the batch provide random in-batch negatives.
- `neg_nums` is ignored by this schema because no `neg` list is present.
- Optional `prompt_for_query` is prepended to `query` before tokenization.

## Triplet Data

Use triplet data when each query has hard negatives.

```json
{"query": "user question", "pos": ["positive passage"], "neg": ["hard negative 1", "hard negative 2"]}
```

Behavior:

- Each `pos` entry is expanded into one training record.
- The dataset samples `neg_nums` negatives from `neg` for each expanded record.
- If `len(neg) < neg_nums`, the implementation repeats the available negatives and samples from the repeated list. This avoids an immediate crash but can reduce hard-negative diversity.
- If `len(neg) >= neg_nums`, it samples exactly `neg_nums` negatives.

Validation expectations:

- `pos` and `neg` must be non-empty lists of strings.
- `neg_nums` should be a positive integer.
- Warn when records have fewer negatives than `neg_nums`; this is allowed but usually worth revisiting.

## Pair-Score Data

Use pair-score data when each query-document pair has a supervised similarity/relevance score.

```json
{"query": "北京是中国的首都吗", "pos": ["北京是中国的首都", "华盛顿是美国的首都"], "scores": [0.8, 0.2]}
```

Important source behavior:

- The README documents `scores: List[float]`.
- The dataset expands each `pos[i]` into a separate record with singular key `score = scores[i]`.
- After expansion, the model sees a `score` tensor and uses KL divergence over the batch.
- A raw input with singular `score` is not the intended JSONL format; use `scores` aligned one-to-one with `pos`.

Validation expectations:

- `pos` and `scores` must have equal lengths.
- Every score should be numeric.
- `neg` should not be mixed into pair-score records for this dataset path.

## Distillation Text Data

Use distillation text data when teacher embeddings already exist in a float32 array/memmap.

```json
{"query": "text to distill", "prompt_for_query": "optional instruction prefix"}
```

Behavior:

- Each JSONL row corresponds to exactly one row in `train_dataset_vec`.
- Optional `prompt_for_query` is prepended to `query` before tokenization.
- Distillation does not consume `pos`, `neg`, or `scores` in this dataset class; only `query` is used.

## `prompt_for_query`

`prompt_for_query` is optional in pair, triplet, pair-score, and distillation text data. When present and non-empty, the source dataset mutates the query string by concatenating the prompt and the query.

Common instruction-style value:

```text
Instruct: Given a user query, retrieve documents helpful for answering the query\nQuery: 
```

Cautions:

- Keep prompt usage consistent between teacher-embedding creation, training, and inference.
- If teacher embeddings were created without the prompt but training prepends it, the student is learning against a mismatched teacher target.
- Preserve the newline in instruction prompts when the source model expects it.

## Teacher Embedding Array Shape

`EmbeddingDistillDataset` opens teacher embeddings as:

```python
np.memmap(path, dtype="float32", mode="r", shape=(jsonl_line_count, teacher_embedding_dim))
```

Therefore:

- The file is expected to contain raw float32 values unless it is explicitly loaded as `.npy` by a helper script.
- Element count must equal `number_of_jsonl_rows * teacher_embedding_dim`.
- Byte size for a raw float32 memmap must equal `number_of_jsonl_rows * teacher_embedding_dim * 4`.
- The first dimension is the number of text rows, not the number of original query records if a teacher creation script deduplicated or expanded texts.

For two-teacher concatenation, set:

```text
teacher_embedding_dim = teacher1_dim + teacher2_dim
```

and ensure both source arrays have the same row count and row order.

## Quick Validation

Use the bundled helper before training:

```bash
python skills/rag-retrieval/sub-skills/embedding-training/scripts/validate_embedding_training_config.py \
  --config /path/to/config.yaml \
  --data /path/to/train_or_distill.jsonl
```

For distillation with a teacher array:

```bash
python skills/rag-retrieval/sub-skills/embedding-training/scripts/validate_embedding_training_config.py \
  --config /path/to/distill_embedding.yaml \
  --data /path/to/text.jsonl \
  --teacher-embeddings /path/to/teacher.mmap
```
