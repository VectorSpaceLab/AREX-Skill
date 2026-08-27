# Data Formats, Chunking, and Vector Store Implications

This reference summarizes ingestion components that determine what gets indexed: file loaders, web crawlers, chunk generation, collection metadata, batching, and vector database routing.

## Default Ingestion Configuration

DeepSearcher 0.0.2 ships with these default ingestion-related settings:

| Component | Default |
| --- | --- |
| File loader | `PDFLoader` with `{}` |
| Web crawler | `FireCrawlCrawler` with `{}` |
| Vector DB | `Milvus(default_collection="deepsearcher", uri="./milvus.db", token="root:Milvus", db="default")` |
| Embedding | `OpenAIEmbedding(model="text-embedding-ada-002")` |
| LLM | `OpenAI(model="o1-mini")` |
| Load settings | `chunk_size=1500`, `chunk_overlap=100` |
| Query max iterations | `max_iter=3` |

`init_config(config)` initializes **all** configured providers: LLM, embedding, file loader, web crawler, vector DB, and RAG agents. Validate inputs before initialization when possible so bad paths do not also trigger unrelated credential or vector DB failures.

## File Loader Matrix

| Loader | Constructor | Direct file behavior | Directory behavior | Supported formats in code |
| --- | --- | --- | --- | --- |
| `PDFLoader` | `PDFLoader()` | `.pdf` via pdfplumber; `.txt`/`.md` as UTF-8 text; returns one `Document` with `metadata={"reference": file_path}`. | Recursive traversal by suffix. | `pdf`, `md`, `txt` |
| `TextLoader` | `TextLoader()` | Reads UTF-8 text and returns one `Document` with `reference`. | Recursive traversal by suffix. | `txt`, `md` |
| `JsonFileLoader` | `JsonFileLoader(text_key)` | Reads `.json` list-of-dicts or `.jsonl` line-delimited dicts; pops `text_key` into `page_content`, leaves remaining fields as metadata, adds `reference`. | Base directory traversal uses `supported_file_types`; this checkout reports `txt`, `md`, so JSON files are not auto-selected by directory traversal. | Implementation reads `.json`/`.jsonl` when passed directly, but reports `txt`, `md`. |
| `UnstructuredLoader` | `UnstructuredLoader()` | Runs Unstructured ingest pipeline on the file path; returns documents from generated JSON elements. | Runs one pipeline for the directory. | Broad list including PDF, Office, images, HTML, Markdown, CSV/TSV, XML, and text. |
| `DoclingLoader` | `DoclingLoader()` | Converts a supported file with Docling and applies Docling `HierarchicalChunker`; returns one `Document` per Docling chunk with `reference` and `text` metadata. | Checks directory then recursively traverses supported suffixes. | PDF, DOCX, XLSX, PPTX, Markdown, AsciiDoc, HTML/XHTML, CSV, PNG/JPEG/TIFF/BMP. |

## Web Crawler Matrix

| Crawler | Constructor | `crawl_url` output | Key runtime requirements |
| --- | --- | --- | --- |
| `FireCrawlCrawler` | `FireCrawlCrawler(**kwargs)` | Markdown `Document` objects. Single scrape if no crawl options; recursive crawl if `max_depth`, `limit`, or `allow_backward_links` is passed. | `FIRECRAWL_API_KEY`, network, compatible `firecrawl-py` with `ScrapeOptions`. |
| `Crawl4AICrawler` | `Crawl4AICrawler(browser_config=None)` | Markdown plus metadata including success, status code, media, links, title, and author when available. | `crawl4ai` package and browser setup. |
| `JinaCrawler` | `JinaCrawler()` | Markdown from Jina Reader with response metadata. | `JINA_API_TOKEN` or `JINAAI_API_KEY`; raises at init without token. |
| `DoclingCrawler` | `DoclingCrawler(**kwargs)` | Docling hierarchical chunks as `Document` objects with `reference` and `text` metadata. | Docling dependencies; network access for URLs. |

## Chunk Generation

DeepSearcher converts loader/crawler `Document` objects into `Chunk` objects with:

```python
from deepsearcher.loader.splitter import split_docs_to_chunks, Chunk

chunks = split_docs_to_chunks(documents, chunk_size=1500, chunk_overlap=100)
```

`Chunk` fields:

| Field | Meaning |
| --- | --- |
| `text` | The chunk text sent to the embedding model and stored in vector DB. |
| `reference` | Source reference copied from document metadata key `reference`. |
| `metadata` | Remaining metadata plus DeepSearcher's context window. |
| `embedding` | Filled later by `embedding_model.embed_chunks(...)`. |

Splitting behavior:

1. Uses LangChain `RecursiveCharacterTextSplitter(chunk_size=..., chunk_overlap=...)`.
2. For each split document, finds the split text in the original document text.
3. Copies source metadata, pops `reference` into the `Chunk.reference`, and adds `metadata["wider_text"]`.
4. `wider_text` includes up to 300 characters before and after the chunk in the original document. RAG components can use this wider context later.

Practical tuning:

| Parameter | Default | Guidance |
| --- | --- | --- |
| `chunk_size` | `1500` | Larger chunks preserve context but cost more embedding tokens and may reduce retrieval precision. Smaller chunks improve pinpoint retrieval but can fragment definitions and tables. |
| `chunk_overlap` | `100` | Keep smaller than `chunk_size`; use 10-20% of `chunk_size` for prose. A zero overlap is acceptable for independent records. |
| `batch_size` | `256` | Passed to `embedding_model.embed_chunks`; reduce for memory/rate-limit issues, increase only when the embedding backend can handle it. |

Avoid `chunk_overlap >= chunk_size`; many splitters reject it or produce poor chunking. Use the validation helper before expensive indexing.

## Collection Metadata and Naming

`collection_description` is passed to vector DB collection creation. It is useful because RAG routing can list collections and read descriptions.

Local loading normalizes collection names:

```python
normalized = collection_name.replace(" ", "_").replace("-", "_")
```

Web loading passes `collection_name` as-is. To avoid cross-workflow mismatch, choose an explicit lowercase underscore name such as `product_knowledge` and use that exact value for local and web calls.

`force_new_collection` is passed to `vector_db.init_collection`:

- `False`: create collection only when absent, then insert new chunks.
- `True`: drop existing collection first when the vector DB implementation supports that behavior, then recreate it.

## Vector DB Routing at a High Level

| Vector DB | Ingestion implications |
| --- | --- |
| `Milvus` | Default and best-covered path. Local file URI such as `./milvus.db` uses Milvus Lite; HTTP URI uses server/Zilliz-style Milvus. Local Milvus Lite path is relative to the current working directory and can lock when reused concurrently. Hybrid mode adds sparse BM25 fields. |
| `Qdrant` | Optional alternative with local path, in-memory, host/port, URL, and API-key options. Creates collection when missing; uses UUID point IDs and payload keys `text`, `reference`, and `metadata`. |
| `AzureSearch` | Optional service path. Constructor requires endpoint, index name, API key, and vector field. Current implementation is less aligned with the common `BaseVectorDB.insert_data(collection, chunks)` call shape, so verify before relying on it for ingestion. |
| `OracleDB` | Optional service/database path requiring Oracle credentials, DSN, wallet/config fields, and table setup. Use only when Oracle vector infrastructure is intentionally selected. |

Route provider credentials and provider-specific config snippets to `provider-configuration`; this sub-skill only covers ingestion consequences.
