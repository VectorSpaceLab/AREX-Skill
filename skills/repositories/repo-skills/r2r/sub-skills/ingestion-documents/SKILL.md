---
name: ingestion-documents
description: "Use R2R document ingestion, metadata, filters, exports, and
  collection/document lifecycle workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Ingestion Documents

Use this sub-skill when the user needs to ingest files, raw text, chunks, or S3 content; edit metadata; build filters; or manage documents, chunks, and collections.

## What it owns

- `documents.create(...)` with `file_path`, `raw_text`, `chunks`, or `s3_url`
- ingestion mode and orchestration choices
- document list/retrieve/download/export/delete flows
- metadata replace/append and delete-by-filter flows
- collection membership, document lists, and collection extraction setup
- chunk and collection listing that is part of ingestion lifecycle work

## Start here

```python
from r2r import R2RClient

client = R2RClient(base_url="http://localhost:7272")
result = client.documents.create(raw_text="Hello from R2R", metadata={"title": "demo"})
print(result.results)
```

## Route out when the work becomes another topic

- Search, retrieval, or RAG on ingested content: `../retrieval-rag/SKILL.md`
- Graph extraction or graph CRUD after ingestion: `../graph-workflows/SKILL.md`
- Server/provider setup needed to make ingestion work: `../server-configuration/SKILL.md`

## Bundled assets

- `references/document-workflows.md`
- `references/data-formats-and-filters.md`
- `references/troubleshooting.md`
- `scripts/ingestion_payload_builder.py`
