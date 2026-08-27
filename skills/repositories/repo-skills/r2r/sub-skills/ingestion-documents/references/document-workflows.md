# Document Workflows

## Ingest modes

Use `documents.create(...)` with one of these common inputs:

- `file_path` for local files
- `raw_text` for inline content
- `chunks` for pre-split chunk text
- `s3_url` for object storage inputs

Common options:

- `collection_ids` to attach the new document to one or more collections
- `metadata` for document-level metadata
- `ingestion_mode` for the documented mode choice (`fast`, `hi-res`, `ocr`, or `custom`)
- `ingestion_config` for mode-specific details
- `run_with_orchestration` when the server should process the task asynchronously

## Lifecycle helpers

- `documents.retrieve()`, `documents.list()`, `documents.list_chunks()`, `documents.list_collections()`
- `documents.download()`, `documents.download_zip()`, `documents.export()`
- `documents.append_metadata()`, `documents.replace_metadata()`, `documents.delete()`, `documents.delete_by_filter()`
- `collections.create()`, `collections.list()`, `collections.add_document()`, `collections.remove_document()`
- `collections.add_user()`, `collections.remove_user()`, `collections.list_documents()`, `collections.list_users()`
- `collections.retrieve_by_name()`, `collections.update()`, `collections.extract()`

## Example flow

```python
from r2r import R2RClient

client = R2RClient(base_url="http://localhost:7272")
doc = client.documents.create(
    file_path="example.pdf",
    collection_ids=["collection-id"],
    metadata={"source": "docs"},
    ingestion_mode="hi-res",
)
print(doc.results)
print(client.documents.list_chunks(doc.results.id).results)
```

## Keep the boundary clear

- If the user wants to search over the document after ingesting it, route to retrieval.
- If the user wants entity, relationship, or community extraction, route to graph workflows.
- If the user only needs server/provider setup to make ingestion succeed, route to server configuration.
