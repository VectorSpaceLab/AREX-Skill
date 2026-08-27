# Data Formats

RAGatouille converts raw retrieval supervision into ColBERT training files. Each `prepare_training_data` call expects a single mode selected by tuple/list arity and `pairs_with_labels`.

## Raw Data Modes

### Unlabeled pairs

Use for query-positive examples when negatives should be mined or sampled.

```python
raw_data = [
    ("what is colbert retrieval?", "ColBERT is a late-interaction retrieval model."),
    ("what is ragatouille?", {"content": "RAGatouille wraps ColBERT for retrieval workflows."}),
    ("who directed spirited away?", ["Hayao Miyazaki directed Spirited Away.", "It was produced by Studio Ghibli."]),
]
trainer.prepare_training_data(raw_data=raw_data, pairs_with_labels=False)
```

Rules:
- Every item has length 2: `(query, positive)`.
- `query` must be a string.
- `positive` may be a string, a list of strings, or a dict with a `content` field when using `RAGTrainer.prepare_training_data`.
- The processor groups duplicate queries and positives before producing triplets.
- You need negatives from `all_documents`, `add_documents`, hard-negative mining, or random sampling; pairs alone can produce zero triplets when no distinct negatives exist.

### Labeled pairs

Use when examples are query-passage-label rows and labels indicate relevance.

```python
raw_data = [
    ("where is studio ghibli based?", "Studio Ghibli is based in Koganei, Tokyo.", 1),
    ("where is studio ghibli based?", "Toei Animation is a separate Japanese studio.", 0),
]
trainer.prepare_training_data(
    raw_data=raw_data,
    pairs_with_labels=True,
    positive_label=1,
    negative_label=0,
    mine_hard_negatives=False,
)
```

Rules:
- Every item has length 3 and `pairs_with_labels=True`.
- `label` must equal `positive_label` or `negative_label`; labels may be ints or strings in `RAGTrainer.prepare_training_data`.
- Positive and negative rows for the same query are combined into triplets.
- If a query has positives but no negatives, add explicit negatives or set `num_new_negatives > 0` with a sufficiently broad collection.

### Triplets

Use when positives and negatives are already known.

```python
raw_data = [
    (
        "who directed spirited away?",
        "Hayao Miyazaki directed Spirited Away.",
        "The Ghibli Museum is in Mitaka.",
    ),
    (
        "what studio made totoro?",
        ["Studio Ghibli made My Neighbor Totoro."],
        ["Toei Animation is a different studio.", "Pixar is an American studio."],
    ),
]
trainer.prepare_training_data(
    raw_data=raw_data,
    pairs_with_labels=False,
    num_new_negatives=0,
    mine_hard_negatives=False,
)
```

Rules:
- Every item has length 3 and `pairs_with_labels=False`.
- The second element is a positive string or list of positive strings.
- The third element is a negative string or list of negative strings.
- Use `num_new_negatives=0` when negatives are complete and no additional mining/sampling is desired.

## Mixing Modes

Do not mix pairs, labeled pairs, and triplets in one `raw_data` list. `RAGTrainer.prepare_training_data` decides the mode from the first item only, so later rows with a different arity or meaning can raise unpacking errors or silently be treated as the wrong type. Split mixed sources into separate calls or normalize into explicit triplets before export.

## Corpus Inputs

`all_documents` supplies extra candidate passages for sampling or hard-negative mining:

```python
trainer.prepare_training_data(
    raw_data=pairs,
    all_documents=full_corpus_or_chunks,
    num_new_negatives=10,
    mine_hard_negatives=True,
)
```

Accepted entries:
- Strings are added directly to the collection.
- `CorpusProcessor.process_corpus` returns dictionaries with `content`; these are accepted as positives or negatives in raw examples, but `all_documents` itself only adds string entries in `RAGTrainer.prepare_training_data`.
- To use processed chunks as `all_documents`, pass `[chunk["content"] for chunk in chunks]`.

## Generated ColBERT Files

`prepare_training_data(..., data_out_path=...)` and `TrainingDataProcessor.export_training_data(...)` create:

### `queries.train.colbert.tsv`

Tab-separated query IDs and query text:

```text
0	what is colbert retrieval?
1	where is studio ghibli based?
```

Notes:
- Query text tabs and newlines are replaced with spaces during export.
- IDs are generated from the processor's query map.

### `corpus.train.colbert.tsv`

Tab-separated passage IDs and passage text:

```text
0	ColBERT is a late-interaction retrieval model.
1	Studio Ghibli is based in Koganei, Tokyo.
```

Notes:
- Passage text tabs and newlines are replaced with spaces during export.
- IDs are generated from the deduplicated collection.

### `triples.train.colbert.jsonl`

One JSON array per line: `[query_id, positive_passage_id, negative_passage_id]`.

```jsonl
[0, 0, 2]
[1, 1, 3]
```

Notes:
- Triplets are shuffled with a fixed seed before export.
- `train()` reads this file when `trainer.training_triplets` is empty.

## Offline Validation

Use the bundled validator before model downloads or GPU training:

From the `training-data-finetuning` sub-skill directory:

```bash
python scripts/validate_training_data.py raw_data.json --mode auto
python scripts/validate_training_data.py labeled.json --mode labeled_pairs --positive-label relevant --negative-label irrelevant
```

JSON input must be a top-level list. Tuples from Python examples should be represented as JSON arrays. The validator checks arity, query strings, labels, passage shapes, mixed modes, and likely zero-triplet cases without importing RAGatouille or downloading models.
