# Local Loading

Use local loading for files and directories already present on disk. DeepSearcher loads them through the configured `file_loader`, splits resulting `Document` objects into chunks, embeds the chunks, and inserts them into the configured vector database collection.

## Public API

```python
deepsearcher.offline_loading.load_from_local_files(
    paths_or_directory,
    collection_name=None,
    collection_description=None,
    force_new_collection=False,
    chunk_size=1500,
    chunk_overlap=100,
    batch_size=256,
)
```

Behavior:

1. Reads global objects created by `init_config(config)`: `configuration.vector_db`, `configuration.embedding_model`, and `configuration.file_loader`.
2. If `collection_name is None`, uses `vector_db.default_collection`.
3. Normalizes the local collection name with `collection_name.replace(" ", "_").replace("-", "_")` before `init_collection` and `insert_data`.
4. Calls `vector_db.init_collection(dim=embedding_model.dimension, collection=normalized_name, description=collection_description, force_new_collection=force_new_collection)`.
5. Converts a string path into a one-item list.
6. For each path, raises `FileNotFoundError` if it does not exist; for directories calls `file_loader.load_directory(path)`, otherwise calls `file_loader.load_file(path)`.
7. Calls `split_docs_to_chunks(..., chunk_size=chunk_size, chunk_overlap=chunk_overlap)`.
8. Calls `embedding_model.embed_chunks(chunks, batch_size=batch_size)` and `vector_db.insert_data(collection=normalized_name, chunks=chunks)`.

## Safe Preflight

Before indexing, run the bundled preflight helper. It does not import or initialize DeepSearcher.

```bash
python scripts/validate_ingestion_inputs.py \
  --path docs/guide.pdf \
  --path notes/summary.md \
  --collection-name "Project-Knowledge" \
  --chunk-size 1500 \
  --chunk-overlap 100 \
  --batch-size 256
```

The helper previews `Project-Knowledge -> Project_Knowledge`, verifies every local path exists, checks URL shape if URLs are provided, and warns about suspicious chunking values.

## Configuration Pattern

Choose providers before `init_config(config)`. The default package configuration uses `PDFLoader`, OpenAI embeddings, and local Milvus Lite at `./milvus.db`.

```python
from deepsearcher.configuration import Configuration, init_config
from deepsearcher.offline_loading import load_from_local_files

config = Configuration()
config.set_provider_config("file_loader", "PDFLoader", {})
config.set_provider_config("vector_db", "Milvus", {"uri": "./milvus.db", "token": ""})
# Set the embedding provider in provider-configuration if the default OpenAIEmbedding is not desired.
init_config(config)

load_from_local_files(
    paths_or_directory=["docs/guide.pdf", "notes/summary.md", "notes/readme.txt"],
    collection_name="team_docs",
    collection_description="Team PDFs, Markdown, and plain text notes",
    force_new_collection=False,
)
```

## Loader Selection

| Loader | Good for | Key constraints |
| --- | --- | --- |
| `PDFLoader` | Simple PDF, Markdown, and plain text ingestion | Supports `.pdf`, `.md`, `.txt`. For PDFs it joins extracted page text with blank lines; scanned/image PDFs may need richer parsing. |
| `TextLoader` | Markdown and plain text only | Supports `.txt`, `.md`; no PDF parsing. |
| `JsonFileLoader` | JSON/JSONL records with one text field plus metadata | Constructor requires `text_key`. In this checkout its `supported_file_types` incorrectly returns `['txt', 'md']`, so directory traversal will not auto-pick `.json`/`.jsonl`; pass JSON files directly or use a custom wrapper. |
| `UnstructuredLoader` | Broad office/document formats and complex PDFs | Optional dependencies are heavy. Uses Unstructured API only when both `UNSTRUCTURED_API_KEY` and `UNSTRUCTURED_API_URL` are set; otherwise local processing. Writes transient processed output under the current working directory. |
| `DoclingLoader` | PDF, Office, Markdown, AsciiDoc, HTML/XHTML, CSV, and images via Docling | Requires Docling dependencies. It performs Docling hierarchical chunking first, then DeepSearcher chunking runs again during ingestion. |

## Mixed PDF/Markdown/Text Collection Without Accidental Overwrite

Use `PDFLoader` for a simple mixed PDF/Markdown/Text corpus. It supports `.pdf`, `.md`, and `.txt`, and directory traversal recursively loads files with matching suffixes.

```python
from deepsearcher.configuration import Configuration, init_config
from deepsearcher.offline_loading import load_from_local_files

config = Configuration()
config.set_provider_config("file_loader", "PDFLoader", {})
config.set_provider_config("vector_db", "Milvus", {"uri": "./milvus.db", "token": ""})
init_config(config)

sources = ["whitepapers/product.pdf", "docs/architecture.md", "notes/release.txt"]
load_from_local_files(
    paths_or_directory=sources,
    collection_name="product_knowledge",  # stored as product_knowledge
    collection_description="Product PDF, Markdown, and text knowledge base",
    force_new_collection=False,            # append/reuse rather than drop existing data
    chunk_size=1200,
    chunk_overlap=120,
    batch_size=128,
)
```

Hardening tips:

- Use one canonical collection spelling. Local loading turns spaces and hyphens into underscores, so `product knowledge`, `product-knowledge`, and `product_knowledge` all collide after normalization.
- Set `force_new_collection=True` only for a deliberate rebuild. If the collection already exists and `force_new_collection=False`, Milvus/Qdrant initialization returns without dropping the collection and new chunks are inserted.
- Do not run multiple local Milvus Lite ingesters against the same `./milvus.db` from the same working directory concurrently; use separate working directories or server Milvus when parallel ingestion is required.

## JSON/JSONL Direct File Pattern

`JsonFileLoader(text_key=...)` expects a JSON file containing a list of dictionaries or a JSONL file containing one dictionary per line. For each record it removes `text_key` into `page_content`, keeps the remaining keys as metadata, and adds `reference` with the file path.

```python
config = Configuration()
config.set_provider_config("file_loader", "JsonFileLoader", {"text_key": "body"})
init_config(config)

load_from_local_files(
    paths_or_directory=["records/articles.jsonl"],
    collection_name="articles",
    collection_description="Article body text with remaining JSON fields as metadata",
)
```

Validate the key before indexing:

```bash
python scripts/validate_ingestion_inputs.py --path records/articles.jsonl --json-text-key body
```

## Local Loading Boundaries

- Do not use this sub-skill for the CLI `load` command syntax; route to `cli-and-service`.
- Do not query immediately after loading in this sub-skill; route answer generation and retrieval to `rag-query`.
- Do not document or embed provider credentials here; use `provider-configuration` for credential matrices and provider-specific setup.
