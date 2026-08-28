---
name: ingest-sources
description: "Guides DocsGPT file, audio, remote, and connector ingestion; parsing, chunking, worker queues, source configuration, status checks, and re-ingestion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Ingest Sources

Use this sub-skill to create and maintain searchable DocsGPT sources from local files, audio, remote content, object storage, or authenticated knowledge connectors.

## Identify the input path

- **Uploaded documents/images/audio**: read [formats, loaders, and connectors](references/formats-loaders-connectors.md), then [ingestion workflows](references/ingestion-workflows.md).
- **URL, sitemap, crawler, GitHub, Reddit, or S3 source**: use the remote-loader guidance in those references.
- **Google Drive, SharePoint, or Confluence**: use connector OAuth/session guidance; never treat a connector token as ordinary source metadata.
- **Chunking or source-level behavior**: read [source configuration](references/source-configuration.md) and validate a proposed object offline.
- **Stuck/empty/failed source**: read [troubleshooting](references/troubleshooting.md).

## Core pipeline

1. Validate size, extension/MIME, credentials, and URL policy before upload/fetch.
2. Create the source or enqueue the remote/connector ingestion task.
3. Poll the returned task id until terminal state. A task id is not proof of success.
4. Parse into normalized documents; apply the source's ingest-time chunking strategy.
5. Embed chunks and write them to the selected vector store while source metadata stays in Postgres.
6. Verify source status, file list/chunk count, and one bounded retrieval query.
7. Re-ingest when bake-time chunking or embeddings changed.

## Supported source families

At this snapshot, source files include RST, Markdown, PDF, text, DOCX, CSV, EPUB, HTML/MDX, JSON, XLSX, PPTX, PNG/JPEG images, and common audio formats handled by STT. Remote loader registry keys are `url`, `sitemap`, `crawler`, `reddit`, `github`, and `s3`. Authenticated connector keys are `google_drive`, `share_point`, and `confluence`.

OCR, image parsing, local speech recognition, and some document formats have optional model/system dependencies. Prove them with a tiny non-sensitive fixture before bulk ingestion.

## Source configuration preflight

Save the proposed source config as JSON or YAML, then run:

```bash
python scripts/validate_source_config.py source-config.json
```

The helper checks strict keys, ranges, strategy/retriever names, pre-screen coherence, and GraphRAG fields. It does not write a source.

Then apply through the source config API or UI. The important timing rule is:

- `retrieval.*` is query-time and applies to the next query;
- `chunking.*` is ingest-time and requires re-ingestion of existing content.

`kind` cannot be changed through the generic config patch; use the dedicated Wiki or GraphRAG action.

## Queue and worker decisions

- A bare Celery worker consumes all configured queues.
- Heavy parsing can use the dedicated `parsing` queue; align `DOCUMENT_PARSE_QUEUE` and run a matching worker.
- Enforce compressed/decompressed size and archive-entry limits before parsing.
- Keep OCR and large-parser memory bounded; recycle worker children rather than allowing unbounded native heap growth.
- Connector sync and re-ingestion are stateful operations. Confirm source ownership/team permissions and expected replacement behavior.

## Validate the result

For every source, record:

- source id/type and owner/team scope;
- terminal task status and error, if any;
- parsed file/chunk count;
- chosen chunking strategy and effective token bounds;
- embedding model/vector store identity;
- one query with expected source citation;
- whether re-ingestion is required after a configuration change.

## Cross-skill routes

- Ranking, embeddings, vector-store choice, hybrid/GraphRAG: [retrieval-vectorstores](../retrieval-vectorstores/SKILL.md)
- Attachment upload followed by chat: [api-client-operations](../api-client-operations/SKILL.md)
- Worker/service deployment: [deploy-configure](../deploy-configure/SKILL.md)
- Read Document in workflows: [tools-integrations](../tools-integrations/SKILL.md)
