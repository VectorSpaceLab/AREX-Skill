# Doc chat workflows

## 1) Local document RAG

Use this path for files you want to search repeatedly.

1. Build a `DocChatAgentConfig`.
2. Choose a vector store and parser settings.
3. Ingest documents or paths.
4. Ask questions with `llm_response(...)` or a `Task`.

```python
from langroid.agent.special.doc_chat_agent import DocChatAgent, DocChatAgentConfig
from langroid.parsing.parser import ParsingConfig, Splitter
from langroid.vector_store.qdrantdb import QdrantDBConfig

cfg = DocChatAgentConfig(
    vecdb=QdrantDBConfig(collection_name="docs", cloud=False),
    parsing=ParsingConfig(splitter=Splitter.MARKDOWN),
)
agent = DocChatAgent(cfg)
agent.ingest_doc_paths(["report.pdf", "notes.md"])
answer = agent.llm_response("What are the main risks?")
```

### Good defaults for this path

- keep `n_similar_chunks` and `n_relevant_chunks` small at first
- use `splitter=Splitter.MARKDOWN` for markdown-like content
- prefer `pypdfium2` for the lowest-friction PDF path
- enable `retain_context` only when follow-up accuracy matters more than tokens

## 2) URL ingestion and crawling

`DocChatAgent.ingest_doc_paths(...)` accepts URLs directly.
`URLLoader` chooses a crawler based on the crawler config.

- `TrafilaturaConfig`: default crawler, no API key
- `ExaCrawlerConfig`: API-backed extraction
- `FirecrawlConfig`: API-backed scraping/crawling
- `Crawl4aiConfig`: browser-style crawl with optional deep crawl

Use document URLs for direct parsing and plain URLs for web-page crawling.

```python
from langroid.parsing.url_loader import URLLoader, TrafilaturaConfig
from langroid.parsing.parser import ParsingConfig

loader = URLLoader(
    urls=["https://example.com/article"],
    parsing_config=ParsingConfig(),
    crawler_config=TrafilaturaConfig(),
)
docs = loader.load()
```

## 3) Direct file attachments

Use `FileAttachment` when you want to send a PDF or image straight to a multimodal model.
This is a different path from retrieval: it does not build a retrieval index.

```python
from langroid.parsing.file_attachment import FileAttachment

attachment = FileAttachment.from_path("report.pdf")
payload = attachment.to_dict("gpt-4o")
```

Use attachments when the question is local to one file.
Use parsing + ingestion when you want persistent retrieval over many files.

## 4) Retrieval tuning

Doc retrieval is a staged pipeline:

1. semantic search from the vector store
2. optional BM25 search
3. optional fuzzy search
4. fusion or reranking
5. optional context-window expansion
6. optional relevance extraction
7. final answer with citations

Main tuning knobs:

- `n_similar_chunks`
- `n_relevant_chunks`
- `n_neighbor_chunks`
- `use_bm25_search`
- `use_fuzzy_match`
- `use_reciprocal_rank_fusion`
- `cross_encoder_reranking_model`
- `rerank_diversity`
- `rerank_periphery`
- `hypothetical_answer`
- `chunk_enrichment_config`
- `relevance_extractor_config`
- `retrieve_only`

## 5) Lance RAG query planning

Use Lance RAG when your documents are really rows with filterable fields.
It adds a planner and critic around the retrieval agent.

```text
User query
  -> LanceQueryPlanAgent
  -> QueryPlanTool
  -> LanceDocChatAgent
  -> AnswerTool / QueryPlanAnswerTool
  -> QueryPlanCritic
  -> feedback loop
```

The query plan can contain:

- `filter`
- `query`
- `dataframe_calc`
- `original_query`

Rules that matter:

- `dataframe_calc` must be one line
- use `filter` only when the query explicitly needs field filtering
- remove filter-field names from the rephrased query
- `dataframe_calc` runs after the filter and retrieval step

## 6) Cleanup and persistence

For local Qdrant stores, call `close()` or use a context manager to release the lock.
Delete collections only when you really mean it.

```python
from langroid.vector_store.qdrantdb import QdrantDB, QdrantDBConfig

with QdrantDB(QdrantDBConfig(cloud=False, collection_name="demo")) as vecdb:
    ...
```

If a backend has persistent local storage, prefer a fresh directory when debugging a corrupt store.
