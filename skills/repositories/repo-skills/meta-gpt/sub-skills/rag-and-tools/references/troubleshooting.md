# RAG and Tools Troubleshooting

Start with a safe diagnostic import check, then isolate the failure to import, config, data/schema, service reachability, model/provider call, or tool execution safety.

## Triage Flow

1. Run `python scripts/rag_import_check.py --group <surface>` for `rag`, `vector-stores`, `search`, `browser`, `registry`, or `tools`.
2. If imports fail, fix the smallest missing dependency group before changing code.
3. If imports pass but construction fails, check config fields, dimensions, paths, provider keys, and service endpoints.
4. If construction passes but retrieval/search/browser output is empty, inspect inputs and returned raw nodes/results before changing prompts.
5. If the task involves network, browser automation, shell, provider APIs, model downloads, or external vector DB services, confirm prerequisites and safety before executing.

## Missing RAG Extras or Deep Imports

Symptoms:

- `ModuleNotFoundError: No module named 'chromadb'` when importing `metagpt.rag.schema`.
- `ModuleNotFoundError: No module named 'llama_index'` or a `llama_index.vector_stores.*` import failure.
- `ImportError` messages from ranker factory recommending a specific `llama-index-postprocessor-*` package.
- `Editor.similarity_search()` raises “To use the similarity search, you need to install the RAG module.”

Actions:

- Install `metagpt[rag]` when the user wants general MetaGPT RAG coverage.
- For minimal local semantic RAG, install only LlamaIndex core/readers, FAISS vector-store integration, and FAISS CPU packages.
- For keyword-only retrieval, prefer `BM25RetrieverConfig()` and install BM25 dependencies without vector-store packages.
- Re-run the import helper after installation; do not run RAG examples that require data, providers, or services as dependency checks.

## Embedding and LLM Config Failures

Symptoms:

- `TypeError: To use RAG, please set your embedding in config2.yaml.`
- Provider auth errors from OpenAI/Azure/Gemini/Ollama embedding or LLM packages.
- FAISS dimension mismatch, low recall, or vector-index errors.
- Context-window error such as “Calculated available context size ... was not non-negative.”
- `LLMRankerConfig` produces parse errors, `IndexError`, or irrelevant reranking.

Actions:

- Set MetaGPT embedding provider fields before using vector retrievers: API type, model, base URL, API key, and dimensions when provider defaults are unknown.
- Match `FAISSRetrieverConfig(dimensions=...)` to the embedding vector size. Known schema defaults include Gemini 768, Ollama 4096, and fallback 1536 when dimensions are absent.
- Pass an explicit LlamaIndex `embed_model` for tests or offline checks; use a mock embedding only for no-embedding configs or synthetic unit-like checks.
- Avoid `LLMRankerConfig` until raw retrieval works; use `ObjectRankerConfig` or no ranker for deterministic flows.
- Adjust MetaGPT LLM context/max token settings when context-window calculations fail.

## Document Input, Chunking, and Schema Issues

Symptoms:

- `ValueError: Must provide either input_dir or input_files.`
- Empty `aretrieve()` results after successful indexing.
- Unsupported file type, blank document content, parser timeout, or OmniParse service errors.
- Object retrieval cannot reconstruct object or `metadata["obj"]` missing.
- Dataframe/data-preprocess tools fail on missing columns, unexpected dtypes, or non-DataFrame inputs.

Actions:

- Prefer explicit `input_files=[...]`; verify files are readable and non-empty before indexing.
- Tune chunking with `SentenceSplitter(chunk_size=..., chunk_overlap=...)` when nodes are too small, too large, or missing answer context.
- For object RAG, ensure each object implements `rag_key()` and is Pydantic-like with `model_dump_json()`; keep the object class importable by module/class name for reconstruction.
- For PDF parsing through OmniParse, treat `config.omniparse.base_url` and API key as external service prerequisites; otherwise rely on LlamaIndex readers.
- For data tools, validate input columns, null handling, and dtype conversions before invoking preprocess/feature engineering transforms.

## Empty or Poor Retrieval Results

Symptoms:

- `aretrieve()` returns `[]` or unrelated nodes.
- `aquery()` returns “Empty Response,” “I don't know,” or a plausible but unsupported answer.
- Hybrid retriever returns duplicate-looking or imbalanced results.

Actions:

- Always inspect `nodes = await engine.aretrieve(question)` before trusting `await engine.aquery(question)`.
- Check the document text that was indexed, chunk boundaries, and metadata exclusions.
- Increase `similarity_top_k` in retriever config or adjust chunk size/overlap.
- Try BM25 for exact keyword/entity queries; try FAISS/Chroma for semantic paraphrases; use hybrid when both matter.
- Add a ranker only after the candidate set contains relevant nodes.
- For hybrid retrieval, build each child retriever alone first; then combine configs after both work.

## FAISS Problems

Symptoms:

- `ModuleNotFoundError: faiss`.
- CPU/GPU FAISS binary incompatibility or import crash.
- Dimension mismatch during insert/search.
- Persisted index cannot reload.
- Delete is unavailable in `FaissStore`.

Actions:

- Use CPU FAISS (`faiss_cpu`) for most local agent workflows unless GPU FAISS is explicitly required and supported.
- Keep FAISS package, Python version, and platform compatible; MetaGPT metadata targets Python `>=3.9,<3.12`.
- Set vector dimensions explicitly when embedding provider output size is known.
- Persist and reload with matching FAISS config/index directory; ensure index and docstore files exist.
- Use retriever/index rebuilds for delete-heavy workflows; `FaissStore.delete()` is not implemented.

## Chroma Problems

Symptoms:

- `ModuleNotFoundError: chromadb`.
- Collection cannot be created or found.
- Persisted collection reload returns empty results.
- `ChromaStore.persist()` raises `NotImplementedError`.

Actions:

- Install Chroma plus LlamaIndex Chroma vector-store integration.
- Use consistent `persist_path` and `collection_name` between `ChromaRetrieverConfig` and `ChromaIndexConfig`.
- Verify path permissions and avoid mixing transient `chromadb.Client()` wrappers with persistent-client workflows.
- Prefer `SimpleEngine` Chroma configs for persistent RAG; treat low-level `ChromaStore` as simple collection wrapper.

## Elasticsearch Problems

Symptoms:

- Connection refused to `http://127.0.0.1:9200` or configured endpoint.
- Authentication or cloud-id/API-key errors.
- Text-vs-vector query mismatch.
- Index name collision or stale mapping.

Actions:

- Verify Elasticsearch service reachability with a safe health check before running indexing.
- Fill the appropriate `ElasticsearchStoreConfig` fields: local `es_url` or cloud/user/password/API-key fields.
- Use `ElasticsearchKeywordRetrieverConfig` for text-only/no-embedding search.
- Use a unique `index_name` for experiments and record cleanup expectations.

## Qdrant, Milvus, LanceDB, and MeiliSearch Problems

Qdrant symptoms/actions:

- Missing `qdrant_client`: install `qdrant-client`.
- `please check QdrantConnection.`: provide exactly one valid connection mode such as `memory=True`, `url=...`, or `host` plus `port`.
- Connection/auth errors: verify service URL, port, API key, and collection exists.
- Vector search shape errors: ensure query vector length matches `VectorParams` dimension.

Milvus symptoms/actions:

- `Please install pymilvus first.`: install `pymilvus` only if Milvus is required.
- `uri must be set`: provide `MilvusConnection(uri=..., token=...)`.
- Collection schema/vector errors: match `dim`, primary id type, vector field, metadata fields, and index metric.

LanceDB symptoms/actions:

- Missing `lancedb` or PyArrow compatibility errors: install a compatible LanceDB/PyArrow stack for the Python version.
- “Table not created yet”: call `write()` or `add()` before `search()`/`delete()`.
- SQL/filter errors: validate `.where(...)` expression and metadata column names.

MeiliSearch symptoms/actions:

- MeiliSearch search tests require an external `meilisearch` binary/server and are skipped in source tests.
- Treat service startup as an external prerequisite; do not start it from a runtime skill unless the user explicitly approves.

## Search Engine Problems

Symptoms:

- Serper/SerpAPI constructor `ValueError` asking for `api_key`.
- Google API import error recommending `metagpt[search-google]`.
- Google constructor `ValueError` asking for `api_key` or `cse_id`.
- DuckDuckGo import error recommending `metagpt[search-ddg]`.
- HTTP 401/403/429, rate limit, quota, proxy, or network timeout.
- Empty/shape-mismatched provider response causes index/key errors.

Actions:

- Pick one search provider; do not install/configure all providers for one task.
- Confirm network permission and whether the query contains private data before calling search APIs.
- Provide `proxy` when the environment requires it.
- For Google Direct, require both `api_key` and `cse_id`.
- Use `SearchEngine.from_search_func()` for offline or mocked search behavior.
- Use `ignore_errors=True` only when an empty string/list is acceptable and the failure is logged.

## Browser and Web Scraping Problems

Symptoms:

- `ModuleNotFoundError: playwright` or Selenium packages.
- Playwright executable path missing; automatic `playwright install` fails.
- Selenium cannot find browser, driver, or webdriver-manager download is blocked.
- Browser page load timeout, blank `inner_text`, certificate/proxy issue, or JS-heavy site failure.
- Interactive `Browser` accessibility tree is empty or element ids are stale.

Actions:

- Ask before installing browser binaries or downloading WebDrivers.
- For Playwright, install package and run `playwright install` only when allowed; use `launch_kwargs={"executable_path": "..."}` if a browser is already managed externally.
- For Selenium, install `metagpt[selenium]`, ensure the named browser exists, and pass `executable_path` when auto-download is unavailable.
- Set `proxy`, `ignore_https_errors`, `user_agent`, or timeout fields only when required by the site/environment.
- Treat browser automation as a stepwise observed workflow: navigate, inspect, then click/type/scroll.
- For `view_page_element_to_scrape`, if RAG narrowing fails, continue from simplified HTML instead of failing the whole scrape.

## Tool Registry Schema Problems

Symptoms:

- Registered tool exists but has weak or empty schema.
- `validate_tool_names()` logs invalid tool name, tag, or method and skips it.
- `ClassTool:method` filter returns no methods.
- Path scanning registers unexpected tools or none.

Actions:

- Add clear class/function docstrings and type annotations; schema generation depends on signatures and docs.
- Use `include_functions=[...]` to expose only safe methods from class tools.
- Verify tool names exactly match class/function names registered in `TOOL_REGISTRY`.
- Use tags for coarse selection but tool names for deterministic selection.
- Avoid scanning broad directories with tests, setup files, generated code, or unsafe modules.

## Tool Recommendation Problems

Symptoms:

- `BM25ToolRecommender` import fails for `rank_bm25` or `numpy`.
- Recommender returns empty list even though tools exist.
- LLM ranking returns malformed JSON or unexpected tool names.
- `EmbeddingToolRecommender` does nothing.

Actions:

- Ensure `metagpt.tools` has been imported so `metagpt.tools.libs` registers built-in tools.
- Use meaningful tool descriptions; BM25 recall searches name, tags, and description.
- For deterministic behavior, use `force=True` or call `validate_tool_names()` directly.
- Do not rely on `EmbeddingToolRecommender`; it is a placeholder.
- If LLM ranking is unavailable, fall back to recalled tools or explicit tool selection.

## Tool Execution Safety

High-risk tool surfaces:

- Shell/terminal execution (`Terminal`, `Bash`, shell helpers).
- Browser navigation, scraping, and provider search APIs.
- Git/PR/issue helpers and deployment helpers.
- Image/model tools that call external services or local model runtimes.
- Custom tools registered from arbitrary paths.

Safety actions:

- Ask before executing shell commands, network calls, browser automation, provider APIs, service startups, model downloads, or writes outside the intended workspace.
- Prefer import/spec checks and schema inspection before execution.
- For custom tools, inspect schema and source intent, restrict methods with `ClassTool:method` or `include_functions`, and avoid broad path scans.
- Never pass secrets into prompts or logs. Refer to required keys by name only.
- Route Data Interpreter orchestration to `data-interpreter`; use this sub-skill only to validate individual tool prerequisites and failure modes.

## Two Hard Usability Cases to Validate

1. Base MetaGPT only, local RAG requested: user asks for a local document QA pipeline but lacks `metagpt[rag]`. The agent should run `scripts/rag_import_check.py --group rag --group vector-stores`, identify the minimal packages for FAISS or BM25, explain embedding dimension/config requirements, and avoid service/browser/network work.
2. Data Interpreter browsing/scraping request: user asks DI to browse and scrape a website. The agent should route orchestration to `data-interpreter`, return here for `WebBrowserEngine`/`Browser`/`view_page_element_to_scrape` prerequisites, flag network/browser safety and Playwright/Selenium setup, and avoid running the browser without approval.
