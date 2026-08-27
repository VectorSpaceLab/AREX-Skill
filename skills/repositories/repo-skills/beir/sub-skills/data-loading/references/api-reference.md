# Data Loading API Reference

This reference covers BEIR 2.2.0 public data-loading and persistence APIs verified from the package source and installed inspection facts.

## `GenericDataLoader`

Import:

```python
from beir.datasets.data_loader import GenericDataLoader
```

Signature:

```python
GenericDataLoader(
    data_folder=None,
    prefix=None,
    corpus_file="corpus.jsonl",
    query_file="queries.jsonl",
    qrels_folder="qrels",
    qrels_file="",
)
```

Constructor behavior:

| Argument | Meaning |
| --- | --- |
| `data_folder` | Base directory for relative corpus, query, and qrels paths. If omitted, file arguments are used as provided. |
| `prefix` | Prepends `<prefix>-` to `query_file` and `qrels_folder` only. It does not alter `corpus_file`. |
| `corpus_file` | Corpus JSONL filename or explicit path. Must end with `jsonl`. |
| `query_file` | Query JSONL filename or explicit path. Must end with `jsonl`. |
| `qrels_folder` | Folder containing split TSV files. Must contain `<split>.tsv` for `load(split=...)`. |
| `qrels_file` | Explicit qrels TSV path for `load_custom()`. |

Methods:

| Method | Use | Return shape |
| --- | --- | --- |
| `load(split="test")` | Load `corpus.jsonl`, `queries.jsonl`, and `qrels/<split>.tsv` under `data_folder`. | `(corpus_dict, queries_dict, qrels_dict)` |
| `load_custom()` | Load explicit `corpus_file`, `query_file`, and `qrels_file` paths. | `(corpus_dict, queries_dict, qrels_dict)` |
| `load_corpus()` | Load only the corpus JSONL. | `dict[str, dict[str, str]]` |

Important behavior:

- `check()` raises `ValueError` when a required file is missing or does not end with the expected extension string.
- `_load_corpus()` reads each JSONL row and uses `line.get("_id")` as the dictionary key. Missing ids can collapse into a `None` key, so validate before loading.
- `_load_queries()` maps each query id to its text string.
- `_load_qrels()` skips the header row and casts score with `int(score)`.
- After qrels load, queries are filtered to query ids present in qrels.

## `HFDataLoader`

Import:

```python
from beir.datasets.data_loader_hf import HFDataLoader
```

Signature:

```python
HFDataLoader(
    hf_repo=None,
    hf_repo_qrels=None,
    data_folder=None,
    prefix=None,
    corpus_file="corpus.jsonl",
    query_file="queries.jsonl",
    qrels_folder="qrels",
    qrels_file="",
    streaming=False,
    keep_in_memory=False,
)
```

Modes:

| Mode | Configure | Behavior |
| --- | --- | --- |
| Hugging Face repo | `HFDataLoader(hf_repo="BeIR/scifact")` | Ignores `data_folder`, `prefix`, and file arguments. Loads configs `corpus` and `queries`; qrels come from `hf_repo_qrels` or `hf_repo + "-qrels"`. |
| Local files through `datasets` | `HFDataLoader(data_folder=path)` | Loads local JSONL and TSV files using `datasets.load_dataset`. Supports `prefix` like `GenericDataLoader`. |

Methods:

| Method | Use | Return shape |
| --- | --- | --- |
| `load(split="test")` | Load corpus, queries, and qrels. | `(corpus_dataset, queries_dataset, qrels_dict)` |
| `load_corpus()` | Load only corpus. | Hugging Face Dataset or iterable dataset |

Important behavior:

- Corpus and query `_id` columns are cast to string and renamed to `id`.
- Corpus columns outside `id`, `text`, and `title` are removed.
- Query columns outside `id` and `text` are removed.
- Qrels features are cast to `query-id`, `corpus-id`, and `score`; qrels are converted into a nested dictionary.
- `streaming=True` can return streaming/iterable dataset objects; avoid assuming random access, materialized length, or full in-memory dictionaries.

## Download Utilities

Import:

```python
from beir import util
```

Functions:

| Function | Use | Notes |
| --- | --- | --- |
| `util.download_url(url, save_path, chunk_size=1024)` | Download one URL to a file. | Uses `requests` streaming and a progress bar. No checksum verification. |
| `util.unzip(zip_file, out_dir)` | Extract a zip archive. | Extracts all archive entries into `out_dir`. Use trusted archives. |
| `util.download_and_unzip(url, out_dir, chunk_size=1024)` | Download `<dataset>.zip` once and extract it once. | Returns `os.path.join(out_dir, dataset.replace(".zip", ""))`. |

Use `download_and_unzip()` for public BEIR dataset zips when network access is allowed. The bundled validation script is safer for offline format checks and does not download anything.

## Persistence Utilities

Functions:

| Function | Use | Notes |
| --- | --- | --- |
| `util.save_runfile(output_file, results, run_name="beir", top_k=1000)` | Write retrieval results in TREC runfile format. | Sorts each query's docs descending by score and truncates to `top_k`. |
| `util.load_runfile(input_file)` | Read TREC runfile into nested result dict. | Requires exactly six space-separated fields per row. |
| `util.save_results(output_file, ndcg, _map, recall, precision, mrr=None, recall_cap=None, hole=None)` | Write metrics JSON. | Optional metric dictionaries are included only when provided/truthy. |
| `util.write_to_json(output_file, data)` | Write corpus/query-like dicts as JSONL. | Dict values become rows with `_id`, `title`, `text`, and empty `metadata`; string values become rows with `_id`, `text`, and empty `metadata`. |
| `util.write_to_tsv(output_file, data)` | Write qrels-like nested dict as TSV. | Header is `query-id`, `corpus-id`, `score`. |

## Minimal Local Loading Snippets

Load a standard dataset folder:

```python
from beir.datasets.data_loader import GenericDataLoader

corpus, queries, qrels = GenericDataLoader(data_folder="my-dataset").load(split="test")
```

Load explicit custom files:

```python
from beir.datasets.data_loader import GenericDataLoader

corpus, queries, qrels = GenericDataLoader(
    corpus_file="my_corpus.jsonl",
    query_file="my_queries.jsonl",
    qrels_file="my_qrels.tsv",
).load_custom()
```

Load a Hugging Face BEIR-style dataset:

```python
from beir.datasets.data_loader_hf import HFDataLoader

corpus, queries, qrels = HFDataLoader(hf_repo="BeIR/scifact").load(split="test")
```
