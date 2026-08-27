# Content API Reference

Khoj registers content ingestion endpoints under `/api/content`. They require an authenticated request unless the server is explicitly running in anonymous mode; use `deployment-api` for base URL, API-key creation, anonymous mode, deployment, and CORS details.

## Local Upload Indexing

- `PUT /api/content`: regenerate indexed content for the selected type. Existing entries of the processed type can be cleared before new entries are written.
- `PATCH /api/content`: incremental sync. New/changed entries are added, removed chunks for uploaded files are deleted, and explicitly empty files can delete existing entries.
- Query parameters:
  - `t`: one of `all`, `org`, `markdown`, `pdf`, `plaintext`, `image`, `docx`, `github`, or `notion`; defaults to `all`.
  - `client`: optional telemetry/client label.
- Multipart contract:
  - Use repeated multipart field name `files`.
  - Each part must include a filename and MIME type.
  - The server maps the MIME type/content to `IndexerInput` dictionaries keyed by filename.
- Successful response: HTTP 200 with a comma-separated string of accepted filenames. Unsupported file types are skipped rather than indexed.
- Failure response: HTTP 500 with body `Failed` if `configure_content` raises or returns false.

Example multipart shape:

```bash
curl -X PATCH "$KHOJ_URL/api/content?t=markdown&client=my-client" \
  -H "Authorization: Bearer $KHOJ_API_KEY" \
  -F 'files=@notes.md;type=text/markdown' \
  -F 'files=@journal.org;type=text/org'
```

## MIME Type Mapping

The upload helper maps MIME types before indexing:

| MIME/input signal | Content type |
| --- | --- |
| `text/markdown` | `markdown` |
| `text/org` | `org` |
| `application/pdf` | `pdf` |
| `application/msword` or OpenXML DOCX MIME | `docx` |
| `image/jpeg`, `image/png`, `image/webp` | `image` |
| Magika content group `text` or `code` | `plaintext` |
| Anything else | `other`, skipped by the indexer |

For text uploads with `charset=...`, the encoding is extracted from the MIME type and used to decode the uploaded bytes. If no encoding is provided for text-like content, code paths may expect bytes to already be compatible with downstream processing; prefer `charset=utf-8` for custom clients.

## Size and Count Limits

When billing limits are enabled, `ApiIndexedDataLimiter` applies before indexing:

- Incoming upload size limit: 50 MB for normal users, 100 MB for subscribed users.
- Total indexed-data limit: 50 MB for normal users, 500 MB for subscribed users.
- Excess returns HTTP 429 with a data-limit message.
- More than 1000 uploaded files returns HTTP 400: `Too many files. Maximum number of files is 1000.`
- `POST /api/content/convert` has its own 10 MB per-file conversion limit and silently skips oversized files.

## Conversion Endpoint

`POST /api/content/convert` converts uploaded documents to extracted text without indexing them.

- Multipart field name: `files`.
- Supported converter types: `org`, `markdown`, `pdf`, `plaintext`, `docx`.
- Unsupported types are skipped.
- Oversized files over 10 MB are skipped.
- PDF and DOCX conversion annotate extracted pages as `Page {index} of {name}:` before returning content.
- Response is JSON list of `{name, content, file_type, size}`.

Use this endpoint for document preview/extraction workflows. Use `PUT` or `PATCH` when the result should become searchable.

## Read and Delete Endpoints

- `GET /api/content/size`: returns `{"indexed_data_size_in_mb": number}`.
- `GET /api/content/types`: returns configured content types intersected with supported search types and always includes `all` when data exists or anonymous mode permits it.
- `GET /api/content/files?truncated=true&page=0`: returns paginated file objects, 10 per page, with `raw_text` truncated to 1000 characters by default.
- `GET /api/content/file?file_name=...`: returns one file object with full raw text; missing files return 404 JSON.
- `DELETE /api/content/file?filename=...`: deletes entries and the file object for one filename.
- `DELETE /api/content/files`: JSON body `{"files": ["path/a.md", "path/b.org"]}` deletes multiple files and returns `deleted_count`.
- `DELETE /api/content/type/{content_type}`: deletes all entries of a type, or all entries for `all`; type must be supported.
- `GET /api/content/{content_source}`: lists filenames by source, such as GitHub, Notion, or Computer source values.
- `DELETE /api/content/source/{content_source}`: deletes source config plus all entries for that source. GitHub and Notion source deletion also removes their stored config rows.

## Empty File and Deletion Semantics

- Text processors collect filenames whose uploaded content is empty (`""`) as deletion candidates.
- Binary processors collect filenames whose uploaded content is empty bytes (`b""`) as deletion candidates.
- During `process()`, deletion candidates are passed to `update_embeddings`, which deletes matching entries and file objects for those filenames.
- With billing checks enabled, zero-byte multipart files are also detected before indexing and matching entries are deleted early.

For explicit deletion, prefer `DELETE /api/content/file` or `DELETE /api/content/files` because the intent is clear and does not depend on MIME/content decoding.

## Remote Source Configuration

Remote sources are configured through JSON endpoints, not multipart local file payloads.

### GitHub

- `GET /api/content/github`: returns user config plus `current_config` with `pat_token` and `repos` when available.
- `POST /api/content/github`: body shape:

```json
{
  "pat_token": "ghp_or_classic_pat",
  "repos": [
    {"owner": "example-owner", "name": "example-repo", "branch": "main"}
  ]
}
```

`pat_token` may be omitted for public repositories, but private repositories and higher rate limits need a classic PAT. Repository objects use `owner`, `name`, and optional `branch` defaulting to `master`.

### Notion

- `GET /api/content/notion`: returns user config plus `current_config` with `token`.
- `POST /api/content/notion`: body shape:

```json
{"token": "secret_notion_integration_token"}
```

When a token is provided, the endpoint schedules background content configuration. The integration must be shared with the target pages/workspaces in Notion before Khoj can see them.

## How Remote Indexing Runs

The content configuration path indexes GitHub and Notion only when no client documents are included in the indexing call. For GitHub, Khoj downloads repository tree blobs, keeps Markdown, Org, and Magika-detected text/code files, and stores entries with source `GITHUB`. For Notion, Khoj searches pages through the Notion API, reads page blocks and children, and stores entries with source `NOTION`.

## Client Considerations

- Web uploads are good for one-off documents; desktop, Obsidian, and Emacs clients are designed for repeated sync.
- Desktop, Obsidian, and Emacs clients need the Khoj URL and API key unless the target server is anonymous.
- Client upload bugs usually show up as wrong field name, missing filename, wrong MIME type, too many files, data limit rejection, or unsupported content type.
- Ingestion success does not guarantee search results: search visibility depends on embedding generation, cache invalidation, search model configuration, and query filters. Use `search-retrieval` for that layer.
