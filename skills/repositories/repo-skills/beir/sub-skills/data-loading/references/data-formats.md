# BEIR Data Formats

BEIR local loaders expect three core files: `corpus.jsonl`, `queries.jsonl`, and `qrels/<split>.tsv`. `GenericDataLoader.load(split="test")` returns three plain Python dictionaries; `HFDataLoader.load(split="test")` returns Hugging Face Dataset objects for corpus and queries plus a qrels dictionary.

## Directory Layout

```text
my-dataset/
  corpus.jsonl
  queries.jsonl
  qrels/
    test.tsv
    dev.tsv
```

For prefixed local datasets, only query and qrels paths are prefixed:

```text
my-dataset/
  corpus.jsonl
  fiqa-queries.jsonl
  fiqa-qrels/
    test.tsv
```

Load the prefixed example with `GenericDataLoader(data_folder="my-dataset", prefix="fiqa").load(split="test")`. Do not rename `corpus.jsonl` for prefix mode unless you also pass a custom `corpus_file`.

## Corpus JSONL

Each line is a JSON object. Required fields:

| Field | Type | Notes |
| --- | --- | --- |
| `_id` | string | Document id used by qrels and retrieval results. Must be unique and non-empty. |
| `text` | string | Document body. Keep as an empty string only when the downstream workflow can handle empty text. |
| `title` | string | Title text. Use `""` when no title exists. |

Extra fields are ignored by the built-in loaders. `GenericDataLoader` stores each row as `corpus[_id] = {"text": text, "title": title}`.

Example:

```json
{"_id":"doc1","title":"Albert Einstein","text":"Albert Einstein developed the theory of relativity."}
{"_id":"doc2","title":"Wheat beer","text":"Wheat beer is brewed with a large proportion of wheat."}
```

## Queries JSONL

Each line is a JSON object. Required fields:

| Field | Type | Notes |
| --- | --- | --- |
| `_id` | string | Query id used by qrels and results. Must be unique and non-empty. |
| `text` | string | Query text. |

`GenericDataLoader` stores each row as `queries[_id] = text`, then filters to only query ids present in qrels when `load()` or `load_custom()` reads qrels.

Example:

```json
{"_id":"q1","text":"Who developed relativity?"}
{"_id":"q2","text":"Which beer uses wheat?"}
```

## Qrels TSV

Qrels are tab-separated relevance judgments. The first row must be the exact header:

```text
query-id	corpus-id	score
q1	doc1	1
q2	doc2	1
```

Rules:

- File path for split loading is `qrels/<split>.tsv`, or `<prefix>-qrels/<split>.tsv` when `prefix` is set.
- `query-id` must exist in `queries.jsonl` or `<prefix>-queries.jsonl`.
- `corpus-id` must exist in `corpus.jsonl`.
- `score` should be integer-compatible for `GenericDataLoader`, because it casts with `int(score)`. `HFDataLoader` casts qrels scores to float internally and then to int when building the returned qrels dict.
- Keep at least one qrel for every query you expect to evaluate; loaders filter out queries with no qrels.

## Python Return Shapes

`GenericDataLoader(data_folder=path).load(split="test")` returns:

```python
corpus = {
    "doc1": {"title": "Albert Einstein", "text": "..."},
}
queries = {
    "q1": "Who developed relativity?",
}
qrels = {
    "q1": {"doc1": 1},
}
```

`GenericDataLoader(corpus_file=..., query_file=..., qrels_file=...).load_custom()` uses explicit file paths instead of `data_folder/qrels/<split>.tsv`.

`HFDataLoader` local-file mode uses the Hugging Face `datasets` package to load JSON/CSV data and returns Dataset-like corpus and queries objects:

```python
corpus[0] == {"id": "doc1", "title": "Albert Einstein", "text": "..."}
queries[0] == {"id": "q1", "text": "Who developed relativity?"}
qrels == {"q1": {"doc1": 1}}
```

`HFDataLoader` repo mode reads `hf_repo` configs named `corpus` and `queries`, and qrels from `hf_repo_qrels` or the default `hf_repo + "-qrels"`.

## Result and Runfile Formats

`util.save_runfile(output_file, results, run_name="beir", top_k=1000)` writes TREC-style rows:

```text
qid Q0 docid 0 score run_name
```

`util.load_runfile(input_file)` expects exactly six space-separated columns per line and returns `dict[str, dict[str, float]]`.

`util.save_results(output_file, ndcg, _map, recall, precision, mrr=None, recall_cap=None, hole=None)` writes JSON with metric names as top-level keys. Metric dictionaries are usually keyed by cutoff values such as `1`, `3`, `5`, `10`, `100`, and `1000`.
