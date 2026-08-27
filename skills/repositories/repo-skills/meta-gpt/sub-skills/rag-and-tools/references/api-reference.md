# RAG and Tools API Reference

This reference names MetaGPT modules and public classes/functions future agents can import from an installed MetaGPT package. Source paths listed in provenance are evidence only, not runtime dependencies.

## RAG Interfaces and Engine

| Import | Purpose | Key methods or fields |
| --- | --- | --- |
| `metagpt.rag.interface.RAGObject` | Protocol for objects stored in RAG | `rag_key() -> str` produces searchable text. |
| `metagpt.rag.interface.NoEmbedding` | Marker protocol for no-embedding configs | Used by `SimpleEngine._resolve_embed_model()` to choose `MockEmbedding`. |
| `metagpt.rag.engines.SimpleEngine` | Main document/object RAG engine | `from_docs`, `from_objs`, `from_index`, `retrieve`, `aretrieve`, `query`, `aquery`, `asearch`, `add_docs`, `add_objs`, `persist`, `count`, `clear`, `delete_docs`. |
| `metagpt.rag.factories.get_rag_embedding` | Create LlamaIndex embedding from MetaGPT config | Supports OpenAI, Azure, Gemini, Ollama embedding configs. |
| `metagpt.rag.factories.get_rag_llm` | Wrap MetaGPT LLM for LlamaIndex | Returns `RAGLLM`, a `llama_index.core.llms.CustomLLM`. |
| `metagpt.rag.factories.get_retriever` | Build retriever(s) from config | Multiple configs return `SimpleHybridRetriever`. |
| `metagpt.rag.factories.get_rankers` | Build ranker/postprocessors | Empty config returns `[]`. |
| `metagpt.rag.factories.get_index` | Load index from index config | Dispatches by index config class. |

`SimpleEngine` details:

- `from_docs(input_dir=None, input_files=None, transformations=None, embed_model=None, llm=None, retriever_configs=None, ranker_configs=None, fs=None)` loads documents with LlamaIndex `SimpleDirectoryReader`; either `input_dir` or `input_files` is required.
- `from_objs(objs=None, transformations=None, embed_model=None, llm=None, retriever_configs=None, ranker_configs=None)` converts objects to `ObjectNode` via `rag_key()` and object metadata.
- `from_index(index_config, embed_model=None, llm=None, retriever_configs=None, ranker_configs=None)` loads a previously maintained index through `get_index()`.
- `asearch(content, **kwargs)` delegates to `aquery()` and lets the engine satisfy MetaGPT `SearchInterface`-style store usage.
- `add_docs()` and `add_objs()` require retrievers that satisfy `ModifiableRAGRetriever` by exposing `add_nodes()`.
- `persist()` requires `PersistableRAGRetriever`; `count()` requires `QueryableRAGRetriever`; `clear()` requires `DeletableRAGRetriever`.
- PDF extraction uses `OmniParse` only when `config.omniparse.base_url` is configured; otherwise built-in LlamaIndex readers are used.

## RAG Config Schemas

Retriever configs from `metagpt.rag.schema`:

| Config | Primary fields | Notes |
| --- | --- | --- |
| `BaseRetrieverConfig` | `similarity_top_k=5` | Common top-k field. |
| `IndexRetrieverConfig` | `index=None`, `similarity_top_k` | Base for retrievers backed by an index. |
| `FAISSRetrieverConfig` | `dimensions=0`, `index=None` | If dimensions is 0, uses `config.embedding.dimensions`, known defaults for Gemini/Ollama, otherwise warns and defaults to 1536. |
| `BM25RetrieverConfig` | `create_index=False`, `index=None` | No-embedding retriever; can create a mock-embedding index for persistence support. |
| `ChromaRetrieverConfig` | `persist_path="./chroma_db"`, `collection_name="metagpt"`, `metadata=None` | Uses Chroma persistent client and collection metadata. |
| `ElasticsearchStoreConfig` | `index_name`, `es_url`, `es_cloud_id`, `es_api_key`, `es_user`, `es_password`, `batch_size=200`, `distance_strategy="COSINE"` | Store connection/config model for ES vector/text retrieval. |
| `ElasticsearchRetrieverConfig` | `store_config`, `vector_store_query_mode=DEFAULT` | Vector/text ES retriever. |
| `ElasticsearchKeywordRetrieverConfig` | `store_config`, `vector_store_query_mode=TEXT_SEARCH` | Text-only, no embedding. |

Ranker configs from `metagpt.rag.schema`:

| Config | Primary fields | Notes |
| --- | --- | --- |
| `BaseRankerConfig` | `top_n=5` | Common rerank output count. |
| `LLMRankerConfig` | `llm=None`, `choice_select_prompt=DEFAULT_CHOICE_SELECT_PROMPT` | Uses LlamaIndex `LLMRerank`; may call configured LLM. |
| `ColbertRerankConfig` | `model="colbert-ir/colbertv2.0"`, `device="cpu"`, `keep_retrieval_score=False` | Requires ColBERT postprocessor package and likely model download. |
| `CohereRerankConfig` | `model="rerank-english-v3.0"`, `api_key="YOUR_COHERE_API"` | Requires Cohere postprocessor package and API key. |
| `BGERerankConfig` | `model="BAAI/bge-reranker-large"`, `use_fp16=True` | Requires flag embedding reranker package. |
| `ObjectRankerConfig` | `field_name`, `order="desc"` or `"asc"` | Sorts object nodes by comparable object field. |

Index configs from `metagpt.rag.schema`:

| Config | Primary fields | Notes |
| --- | --- | --- |
| `BaseIndexConfig` | `persist_path` | Common persisted-index path. |
| `VectorIndexConfig` | `persist_path`, `embed_model=None` | Base for vector indexes. |
| `FAISSIndexConfig` | `persist_path`, `embed_model=None` | Loads FAISS vector store from persist directory. |
| `ChromaIndexConfig` | `persist_path`, `collection_name="metagpt"`, `metadata=None`, `embed_model=None` | Connects to Chroma collection and vector store. |
| `BM25IndexConfig` | `persist_path` | No-embedding index load. |
| `ElasticsearchIndexConfig` | `store_config`, `persist_path=""`, `embed_model=None` | Creates index from ES vector store. |
| `ElasticsearchKeywordIndexConfig` | `store_config`, `persist_path=""` | Text-only no-embedding ES index. |

Object and parser schemas:

- `ObjectNodeMetadata`: stores `is_obj=True`, object JSON, object class name, and module name.
- `ObjectNode`: a LlamaIndex `TextNode` that excludes object metadata keys from LLM/embedding metadata and provides `get_obj_metadata(obj)`.
- `OmniParseType`: `PDF`, `DOCUMENT`.
- `ParseResultType`: `text`, `markdown`, `json`.
- `OmniParseOptions`: `result_type=markdown`, `parse_type=DOCUMENT`, `max_timeout=120`, `num_workers` from 1 to 9.
- `OmniParsedResult`: normalized parse output with `markdown`, `text`, `images`, and `metadata`.

## Retriever and Ranker Classes

Retrievers:

| Import | Responsibility |
| --- | --- |
| `metagpt.rag.retrievers.base.RAGRetriever` | Abstract async/sync retrieval base over LlamaIndex retriever. |
| `ModifiableRAGRetriever` | Structural marker requiring `add_nodes()`. |
| `PersistableRAGRetriever` | Structural marker requiring `persist()`. |
| `QueryableRAGRetriever` | Structural marker requiring `query_total_count()`. |
| `DeletableRAGRetriever` | Structural marker requiring `clear()`. |
| `metagpt.rag.retrievers.faiss_retriever.FAISSRetriever` | LlamaIndex vector-index retriever with FAISS-specific mutation/persistence. |
| `metagpt.rag.retrievers.chroma_retriever.ChromaRetriever` | Chroma vector-index retriever. |
| `metagpt.rag.retrievers.es_retriever.ElasticsearchRetriever` | Elasticsearch vector/text retriever. |
| `metagpt.rag.retrievers.bm25_retriever.DynamicBM25Retriever` | BM25 retriever that can update nodes dynamically. |
| `metagpt.rag.retrievers.hybrid_retriever.SimpleHybridRetriever` | Runs multiple retrievers and deduplicates node ids. |

Rankers:

| Import | Responsibility |
| --- | --- |
| `metagpt.rag.rankers.base.RAGRanker` | Base node postprocessor. |
| `metagpt.rag.rankers.object_ranker.ObjectSortPostprocessor` | Sorts object nodes by configured metadata/object field. |

## Document Store API

| Import | Constructor | Core methods | Notes |
| --- | --- | --- | --- |
| `metagpt.document_store.base_store.BaseStore` | Abstract | `search`, `write`, `add` | Common abstract interface. |
| `metagpt.document_store.base_store.LocalStore` | `raw_data_path`, `cache_dir=None` | `_load`, `_write`, plus base methods | Loads or writes local cache. |
| `metagpt.document_store.faiss_store.FaissStore` | `raw_data`, `cache_dir=None`, `meta_col="source"`, `content_col="output"`, `embedding=None` | `search`, `asearch`, `write`, `add`, `persist`, `delete` | Delete raises `NotImplementedError`; FAISS index uses dimension 1536 in this wrapper. |
| `metagpt.document_store.chromadb_store.ChromaStore` | `name`, `get_or_create=False` | `search`, `write`, `add`, `delete`, `persist` | `persist()` raises `NotImplementedError`. |
| `metagpt.document_store.lancedb_store.LanceStore` | `name` | `search`, `write`, `add`, `delete`, `drop`, `persist` | Uses LanceDB at `./data/lancedb`; search expects vector query. |
| `metagpt.document_store.qdrant_store.QdrantConnection` | `url=None`, `host=None`, `port=None`, `memory=False`, `api_key=None` | dataclass | Selects memory, URL, or host/port mode. |
| `metagpt.document_store.qdrant_store.QdrantStore` | `QdrantConnection` | `create_collection`, `has_collection`, `delete_collection`, `add`, `search`, `write` | `write()` is a placeholder; `add()` upserts `PointStruct` list. |
| `metagpt.document_store.milvus_store.MilvusConnection` | `uri=None`, `token=None` | dataclass | Requires `uri`. |
| `metagpt.document_store.milvus_store.MilvusStore` | `MilvusConnection` | `create_collection`, `search`, `add`, `delete`, `write` | `write()` is a placeholder; imports `pymilvus` inside constructor. |

## Search APIs

Search types from `metagpt.configs.search_config.SearchEngineType`:

| Enum | Value | Wrapper | Required constructor fields |
| --- | --- | --- | --- |
| `SERPAPI_GOOGLE` | `"serpapi"` | `SerpAPIWrapper` | `api_key`; optional `params`, `url`, `proxy`, `aiosession`. |
| `SERPER_GOOGLE` | `"serper"` | `SerperWrapper` | `api_key`; optional `payload`, `url`, `proxy`, `aiosession`. |
| `DIRECT_GOOGLE` | `"google"` | `GoogleAPIWrapper` | `api_key`, `cse_id`; optional `discovery_service_url`, `proxy`, loop/executor. |
| `DUCK_DUCK_GO` | `"ddg"` | `DDGAPIWrapper` | optional `proxy`, loop/executor. |
| `CUSTOM_ENGINE` | `"custom"` | custom coroutine | `run_func`. |
| `BING` | `"bing"` | `BingAPIWrapper` | `api_key`; optional `bing_url`, `proxy`, `aiosession`. |

`metagpt.tools.search_engine.SearchEngine` fields and methods:

- Fields: `engine=SearchEngineType.SERPER_GOOGLE`, `run_func=None`, `api_key=None`, `proxy=None`, plus extra provider fields.
- `from_search_config(config, **kwargs)` creates from `SearchConfig`.
- `from_search_func(search_func, **kwargs)` creates a custom engine.
- `run(query, max_results=8, as_string=True, ignore_errors=False)` returns a string or list of focused result dicts.

## Browser and Scraping APIs

Browser types from `metagpt.configs.browser_config.WebBrowserEngineType`:

| Enum | Value | Wrapper | Browser type values |
| --- | --- | --- | --- |
| `PLAYWRIGHT` | `"playwright"` | `PlaywrightWrapper` | `chromium`, `firefox`, `webkit`. |
| `SELENIUM` | `"selenium"` | `SeleniumWrapper` | `chrome`, `firefox`, `edge`, `ie`. |
| `CUSTOM` | `"custom"` | custom coroutine | Depends on `run_func`. |

`metagpt.tools.web_browser_engine.WebBrowserEngine`:

- Fields: `engine=PLAYWRIGHT`, `run_func=None`, `proxy=None`, extra wrapper-specific fields.
- `from_browser_config(config, **kwargs)` creates from `BrowserConfig`.
- `run(url, *urls, per_page_timeout=None)` returns one `WebPage` or a list.

Wrapper details:

- `PlaywrightWrapper` fields: `browser_type="chromium"`, `launch_kwargs={}`, `proxy=None`, `context_kwargs={}`. It may call `python -m playwright install <browser>` during precheck if no executable exists.
- `SeleniumWrapper` fields: `browser_type="chrome"`, `launch_kwargs={}`, `proxy=None`, loop/executor. It uses webdriver-manager unless `executable_path` is provided.
- `metagpt.tools.libs.browser.Browser`: registered interactive browser tool tagged `web` and `browse`; exposes `goto`, `click`, `type`, `hover`, `press`, `scroll`, `go_back`, `go_forward`, `tab_focus`, `close_tab`, `view`, `start`, and `stop`.
- `metagpt.tools.libs.web_scraping.view_page_element_to_scrape(url, requirement, keep_links=False)`: registered `web scraping` function that simplifies page HTML and optionally uses RAG to narrow content.

## Tool Registry API

Core models:

- `metagpt.tools.tool_data_type.ToolSchema`: Pydantic model with `description`.
- `metagpt.tools.tool_data_type.Tool`: fields `name`, `path`, `schemas`, `code`, `tags`.
- `metagpt.tools.tool_registry.ToolRegistry`: local registry model.
- `metagpt.tools.tool_registry.TOOL_REGISTRY`: module-level global registry.
- `metagpt.tools.tool_registry.register_tool(tags=None, schema_path="", **kwargs)`: decorator for global registration.

`ToolRegistry` methods:

| Method | Purpose |
| --- | --- |
| `register_tool(tool_name, tool_path, schemas=None, schema_path="", tool_code="", tags=None, tool_source_object=None, include_functions=None, verbose=False)` | Generate/validate schema and register a tool. |
| `has_tool(key)` | Boolean existence check by tool name. |
| `get_tool(key)` | Return a registered `Tool` or `None`. |
| `get_tools_by_tag(key)` | Return `{tool_name: Tool}` for a tag. |
| `get_all_tools()` | Return all registered tools. |
| `has_tool_tag(key)` | Boolean tag existence check. |
| `get_tool_tags()` | Return registered tag names. |

Module-level helpers:

- `make_schema(tool_source_object, include, path)` converts source object docstrings/signatures into schemas.
- `validate_tool_names(tools)` accepts tool names, tags, files/directories, and `ClassTool:method1,method2` filters; invalid entries are skipped with warnings.
- `register_tools_from_file(file_path)` scans non-test `.py` files and registers schemas parsed from AST.
- `register_tools_from_path(path)` scans one file or a directory tree.

## Tool Recommendation API

`metagpt.tools.tool_recommend` classes:

| Class | Role | Dependencies/notes |
| --- | --- | --- |
| `ToolRecommender` | Base recall/rank flow; validates `tools` input | Ranking calls `LLM().aask()` and repairs JSON outputs. |
| `TypeMatchToolRecommender` | Recalls by matching plan task type to tool tags | Returns specified tools when no plan exists. |
| `BM25ToolRecommender` | Recalls with `rank_bm25.BM25Okapi` over names/tags/descriptions | Requires `rank_bm25`, `numpy`, and registered tool schemas. |
| `EmbeddingToolRecommender` | Declared placeholder | `recall_tools()` currently `pass`; do not rely on it. |

Useful methods:

- `recommend_tools(context="", plan=None, recall_topk=20, topk=5) -> list[Tool]`.
- `get_recommended_tool_info(fixed=None, **kwargs) -> str` returns prompt text containing selected schemas.
- `recall_tools(...)` is implemented by subclasses.
- `rank_tools(...)` uses the LLM ranking prompt.

## Registered Tool Families

Importing `metagpt.tools` imports `metagpt.tools.libs`, which registers these notable families:

| Family | Examples | Tags/notes |
| --- | --- | --- |
| Browser/web | `Browser`, `view_page_element_to_scrape` | Tags include `web`, `browse`, `web scraping`; network/browser prerequisites. |
| Editor/file | `Editor` | Registered class exposes selected file editing/search methods; similarity search needs RAG. |
| Terminal/shell | `Terminal`, `Bash` | Shell execution surfaces; require safety gating. |
| Data preprocess | `FillMissingValue`, `MinMaxScale`, `StandardScale`, `MaxAbsScale`, `RobustScale`, `OrdinalEncode`, `OneHotEncode`, `LabelEncode` | Data Interpreter-adjacent; route orchestration to `data-interpreter`. |
| Feature engineering | `PolynomialExpansion`, `CatCount`, `TargetMeanEncoder`, `KFoldTargetMeanEncoder`, `CatCross`, `GroupStat`, `GeneralSelection`, `VarianceBasedSelection` | Some transforms need optional ML packages. |
| Software helpers | Git issue/PR helpers, deployer, code review | External service or shell/network side effects. |
| Multimodal | Stable Diffusion engine, GPT-V generator, image getter | External models/services or image dependencies. |

## Provenance Evidence

The public API above was distilled from repo evidence including `metagpt/rag/interface.py`, `metagpt/rag/schema.py`, `metagpt/rag/factories/*`, `metagpt/rag/engines/simple.py`, `metagpt/rag/retrievers/*`, `metagpt/rag/rankers/*`, `metagpt/document_store/*`, `metagpt/tools/*`, `metagpt/tools/libs/*`, RAG examples, and RAG/tool tests. These paths are provenance only; future agents should use installed package imports and bundled references/scripts instead of opening the original checkout.
