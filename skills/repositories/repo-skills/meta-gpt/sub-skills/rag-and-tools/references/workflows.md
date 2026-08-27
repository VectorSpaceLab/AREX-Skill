# RAG and Tools Workflows

This reference distills MetaGPT RAG and tool evidence into self-contained recipes. Treat external API keys, service endpoints, browser binaries, network access, model downloads, and long LLM/reranker calls as prerequisites or skips.

## Preflight Before Any RAG or Tool Work

1. Run the bundled helper for the intended surface:
   - `python scripts/rag_import_check.py --group rag`
   - `python scripts/rag_import_check.py --group vector-stores`
   - `python scripts/rag_import_check.py --group search --group browser --group registry`
2. Confirm configuration for embeddings and LLMs before building vector indexes:
   - RAG embedding factory uses MetaGPT embedding config first, then compatible OpenAI/Azure LLM config for backward compatibility.
   - If no supported embedding config exists, `get_rag_embedding()` raises a type/config error such as “To use RAG, please set your embedding in config2.yaml.”
3. Choose the smallest dependency set for the requested task. Do not install every optional package when a local BM25-only or single-vector-store path is enough.
4. Mark external services as prerequisites:
   - Elasticsearch URL/cloud/API credentials for ES retrievers.
   - Qdrant/Milvus/MeiliSearch server or cloud credentials unless using Qdrant `memory=True` for local in-memory checks.
   - Search provider keys for Serper, SerpAPI, Google CSE, or Bing.
   - Playwright browser binaries or Selenium WebDriver/browser installation for browser tools.

## Build a Minimal RAG Pipeline

Use `metagpt.rag.engines.SimpleEngine` for document reading, chunking, embedding, indexing, retrieving, ranking, and query synthesis.

Typical sequence:

```python
from metagpt.rag.engines import SimpleEngine
from metagpt.rag.schema import FAISSRetrieverConfig

engine = SimpleEngine.from_docs(
    input_files=["docs/notes.txt"],
    retriever_configs=[FAISSRetrieverConfig()],
    ranker_configs=None,
)
nodes = await engine.aretrieve("What does the document say about shipping?")
answer = await engine.aquery("What does the document say about shipping?")
```

Key choices:

- `input_files=[...]` is safest when the user names exact files; `input_dir="..."` loads a directory through LlamaIndex `SimpleDirectoryReader`.
- `transformations` defaults to `[SentenceSplitter()]`; provide explicit LlamaIndex transformations for chunk size/overlap control.
- `embed_model` can be a LlamaIndex `BaseEmbedding`; otherwise MetaGPT creates one from config.
- `llm` can be a LlamaIndex-compatible LLM; otherwise MetaGPT wraps its configured `metagpt.llm.LLM` through `RAGLLM`.
- `ranker_configs=None` avoids extra reranker dependencies and long/paid calls.

Validation steps:

- Retrieve before querying: `await engine.aretrieve(question)` shows whether any nodes are recalled.
- Check empty results separately from LLM answer quality.
- If `aquery()` returns an empty or irrelevant response, inspect retrieved nodes and scores before changing prompts.

## Add Documents or Objects After Initialization

`SimpleEngine.add_docs()` and `SimpleEngine.add_objs()` require a retriever that supports `add_nodes`, such as MetaGPT RAG retrievers. A plain LlamaIndex retriever returned by the default path may not support all mutation methods.

Document add flow:

```python
engine.add_docs(["docs/new-file.txt"])
nodes = await engine.aretrieve("question about the new file")
```

Object add flow:

```python
from pydantic import BaseModel

class Player(BaseModel):
    name: str
    goal: str

    def rag_key(self) -> str:
        return self.goal

engine = SimpleEngine.from_objs(
    objs=[Player(name="Mike", goal="Win the 100-meter Sprint")],
    retriever_configs=[FAISSRetrieverConfig()],
)
nodes = await engine.aretrieve("100-meter Sprint")
obj = nodes[0].metadata.get("obj")
```

Object indexing requirements:

- Object classes must behave like Pydantic models with `model_dump_json()`.
- Objects must implement `rag_key()`; the returned text becomes the retrievable node text.
- Reconstructed objects are placed in `node.metadata["obj"]` after retrieval.

## Persist and Reload Indexes

For persistence, use a store-specific retriever config when building and matching index config when loading.

Chroma example:

```python
from metagpt.rag.schema import ChromaIndexConfig, ChromaRetrieverConfig

SimpleEngine.from_docs(
    input_files=["docs/travel.txt"],
    retriever_configs=[ChromaRetrieverConfig(persist_path="./rag_store", collection_name="metagpt")],
)
engine = SimpleEngine.from_index(index_config=ChromaIndexConfig(persist_path="./rag_store", collection_name="metagpt"))
answer = await engine.aquery("What does Bob like?")
```

FAISS reload example:

```python
from metagpt.rag.schema import FAISSIndexConfig, FAISSRetrieverConfig

engine = SimpleEngine.from_docs(
    input_files=["docs/articles.txt"],
    retriever_configs=[FAISSRetrieverConfig(dimensions=1536)],
)
engine.persist("./faiss_index")
reloaded = SimpleEngine.from_index(index_config=FAISSIndexConfig(persist_path="./faiss_index"))
```

Elasticsearch example:

```python
from metagpt.rag.schema import ElasticsearchIndexConfig, ElasticsearchRetrieverConfig, ElasticsearchStoreConfig

store = ElasticsearchStoreConfig(index_name="travel", es_url="http://127.0.0.1:9200")
SimpleEngine.from_docs(input_files=["docs/travel.txt"], retriever_configs=[ElasticsearchRetrieverConfig(store_config=store)])
engine = SimpleEngine.from_index(index_config=ElasticsearchIndexConfig(store_config=store))
```

Persistence cautions:

- FAISS config dimensions must match the embedding output dimension.
- Chroma persistence uses a `chromadb.PersistentClient` path and collection name.
- Elasticsearch config needs reachable service credentials or URL.
- BM25 can be index-backed with `BM25RetrieverConfig(create_index=True)` but is often better for in-memory or hybrid retrieval.

## Choose Retrievers and Rankers

Retrievers:

| Need | Recommended config | Notes |
| --- | --- | --- |
| Simple local semantic search | `FAISSRetrieverConfig(dimensions=...)` | Requires FAISS package and LlamaIndex FAISS vector-store package. CPU FAISS is usually simplest. |
| Keyword/no-embedding retrieval | `BM25RetrieverConfig()` | Uses `rank_bm25`; no embedding if all configs are no-embedding. |
| Hybrid semantic + keyword | `[FAISSRetrieverConfig(...), BM25RetrieverConfig()]` | Factory returns `SimpleHybridRetriever` and deduplicates by node id. |
| Local Chroma collection | `ChromaRetrieverConfig(persist_path=..., collection_name=...)` | Requires `chromadb` and Chroma LlamaIndex vector store. |
| Elasticsearch vector/text | `ElasticsearchRetrieverConfig(store_config=...)` | Requires ES vector-store package and reachable ES. |
| Elasticsearch text-only | `ElasticsearchKeywordRetrieverConfig(store_config=...)` | No embedding path; query mode is text search. |

Rankers/postprocessors:

| Need | Config | Notes |
| --- | --- | --- |
| No reranker | `ranker_configs=None` | Lowest dependency and cost. |
| LLM rerank | `LLMRankerConfig(top_n=...)` | Calls configured LLM; examples warn weaker models can return unparsable rerank outputs. |
| Object sort | `ObjectRankerConfig(field_name="...", order="desc")` | Sorts object nodes by metadata field; no external model. |
| Cohere rerank | `CohereRerankConfig(api_key="...")` | Requires `llama-index-postprocessor-cohere-rerank` and Cohere key. |
| ColBERT rerank | `ColbertRerankConfig(model="colbert-ir/colbertv2.0", device="cpu")` | May download models and can be slow. |
| BGE rerank | `BGERerankConfig(model="BAAI/bge-reranker-large", use_fp16=True)` | Requires flag embedding reranker package and suitable runtime. |

## Use RAG as a Role Search Store

Roles that accept a `store` can use a RAG engine implementing `asearch`.

```python
from metagpt.rag.engines import SimpleEngine
from metagpt.roles import Sales

store = SimpleEngine.from_docs(input_files=["docs/product.txt"])
role = Sales(profile="Sales", store=store)
result = await role.run("Summarize the product positioning")
```

Keep this in the RAG/tools area for store setup and retrieval failures. Route broader `Role`/`Action` design or software-company workflows to the sibling software-company guidance.

## Use Document Store Wrappers

MetaGPT also exposes lower-level document/vector store wrappers under `metagpt.document_store`.

Typical choices:

- `FaissStore(raw_data, cache_dir=None, meta_col="source", content_col="output", embedding=None)`: initializes from an indexable JSON/XLSX-like data file, persists through LlamaIndex storage context, and supports `search()`, `asearch()`, `add()`, and `persist()`. Delete is not implemented.
- `ChromaStore(name, get_or_create=False)`: simple in-process Chroma collection wrapper with `search()`, `write()`, `add()`, and `delete()`. Local `persist()` is not implemented in this wrapper.
- `LanceStore(name)`: local LanceDB table wrapper using `./data/lancedb`, vector `search()`, `write()`, `add()`, `delete()`, and `drop()`.
- `QdrantStore(QdrantConnection(...))`: service/cloud/in-memory Qdrant wrapper with collection creation, upsert, search, delete collection, and collection existence checks.
- `MilvusStore(MilvusConnection(uri=..., token=...))`: Milvus client wrapper with collection creation, vector search, add, and delete.

Prefer `SimpleEngine` for agent-facing RAG unless the user specifically needs low-level store operations.

## Use Search Engines Safely

Search dispatch uses `metagpt.tools.search_engine.SearchEngine` with `SearchEngineType` values:

- `SearchEngineType.SERPER_GOOGLE` (`"serper"`): requires `api_key`; posts to Serper.
- `SearchEngineType.SERPAPI_GOOGLE` (`"serpapi"`): requires `api_key`; calls SerpAPI.
- `SearchEngineType.DIRECT_GOOGLE` (`"google"`): requires `google-api-python-client`, `api_key`, and `cse_id`.
- `SearchEngineType.DUCK_DUCK_GO` (`"ddg"`): requires `duckduckgo-search`; no provider key, but still uses network.
- `SearchEngineType.BING` (`"bing"`): requires `api_key`; calls Bing Web Search endpoint.
- `SearchEngineType.CUSTOM_ENGINE` (`"custom"`): requires a coroutine `run_func(query, max_results, as_string)`.

Example:

```python
from metagpt.tools import SearchEngineType
from metagpt.tools.search_engine import SearchEngine

engine = SearchEngine(engine=SearchEngineType.DUCK_DUCK_GO, proxy=None)
results = await engine.run("MetaGPT RAG", max_results=5, as_string=False)
```

Safety rules:

- Ask before network searches if the task has privacy, policy, or rate-limit implications.
- Never invent provider keys; surface required names and skip when missing.
- Use `ignore_errors=True` only when an empty search result is acceptable and logged.

## Use Browser and Scraping Tools Safely

`metagpt.tools.web_browser_engine.WebBrowserEngine` dispatches by `WebBrowserEngineType`:

- `PLAYWRIGHT`: browser types `chromium`, `firefox`, `webkit`; may try `python -m playwright install <browser>` if no executable is present.
- `SELENIUM`: browser types `chrome`, `firefox`, `edge`, `ie`; uses Selenium plus webdriver-manager unless `executable_path` is supplied.
- `CUSTOM`: pass a custom coroutine `run_func`.

Light scrape example:

```python
from metagpt.tools import WebBrowserEngineType
from metagpt.tools.web_browser_engine import WebBrowserEngine

browser = WebBrowserEngine(engine=WebBrowserEngineType.PLAYWRIGHT, browser_type="chromium")
page = await browser.run("https://example.com", per_page_timeout=20)
text = page.inner_text
```

Interactive browser tool:

- `metagpt.tools.libs.browser.Browser` is a registered tool tagged `web` and `browse`.
- It exposes `goto`, `click`, `type`, `hover`, `press`, `scroll`, `go_back`, `go_forward`, `tab_focus`, and `close_tab`.
- It maintains an accessibility tree and should be used as a standalone browsing task, observing between steps.

Web scraping helper:

- `metagpt.tools.libs.web_scraping.view_page_element_to_scrape(url, requirement, keep_links=False)` uses `Browser` to simplify HTML and optionally narrows content through `SimpleEngine.from_docs` if RAG imports are available.
- If RAG fails in that helper, simplified HTML is the fallback.

## Use Editor, Data, Shell, and Registered Library Tools

Importing `metagpt.tools` imports `metagpt.tools.libs`, which registers selected tools into `TOOL_REGISTRY`.

Useful library surfaces:

- `metagpt.tools.libs.editor.Editor`: file reading/editing/search helpers; `Editor.similarity_search()` requires RAG/index-repo imports.
- `metagpt.tools.libs.data_preprocess`: registered preprocessing tools such as fill-missing, scalers, encoders, and label encoding; requires pandas/numpy/sklearn-style data frames.
- `metagpt.tools.libs.feature_engineering`: registered feature engineering transforms; some tests skip tree-based selection because LightGBM is required.
- `metagpt.tools.libs.terminal.Terminal` and `Bash`: shell command execution surfaces; require user safety review before arbitrary commands.
- `metagpt.tools.libs.browser.Browser` and `web_scraping`: network/browser surfaces; require browser and network prerequisites.

Route Data Interpreter orchestration to `data-interpreter`; use this sub-skill for the individual tool dependencies, schema selection, and safety checks.

## Register Custom Tools

Use `ToolRegistry` directly when constructing a local registry, or the module-level `@register_tool` decorator to register global tools.

Decorator pattern:

```python
from metagpt.tools.tool_registry import register_tool

@register_tool(tags=["analysis", "csv"], include_functions=["run"])
class CsvProfiler:
    """Profile CSV columns and missing values."""

    def run(self, path: str) -> dict:
        """Return schema and missing-value summary."""
        ...
```

Manual registration:

```python
from metagpt.tools.tool_registry import ToolRegistry

registry = ToolRegistry()
registry.register_tool(
    tool_name="CsvProfiler",
    tool_path="tools/csv_profiler.py",
    tool_source_object=CsvProfiler,
    tags=["analysis", "csv"],
)
tool = registry.get_tool("CsvProfiler")
```

Registration details:

- Tool schemas are generated from class/function docstrings and method signatures through `tool_convert` helpers.
- `include_functions` filters class methods exposed in the schema.
- `validate_tool_names([...])` accepts tool names, tags, paths to Python files/directories, and `ClassTool:method1,method2` filters.
- Invalid names/tags/methods are skipped with warnings, not hard failures.
- Avoid registering tools with unsafe side effects unless execution is explicitly gated.

## Recommend Tools

Tool recommenders live in `metagpt.tools.tool_recommend`:

- `ToolRecommender(tools=[...], force=False)`: base class; ranking uses an LLM to choose among recalled tools.
- `TypeMatchToolRecommender`: recalls by exact match between plan task type and tool tag.
- `BM25ToolRecommender`: recalls by BM25 over tool name, tags, and description; requires `rank_bm25` and `numpy`.
- `EmbeddingToolRecommender`: declared but not implemented.

Example:

```python
from metagpt.tools.tool_recommend import BM25ToolRecommender

recommender = BM25ToolRecommender(tools=["web scraping", "Browser", "Editor"])
recommended = await recommender.recommend_tools(context="scrape product names from a page", topk=3)
```

Operational notes:

- `tools=["<all>"]` uses every registered tool.
- `force=True` returns the specified tools without recall/rank when possible.
- LLM ranking may return malformed JSON; MetaGPT attempts repair, then falls back to recalled tools when needed.
- For deterministic or offline diagnostics, use `force=True` or inspect `validate_tool_names()` rather than calling `recommend_tools()`.
