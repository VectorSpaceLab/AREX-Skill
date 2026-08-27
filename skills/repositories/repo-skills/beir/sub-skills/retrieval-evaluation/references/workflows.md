# Retrieval Evaluation Workflows

These workflows assume `corpus`, `queries`, and `qrels` are already loaded in BEIR shape. Route dataset layout, loaders, and file validation to `../data-loading/SKILL.md`. Route second-stage reranking to `../reranking/SKILL.md`.

## 1. Offline Dense Retrieval Smoke Test

Use this before debugging user models or optional backends:

```bash
python scripts/retrieval_smoke.py
python scripts/retrieval_smoke.py --output-dir beir-retrieval-smoke-output
```

The script builds a tiny in-memory BEIR dataset, uses a deterministic toy encoder implementing `encode_queries()` and `encode_corpus()`, runs `DenseRetrievalExactSearch` through `EvaluateRetrieval`, asserts standard metric keys, asserts custom metrics, checks invalid score-function handling, and optionally writes `toy.run.trec` plus `toy.metrics.json`.

## 2. Dense Exact Retrieval

Use exact dense retrieval as the default first-stage path for custom models and small/medium corpora.

```python
from beir.retrieval import models
from beir.retrieval.evaluation import EvaluateRetrieval
from beir.retrieval.search.dense import DenseRetrievalExactSearch as DRES

encoder = models.SentenceBERT("sentence-transformers/msmarco-distilbert-base-v3")
searcher = DRES(encoder, batch_size=32, corpus_chunk_size=10000, show_progress_bar=False)
retriever = EvaluateRetrieval(searcher, k_values=[1, 3, 10, 100], score_function="cos_sim")

results = retriever.retrieve(corpus, queries)
ndcg, metric_map, recall, precision = retriever.evaluate(qrels, results, retriever.k_values)
mrr = retriever.evaluate_custom(qrels, results, retriever.k_values, metric="mrr")
```

Validation checklist:

- `results` contains each evaluated query id.
- Every returned doc id exists in `corpus`.
- `qrels` and `results` query ids overlap.
- Metric dictionaries contain keys such as `NDCG@10`, `MAP@10`, `Recall@10`, and `P@10` for requested cutoffs.
- If a query id equals a corpus id and that self-match matters, call `EvaluateRetrieval.evaluate(..., ignore_identical_ids=False)`.

## 3. Custom Dense Model Protocol

Adapt a custom model by implementing only the encoder protocol and wrapping it with `DenseRetrievalExactSearch`:

```python
import numpy as np

class CustomEncoder:
    def encode_queries(self, queries, batch_size=16, **kwargs):
        return np.asarray([...], dtype="float32")

    def encode_corpus(self, corpus, batch_size=16, **kwargs):
        texts = [(doc.get("title", "") + " " + doc.get("text", "")).strip() for doc in corpus]
        return np.asarray([...], dtype="float32")

searcher = DRES(CustomEncoder(), batch_size=16, show_progress_bar=False)
retriever = EvaluateRetrieval(searcher, score_function="dot")
results = retriever.retrieve(corpus, queries)
```

Hard protocol checks:

- Return exactly one row per input query/document.
- Return a rectangular numeric 2-D matrix.
- Use the same embedding dimension for queries and documents.
- Accept and ignore extra keyword arguments such as `show_progress_bar`, `convert_to_tensor`, or `normalize_embeddings` if the model does not need them.
- Raise a clear error for empty inputs or non-finite embeddings before passing results to BEIR.

The bundled smoke script contains a full deterministic implementation.

## 4. Evaluate Standard and Custom Metrics

Run standard metrics:

```python
ndcg, metric_map, recall, precision = retriever.evaluate(qrels, results, retriever.k_values)
```

Run custom metrics:

```python
mrr = retriever.evaluate_custom(qrels, results, retriever.k_values, metric="mrr")
recall_cap = retriever.evaluate_custom(qrels, results, retriever.k_values, metric="recall_cap")
hole = retriever.evaluate_custom(qrels, results, retriever.k_values, metric="hole")
accuracy = retriever.evaluate_custom(qrels, results, retriever.k_values, metric="top_k_accuracy")
```

Interpretation notes:

- `Hole@k` measures the fraction of retrieved top-k docs not annotated anywhere in qrels.
- `R_cap@k` caps the denominator by `min(number_of_relevant_docs, k)`.
- `Accuracy@k` is 1 for a query if any relevant document appears in top-k.
- Metrics require qrels entries for result query ids; missing query ids usually surface as errors or misleading zero coverage.

## 5. Export Results and Metrics

```python
from beir import util

util.save_runfile("run.trec", results, run_name="my-system", top_k=1000)
util.save_results("metrics.json", ndcg, metric_map, recall, precision, mrr=mrr, recall_cap=recall_cap, hole=hole)
loaded_results = util.load_runfile("run.trec")
```

Runfiles are useful as reranking input. Metric JSON is useful for reports. Keep export paths under the user's chosen output directory, not inside the package installation or generated skill directory unless explicitly requested for skill maintenance.

## 6. Embedding Persistence with `encode_and_retrieve()`

Use when encoding is expensive or provider-backed:

```python
results = retriever.encode_and_retrieve(
    corpus=corpus,
    queries=queries,
    encode_output_path="embeddings/my-model-scifact-test",
    overwrite=False,
    query_filename="queries.pkl",
    corpus_filename="corpus.*.pkl",
)
```

Operational rules:

- Requires `faiss` because saved embeddings are searched from files with a FAISS flat index.
- Set `overwrite=True` after changing model weights, prompts, normalization, max length, corpus, queries, or split.
- Delete stale `corpus.*.pkl` shards when shrinking a corpus or changing `corpus_chunk_size`.
- Keep cache directories named by dataset, split, model, prompt/normalization assumptions, and date or version.

## 7. FAISS Retrieval and Index Persistence

Example with flat inner-product FAISS:

```python
from beir.retrieval import models
from beir.retrieval.evaluation import EvaluateRetrieval
from beir.retrieval.search.dense import FlatIPFaissSearch

encoder = models.SentenceBERT("sentence-transformers/msmarco-distilbert-base-v3")
searcher = FlatIPFaissSearch(encoder, batch_size=128)
retriever = EvaluateRetrieval(searcher, score_function="dot")
results = retriever.retrieve(corpus, queries)

searcher.save(output_dir="faiss-index", prefix="my-index", ext="flat")
```

Load a saved index:

```python
searcher = FlatIPFaissSearch(encoder, batch_size=128)
searcher.load(input_dir="faiss-index", prefix="my-index", ext="flat")
retriever = EvaluateRetrieval(searcher, score_function="dot")
results = retriever.retrieve(corpus, queries)
```

Use `score_function="cos_sim"` when embeddings need normalization before indexing/searching. Use `"dot"` when the model was trained for dot product or already normalizes embeddings in a way where inner product is intended.

## 8. Sparse Retrieval

SPARTA-style sparse search:

```python
from beir.retrieval import models
from beir.retrieval.evaluation import EvaluateRetrieval
from beir.retrieval.search.sparse import SparseSearch

searcher = SparseSearch(models.SPARTA("BeIR/sparta-msmarco-distilbert-base-v1"), batch_size=128)
retriever = EvaluateRetrieval(searcher)
results = retriever.retrieve(corpus, queries)
```

UniCOIL-style sparse search:

```python
searcher = SparseSearch(models.UniCOIL("castorini/unicoil-d2q-msmarco-passage"), batch_size=32)
retriever = EvaluateRetrieval(searcher, score_function="dot")
results = retriever.retrieve(corpus, queries, query_weights=True)
```

SPLADE is usually evaluated as a high-dimensional dense protocol model:

```python
searcher = DRES(models.SPLADE("path-or-model-name"), batch_size=128)
retriever = EvaluateRetrieval(searcher, score_function="dot")
results = retriever.retrieve(corpus, queries)
```

## 9. BM25 / Elasticsearch Retrieval

Before coding, confirm two separate requirements:

1. The Python package `elasticsearch` imports.
2. A reachable Elasticsearch-compatible service is running at `hostname`.

Example:

```python
from beir.retrieval.evaluation import EvaluateRetrieval
from beir.retrieval.search.lexical import BM25Search

searcher = BM25Search(
    index_name="scifact",
    hostname="localhost",
    initialize=True,
    number_of_shards=1,
    keys={"title": "title", "body": "txt"},
    language="english",
)
retriever = EvaluateRetrieval(searcher)
results = retriever.retrieve(corpus, queries)
```

Safe-use guidance:

- Use a disposable lowercase index name for experiments.
- Set `initialize=False` when the target index already contains the corpus and should not be deleted.
- Keep `keys` consistent between indexing and querying.
- Increase `sleep_for` or explicitly refresh the index if retrieval immediately after indexing misses documents.
- For user reports saying "BM25 installed but fails", first distinguish missing package, unreachable service, invalid index name, wrong language analyzer, and wrong document field mapping.

## 10. API-Backed Retrieval

Cohere example:

```python
from beir.retrieval import apis
from beir.retrieval.evaluation import EvaluateRetrieval
from beir.retrieval.search.dense import DenseRetrievalExactSearch as DRES

api_encoder = apis.CohereEmbedAPI(model_path="embed-v4.0", api_key=None, normalize=True, torch_dtype="float32")
searcher = DRES(api_encoder, batch_size=96)
retriever = EvaluateRetrieval(searcher, score_function="cos_sim")
results = retriever.encode_and_retrieve(corpus, queries, encode_output_path="embeddings/cohere-scifact")
```

Voyage uses `apis.VoyageAPI` with the same search wrapper. Before running:

- Confirm package import with `scripts/inspect_optional_backends.py`.
- Confirm credentials are configured.
- Confirm the user accepts network calls, rate limits, and possible costs.
- Cache embeddings deliberately to avoid repeated provider calls.

## 11. Hand Off to Reranking

After first-stage retrieval:

1. Save `results` as a runfile or keep the in-memory dictionary.
2. Route the reranking task to `../reranking/SKILL.md`.
3. Preserve `corpus`, `queries`, and first-stage `results` shapes.
4. Evaluate first-stage and reranked results separately so improvements are measurable.

## 12. Hard Usability Cases to Support

Use these for future verification planning:

- Custom model returns ragged or mismatched query/corpus embedding shapes. Expected guidance: run `scripts/retrieval_smoke.py`, compare model protocol against the custom dense checklist, and fail before BEIR retrieval with a clear shape error.
- User installed BEIR and `elasticsearch` but BM25 fails because no service is running. Expected guidance: use `scripts/inspect_optional_backends.py` to show import-level readiness, then explain that BM25 also needs a reachable Elasticsearch-compatible service and valid index configuration.
