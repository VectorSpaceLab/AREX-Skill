# Formats, Loaders, and Connectors

## Local source formats

| Family | Extensions / behavior | Main prerequisites |
|---|---|---|
| text/markup | `.txt`, `.md`, `.mdx`, `.rst`, `.html` | encoding and size limits; HTML is sanitized/normalized |
| office/ebook | `.docx`, `.pptx`, `.xlsx`, `.epub` | matching parser libraries; validate embedded/oversized content |
| tabular/data | `.csv`, `.xlsx`, `.json` | bounded bytes/rows; inspect schema and repeated headers |
| PDF | `.pdf` | Docling/PDF dependencies; optional image/OCR mode; possible system PDF tools |
| image | `.png`, `.jpg`, `.jpeg` | OCR or remote image parsing when text extraction is required |
| audio | `.wav`, `.mp3`, `.m4a`, `.ogg`, `.webm` | OpenAI STT credentials or optional local `faster_whisper` backend |

Do not infer actual parser success from extension alone. MIME, corruption, password protection, decompressed size, table complexity, language and model availability can change the result.

## Remote loaders

| Key | Input idea | Safety/behavior |
|---|---|---|
| `url` | one URL or URL list | subject to URL/SSRF policy; network fetch |
| `sitemap` | sitemap URL | potentially large fan-out; bound pages and domain |
| `crawler` | root URL | recursive network activity; constrain scope |
| `github` | repository URL | may require `GITHUB_ACCESS_TOKEN` for private/rate-limited content |
| `reddit` | JSON-like subreddit/query configuration | network/rate limits; stored config may be serialized JSON |
| `s3` | bucket/object configuration | requires storage credentials and object access |

Remote source metadata has historical shapes. URL-like loaders normalize common keys such as URL, URLs, repo URL, or legacy raw value; Reddit expects serialized JSON at the loader boundary; S3 accepts structured configuration. Prefer the current API/UI schema and preview normalized values before sync.

## Authenticated connectors

Supported connector ids:

- `google_drive`
- `share_point`
- `confluence`

Typical flow:

1. configure provider client id/secret and an exact callback base URI;
2. initiate connector auth for the current user;
3. complete callback and validate the stored session;
4. list/select files or spaces/sites;
5. enqueue ingestion or sync;
6. poll status and verify source ownership;
7. disconnect/revoke when access is no longer needed.

Tokens must be user-scoped, encrypted at rest, excluded from logs, and removed on disconnect. OAuth redirect URIs must match the browser-facing deployment, not an internal container hostname.

## Source versus attachment

A **source** is persisted and indexed for retrieval. An **attachment** is user-scoped input for a chat/workflow turn and is processed asynchronously before use. If a file should become reusable knowledge, ingest it as a source. If it is turn-specific, use the attachment flow in the API sub-skill.

## Safety boundaries

- Enforce file count, compressed and decompressed byte limits, and archive-entry limits.
- Do not crawl private/link-local/metadata endpoints by weakening URL validation.
- Confirm connector scopes and data residency before indexing enterprise content.
- Use non-sensitive tiny fixtures for parser/OCR/STT tests.
- Treat sync/re-ingest as data replacement work; communicate citation/source-id impacts.
