# Model and Backend Guide

Use this guide to choose a BEIR retrieval backend and to inspect optional runtime readiness without contacting external services. For exact signatures and method contracts, read [api-reference.md](api-reference.md). For runnable offline checks, use `scripts/retrieval_smoke.py` and `scripts/inspect_optional_backends.py`.

## Decision Matrix

| User Need | Backend | Model Wrapper | Required Runtime | Main Trade-Off |
| --- | --- | --- | --- | --- |
| Fast local correctness check, custom encoder validation, small corpus retrieval | `DenseRetrievalExactSearch` | Any object with `encode_queries` and `encode_corpus` | BEIR core deps plus torch/pytrec_eval | Simple and deterministic; encodes corpus each run unless cached. |
| Dense retrieval with Sentence-Transformers models | `DenseRetrievalExactSearch` | `models.SentenceBERT` | `sentence-transformers`, model download/cache | Easiest model path; downloads can be large. |
| Dense retrieval with HF AutoModel pooling or PEFT merge | `DenseRetrievalExactSearch` or FAISS | `models.HuggingFace` | `transformers`, torch, optional `peft`, model download/cache | Flexible pooling/prompts; version/GPU memory sensitive. |
| Large dense corpus or reusable ANN index | `FlatIPFaissSearch`, `HNSWFaissSearch`, `PQFaissSearch`, `SQFaissSearch`, `PCAFaissSearch`, `BinaryFaissSearch` | Dense model protocol | `faiss-cpu` or GPU-compatible FAISS | Faster repeated search and persistence; extra dependency and index tuning. |
| Precompute embeddings, then search saved pickle shards | `DenseRetrievalExactSearch.encode_and_retrieve()` | Dense model protocol | `faiss` for file search | Separates expensive encoding from search; requires cache hygiene. |
| Sparse token matching from SPARTA/UniCOIL | `SparseSearch` | `models.SPARTA`, `models.UniCOIL`, or protocol-compatible sparse model | `scipy`, `transformers`, model download/cache | Avoids dense similarity; protocol differs by query weighting. |
| Traditional BM25 over BEIR corpus | `BM25Search` | None | Python `elasticsearch` package plus running Elasticsearch-compatible service | No GPU/model required; service/index setup is mandatory. |
| Provider-hosted embeddings | `DenseRetrievalExactSearch` or `encode_and_retrieve()` | `apis.CohereEmbedAPI`, `apis.VoyageAPI` | Provider package, credentials, network, rate budget | High-quality hosted embeddings; external dependency and cost/latency. |
| vLLM/LoRA/NVEmbed/LLM2Vec workflows | Dense exact or FAISS | `models.VLLMEmbed`, `models.NVEmbed`, `models.LLM2Vec`, `models.HuggingFace(peft_model_path=...)` | Optional extras, large downloads, often GPU | Powerful modern embeddings; most environment-sensitive route. |

## Backend Selection Patterns

### Exact Dense First

Prefer `DenseRetrievalExactSearch` when:

- You are validating a custom model protocol.
- The corpus is small or medium enough to encode in chunks.
- The task needs reproducible metric correctness more than index reuse.
- You need a minimal path before adding FAISS or API providers.

Tuning knobs:

- `batch_size`: model inference batch size; reduce on out-of-memory.
- `corpus_chunk_size`: number of corpus documents scored at once; reduce when `torch.topk` or similarity matrices are too large.
- `show_progress_bar=False`: useful for tests or CI logs.
- `convert_to_tensor`: dense exact search asks encoders for tensors by default; if a custom model ignores it, return a 2-D numpy array or tensor consistently.

### FAISS for Reuse or Scale

Use FAISS when exact dense search is too slow for repeated runs or when an index must be saved and reused. Install a FAISS package compatible with the Python, CPU/GPU, and platform in use.

Index choices:

- `FlatIPFaissSearch`: safest first FAISS choice; exhaustive inner-product search and straightforward save/load.
- `HNSWFaissSearch`: approximate search with `hnsw_store_n`, `hnsw_ef_search`, and `hnsw_ef_construction` tuning.
- `PQFaissSearch`: product quantization for memory reduction, with `num_of_centroids` and `code_size` tuning.
- `SQFaissSearch` / `HNSWSQFaissSearch`: scalar quantization variants.
- `PCAFaissSearch`: dimensionality reduction before a caller-provided base index.
- `BinaryFaissSearch`: binary hash workflows; combine with compatible binary embeddings.

Persistence contract:

```python
faiss_search.save(output_dir="indexes", prefix="my-index", ext="flat")
faiss_search.load(input_dir="indexes", prefix="my-index", ext="flat")
```

Save/load writes two files: `{prefix}.{ext}.faiss` for the index and `{prefix}.{ext}.tsv` for BEIR-to-FAISS id mapping. Keep those files together.

### Sparse Search

Use `SparseSearch` only with models that expose `encode_corpus()` plus `encode_query()`:

- SPARTA-style: pass `query_weights=False` or omit it. The query encoder returns token ids, and the sparse matrix is sliced by those ids.
- UniCOIL-style: pass `query_weights=True`. The query encoder returns a weighted query vector and retrieval uses a matrix dot product.

SPLADE in BEIR is usually used through dense exact search with `score_function="dot"` because it exposes `encode_queries()` and `encode_corpus()` returning high-dimensional arrays, not the `SparseSearch.encode_query()` protocol.

### BM25 / Elasticsearch

Use `BM25Search` when the user asks for traditional lexical BM25. Installing BEIR or the `elasticsearch` Python package is not enough: a reachable Elasticsearch-compatible service must be running.

Minimal shape:

```python
from beir.retrieval.search.lexical import BM25Search

searcher = BM25Search(
    index_name="scifact",
    hostname="localhost",
    keys={"title": "title", "body": "txt"},
    language="english",
    initialize=True,
    number_of_shards=1,
)
```

Operational guidance:

- Use lowercase index names and avoid illegal index characters.
- Use `initialize=True` only when it is safe to delete/recreate the index.
- Use `initialize=False` only when a compatible index already exists.
- For small corpora, `number_of_shards=1` is often simpler.
- Confirm `keys` align with how documents are indexed; BEIR documents use `title` and `text`, while BM25 defaults map text into an Elasticsearch field named `txt`.
- `sleep_for` is a crude refresh delay after indexing; increasing it can help immediately-after-indexing retrieval misses.

### API-Backed Embeddings

BEIR wraps Cohere and Voyage embedding APIs as dense model protocol implementations.

Cohere pattern:

```python
from beir.retrieval import apis
from beir.retrieval.search.dense import DenseRetrievalExactSearch as DRES

model = DRES(
    apis.CohereEmbedAPI(
        model_path="embed-v4.0",
        api_key=None,
        normalize=True,
        torch_dtype="float32",
    ),
    batch_size=96,
)
```

Voyage follows the same dense wrapper pattern with `apis.VoyageAPI`. For either provider:

- Confirm the provider package is installed.
- Confirm credentials are configured, such as `COHERE_API_KEY` for Cohere.
- Expect network calls, provider rate limits, billing, and transient failures.
- Prefer `encode_and_retrieve()` plus an explicit cache directory when provider calls are expensive.

## Custom Dense Model Checklist

A custom dense model should pass these checks before running against a real corpus:

1. `encode_queries(list_of_strings, batch_size=..., **kwargs)` exists.
2. `encode_corpus(list_of_doc_dicts, batch_size=..., **kwargs)` exists.
3. Both return a 2-D matrix, not a list of ragged vectors.
4. Query and corpus embedding dimensions match.
5. The number of returned rows equals the number of inputs.
6. The embeddings are numeric and finite.
7. The chosen `score_function` matches training assumptions: normalized cosine models often use `"cos_sim"`; dot-trained models use `"dot"`.

Run the bundled smoke test for a working no-download example:

```bash
python scripts/retrieval_smoke.py
```

If a user's model fails only on full datasets, reduce `batch_size` and `corpus_chunk_size` before changing model code.

## Optional Backend Inspection

Run:

```bash
python scripts/inspect_optional_backends.py --json
```

The helper reports import availability and environment signals for:

- `faiss`
- `elasticsearch`
- `cohere`
- `voyageai` / `voyage`
- `vllm`
- `peft`
- `llm2vec`
- `torch` and CUDA status

It does not contact Elasticsearch, API providers, model hubs, or GPU services. Treat `present: true` as only an import-level signal; BM25 still needs a running service, API wrappers still need credentials/network, and GPU-heavy wrappers still need compatible hardware and available model weights.

## Score Function Guidance

- `DenseRetrievalExactSearch`: accepts `"cos_sim"` and `"dot"`; invalid strings raise `ValueError`.
- FAISS search classes: assert score function is one of `"cos_sim"` or `"dot"`; cosine mode normalizes embeddings before indexing/searching.
- BM25 and `SparseSearch` receive the score function but do not use it like dense exact search.
- For normalized embedding models, `"cos_sim"` and `"dot"` may be numerically close, but do not assume they are equivalent unless the encoder normalizes outputs.

## Embedding and Index Persistence

`EvaluateRetrieval.encode_and_retrieve()` writes query and corpus pickle files, then searches them through FAISS flat search:

```python
results = retriever.encode_and_retrieve(
    corpus=corpus,
    queries=queries,
    encode_output_path="embeddings",
    overwrite=False,
    query_filename="queries.pkl",
    corpus_filename="corpus.*.pkl",
)
```

Use this when:

- Model encoding is expensive.
- API calls should not be repeated.
- You want to inspect or reuse embedding shards.

Avoid accidental cache reuse:

- Include model name, dataset, split, prompt, and score-function assumptions in the cache directory name.
- Use `overwrite=True` when changing encoders, prompts, max length, normalization, or corpus/query content.
- Delete stale `corpus.*.pkl` shards when the new corpus has fewer chunks than the old corpus.

FAISS index persistence is separate from embedding pickle persistence. Do not mix a FAISS index created from one corpus/model with results from another corpus/model.

## Source Example Adaptation Notes

The bundled `retrieval_smoke.py` adapts the repository's custom dataset, custom model, and custom metric examples into an offline deterministic fixture. Other dense, lexical, API, FAISS, and Pyserini examples are reference-only for this skill because they require downloads, services, credentials, external stacks, or local paths not suitable for a public runtime skill.
