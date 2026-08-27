# Data Formats

FlagEmbedding custom evaluation uses three JSONL files in one dataset directory. The default split is `test`, so the default file names are `corpus.jsonl`, `test_queries.jsonl`, and `test_qrels.jsonl`.

## Directory Layout

Single custom dataset:

```text
my_retrieval_data/
  corpus.jsonl
  test_queries.jsonl
  test_qrels.jsonl
```

Multiple local datasets for custom evaluation:

```text
datasets/
  finance/
    corpus.jsonl
    test_queries.jsonl
    test_qrels.jsonl
  support/
    corpus.jsonl
    test_queries.jsonl
    test_qrels.jsonl
```

For multiple custom subdirectories, run one `python -m FlagEmbedding.evaluation.custom` command per leaf directory. The custom data loader reports no dataset names, so `--dataset_names finance support` is not a valid custom command.

Official benchmark loaders use their own dataset-name lists. When they are pointed at local data with `--dataset_dir` and `--dataset_names`, each dataset name is resolved as a child directory under `--dataset_dir`.

## Corpus JSONL

File: `corpus.jsonl`

Each line is one document:

```json
{"id": "doc-001", "title": "Optional short title", "text": "Document body text."}
```

Fields:

- `id`: required string document id.
- `title`: optional string. When present, retrieval concatenates title and text with a space.
- `text`: required string document body.

Use stable string ids. Integers may load, but string ids avoid accidental mismatches across JSON, qrels, and search outputs.

## Queries JSONL

File: `<split>_queries.jsonl`, for example `test_queries.jsonl`.

Each line is one query:

```json
{"id": "q-001", "text": "Which document explains evaluation outputs?"}
```

Fields:

- `id`: required string query id.
- `text`: required string query text.

The split name in the file name must match `--splits`. If the command uses `--splits dev`, the query file must be `dev_queries.jsonl`.

## Qrels JSONL

File: `<split>_qrels.jsonl`, for example `test_qrels.jsonl`.

Each line is one query-document relevance label:

```json
{"qid": "q-001", "docid": "doc-001", "relevance": 1}
```

Fields:

- `qid`: required query id matching a queries file `id`.
- `docid`: required document id matching a corpus file `id`.
- `relevance`: required integer relevance label. Positive values count as relevant; `0` is non-relevant.

Every evaluated query should have at least one qrel row. Queries with no qrels can produce metric errors or misleading averages. Use `0` relevance rows only when the metric setup needs explicit non-relevant labels.

## Tiny Fixture

Create a deterministic local fixture:

```shell
python scripts/create_tiny_retrieval_dataset.py --output-dir ./tiny_retrieval --overwrite
```

Then evaluate it with `python -m FlagEmbedding.evaluation.custom` after selecting an embedder and dependencies. The fixture is intentionally small; it validates layout and command wiring, not model quality.

## Search Output Structure

The raw retrieval stage writes JSON files under:

```text
<output_dir>/<embedder_name>/NoReranker/<split>.json
```

With a reranker, reranked output is written under:

```text
<output_dir>/<embedder_name>/<reranker_name>/<split>.json
```

For named benchmark datasets, output file names include the dataset name, such as `<dataset>-<split>.json`. BEIR `cqadupstack` also includes subdataset names.

Each search result JSON contains metadata and results:

```json
{
  "eval_name": "my_retrieval_eval",
  "model_name": "bge-m3",
  "reranker_name": "NoReranker",
  "split": "test",
  "dataset_name": null,
  "search_results": {
    "q-001": {
      "doc-001": 0.91,
      "doc-002": 0.13
    }
  }
}
```

The evaluator writes per-run metrics to:

```text
<output_dir>/<embedder_name>/NoReranker/EVAL/eval_results.json
<output_dir>/<embedder_name>/<reranker_name>/EVAL/eval_results.json
```

It also writes an aggregate report to `--eval_output_path` using `--eval_output_method` (`markdown` or `json`).

## Corpus Embedding Cache

When `--corpus_embd_save_dir` is set, corpus embeddings are saved as `doc.npy` under a model and dataset-specific child directory. Reusing this directory avoids re-encoding the corpus when `--overwrite False` and the same embedder/data are used.

Do not reuse a corpus embedding cache across different embedders, pooling methods, instructions, dimensions, truncation settings, or corpus contents.

## MKQA Note

MKQA is not a generic retrieval-qrels path. Its evaluator uses answer strings and QA recall. For ordinary `qid`/`docid`/`relevance` qrels, use the `custom` module.
