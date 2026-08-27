# RAG Clients and Loaders

CrewAI exposes two related RAG surfaces:

- Native provider-neutral RAG clients under `crewai.rag`, used by knowledge storage and direct vector-store workflows.
- `crewai_tools.RagTool`, a `BaseTool` wrapper that loads content, chunks it, embeds it, stores it, and answers queries through the native RAG client stack.

Use [embedding-and-storage.md](embedding-and-storage.md) for vector DB and embedding provider configuration details.

## Native RAG Client API

```python
from crewai.rag.chromadb.config import ChromaDBConfig
from crewai.rag.config.utils import clear_rag_config, get_rag_client, set_rag_config
from crewai.rag.qdrant.config import QdrantConfig

# ChromaDB is the default provider.
set_rag_config(ChromaDBConfig())
client = get_rag_client()

client.get_or_create_collection(collection_name="docs")
client.add_documents(
    collection_name="docs",
    documents=[{"content": "CrewAI enables collaborative AI agents."}],
)
results = client.search(
    collection_name="docs",
    query="collaborative agents",
    limit=3,
    score_threshold=0.35,
)

# Switch to Qdrant when the optional dependency and desired config are available.
set_rag_config(QdrantConfig())
qdrant_client = get_rag_client()
clear_rag_config()
```

Common client methods implemented by ChromaDB and Qdrant clients:

| Method | Purpose |
| --- | --- |
| `create_collection(...)` | Create a collection with provider-specific options. |
| `get_or_create_collection(collection_name=...)` | Ensure a collection exists. |
| `add_documents(collection_name=..., documents=[...])` | Add records shaped like `{"content": str, "doc_id": optional str, "metadata": optional mapping}`. |
| `search(collection_name=..., query=..., limit=..., metadata_filter=..., score_threshold=...)` | Return normalized search results with `id`, `content`, `metadata`, and `score`. |
| `delete_collection(collection_name=...)` | Remove a collection. |
| `reset()` | Reset provider state when supported. |

Use `register_rag_client_factory(provider, factory)` only at application startup when you need to override built-in `chromadb` or `qdrant` clients or register a new provider behind the same `BaseClient` interface.

## RagTool Quick Reference

```python
from crewai import Agent
from crewai_tools import RagTool

rag_tool = RagTool(
    collection_name="product_docs",
    similarity_threshold=0.6,
    limit=5,
)

rag_tool.add(path="docs/product_guide.txt", data_type="text_file")
rag_tool.add("Short inline policy text", data_type="text")

agent = Agent(
    role="Documentation Expert",
    goal="Answer questions from indexed local docs.",
    backstory="Uses only the local RAG collection provided for this task.",
    tools=[rag_tool],
)
```

`RagTool` fields:

| Field | Default | Notes |
| --- | --- | --- |
| `name` | `"Knowledge base"` | Model-facing tool name. |
| `description` | `"A knowledge base that can be used to answer questions."` | Override when a collection has a narrow domain. |
| `collection_name` | `"rag_tool_collection"` | Vector collection name used by the adapter. |
| `similarity_threshold` | `0.6` | Minimum score for `_run(...)` unless overridden per query. |
| `limit` | `5` | Maximum result count unless overridden per query. |
| `summarize` | `False` | Stored for adapter use; keep off unless summarization behavior is explicitly desired. |
| `config` | empty `RagToolConfig` | Defaults to ChromaDB; can specify `vectordb` and `embedding_model`. |
| `adapter` | auto-built `CrewAIRagAdapter` | Supply a custom adapter only when it implements the `Adapter` interface. |

`RagTool._run(query, similarity_threshold=None, limit=None)` returns a string beginning with `Relevant Content:` followed by adapter query results. Adding content calls loaders and vector storage; querying calls the vector client.

## RagTool Configuration

```python
from crewai_tools import RagTool
from crewai_tools.tools.rag.types import ProviderSpec, RagToolConfig, VectorDbConfig

vectordb: VectorDbConfig = {
    "provider": "qdrant",
    "config": {
        # QdrantConfig keyword arguments go here, such as options or vectors_config.
    },
}

embedding_model: ProviderSpec = {
    "provider": "openai",
    "config": {
        "model_name": "text-embedding-3-small",
        "dimensions": 1536,
    },
}

config: RagToolConfig = {
    "vectordb": vectordb,
    "embedding_model": embedding_model,
}

rag_tool = RagTool(config=config, collection_name="support_articles")
```

Supported vector DB providers in `RagToolConfig`: `chromadb` and `qdrant`. Unsupported names raise `ValueError` with the supported provider list.

`RagTool` validates embedding provider dicts through CrewAI's provider spec union and tries to report errors for the selected provider rather than showing every possible provider schema.

## Add Content API

`RagTool.add(...)` accepts positional content or keyword aliases:

```python
rag_tool.add("plain text", data_type="text")
rag_tool.add(path="docs/guide.pdf", data_type="pdf_file")
rag_tool.add(file_path="docs/config.json", data_type="json")
rag_tool.add(directory_path="docs", data_type="directory")
rag_tool.add(url="https://example.com/page", data_type="website")
rag_tool.add(github_url="https://github.com/org/repo", data_type="github")
rag_tool.add(youtube_url="https://www.youtube.com/watch?v=VIDEO_ID", data_type="youtube_video")
```

Accepted `data_type` values:

| Value | Typical source | Notes |
| --- | --- | --- |
| `file` | Local file path | Auto-detects by extension. |
| `pdf_file` | `.pdf` | Requires PDF parsing dependencies; URL PDFs trigger HTTP retrieval. |
| `text_file` | `.txt`, unknown existing text file | Reads local text. |
| `csv` | `.csv` | Structured chunker. |
| `json` | `.json` | Structured chunker. |
| `xml` | `.xml` | Structured chunker. |
| `docx` | `.docx` | Requires `python-docx`; URL DOCX triggers HTTP retrieval. |
| `mdx` | `.mdx` or `.md` | Markdown/MDX chunking. |
| `directory` | Local directory | Walks non-hidden files, skips many binary extensions and `__pycache__`. |
| `website` | HTTP(S) URL | Uses web page loader; network-bound. |
| `docs_site` | Documentation site URL | Uses HTTP retrieval and link extraction; network-bound. |
| `github` | GitHub repository URL | Uses GitHub API/client; optional token may be needed. |
| `youtube_video` | YouTube video URL | Requires transcript dependency and network retrieval. |
| `youtube_channel` | YouTube channel URL | Requires YouTube dependencies and network retrieval. |
| `mysql` | MySQL URI | Database-bound; requires `pymysql` and credentials. |
| `postgres` | PostgreSQL URI | Database-bound; requires PostgreSQL driver and credentials. |
| `text` | Raw string | Safest keyless input. |

If `data_type` is omitted, `RagTool` uses `DataTypes.from_content(...)`:

- Existing local files are mapped by extension.
- Existing directories map to `directory`.
- HTTP(S) URLs with known file extensions map to matching file loaders.
- GitHub URLs map to `github`; docs-like URLs map to `docs_site`; other URLs map to `website`.
- Other strings are treated as raw `text`.

## Loader Safety Boundaries

`RagTool.add(...)` validates file paths and URLs before loading:

- File paths are resolved against the current working directory by default and path traversal outside that directory is rejected unless the unsafe-path escape hatch is deliberately enabled by the application.
- `file://` URLs are rejected by URL validation. Pass an approved local file path instead.
- HTTP(S) URLs resolving to private/reserved IP addresses are rejected to reduce SSRF risk.
- Keyword aliases (`path`, `file_path`, `directory_path`, `url`, `website`, `github_url`, `youtube_url`) go through the same checks as positional inputs.

Safe default for local-only work:

```python
rag_tool = RagTool(collection_name="local_docs")
rag_tool.add("Project policy: no production deploys on Friday.", data_type="text")
rag_tool.add(path="knowledge/policy.txt", data_type="text_file")
```

Avoid these unless authorized:

- `website`, `docs_site`, `github`, `youtube_video`, and `youtube_channel` because they fetch remote content.
- `mysql` and `postgres` because they connect to databases and may read private data.
- Broad `directory` ingestion over large repositories unless include/exclude rules are scoped.

## Loader Behavior Highlights

- Text loader hashes raw text for source/doc IDs; text-file loader hashes file path plus content.
- Directory loader supports `recursive`, `include_extensions`, `exclude_extensions`, and `max_files` options. It ignores hidden files/directories by default and records per-file metadata and processing errors.
- Directory ingestion inside `CrewAIRagAdapter` silently skips files that cannot be processed; inspect collection counts and source metadata if expected files are missing.
- For a single file-like source, missing local files raise `FileNotFoundError` before vector insertion.
- Unsupported explicit `data_type` values raise `ValueError` listing valid values.
- `RagTool.add(data_type="file")` means auto-detect; it does not force one generic file loader.

## Relation to File and Tool Sub-Skills

- Use this reference for RAG ingestion and retrieval behavior.
- Use [../../files-and-multimodal/SKILL.md](../../files-and-multimodal/SKILL.md) for general file resolver, MIME, upload, and multimodal payload constraints.
- Use [../../tools-and-mcp/SKILL.md](../../tools-and-mcp/SKILL.md) for general `BaseTool` design and non-RAG tool selection.

## Source Evidence Notes

This reference distills CrewAI native RAG client APIs, `RagTool`, loader data types, adapter behavior, and loader tests into standalone guidance. Source repository docs and tests were used as evidence only; future agents should use the bundled guidance and scripts here instead of reopening source files.
