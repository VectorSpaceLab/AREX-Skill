# Retrieval Evaluation API Reference

This reference distills the BEIR retrieval and evaluation APIs for first-stage retrieval. It is evidence-backed by `README.md`, `beir/retrieval/evaluation.py`, `beir/retrieval/custom_metrics.py`, `beir/retrieval/search/base.py`, dense/sparse/lexical search modules, retrieval model wrappers, API wrappers, and retrieval evaluation examples.

## Core Evaluator

### `EvaluateRetrieval(retriever=None, k_values=[1, 3, 5, 10, 100, 1000], score_function="cos_sim")`

- `retriever` is any search object implementing BEIR's `BaseSearch` protocol.
- `k_values` controls metric cutoffs and sets `top_k = max(k_values)` for retrieval.
- `score_function` is passed to the search backend; dense exact search accepts only `"cos_sim"` and `"dot"`.

Important methods:

| Method | Purpose | Notes |
| --- | --- | --- |
| `retrieve(corpus, queries, **kwargs)` | Calls `retriever.search(corpus, queries, top_k, score_function, **kwargs)` | Raises `ValueError` if no retriever was supplied. Results shape is `dict[query_id, dict[doc_id, score]]`. |
| `encode_and_retrieve(corpus, queries, encode_output_path="./embeddings/", overwrite=False, query_filename="queries.pkl", corpus_filename="corpus.*.pkl", **kwargs)` | Encodes queries/corpus to pickle shards, then searches those files with FAISS flat search | Requires the dense exact backend and `faiss` for `search_from_files`. Use a deliberate cache directory and `overwrite=True` only when replacing old embeddings. |
| `evaluate(qrels, results, k_values, ignore_identical_ids=True)` | Returns `(ndcg, map, recall, precision)` dictionaries | By default removes result entries where `query_id == doc_id` before scoring. |
| `evaluate_custom(qrels, results, k_values, metric)` | Returns one custom metric dictionary | Supported aliases include MRR, recall-cap, hole, and top-k accuracy. |

### Input and Output Shapes

- `corpus`: `dict[str, dict[str, str]]`, where each document should expose `title` and/or `text` keys.
- `queries`: `dict[str, str]`.
- `qrels`: `dict[str, dict[str, int]]`, where positive relevance labels are integers greater than zero.
- `results`: `dict[str, dict[str, float]]`, where every query id should match a qrels query id for metric evaluation.

Route dataset schema construction and validation to `../data-loading/SKILL.md`.

## Search Protocol

`BaseSearch` defines three methods:

| Method | Required for | Contract |
| --- | --- | --- |
| `search(corpus, queries, top_k, **kwargs)` | Normal retrieval | Return BEIR results keyed by query id then corpus id. |
| `encode(corpus, queries, encode_output_path, overwrite, query_filename, corpus_filename, **kwargs)` | Embedding persistence | Write query and corpus embedding pickle files. |
| `search_from_files(query_embeddings_file, corpus_embeddings_files, top_k, **kwargs)` | Retrieval from saved embeddings | Load query/corpus embedding pickles and return BEIR results. |

Many practical custom models only implement `encode_queries()` and `encode_corpus()` and are wrapped by a BEIR search class such as `DenseRetrievalExactSearch`.

## Dense Exact Search

### `DenseRetrievalExactSearch(model, batch_size=128, corpus_chunk_size=50000, **kwargs)`

Use as:

```python
from beir.retrieval.evaluation import EvaluateRetrieval
from beir.retrieval.search.dense import DenseRetrievalExactSearch as DRES

searcher = DRES(model, batch_size=32, corpus_chunk_size=10000, show_progress_bar=False)
retriever = EvaluateRetrieval(searcher, k_values=[1, 10, 100], score_function="cos_sim")
results = retriever.retrieve(corpus, queries)
```

Model protocol:

| Method | Input | Return |
| --- | --- | --- |
| `encode_queries(queries: list[str], batch_size: int, **kwargs)` | Query strings in BEIR query-id order | A 2-D tensor/array with shape `(num_queries, dim)`. |
| `encode_corpus(corpus: list[dict[str, str]], batch_size: int, **kwargs)` | Document dictionaries sorted by document length | A 2-D tensor/array with shape `(num_docs_in_chunk, dim)`. |

Dense exact search supports `score_function="cos_sim"` and `score_function="dot"`. It removes documents whose corpus id equals the query id while building result heaps; `EvaluateRetrieval.evaluate()` also ignores identical query/doc ids by default.

## FAISS Search

FAISS-backed classes live under `beir.retrieval.search.dense` and require a `faiss` Python module, usually from `faiss-cpu` or a compatible GPU package.

| Class | Use When | Save/Load Extension |
| --- | --- | --- |
| `FlatIPFaissSearch` | Exhaustive inner-product search with a FAISS index; useful when saving/loading an index. | `flat` |
| `PQFaissSearch` | Product quantization for smaller approximate indexes. | `pq` |
| `HNSWFaissSearch` | Approximate nearest-neighbor HNSW search. | `hnsw` |
| `HNSWSQFaissSearch` | HNSW with scalar quantization. | `hnsw-sq` |
| `SQFaissSearch` | Scalar quantization flat search. | `sq` |
| `PCAFaissSearch` | PCA transform plus a caller-provided FAISS base index. | `pca` |
| `BinaryFaissSearch` | Binary hashing with optional reranking. | `bin` |

FAISS search methods:

- `search(corpus, queries, top_k, score_function, **kwargs)` builds an index if one is not already loaded.
- `save(output_dir, prefix="my-index", ext="flat")` writes `{prefix}.{ext}.faiss` plus `{prefix}.{ext}.tsv` id mapping.
- `load(input_dir, prefix="my-index", ext="flat")` loads both files and restores BEIR document ids.
- For `score_function="cos_sim"`, FAISS search normalizes embeddings before indexing/searching; `"dot"` leaves them unnormalized.

## Sparse Search

### `SparseSearch(model, batch_size=16, **kwargs)`

Use with sparse token-weight models such as `SPARTA` or `UniCOIL`:

```python
from beir.retrieval.search.sparse import SparseSearch

searcher = SparseSearch(sparse_model, batch_size=32)
retriever = EvaluateRetrieval(searcher, score_function="dot")
results = retriever.retrieve(corpus, queries, query_weights=True)
```

Model protocol:

| Method | Required Return |
| --- | --- |
| `encode_corpus(corpus, batch_size=...)` | Sparse matrix containing document weights. |
| `encode_query(query, **kwargs)` | Token ids or a query-weight vector, depending on `query_weights`. |

`query_weights=False` is used for SPARTA-style binary query token matching. `query_weights=True` is used for UniCOIL-style weighted query vectors.

## Lexical BM25 Search

### `BM25Search(index_name, hostname="localhost", keys={"title": "title", "body": "txt"}, language="english", batch_size=128, timeout=100, retry_on_timeout=True, maxsize=24, number_of_shards="default", initialize=True, sleep_for=2)`

Use as:

```python
from beir.retrieval.search.lexical import BM25Search

searcher = BM25Search(
    index_name="scifact",
    hostname="localhost",
    initialize=True,
    number_of_shards=1,
)
retriever = EvaluateRetrieval(searcher)
results = retriever.retrieve(corpus, queries)
```

Key behavior:

- Requires the `elasticsearch` Python package and a running Elasticsearch-compatible service.
- `initialize=True` deletes and recreates the index, then indexes the supplied corpus.
- `initialize=False` uses an existing index; the index must already contain compatible BEIR document ids and fields.
- `keys` maps BEIR document `title` and `text` into Elasticsearch fields; defaults are `title` and `txt`.
- Index names must be lowercase, not `.` or `..`, not start with `_`, `-`, or `+`, and not contain characters such as `#:\/*?"<>|,`.
- The language analyzer must be one of Elasticsearch's supported language analyzers in BEIR's `ElasticSearch.languages` list.

## Built-In Retrieval Model Wrappers

Dense wrappers implement `encode_queries()` and `encode_corpus()` and are usually passed to `DenseRetrievalExactSearch` or a FAISS search class.

| Wrapper | Typical Use | Important Parameters |
| --- | --- | --- |
| `models.SentenceBERT` | Sentence-Transformers models, optionally separate query/doc encoders. | `model_path`, `max_length`, `sep`, `prompts`, `prompt_names`. |
| `models.HuggingFace` | AutoModel/AutoTokenizer embedding with pooling. | `model_path`, `max_length`, `pooling` (`cls`, `mean`, `eos`), `normalize`, `prompts`, `append_eos_token`, `peft_model_path`, `convert_to_numpy`. |
| `models.VLLMEmbed` | vLLM embedding inference, optionally with LoRA. | `model_path`, `lora_name_or_path`, `lora_r`, `pooling`, `normalize`, `append_eos_token`, `torch_dtype`, `cache_dir`. |
| `models.NVEmbed` | NV-Embed style model wrapper. | Often needs GPU and large model downloads. |
| `models.LLM2Vec` | LLM2Vec embedding wrapper. | Requires optional `llm2vec` stack and compatible model weights. |
| `models.BinarySentenceBERT` | Binary embedding variant for binary FAISS search. | Use with binary-compatible workflows. |
| `models.TLDR` | TLDR retrieval wrapper. | Follows dense model protocol. |
| `models.SPLADE` | Sparse lexical expansion model that returns dense numpy token-weight arrays. | Often used through dense exact search with `score_function="dot"`. |
| `models.SPARTA` | Sparse retrieval with token-id matching. | Use with `SparseSearch`, `query_weights=False`. |
| `models.UniCOIL` | Sparse retrieval with weighted query/document tokens. | Use with `SparseSearch`, `query_weights=True`. |

## API-Backed Embedding Wrappers

| Wrapper | Package | Credential Signal | Notes |
| --- | --- | --- | --- |
| `apis.CohereEmbedAPI` | `cohere` | `COHERE_API_KEY` or explicit `api_key` | Uses Cohere v2 embedding input types `search_query` and `search_document`. |
| `apis.VoyageAPI` | `voyageai` | Voyage client environment/configuration or explicit provider setup | Uses Voyage input types `query` and `document`. |

Both wrappers implement the dense model protocol. They can be wrapped with `DenseRetrievalExactSearch` and evaluated with `EvaluateRetrieval`, but network access, rate limits, and provider credentials are runtime requirements.

## Metrics

`EvaluateRetrieval.evaluate()` returns dictionaries keyed exactly as:

- `NDCG@{k}`
- `MAP@{k}`
- `Recall@{k}`
- `P@{k}`

`EvaluateRetrieval.evaluate_custom()` accepts these aliases:

| Metric Family | Accepted Aliases | Output Key |
| --- | --- | --- |
| Mean reciprocal rank | `mrr`, `mrr@k`, `mrr_cut` | `MRR@{k}` |
| Recall cap | `recall_cap`, `r_cap`, `r_cap@k` | `R_cap@{k}` |
| Hole | `hole`, `hole@k` | `Hole@{k}` |
| Top-k accuracy | `acc`, `top_k_acc`, `accuracy`, `accuracy@k`, `top_k_accuracy` | `Accuracy@{k}` |

## Result Export

BEIR utility helpers are useful after retrieval/evaluation:

```python
from beir import util

util.save_runfile("run.trec", results, run_name="beir", top_k=1000)
util.save_results("metrics.json", ndcg, metric_map, recall, precision, mrr=mrr)
loaded_results = util.load_runfile("run.trec")
```

Use runfiles when routing first-stage results to reranking. Use metric JSON when capturing an evaluation report.
