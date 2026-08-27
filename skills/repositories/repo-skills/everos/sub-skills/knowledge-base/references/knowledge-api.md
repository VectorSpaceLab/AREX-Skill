# Knowledge API Reference

## Upload: `POST /api/v2/knowledge/documents`

Multipart form fields:

| Field | Required | Notes |
|---|---|---|
| `file` | yes | Uploaded source document. |
| `title` | yes | Human-readable title, must contain a word character. |
| `source_type` | no | Provenance label such as `file` or `url`. |
| `category_id` | no | If set, bypasses LLM category selection. |
| `app_id`, `project_id` | no | Defaults `default`; scope the knowledge root. |

Requires embedding and rerank capability. Extraction also uses the LLM-backed knowledge extractor. Oversized uploads are rejected based on `knowledge.max_upload_bytes`.

## Replace: `PUT /documents/{doc_id}`

Same multipart shape as upload. The service backs up the existing Markdown directory, writes the replacement, and restores the backup if extraction fails.

## Patch: `PATCH /documents/{doc_id}`

JSON body fields:

```json
{"title":"New title","category_id":"Technology","app_id":"default","project_id":"default"}
```

Metadata patch does not require embedding or rerank. Category changes move the document directory and rewrite topic category frontmatter.

## Delete/list/detail/topic/category

These read or clean up existing Markdown/SQLite state and intentionally remain reachable when providers are missing:

```bash
GET    /api/v2/knowledge/documents?page=1&page_size=20
GET    /api/v2/knowledge/documents/{doc_id}
GET    /api/v2/knowledge/topics/{topic_id}
GET    /api/v2/knowledge/categories
DELETE /api/v2/knowledge/documents/{doc_id}
```

`DELETE` returns `204` when the document does not exist or no topics were deleted; otherwise it returns a normal success envelope with `deleted_topics`.

## Search: `POST /api/v2/knowledge/search`

Request:

| Field | Notes |
|---|---|
| `query` | Required, 1..2000 chars. |
| `method` | `keyword`, `vector`, or `hybrid`; default `hybrid`. |
| `top_k` | 1..100, default 10. |
| `score_threshold` | Optional score filter. |
| `include_content` | Include full topic content in hits when true. |
| `app_id`, `project_id` | Scope; defaults `default`. |

Even `keyword` knowledge search currently passes the endpoint gate requiring embedding and rerank, because the knowledge retrieval pipeline embeds the query and reranks/enriches candidates.

Response hits include topic metadata, score, retrieval method, optional content, source, and parent document context.
