# RAG, Vector Backends, and Storage

## RAG Surfaces

LangBot knowledge bases combine uploaded files, parsers, knowledge engines,
chunking/retrieval services, vector backends, and storage providers. HTTP/MCP
surfaces expose list/get/retrieve operations and selected management endpoints.

## Vector Backends

Config supports multiple vector stores, including Chroma, Qdrant, SeekDB,
Milvus, pgvector, and Valkey Search. Treat service-backed integrations as
optional unless the task changes that backend.

First checks:

- Manager selection and filter conversion unit tests for generic behavior.
- Backend-specific config keys and service reachability for live integration.
- Dimension compatibility between embedding model and vector index.
- Timeout settings for backends with strict default request timeouts.

## Storage

Storage supports local and S3-style providers with object read limits, cleanup,
retention, upload paths, and traversal protections. When changing file upload or
knowledge ingestion, verify file size limits, Workspace scoping, path traversal,
cleanup, and secret redaction.

## Parser/Engine Plugins

Some knowledge engines and parsers are plugin-provided. If a failure crosses
into plugin action calls or Runtime schemas, route to `plugin-box-skills` after
confirming RAG service inputs.
