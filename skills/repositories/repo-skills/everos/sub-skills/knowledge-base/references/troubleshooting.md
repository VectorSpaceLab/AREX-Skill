# Knowledge Base Troubleshooting

## `PROVIDER_NOT_CONFIGURED` on upload or search

Knowledge upload/replace/search require both embedding and rerank. Configure `[embedding]` and `[rerank]`, then restart the server. Reads, delete, and patch should still work without those providers.

## Plain text works but PDF/HTML/Office fails

Plain UTF-8 Markdown/text/RST can bypass the parser. Non-text formats need parser support:

- Install `everos[multimodal]`.
- Configure `[multimodal]` for a vision/document-capable model.
- Install LibreOffice for Office formats.
- HTML is deliberately parsed/cleaned rather than treated as plain text.

## Upload returns unsupported format or invalid input

Check:
- The file is non-empty and decodes/parse to non-empty text.
- `title` contains at least one word character.
- Filename is not path traversal, empty, `.`/`..`, too long, or containing NUL.
- Upload size is under `knowledge.max_upload_bytes`.

## Search misses an uploaded document

Knowledge upload writes Markdown first, then cascade indexes topics. Check `/health` cascade readiness, retry with backoff, and confirm the same `app_id` and `project_id` are used for upload and search.

## Downgraded deployment cannot write new knowledge

This is expected without embedding+rerank. Use existing read/list/delete/patch routes to inspect or clean up old documents, or restore providers before writing/searching knowledge.
