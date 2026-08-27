# Optional Extras

Upsonic keeps many backends and integrations optional. Install the smallest extra set that matches the requested workflow.

## Common extras

| Extra | Typical workflows | Notes |
| --- | --- | --- |
| `mcp` | Model Context Protocol tools and servers | Required for `upsonic.tools.mcp`. |
| `models` | Provider SDKs and provider-specific model backends | Useful when a workflow uses non-base provider clients. |
| `embeddings` | Embedding providers | Needed for retrieval pipelines that embed documents or queries. |
| `loaders` | Document loaders and converters | Needed for RAG/document ingestion workflows. |
| `vectordb` | Vector database backends | Umbrella extra for Chroma, Qdrant, Milvus, Weaviate, Pinecone, FAISS, PGVector, and related tooling. |
| `storage` | Persistent session/memory backends | Umbrella extra for SQLite, Redis, PostgreSQL, MongoDB, and Mem0 storage. |
| `ocr` | OCR engines and PDF OCR support | Needed when extracting text from scanned or image-heavy documents. |
| `tools` | Web/search/data helper tools | Useful for tool-rich agents and orchestration workflows. |
| `web` | FastAPI/Celery server stack | Needed for CLI project serving and API deployment. |
| `custom-tools` and interface extras | Slack, Gmail, Discord, Mail, Telegram, WhatsApp, Notion, Jira, Drive, Apify, Crawlee, Firecrawl | Only install the integrations a workflow actually needs. |

## Installation reminders

- Use `python scripts/list_optional_extras.py` to inspect the bundled extras snapshot from this distillation.
- Use `python scripts/list_optional_extras.py --pyproject pyproject.toml` when you intentionally want to inspect a newer checkout.
- Prefer a targeted install such as `python -m pip install 'upsonic[mcp]'` or `python -m pip install 'upsonic[sqlite-storage]'` over installing every extra.
- Base installs are enough for import, signature inspection, CLI help, and many unit tests.
