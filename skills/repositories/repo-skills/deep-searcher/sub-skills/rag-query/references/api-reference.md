# RAG Query API Reference

This reference covers DeepSearcher `0.0.2` query and retrieval APIs. The import module is `deepsearcher`; the console script `deepsearcher` is implemented by `deepsearcher.cli:main`.

## Initialization prerequisite

The global `deepsearcher.online_query` functions use module-level objects initialized by `deepsearcher.configuration.init_config(config)`. In normal use, initialize configuration and load data before calling query APIs.

```python
from deepsearcher.configuration import Configuration, init_config

config = Configuration()  # default config path is deepsearcher/config.yaml
# Provider setup belongs to provider-configuration.
init_config(config=config)
```

Default config facts to preserve when reasoning about behavior:

| Area | Default |
| --- | --- |
| LLM | `OpenAI` model `o1-mini` |
| Embedding | `OpenAIEmbedding` model `text-embedding-ada-002` |
| File loader | `PDFLoader` |
| Web crawler | `FireCrawlCrawler` |
| Vector DB | `Milvus` with `uri: ./milvus.db`, default collection `deepsearcher` |
| Query | `max_iter: 3` |
| Loading | `chunk_size: 1500`, `chunk_overlap: 100` |

## Global online query functions

Import from `deepsearcher.online_query`.

| Function | Signature | Return shape | Notes |
| --- | --- | --- | --- |
| `query` | `query(original_query, max_iter=3)` | `(answer, refs, consumed_tokens)` | Uses `configuration.default_searcher`, a `RAGRouter` over `DeepSearch` and `ChainOfRAG`. `answer` is `str`; `refs` is `list[RetrievalResult]`; `consumed_tokens` is an `int`. |
| `retrieve` | `retrieve(original_query, max_iter=3)` | `(retrieved_results, empty_list, consumed_tokens)` | Uses the same `default_searcher.retrieve`. The second item is currently an empty list placeholder. |
| `naive_retrieve` | `naive_retrieve(query, collection=None, top_k=10)` | `list[RetrievalResult]` | Uses `configuration.naive_rag.retrieve(query)` and returns only retrieved results. Current implementation accepts `collection` and `top_k` but does not directly pass them through. |
| `naive_rag_query` | `naive_rag_query(query, collection=None, top_k=10)` | `(answer, retrieved_results)` | Uses `configuration.naive_rag.query(query)` and discards token count. Current implementation accepts `collection` and `top_k` but does not directly pass them through. |

### Global API examples

```python
from deepsearcher.online_query import query, retrieve, naive_retrieve, naive_rag_query

answer, refs, tokens = query("Write a report about the loaded product notes.", max_iter=2)
retrieved_results, _, retrieve_tokens = retrieve("Which note mentions renewal risk?", max_iter=1)
quick_refs = naive_retrieve("renewal risk")
quick_answer, quick_answer_refs = naive_rag_query("Summarize renewal risks.")
```

If you need to enforce `top_k` or disable collection routing, instantiate `NaiveRAG` manually instead of relying on `naive_retrieve`/`naive_rag_query` wrappers.

## RAG constructors

Import agents from `deepsearcher.agent` and routers from their modules.

| Class | Constructor | Best fit |
| --- | --- | --- |
| `DeepSearch` | `DeepSearch(llm, embedding_model, vector_db, max_iter=3, route_collection=True, text_window_splitter=True)` | Broad reports, surveys, open-ended synthesis, iterative gap search. |
| `ChainOfRAG` | `ChainOfRAG(llm, embedding_model, vector_db, max_iter=4, early_stopping=False, route_collection=True, text_window_splitter=True)` | Concrete factual/multi-hop questions with intermediate Q/A and support-doc filtering. |
| `NaiveRAG` | `NaiveRAG(llm, embedding_model, vector_db, top_k=10, route_collection=True, text_window_splitter=True)` | Low-cost direct retrieve-and-summarize. |
| `RAGRouter` | `RAGRouter(llm, rag_agents, agent_descriptions=None)` | Route each query to exactly one agent by LLM-chosen description. |
| `CollectionRouter` | `CollectionRouter(llm, vector_db, dim)` | Route a query to one or more vector DB collections using collection descriptions and embedding dimension. |

`init_config(config)` creates a default `RAGRouter` with:

- `DeepSearch(..., max_iter=config.query_settings["max_iter"], route_collection=True, text_window_splitter=True)`
- `ChainOfRAG(..., max_iter=config.query_settings["max_iter"], route_collection=True, text_window_splitter=True)`

It also creates `configuration.naive_rag` as `NaiveRAG(..., top_k=10, route_collection=True, text_window_splitter=True)`.

## Manual agent examples

```python
from deepsearcher.agent import DeepSearch, ChainOfRAG, NaiveRAG
from deepsearcher.agent.rag_router import RAGRouter

naive = NaiveRAG(llm, embedding_model, vector_db, top_k=5, route_collection=False)
answer, refs, tokens = naive.query("What is the renewal policy?")

search = DeepSearch(llm, embedding_model, vector_db, max_iter=2)
refs, retrieve_tokens, metadata = search.retrieve("Write a report on renewal risk.")
answer, refs, total_tokens = search.query("Write a report on renewal risk.", max_iter=1)

chain = ChainOfRAG(llm, embedding_model, vector_db, max_iter=3, early_stopping=True)
answer, refs, total_tokens = chain.query("Which clause resolves the renewal date?", max_iter=2)

router = RAGRouter(
    llm=llm,
    rag_agents=[naive, search, chain],
    agent_descriptions=[
        "Cheap direct retrieval and summary for simple questions.",
        "Broad report writing with iterative sub-query expansion.",
        "Concrete multi-hop fact finding with intermediate answers.",
    ],
)
answer, refs, tokens = router.query("Compare the two renewal clauses.")
```

## Method return shapes

All `RAGAgent` implementations expose:

| Method | Return shape | Metadata |
| --- | --- | --- |
| `agent.retrieve(query, **kwargs)` | `(retrieved_results, consumed_tokens, metadata)` | `DeepSearch` metadata contains `all_sub_queries`; `ChainOfRAG` metadata contains `intermediate_context`; `NaiveRAG` returns `{}`. |
| `agent.query(query, **kwargs)` | `(answer, retrieved_results, consumed_tokens)` | Token count includes retrieval-time LLM calls and final summarization/generation where used. |

## RetrievalResult fields

`deepsearcher.vector_db.base.RetrievalResult` represents each returned chunk:

| Field | Meaning |
| --- | --- |
| `embedding` | Stored vector for the retrieved chunk. Usually not needed for answer display. |
| `text` | Retrieved chunk text. |
| `reference` | Source reference string for the chunk. Preserve this when citing evidence. |
| `metadata` | Arbitrary metadata. When `metadata["wider_text"]` exists and `text_window_splitter=True`, RAG agents use it instead of `text` in summarization prompts. |
| `score` | Similarity score, default `0.0`; exact interpretation depends on vector DB implementation. |

Duplicate retrievals are removed by chunk `text` via `deduplicate_results`, so two references with identical text collapse to the first occurrence.

## Collection routing API

`CollectionRouter(llm, vector_db, dim)` calls `vector_db.list_collections(dim=dim)` and uses each `CollectionInfo(collection_name, description)` in an LLM prompt. Behavior:

- No collections: returns `([], 0)` and logs a warning.
- One collection: returns that collection without an LLM routing call.
- Multiple collections: asks the LLM to return a Python `list[str]` of collection names.
- Any collection with an empty description is always included.
- The vector DB `default_collection` is always included when present.

The `dim` argument should match `embedding_model.dimension`; mismatched dimensions can hide collections or cause vector DB search errors depending on backend.
