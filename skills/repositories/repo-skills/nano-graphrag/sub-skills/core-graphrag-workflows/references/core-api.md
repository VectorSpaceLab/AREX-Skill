# Core GraphRAG API

This reference captures the installed `nano_graphrag` core API needed for ordinary GraphRAG lifecycle work. It is self-contained: future agents should not need the source checkout to use these signatures and contracts.

## Import and package shape

```python
from nano_graphrag import GraphRAG, QueryParam
```

- Distribution name: `nano-graphrag`.
- Import module: `nano_graphrag`.
- Root exports: `GraphRAG`, `QueryParam`.
- There is no package console script for core workflows.
- Import-time caveat: the package imports `transformers.AutoTokenizer` even when the default tokenizer is `tiktoken`; if import fails with `ModuleNotFoundError: No module named 'transformers'`, install `transformers` in the active Python environment.

## `GraphRAG` constructor essentials

`GraphRAG` is a dataclass. Its constructor accepts the fields below; fields are grouped by the workflow decision they affect.

### Location, modes, and chunking

| Field | Default | Use |
| --- | --- | --- |
| `working_dir` | generated timestamped `./nano_graphrag_cache_...` | Directory where default JSON, vector, cache, and GraphML artifacts are loaded from and saved to. Prefer an explicit stable directory for real work. |
| `enable_local` | `True` | Enables entity-vector index and permits `QueryParam(mode="local")`. |
| `enable_naive_rag` | `False` | Enables chunk-vector index and permits `QueryParam(mode="naive")`. Enable it before insertion if you will query naive mode. |
| `tokenizer_type` | `"tiktoken"` | Tokenizer backend; supported values are `"tiktoken"` and `"huggingface"`. |
| `tiktoken_model_name` | `"gpt-4o"` | Encoding name used when `tokenizer_type="tiktoken"`. |
| `huggingface_model_name` | `"bert-base-uncased"` | Model name used when `tokenizer_type="huggingface"`; local availability matters in no-network environments. |
| `chunk_func` | `chunking_by_token_size` | Callable that receives token batches and returns chunk dictionaries. |
| `chunk_token_size` | `1200` | Max tokens per chunk passed to the chunk function. |
| `chunk_overlap_token_size` | `100` | Overlap tokens passed to the chunk function. Keep this smaller than `chunk_token_size`. |

### Entity extraction, graph, and reports

| Field | Default | Use |
| --- | --- | --- |
| `entity_extract_max_gleaning` | `1` | Extra entity-extraction passes after the first LLM response. |
| `entity_summary_to_max_tokens` | `500` | Token threshold for summarizing long merged entity/relation descriptions. |
| `graph_cluster_algorithm` | `"leiden"` | Community clustering algorithm; default graph storage supports Leiden. |
| `max_graph_cluster_size` | `10` | Leiden max cluster size. |
| `graph_cluster_seed` | `3735928559` | Leiden random seed. |
| `special_community_report_llm_kwargs` | `{"response_format": {"type": "json_object"}}` | Extra kwargs used when asking the best model for community report JSON. |
| `entity_extraction_func` | built-in `extract_entities` | Override only for advanced extraction or no-network tests; see customization troubleshooting for real extraction changes. |
| `convert_response_to_json_func` | built-in JSON converter | Converts community/global-map LLM output to dictionaries. Route custom repair to customization troubleshooting. |

### Embedding and model hooks

| Field | Default | Use |
| --- | --- | --- |
| `embedding_func` | built-in OpenAI embedding function | Async embedding callable wrapped as `EmbeddingFunc`; replace for no-network or custom embeddings. |
| `embedding_batch_num` | `32` | Chunk/entity embedding batch size. |
| `embedding_func_max_async` | `16` | Concurrency limiter around the embedding function. |
| `query_better_than_threshold` | `0.2` | Default similarity threshold passed to `NanoVectorDBStorage`. |
| `best_model_func` | built-in GPT-4o completion | Main LLM for entity extraction, report generation, query planning, and final responses. |
| `best_model_max_token_size` | `32768` | Token budget for best-model prompts. |
| `best_model_max_async` | `16` | Concurrency limiter around the best model. |
| `cheap_model_func` | built-in GPT-4o-mini completion | Summary/model-lite LLM. |
| `cheap_model_max_token_size` | `32768` | Token budget for cheap-model prompts. |
| `cheap_model_max_async` | `16` | Concurrency limiter around the cheap model. |
| `using_azure_openai` | `False` | Switches default OpenAI hooks to Azure variants if custom hooks were not supplied. |
| `using_amazon_bedrock` | `False` | Switches default model and embedding hooks to Bedrock variants. |
| `best_model_id`, `cheap_model_id` | Bedrock Claude model ids | Used only by the Bedrock switch. |

Provider-specific implementations, credentials, unsupported kwargs, and hosted/local model recipes belong to `provider-and-model-integrations`.

### Storage and extension fields

| Field | Default | Use |
| --- | --- | --- |
| `key_string_value_json_storage_cls` | `JsonKVStorage` | Key/value JSON storage class for docs, chunks, cache, and reports. |
| `vector_db_storage_cls` | `NanoVectorDBStorage` | Vector storage class for entity and chunk indexes. |
| `vector_db_storage_cls_kwargs` | `{}` | Extra vector storage options. |
| `graph_storage_cls` | `NetworkXStorage` | Graph storage class for entity/relation graph. |
| `enable_llm_cache` | `True` | Creates and persists LLM response cache storage. |
| `always_create_working_dir` | `True` | Creates the working directory when it does not exist. |
| `addon_params` | `{}` | Extension/config bag used by some advanced backends and report packing behavior. |

Storage-class selection and third-party backend contracts belong to `storage-backends`.

## `GraphRAG` methods

```python
rag.insert(string_or_strings)
await rag.ainsert(string_or_strings)

rag.query(query: str, param: QueryParam = QueryParam())
await rag.aquery(query: str, param: QueryParam = QueryParam())
```

- `insert` and `query` are synchronous wrappers around `ainsert` and `aquery` using the current or a newly created event loop.
- `insert` accepts either one string or a list of strings. Each document is stripped and keyed by an MD5-derived `doc-...` id.
- New chunks are keyed by an MD5-derived `chunk-...` id of chunk content. Existing docs/chunks are filtered out before indexing.
- On a non-empty insert, `community_reports` are dropped and regenerated after entity extraction and graph clustering.
- If all docs or all chunks already exist, the insert returns early and does not rebuild downstream indexes.
- `_insert_done` persists default storages after insertion; `_query_done` persists the LLM cache after queries.

## `QueryParam` dataclass

```python
QueryParam(
    mode: Literal["local", "global", "naive"] = "global",
    only_need_context: bool = False,
    response_type: str = "Multiple Paragraphs",
    level: int = 2,
    top_k: int = 20,
    local_max_token_for_text_unit: int = 4000,
    local_max_token_for_local_context: int = 4800,
    local_max_token_for_community_report: int = 3200,
    local_community_single_one: bool = False,
    global_min_community_rating: float = 0,
    global_max_consider_community: float = 512,
    global_max_token_for_community_report: int = 16384,
    global_special_community_map_llm_kwargs: dict = {"response_format": {"type": "json_object"}},
)
```

The source also defines `naive_max_token_for_text_unit = 12000` as a query parameter attribute used by naive search, although it is not emitted by the installed dataclass signature inspection.

### Query modes

| Mode | Enable flag | Index used | Behavior |
| --- | --- | --- | --- |
| `"global"` | no explicit mode guard | graph communities and community reports | Default. Maps selected community reports to support points, then reduces them into a final answer unless `only_need_context=True`. The mapping step still calls the best model. |
| `"local"` | `GraphRAG(enable_local=True)` | entity vector index, graph, community reports, text chunks | Retrieves entities, related reports, relationships, and source chunks. Raises `ValueError` if local mode is disabled. With `only_need_context=True`, returns the retrieved CSV-like context and skips final answer generation. |
| `"naive"` | `GraphRAG(enable_naive_rag=True)` | chunk vector index and text chunks | Retrieves top chunks directly. Raises `ValueError` if naive mode is disabled. With `only_need_context=True`, returns joined chunk context and skips final answer generation. |

Unknown modes raise `ValueError(f"Unknown mode {param.mode}")`.

## Chunking APIs and custom chunk contract

Available core functions:

```python
from nano_graphrag._op import (
    chunking_by_token_size,
    chunking_by_seperators,  # spelling in package API
    get_chunks,
)

chunking_by_token_size(tokens_list, doc_keys, tokenizer_wrapper, overlap_token_size=128, max_token_size=1024)
chunking_by_seperators(tokens_list, doc_keys, tokenizer_wrapper, overlap_token_size=128, max_token_size=1024)
get_chunks(new_docs, chunk_func=chunking_by_token_size, tokenizer_wrapper=None, **chunk_func_params)
```

A current custom chunk function must accept the `TokenizerWrapper`, not a raw tiktoken encoder:

```python
def my_chunk_func(
    tokens_list: list[list[int]],
    doc_keys: list[str],
    tokenizer_wrapper,
    overlap_token_size: int = 128,
    max_token_size: int = 1024,
) -> list[dict]:
    results = []
    for doc_index, tokens in enumerate(tokens_list):
        for chunk_index, start in enumerate(range(0, len(tokens), max_token_size - overlap_token_size)):
            piece_tokens = tokens[start : start + max_token_size]
            results.append({
                "tokens": len(piece_tokens),
                "content": tokenizer_wrapper.decode(piece_tokens).strip(),
                "chunk_order_index": chunk_index,
                "full_doc_id": doc_keys[doc_index],
            })
    return results
```

Required keys in every returned chunk dictionary:

- `tokens`: integer token count.
- `content`: decoded chunk text.
- `chunk_order_index`: zero-based order within its full document.
- `full_doc_id`: the matching document key from `doc_keys`.

Validation tips:

- Ensure `max_token_size > overlap_token_size`; otherwise token-window chunkers can fail or loop incorrectly.
- Use `tokenizer_wrapper.decode(...)` or `tokenizer_wrapper.decode_batch(...)`; stale examples that expect a raw `tiktoken_model` argument do not match the current API.
- `chunking_by_seperators` uses default text separators from package prompts and returns the same chunk schema.

## Default `working_dir` artifacts

With default storage classes, `GraphRAG` uses the following files inside `working_dir`:

| Artifact | Created when | Contents |
| --- | --- | --- |
| `kv_store_full_docs.json` | after successful insert | Original full documents keyed by `doc-...`. |
| `kv_store_text_chunks.json` | after successful insert | Chunk dictionaries keyed by `chunk-...`. |
| `kv_store_llm_response_cache.json` | when `enable_llm_cache=True` and callbacks persist | Cached LLM responses. |
| `kv_store_community_reports.json` | after successful graph clustering and report generation | Community report strings/JSON plus graph community metadata. |
| `graph_chunk_entity_relation.graphml` | after graph callback persists | NetworkX GraphML entity/relation graph. |
| `vdb_entities.json` | when `enable_local=True` and entities are indexed | Entity vector index for local search. |
| `vdb_chunks.json` | when `enable_naive_rag=True` and chunks are indexed | Chunk vector index for naive search. |

Reconstructing `GraphRAG` with the same `working_dir` reloads these default artifacts. Keep the same enable flags and compatible model/embedding dimensions when you expect mode-specific vector indexes to keep working.
