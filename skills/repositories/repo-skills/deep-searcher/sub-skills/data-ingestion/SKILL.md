---
name: data-ingestion
description: "Load local files, directories, and websites into DeepSearcher
  collections while validating inputs, loader choices, chunking, and vector
  database implications."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data Ingestion

Use this sub-skill when the user needs to load documents or web pages into a DeepSearcher collection, choose an ingestion loader or crawler, tune chunking and batching, prevent collection overwrite mistakes, or validate ingestion inputs before indexing.

Prefer DeepSearcher's Python APIs for ingestion workflows:

- Local files and directories: `deepsearcher.offline_loading.load_from_local_files(...)`
- Websites and web-readable documents: `deepsearcher.offline_loading.load_from_website(...)`
- Configuration: `deepsearcher.configuration.Configuration` and `deepsearcher.configuration.init_config(...)`

For command-line `deepsearcher load ...` syntax, route to `cli-and-service`. For provider credentials and model/provider selection, route to `provider-configuration`. For querying or retrieval after ingestion, route to `rag-query`. For evaluation dataset loading, route to `evaluation`.

## Fast Routing

| User intent | Read |
| --- | --- |
| Load PDFs, Markdown, text, JSON/JSONL, or a directory | [references/local-loading.md](references/local-loading.md) |
| Crawl or scrape websites into a collection | [references/web-loading.md](references/web-loading.md) |
| Pick PDF/Text/JSON/Unstructured/Docling loaders or tune chunks | [references/data-formats-and-chunking.md](references/data-formats-and-chunking.md) |
| Diagnose missing files, empty chunks, FireCrawl key errors, Milvus Lite locks, or version incompatibilities | [references/troubleshooting.md](references/troubleshooting.md) |
| Validate paths, URLs, chunk parameters, and collection-name normalization without indexing | [scripts/validate_ingestion_inputs.py](scripts/validate_ingestion_inputs.py) |

## Operating Checklist

1. Confirm the ingestion source type: local path(s), directory, URL(s), or a mix that should be split into separate local and web ingestion calls.
2. Confirm the intended collection name and overwrite policy. For local loading, names are normalized by replacing spaces and hyphens with underscores; set `force_new_collection=True` only when the existing collection should be dropped.
3. Choose the configured file loader or web crawler before calling `init_config(config)`. Do not initialize configuration just to validate user input.
4. Validate local paths, URL shape, chunk parameters, and optional JSON text key with the bundled helper when practical. The helper performs no indexing, no network calls, and no provider initialization.
5. Initialize DeepSearcher only after credentials, optional dependencies, and vector DB readiness are accounted for.
6. Load data, then route post-load search, retrieval, answer generation, and token accounting to `rag-query`.

## Minimal API Pattern

```python
from deepsearcher.configuration import Configuration, init_config
from deepsearcher.offline_loading import load_from_local_files

config = Configuration()
config.set_provider_config("file_loader", "PDFLoader", {})
config.set_provider_config("vector_db", "Milvus", {"uri": "./milvus.db", "token": ""})
init_config(config)

load_from_local_files(
    paths_or_directory=["docs/guide.pdf", "notes/summary.md", "notes/plain.txt"],
    collection_name="project_knowledge",
    collection_description="Project PDFs, Markdown, and text notes",
    force_new_collection=False,
    chunk_size=1500,
    chunk_overlap=100,
    batch_size=256,
)
```

Treat credentialed, networked, remote-service, and expensive ingestion as optional unless the user explicitly asks to run it and the required provider configuration is ready.
