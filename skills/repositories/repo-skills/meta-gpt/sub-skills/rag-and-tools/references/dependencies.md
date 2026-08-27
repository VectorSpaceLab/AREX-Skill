# RAG and Tools Dependencies

MetaGPT keeps many RAG, search, browser, vector-store, and tool-recommendation packages optional. Diagnose the requested path first and install the smallest package set that matches the chosen retriever/tool/provider.

## Safe Dependency Diagnostics

Use the bundled helper before importing deep optional modules:

```bash
python scripts/rag_import_check.py --group rag
python scripts/rag_import_check.py --group vector-stores
python scripts/rag_import_check.py --group search --group browser --group registry
python scripts/rag_import_check.py --all
```

The helper only checks import specs/imports and prints advice. It does not start vector DB services, run searches, instantiate browser engines, install browsers, download models, or call LLMs.

## MetaGPT Extras and Base Requirements

Package metadata exposes these relevant extras:

| Need | Install target | Includes from package metadata | Notes |
| --- | --- | --- | --- |
| RAG core and LlamaIndex integrations | `metagpt[rag]` | `llama-index-core==0.10.15`, OpenAI/Azure/Gemini/Ollama embeddings, Azure OpenAI LLM, file readers, BM25 retriever, FAISS/Elasticsearch/Chroma vector stores, Cohere/ColBERT/BGE rerankers, `docx2txt==0.8` | Does not cover every low-level document-store wrapper such as Qdrant/Milvus/LanceDB in all install modes. |
| Selenium browser | `metagpt[selenium]` | `selenium>4`, `webdriver_manager`, `beautifulsoup4` | Requires installed browser/WebDriver compatibility. |
| Google API search | `metagpt[search-google]` | `google-api-python-client==2.94.0` | Also requires Google API key and CSE id. |
| DuckDuckGo search | `metagpt[search-ddg]` | `duckduckgo-search~=4.1.1` | No provider key, but still requires network. |
| Pyppeteer legacy | `metagpt[pyppeteer]` | `pyppeteer>=1.0.2` | Marked as unmaintained/conflicting in package metadata; prefer Playwright/Selenium surfaces when possible. |

Relevant base `requirements.txt` evidence includes `faiss_cpu==1.7.4`, `lancedb==0.4.0`, `meilisearch==0.21.0`, `numpy~=1.26.4`, `beautifulsoup4==4.12.3`, `pandas==2.1.1`, `qdrant-client==1.7.0`, `scikit_learn==1.3.2`, and `playwright>=1.26`. `pymilvus`, Selenium, and webdriver-manager are commented in base requirements and should be treated as optional unless installed by extras or the user.

## RAG Core Dependencies

| Import or feature | Package/module | Symptom when missing | Minimal action |
| --- | --- | --- | --- |
| `metagpt.rag.schema` | `chromadb`, `llama-index-core` | `ModuleNotFoundError: No module named 'chromadb'` or `No module named 'llama_index'` during schema import. | Install `metagpt[rag]` or install `chromadb` plus the needed LlamaIndex packages. |
| `SimpleEngine.from_docs` | `llama-index-core`, `fsspec`, configured embedding/LLM provider packages | Import errors, embedding config errors, or provider authentication errors. | Install RAG core and configure embedding/LLM keys/base URLs. |
| File readers for docx/pdf/etc. | `llama-index-readers-file`, `docx2txt`; optional OmniParse service for PDF if configured | Unsupported file type, parse failure, service timeout. | Install file-reader packages; for OmniParse, configure service URL/API key and mark external service prerequisite. |
| BM25 retriever | `llama-index-retrievers-bm25`, `rank_bm25` | Import failure in BM25 retriever or tool recommender. | Install RAG extra or `llama-index-retrievers-bm25`/`rank_bm25`. |
| RAG LLM wrapper | MetaGPT LLM config plus LlamaIndex core | Context-window error such as “Calculated available context size ... was not non-negative” or auth failure. | Set MetaGPT LLM model/max token/context length and provider credentials. |
| RAG embedding factory | LlamaIndex embedding integration for configured provider | “embedding type not supported” or provider package missing. | Install provider-specific LlamaIndex embedding package and configure `embedding.api_type`, model, dimensions, and keys. |

## Retriever and Index Dependencies

| Path | Packages/services | Missing or incompatible symptom | Minimal action |
| --- | --- | --- | --- |
| FAISS retriever/index | `faiss`/`faiss_cpu`, `llama-index-vector-stores-faiss` | `ModuleNotFoundError: faiss`; import error for `llama_index.vector_stores.faiss`; dimension mismatch during index/search. | Install CPU FAISS for most local cases; set `FAISSRetrieverConfig(dimensions=...)` to match embedding output. Use GPU FAISS only when environment supports it. |
| Chroma retriever/index | `chromadb`, `llama-index-vector-stores-chroma` | `ModuleNotFoundError: chromadb`; collection/persist path errors. | Install Chroma packages; choose writable `persist_path` and stable `collection_name`. |
| Elasticsearch retriever/index | `llama-index-vector-stores-elasticsearch`, reachable Elasticsearch service | Connection refused, auth error, index creation/search failure. | Provide `ElasticsearchStoreConfig` with `es_url` or cloud credentials; verify service reachability outside long RAG runs. |
| BM25 retriever/index | `rank_bm25`, `llama-index-retrievers-bm25` | Missing BM25 package, empty node list, no index when requested. | Install BM25 dependency and pass nodes/documents; use `create_index=True` only when persistence-like behavior is required. |
| Hybrid retriever | Dependencies for every child retriever | One child fails to import/build, entire hybrid build fails. | Start with one retriever, then add BM25/vector retrievers incrementally. |

## Ranker Dependencies

| Ranker | Packages/services | Symptoms | Minimal action |
| --- | --- | --- | --- |
| No ranker | None beyond retriever | Lower precision, no rerank. | Use when dependencies or LLM calls are constrained. |
| `LLMRankerConfig` | LlamaIndex core plus configured MetaGPT LLM | Paid/long call, auth failure, malformed rerank output, `IndexError`/parse errors from weak LLMs. | Use a strong configured model; reduce `top_n`; skip if deterministic behavior is needed. |
| `ObjectRankerConfig` | None beyond RAG core | Field missing or values not comparable. | Ensure object metadata contains `field_name` and comparable values. |
| `CohereRerankConfig` | `llama-index-postprocessor-cohere-rerank`, Cohere API key | Explicit import error recommending package; API auth failure. | Install only if Cohere reranking is required and key is available. |
| `ColbertRerankConfig` | `llama-index-postprocessor-colbert-rerank`, model runtime | Explicit import error; model download latency; CPU slowness. | Treat as optional/long-running; confirm downloads and runtime. |
| `BGERerankConfig` | `llama-index-postprocessor-flag-embedding-reranker`, compatible ML stack | Explicit import error; model download/GPU/FP16 issues. | Use CPU/no-fp16 where needed; confirm model downloads. |

## Document Store Dependencies

| Store | Package/service | Symptom | Notes |
| --- | --- | --- | --- |
| `FaissStore` | `faiss`, `llama-index-vector-stores-faiss`, configured embedding | Missing FAISS/import error; index files absent; delete not implemented. | Good for local file-backed vector search from indexable data. |
| `ChromaStore` | `chromadb` | Missing Chroma package; local persist not implemented in wrapper. | For higher-level persistent Chroma, prefer RAG `ChromaRetrieverConfig`/`ChromaIndexConfig`. |
| `LanceStore` | `lancedb`, PyArrow-compatible environment | Missing LanceDB/PyArrow error; “Table not created yet”; schema/vector mismatch. | Search expects vector query and table initialized by `write()`/`add()`. |
| `QdrantStore` | `qdrant-client`; optional Qdrant server/cloud | Missing qdrant client; connection refused; auth failure; collection absent. | Use `QdrantConnection(memory=True)` for in-memory checks; URL/host modes require service. |
| `MilvusStore` | `pymilvus`; Milvus URI/token | `Please install pymilvus first.`; missing URI; service/auth failure. | Constructor imports `pymilvus` lazily and requires `uri`. |

## Search Dependencies and Keys

| Engine | Packages | Required keys/config | Symptoms |
| --- | --- | --- | --- |
| Serper Google | `aiohttp` | `api_key` | Constructor `ValueError` saying to provide `api_key`; HTTP auth/rate-limit errors. |
| SerpAPI Google | `aiohttp` | `api_key`; optional SerpAPI `params` | Constructor `ValueError`; provider error in response. |
| Direct Google | `google-api-python-client`, `httplib2` | `api_key`, `cse_id` | Import error recommending `metagpt[search-google]`; `ValueError` for missing `api_key`/`cse_id`. |
| DuckDuckGo | `duckduckgo-search` | Optional proxy | Import error recommending `metagpt[search-ddg]`; network/rate-limit failures. |
| Bing | `aiohttp` | `api_key` | API auth/rate-limit errors; response shape errors if no web pages. |
| Custom | none beyond user function | `run_func` coroutine | `NoneType` callable errors if `run_func` missing. |

Do not run searches without user consent when queries may contain private data or external network access is restricted.

## Browser and Scraping Dependencies

| Surface | Packages/binaries | Symptoms | Minimal action |
| --- | --- | --- | --- |
| `WebBrowserEngineType.PLAYWRIGHT` | `playwright`; browser binaries | Import error; executable path missing; attempted browser install fails; timeout loading page. | Install Playwright package and run `playwright install` only with user approval. Provide proxy if needed. |
| `WebBrowserEngineType.SELENIUM` | `selenium`, `webdriver_manager`, `beautifulsoup4`; installed browser/driver | Import error; browser not found; WebDriver download blocked; renderer/no-sandbox errors. | Install `metagpt[selenium]`; specify `browser_type` and `executable_path` when auto-download is not allowed. |
| `metagpt.tools.libs.browser.Browser` | Playwright runtime and browser binaries | Fails at `start()`/`goto()`; accessibility tree empty. | Treat browser use as standalone, observed steps; confirm network/browser safety. |
| `view_page_element_to_scrape` | Browser dependencies; optional RAG imports | Browser failure; RAG narrowing skipped/fails. | If RAG fails, use simplified HTML fallback; do not require RAG for basic scrape. |

## Tool Registry and Recommendation Dependencies

| Surface | Packages | Symptoms | Minimal action |
| --- | --- | --- | --- |
| `ToolRegistry` and `register_tool` | Pydantic and MetaGPT tool conversion utilities | Empty schema from missing docstring/signature; invalid tool skipped. | Add clear docstrings and type annotations; use `include_functions` to expose only safe methods. |
| `validate_tool_names` path scanning | Readable Python file/directory | Test/setup/private files skipped; invalid path yields no tools. | Pass a specific safe tool file or registered names/tags. |
| `BM25ToolRecommender` | `rank_bm25`, `numpy`; registered tool schemas | Import error; empty corpus; weak recall from poor descriptions. | Ensure tools are registered and descriptions are meaningful. |
| `ToolRecommender.rank_tools` | Configured MetaGPT LLM | Long/paid calls; malformed JSON requiring repair; fallback to recalled tools. | Use `force=True` or direct registry validation for deterministic/offline flows. |
| Data preprocess/feature tools | `pandas`, `numpy`, `scikit_learn`; sometimes optional ML libs | Import errors, dataframe schema mismatch, skipped LightGBM tree selection. | Route DI orchestration elsewhere; here validate tool-specific packages and dataframe inputs. |

## Minimal Dependency Recipes

Local document RAG with FAISS:

- Install `metagpt[rag]` or at minimum LlamaIndex core, file readers, FAISS vector-store integration, and FAISS CPU package.
- Configure embedding provider and dimensions.
- Use `FAISSRetrieverConfig(dimensions=<embedding_dim>)`; skip LLM ranker first.

Local keyword-only RAG:

- Install BM25 dependency (`rank_bm25` and LlamaIndex BM25 retriever integration).
- Use `BM25RetrieverConfig()` and avoid embedding-dependent configs.
- Pass documents or objects so node list is not empty.

Chroma persistence:

- Install `chromadb` and LlamaIndex Chroma vector-store integration.
- Use `ChromaRetrieverConfig(persist_path=..., collection_name=...)` to build and `ChromaIndexConfig(...)` to load.

Search-only task:

- Pick one provider. For no provider key, use DuckDuckGo only if network access is allowed and `duckduckgo-search` is installed.
- For Google API, install `metagpt[search-google]` and require both `api_key` and `cse_id`.

Browse/scrape task:

- Prefer Playwright when available; require browser binaries.
- Use Selenium only when a compatible installed browser/WebDriver path is known or auto-download is allowed.
- Route Data Interpreter plan/execution to `data-interpreter`; keep browser prerequisite diagnosis here.
