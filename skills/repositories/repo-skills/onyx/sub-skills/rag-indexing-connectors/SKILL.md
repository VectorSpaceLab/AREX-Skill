---
name: rag-indexing-connectors
description: "Onyx connector, file-store, indexing, and OpenSearch operating
  knowledge for RAG/search ingestion, slim docs, permissions, and attachment
  handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# RAG Indexing Connectors

Use this sub-skill when you are changing Onyx connector classes, registry/factory wiring, document ingestion, slim-doc pruning, permission sync, file-backed sections, document indexing, or OpenSearch search behavior.

Keep generic API/DB/Celery mechanics in the backend-platform sub-skill, chat/agent tooling in agents-craft-and-tools, and connector form work in the web-frontend sub-skill.

Read [connectors.md](references/connectors.md) when you are changing connector interfaces, registry/factory wiring, DocumentSource, credentials, attachments, or connector-facing tests and UI touchpoints.
Read [indexing-and-search.md](references/indexing-and-search.md) when the change affects docfetching, chunking, embeddings, contextual RAG, file-backed sections, or OpenSearch retrieval.
Read [data-formats.md](references/data-formats.md) when you need the exact Document, Section, SlimDocument, failure, metadata, or file-id contracts.
Read [troubleshooting.md](references/troubleshooting.md) when validation, credential refresh, permissions, oversized/empty docs, embeddings, or OpenSearch scoring is failing.
Run [inspect_connector_registry.py](scripts/inspect_connector_registry.py) for a read-only registry and input-type smoke check after adding or renaming a source.

For a new connector, update the backend registry, the web connector metadata, docs, and tests together so the main pass, slim pass, and permission-sync pass stay aligned.
