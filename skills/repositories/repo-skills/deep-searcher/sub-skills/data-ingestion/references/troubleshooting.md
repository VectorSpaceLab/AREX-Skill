# Data Ingestion Troubleshooting

Use this reference for failures before or during `load_from_local_files(...)` and `load_from_website(...)`. Provider credential setup belongs in `provider-configuration`; CLI syntax belongs in `cli-and-service`; querying failures after successful indexing belong in `rag-query`.

## Preflight First

Run the bundled helper before expensive or credentialed ingestion:

```bash
python scripts/validate_ingestion_inputs.py \
  --path docs/guide.pdf \
  --url https://example.com/docs \
  --collection-name "Team Docs" \
  --chunk-size 1500 \
  --chunk-overlap 100 \
  --batch-size 256
```

It performs no network calls, no indexing, no credentials reads beyond ordinary environment access, and no DeepSearcher provider initialization.

## Common Local Loading Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `FileNotFoundError: ... does not exist` | A path passed to `load_from_local_files` does not exist. | Validate paths with the helper, expand globs yourself before calling the API, and pass absolute or process-cwd-correct relative paths. |
| Directory loads fewer files than expected | Loader `supported_file_types` filtering skipped extensions. | Choose a loader whose supported suffix list includes the files, or pass specific files directly. `JsonFileLoader` can read JSON/JSONL files passed directly but reports `txt`/`md` for directory traversal in this checkout. |
| PDF text is empty or poor quality | `PDFLoader` uses pdfplumber text extraction and may not handle scans, images, or complex layouts. | Use `UnstructuredLoader` or `DoclingLoader` if dependencies are available; otherwise OCR/preprocess outside DeepSearcher and load text/Markdown. |
| Unicode decode error for text/Markdown | `TextLoader` and `PDFLoader` read text with UTF-8. | Convert the file to UTF-8 or implement a custom loader outside this skill. |
| JSON load fails with `KeyError` | The selected `text_key` is absent in at least one record. | Validate with `--json-text-key`, inspect record schema, or normalize the JSON/JSONL before ingestion. |
| JSON file must contain list of dictionaries | `JsonFileLoader` expects a `.json` top-level list, not a single object. | Convert to list-of-dicts or JSONL. |
| Unstructured creates or removes `./pdf_processed_outputs` | `UnstructuredLoader` uses that cwd-relative transient output directory and clears it at initialization. | Run ingestion from a controlled working directory and avoid storing unrelated files in that directory. |
| Docling file rejected as unsupported | `DoclingLoader` checks extension against its supported list. | Convert to a supported format or use `UnstructuredLoader` if appropriate. |

## Common Web Loading Failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| FireCrawl authentication error or empty key failure | `FIRECRAWL_API_KEY` is missing or invalid. | Treat FireCrawl as optional/blocked until a key is supplied. Consider `JinaCrawler`, `Crawl4AICrawler`, `DoclingCrawler`, or local loading of downloaded content. |
| Import error mentioning `ScrapeOptions` or FireCrawl API types | This checkout imports `from firecrawl import FirecrawlApp, ScrapeOptions`; firecrawl-py 4.x may not match, while 2.16.5 worked in inspection. | Use a compatible firecrawl-py 2.x version or revise the crawler implementation in application code. Do not claim FireCrawl is verified on firecrawl-py 4.x. |
| Crawl is unexpectedly broad | `allow_backward_links=True`, high `max_depth`, or high `limit`. | Bound recursive crawls with `max_depth=1 or 2`, a small `limit`, and `allow_backward_links=False` unless the user explicitly wants broader crawl scope. |
| Jina crawler raises during configuration initialization | `JINA_API_TOKEN` and `JINAAI_API_KEY` are absent. | Configure credentials via `provider-configuration` or choose a different crawler. |
| Crawl4AI returns empty list | Browser setup or page rendering failed; implementation catches exceptions and logs an error. | Verify Crawl4AI browser setup, simplify to a single URL, or use FireCrawl/Jina/Docling depending on credentials and page type. |
| Docling URL processing raises `IOError` | Docling conversion failed for the URL or format. | Try downloading to a local supported file and use `DoclingLoader`, or switch crawler. |

## Collection Overwrite and Naming Problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Data appears in a collection with underscores | `load_from_local_files` normalizes spaces and hyphens to underscores. | Use explicit underscore names consistently, e.g. `team_docs`. |
| Local and web ingestion went to different collections | Local loading normalized the name, web loading did not. | Use a pre-normalized collection name for both APIs. |
| Existing collection disappeared | `force_new_collection=True` dropped it before indexing. | Only use `force_new_collection=True` for deliberate rebuilds; use `False` for appends. |
| Different experiments collide | Reused the same default collection `deepsearcher` or normalized names collided. | Give each corpus a unique explicit collection and description. |

## Chunking and Batching Problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Splitter error or pathological output | `chunk_overlap >= chunk_size`, zero/negative values, or very small chunks. | Use the helper. Keep `chunk_size > chunk_overlap >= 0`; start with `1500/100`. |
| Embedding API rate limit or memory pressure | `batch_size` too high for backend. | Lower `batch_size` to 16-128 depending on provider limits. |
| Retrieval misses context | Chunks too small or overlap too low. | Increase `chunk_size` and overlap. Remember DeepSearcher also stores `metadata["wider_text"]` with a 300-character context window. |
| Retrieval returns bloated or imprecise chunks | Chunks too large or broad documents are poorly segmented. | Lower `chunk_size`, use a richer loader, or preprocess source documents. |

## Milvus and Vector DB Issues

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Local Milvus Lite DB lock or concurrent access error | Default `uri="./milvus.db"` is cwd-relative and local-file backed. Multiple processes can collide. | Use separate working directories/URIs per ingestion job or a standalone Milvus server for concurrent ingestion. |
| Local Milvus Lite smoke fails after dependency upgrade | Inspection found local Milvus Lite passed with `pymilvus==2.5.8` and `milvus-lite==2.5.1`; pymilvus 3.x or milvus-lite 3.x produced local DB smoke failures. | Pin compatible 2.5.x versions for local Lite workflows or verify server Milvus separately. |
| Unexpected remote Milvus connection | URI points to HTTP/HTTPS endpoint instead of local file path. | Confirm vector DB config before `init_config(config)`. |
| Azure Search ingestion call shape mismatch | Current `AzureSearch.insert_data` expects `documents: List[dict]`, not the same `(collection, chunks)` signature used by `load_from_*`. | Treat Azure ingestion as optional and verify with a smoke test before relying on it. |
| Oracle/Qdrant dependency import errors | Optional dependencies or service credentials are missing. | Route credential/dependency setup to `provider-configuration`; verify vector DB readiness before ingestion. |

## Initialization Side Effects

`init_config(config)` creates the LLM, embedding model, file loader, web crawler, vector DB, and default RAG agents. This means a local path typo can be hidden behind an earlier provider error if you initialize too soon.

Best practice:

1. Validate paths, URLs, chunk settings, and collection normalization with `scripts/validate_ingestion_inputs.py`.
2. Decide loaders, crawlers, embedding provider, and vector DB.
3. Ensure optional credentials/dependencies are available.
4. Call `init_config(config)`.
5. Call the ingestion API.

Compatibility warning: the console script `deepsearcher` maps to `deepsearcher.cli:main`, but CLI help initializes providers before argparse, so help can fail without credentials or vector DB readiness. Use Python API validation for ingestion planning and route CLI usage to `cli-and-service`.
