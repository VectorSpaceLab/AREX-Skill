---
name: knowledge-base
description: "Use this sub-skill for EverOS knowledge document upload, topic
  taxonomy, knowledge search, provider gates, and knowledge storage
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# EverOS Knowledge Base

Use this sub-skill for EverOS knowledge documents and topics: uploading source files, replacing documents, patching metadata, listing documents/categories, reading topics, searching knowledge, and diagnosing knowledge provider gates.

## Read/run map

- Read [knowledge API](references/knowledge-api.md) for endpoint shapes, multipart fields, search request fields, and the provider gate contract.
- Read [storage and taxonomy](references/storage-and-taxonomy.md) for category/document/topic layout, `.taxonomy.md`, `_original/`, and Markdown source-of-truth behavior.
- Read [troubleshooting](references/troubleshooting.md) for missing embedding/rerank, parser, unsupported format, oversized upload, and downgrade scenarios.
- Run [knowledge_api_probe.py](scripts/knowledge_api_probe.py) against a running server. It defaults to safe read probes; writes require `--allow-write` and a file.

## Core routes

All routes are under `/api/v2/knowledge` for new integrations:

| Route | Capability |
|---|---|
| `POST /documents` | Upload and extract a knowledge document. |
| `PUT /documents/{doc_id}` | Replace a document atomically. |
| `PATCH /documents/{doc_id}` | Update title/category metadata. |
| `DELETE /documents/{doc_id}` | Delete a document. |
| `GET /documents` | Paginated document list. |
| `GET /documents/{doc_id}` | Document detail with topics. |
| `GET /topics/{topic_id}` | Full topic detail. |
| `GET /categories` | Taxonomy categories. |
| `POST /search` | Keyword/vector/hybrid knowledge retrieval. |

## Non-negotiable gate facts

Knowledge writes (`POST`, `PUT`) and knowledge search require both embedding and rerank capability. Reads, deletes, and metadata patch remain reachable if a deployment downgrades from Tier 3 to Tier 1/2. This lets users inspect, rename, recategorize, and clean up existing documents even when providers are no longer configured.

Plain UTF-8 Markdown/text/RST files can bypass the parser path. PDF, HTML, Office, image, and other non-text formats may require parser and multimodal LLM support; Office formats also need LibreOffice.
