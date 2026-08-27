---
name: content-indexing
description: "Ingest, convert, parse, and manage user content in Khoj through
  /api/content, local parsers, and remote source configuration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Content Indexing

Use this sub-skill when a task touches Khoj content ingestion, conversion, parser behavior, file object/entry management, or client sync payloads. It is focused on how content reaches the index; route semantic query filters, ranking, reranking, and result interpretation to `search-retrieval`, and route server URL, auth, deployment, migrations, or API-key setup to `deployment-api`.

## Route Here For

- Implementing or debugging `/api/content` `PUT`, `PATCH`, `DELETE`, `GET`, `/convert`, `/github`, or `/notion` behavior.
- Building client upload/sync flows for Markdown, Org, PDF, DOCX, plaintext/HTML/XML, images, GitHub, or Notion content.
- Understanding parser entry shape: `raw`, `compiled`, `heading`, `file`, `uri`, and `corpus_id`.
- Diagnosing upload limits, unsupported MIME types, empty-file deletion semantics, stale index visibility, remote-source credentials, OCR/PDF/DOCX extraction, or parser failures.

## Start With

- `references/content-api.md` for endpoint contracts, multipart payloads, auth/client notes, delete/update/convert flows, and remote-source config.
- `references/parser-reference.md` for parser classes, static methods, chunking, line-number URIs, entries, deletion markers, and safe parser-only usage.
- `references/data-formats.md` for supported MIME types, parser examples, and fixture-style tiny payloads.
- `references/troubleshooting.md` for practical failures and how to separate ingestion problems from search visibility problems.
- `scripts/parse_content_fixture.py` to parse tiny Markdown, Org, or plaintext content into JSON without database writes.

## Safe Workflow

1. Confirm whether the caller is uploading local files, configuring a remote source, converting documents, deleting indexed data, or inspecting parser output.
2. For local uploads, use multipart field name `files`, include a meaningful filename, and set a MIME type that maps to a supported content type.
3. For remote sources, first store source credentials/config through `/api/content/github` or `/api/content/notion`; then trigger indexing through the normal content configure/update path with no client documents.
4. For parser-only debugging, call static extraction methods or the bundled helper; do not call `process()` unless a real Khoj user/database/search model context is intended.
5. After successful indexing, use `search-retrieval` when validating query behavior, because ingestion success only proves entries were accepted and embeddings/cache were refreshed.

## Important Boundaries

- `/api/content` indexing writes database entries and file objects; parser static methods do not.
- `PUT /api/content` regenerates selected content, while `PATCH /api/content` syncs incrementally.
- Empty uploaded content is treated as deletion input by processors and, when billing limits are active, by the upload limiter.
- The console script `khoj --help` can trigger server startup side effects in this repo; for parser-only CLI checks import `khoj.utils.cli.cli` or run the bundled helper instead.
