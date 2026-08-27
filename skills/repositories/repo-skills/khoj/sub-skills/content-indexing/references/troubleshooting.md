# Content Indexing Troubleshooting

Use this guide to isolate whether a failure is in upload/configuration, parsing, database indexing, or later search retrieval. Route server startup, auth, API-key, and deployment setup to `deployment-api`; route semantic result quality and query filters to `search-retrieval`.

## Request Is Rejected Before Indexing

Symptoms:

- HTTP 403 on `/api/content`.
- HTTP 422 for invalid `t` values.
- HTTP 400 with `Too many files. Maximum number of files is 1000.`
- HTTP 429 with a data-limit message.

Checks:

- Confirm the request has `Authorization: Bearer <api-key>` unless the server is anonymous.
- Confirm `t` is one of `all`, `org`, `markdown`, `pdf`, `plaintext`, `image`, `docx`, `github`, or `notion`.
- Keep multipart batches at or below 1000 files.
- If billing limits are enabled, keep incoming data below 50 MB for normal users or 100 MB for subscribed users, and total indexed data below the applicable total limit.
- Use `POST /api/content/convert` only for conversion previews; it skips files over 10 MB.

## Files Are Accepted But Not Indexed

Common causes:

- Multipart field name is not `files`.
- The part has no filename.
- MIME type maps to `other` and is skipped.
- Text upload lacks a usable encoding and downstream parsing gets bytes where it expects text.
- `t` selects a different type from the uploaded files.
- The uploaded file content is empty, which can be treated as a deletion marker.

Fixes:

- Send repeated `files` fields with explicit filename and MIME type.
- Use `text/markdown` for Markdown and `text/org` for Org; do not rely on generic `text/plain` for those formats.
- Add `charset=utf-8` to text MIME types for custom clients when possible.
- Use `PATCH /api/content?t=all` for mixed uploads, or match `t` to the uploaded type.
- Prefer explicit delete endpoints instead of uploading empty files when deletion is intended.

## Empty or Deleted Files

Khoj uses empty upload content as a deletion signal in multiple paths:

- Markdown, Org, and plaintext processors treat `""` as a delete marker.
- PDF, DOCX, and image processors treat `b""` as a delete marker.
- The billing limiter also deletes entries for zero-byte upload filenames when billing checks are active.

If a file disappeared unexpectedly, inspect whether the client sent a zero-byte multipart part during sync. For deliberate deletion, use `DELETE /api/content/file?filename=...` or `DELETE /api/content/files` with a JSON body.

## Unsupported Content Type

Symptoms:

- Successful HTTP 200 but filename is absent from the response body.
- Logs mention skipped unsupported type.
- `/api/content/files` does not show the file after upload.

Checks:

- Verify MIME type maps to a supported type.
- For code/text files, ensure the bytes are detectable as text/code by Magika or send a safer text MIME type.
- For images, use `.png`, `.jpg`, `.jpeg`, or `.webp` filenames and matching image MIME types.
- For DOCX, use the OpenXML DOCX MIME type rather than generic zip/octet-stream.

## Parser Errors

Markdown/Org:

- Very small `max_tokens` can force recursive splitting; check heading ancestry and expected line starts with the helper.
- Non-incremental heading levels are supported, but malformed headings may produce unexpected splits.
- Org heading-only entries are ignored by default; set `index_heading_entries=True` only in parser-only diagnostics if you need to inspect them.

Plaintext/HTML/XML:

- HTML/XML parsing depends on BeautifulSoup parser behavior and strips markup to visible text.
- One plaintext file becomes one entry before token splitting, so large files split later via `TextToEntries.split_entries_by_max_tokens()`.

PDF/DOCX:

- Extraction depends on document loader support and file validity.
- Encrypted, malformed, scanned, or image-only PDFs can extract empty text.
- DOCX features unsupported by the loader may be lost.
- Use `/api/content/convert` to preview extracted text before indexing.

Image:

- OCR requires `rapidocr_onnxruntime`; without it, image files are skipped with a warning.
- Unsupported extensions are skipped even if the MIME type is image-like.
- OCR quality depends on image clarity and language support.

## GitHub Sync Fails

Symptoms:

- No GitHub entries after configuring `/api/content/github`.
- Logs mention rate limit, unable to download repo, or private repo access.
- Repository appears configured but indexing produces no files.

Checks:

- Payload shape must include `repos`, each with `owner`, `name`, and optional `branch`.
- If private repos are needed, use a classic PAT with repository access.
- Confirm the configured branch exists; default branch is `master` if omitted.
- Confirm the repository contains Markdown, Org, or text/code blobs; binary-only repositories may index nothing.
- If rate limited, provide a PAT or wait for GitHub rate limit reset.
- Remember that GitHub indexing runs from stored config when no client documents are sent to the content configuration path.

## Notion Sync Fails

Symptoms:

- `/api/content/notion` accepts the token but no pages appear.
- Logs mention missing title, empty search results, or Notion API errors.
- Some blocks are missing from indexed content.

Checks:

- Token must be a Notion integration token.
- The integration must be shared with the pages/workspaces to index.
- The processor discovers pages through Notion search; inaccessible pages do not appear.
- Page title must be in a recognized title field such as `title`, `Title`, `Name`, `Page`, or `Event`.
- Databases and unsupported block types are not fully indexed by the current processor path.
- Links are flattened into simple anchor strings; rich Notion structures can lose formatting.

## Stale Index Visibility

If upload/indexing succeeds but search results look stale:

- Confirm `/api/content/files?truncated=false` shows the updated raw file object.
- Confirm `/api/content/types` includes the expected content type.
- Confirm the client used `PUT` for full regeneration or `PATCH` for incremental sync intentionally.
- Remember that `configure_content` invalidates the per-user query cache after indexing.
- Use `search-retrieval` to debug embeddings, search model config, query filters, reranking, and thresholds.
- Re-index if the search model changed, because old embeddings may not match the new model.

## Safe Local Debug Checklist

1. Reproduce parser output without database writes:

```bash
python skills/khoj/sub-skills/content-indexing/scripts/parse_content_fixture.py --type markdown --text '# A\nBody' --name debug.md
```

2. Validate multipart shape with one tiny file and a matching MIME type.
3. Use `/api/content/convert` for PDF/DOCX extraction preview before indexing.
4. Use explicit delete endpoints for deletes rather than empty upload files.
5. Check remote-source config payload separately from the later indexing trigger.
6. Move to `search-retrieval` only after entries/file objects are visibly updated.
