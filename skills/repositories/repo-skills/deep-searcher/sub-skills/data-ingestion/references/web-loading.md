# Web Loading

Use web loading when the source is an HTTP or HTTPS URL. DeepSearcher delegates page fetching to the configured `web_crawler`, then applies the same chunking, embedding, and vector database insertion path as local loading.

## Public API

```python
deepsearcher.offline_loading.load_from_website(
    urls,
    collection_name=None,
    collection_description=None,
    force_new_collection=False,
    chunk_size=1500,
    chunk_overlap=100,
    batch_size=256,
    **crawl_kwargs,
)
```

Behavior:

1. Converts a single string URL into a one-item list.
2. Reads global objects created by `init_config(config)`: `configuration.vector_db`, `configuration.embedding_model`, and `configuration.web_crawler`.
3. Calls `vector_db.init_collection(dim=embedding_model.dimension, collection=collection_name, description=collection_description, force_new_collection=force_new_collection)`.
4. Calls `web_crawler.crawl_urls(urls, **crawl_kwargs)`.
5. Calls `split_docs_to_chunks(..., chunk_size=chunk_size, chunk_overlap=chunk_overlap)`.
6. Calls `embedding_model.embed_chunks(chunks, batch_size=batch_size)` and inserts into the selected collection.

Important difference from local loading: this function does **not** normalize `collection_name`; `None` is passed through to the vector database, whose implementations usually fall back to their `default_collection`. Use a safe explicit collection name to avoid surprises.

## Safe Preflight

Validate URL shape and chunk settings without network, credentials, or DeepSearcher initialization:

```bash
python scripts/validate_ingestion_inputs.py \
  --url https://example.com/docs \
  --collection-name web_docs \
  --chunk-size 1500 \
  --chunk-overlap 100 \
  --batch-size 256
```

The helper does not test that the URL is reachable; it only catches malformed schemes, missing hosts, and invalid local/chunk options.

## Crawler Selection

| Crawler | Good for | Credential/dependency implications | Notes |
| --- | --- | --- | --- |
| `FireCrawlCrawler` | Managed scrape/crawl service and recursive website ingestion | Requires `FIRECRAWL_API_KEY`; network service. | Supports single-page scrape by default and recursive crawl when any of `max_depth`, `limit`, or `allow_backward_links` is passed. This checkout imports `firecrawl.ScrapeOptions`; firecrawl-py 4.x may fail while firecrawl-py 2.16.5 worked in inspection. |
| `Crawl4AICrawler` | Browser-rendered pages and JavaScript-heavy content | Requires `crawl4ai` and its browser setup. | Accepts `browser_config` in provider config. `crawl_kwargs` are not used by the implementation. |
| `JinaCrawler` | Jina Reader extraction into Markdown | Requires `JINA_API_TOKEN` or `JINAAI_API_KEY`; network service. | Raises during crawler initialization when no token exists. |
| `DoclingCrawler` | Web-readable PDFs, Markdown, and structured documents | Requires Docling dependencies; may fetch network content through Docling. | Produces Docling hierarchical chunks first, then DeepSearcher chunking runs again. |

## FireCrawl Patterns

Single-page scrape:

```python
from deepsearcher.configuration import Configuration, init_config
from deepsearcher.offline_loading import load_from_website

config = Configuration()
config.set_provider_config("web_crawler", "FireCrawlCrawler", {})
config.set_provider_config("vector_db", "Milvus", {"uri": "./milvus.db", "token": ""})
init_config(config)

load_from_website(
    urls="https://example.com/overview",
    collection_name="example_overview",
    collection_description="Single-page scrape from example.com overview",
    force_new_collection=False,
)
```

Recursive crawl with bounded scope:

```python
load_from_website(
    urls="https://example.com/docs",
    collection_name="example_docs",
    collection_description="Bounded documentation crawl",
    force_new_collection=True,
    max_depth=2,
    limit=20,
    allow_backward_links=False,
)
```

`FireCrawlCrawler` behavior:

- If `max_depth`, `limit`, and `allow_backward_links` are all omitted, it calls `scrape_url(url=url, formats=["markdown"])`.
- If any of those options is provided, it calls `crawl_url(...)` with defaults `limit=20`, `max_depth=2`, `allow_backward_links=False`, and `ScrapeOptions(formats=["markdown"])`.
- Returned documents use Markdown page content and metadata with a `reference` derived from the crawled URL or metadata URL.

## Missing FireCrawl API Key and Alternatives

When the user requests FireCrawl but no key is available:

1. Do not treat the workflow as verified. Mark FireCrawl ingestion as optional/blocked on `FIRECRAWL_API_KEY`.
2. If a single public URL is enough and Jina credentials are available, consider `JinaCrawler`.
3. If JavaScript rendering is required and browser dependencies are prepared, consider `Crawl4AICrawler`.
4. If the URL points to a PDF/Markdown/HTML document and Docling dependencies are available, consider `DoclingCrawler`.
5. If the user can download the page or document outside DeepSearcher, switch to local loading with `PDFLoader`, `TextLoader`, `UnstructuredLoader`, or `DoclingLoader`.

Example fallback sketch:

```python
config = Configuration()
config.set_provider_config("web_crawler", "DoclingCrawler", {})
config.set_provider_config("file_loader", "DoclingLoader", {})
config.set_provider_config("vector_db", "Milvus", {"uri": "./milvus.db", "token": ""})
init_config(config)

load_from_website(
    urls=["https://example.com/manual.pdf", "https://example.com/guide.md"],
    collection_name="example_docs_docling",
    collection_description="Docling-based URL document crawl",
)
```

## Collection and Overwrite Safety

- Unlike local loading, web loading does not replace spaces or hyphens in `collection_name` before `init_collection`; choose a collection name already compatible with the selected vector DB.
- `force_new_collection=True` can drop an existing collection before recreating it. Use it only for deliberate rebuilds.
- For mixed local and web sources, run two ingestion calls into the same explicit safe collection name, but keep `force_new_collection=True` only on the first rebuild call and `False` on subsequent append calls.

## Web Loading Boundaries

- Provider credential matrices and environment variable inventories belong in `provider-configuration`.
- CLI command syntax belongs in `cli-and-service`.
- Query, retrieve, and RAG behavior after ingestion belongs in `rag-query`.
