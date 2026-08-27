# Data Formats

Khoj accepts local uploads through `/api/content` and remote content through GitHub/Notion configuration. This reference gives tiny, self-contained examples and parser expectations without relying on repository fixtures.

## Supported Local Upload Types

| Type | Filename examples | MIME type to send | Parser |
| --- | --- | --- | --- |
| Markdown | `notes.md`, `readme.markdown` | `text/markdown` | `MarkdownToEntries` |
| Org | `journal.org` | `text/org` | `OrgToEntries` |
| PDF | `paper.pdf` | `application/pdf` | `PdfToEntries` |
| DOCX | `brief.docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `DocxToEntries` |
| Plaintext/code | `notes.txt`, `page.html`, `data.xml`, source files | `text/plain` or any Magika-detected text/code upload | `PlaintextToEntries` |
| Image OCR | `scan.png`, `photo.jpg`, `image.webp` | `image/png`, `image/jpeg`, `image/webp` | `ImageToEntries` |

The server primarily trusts MIME type for Markdown, Org, PDF, DOCX, and images. For generic text/code, it falls back to Magika content detection and maps text/code to `plaintext`.

## Markdown Fixture

Input:

```markdown
Intro before headings
# Project Alpha
Status update
## Risks
Budget risk
# Project Beta
Done
```

Expected parser behavior:

- Intro text can become its own entry when token limits force splitting.
- Child entries include heading ancestry, such as `# Project Alpha\n## Risks`.
- `compiled` includes the filename as a top-level heading context.
- Local `uri` values include `file://...#line=N` where `N` points to the source section start.

## Org Fixture

Input:

```org
Intro before entries
* Project Alpha
Body line
** TODO Follow up :work:
SCHEDULED: <2026-07-01 Wed>
Details
* Empty heading
```

Expected parser behavior:

- Intro text can be indexed.
- Heading ancestry is reflected in compiled text, usually as filename plus ancestor trail.
- TODO state, tags, scheduled/closed metadata, and body text are folded into compiled text.
- Heading-only entries are ignored by default unless `index_heading_entries=True` is used by the parser caller.

## Plaintext, HTML, and XML Fixture

Plaintext input:

```text
2026-06-30 Journal Entry
Met with design team about search onboarding.
```

HTML input:

```html
<html><body><h1>Meeting</h1><p>Discussed onboarding.</p></body></html>
```

Expected parser behavior:

- Plaintext becomes one entry before chunking.
- HTML/XML filenames are stripped to visible text with line separators.
- `compiled` is filename plus raw/extracted text.
- Plaintext chunking uses `raw_is_compiled=True`, so chunk `raw` mirrors the chunk text after splitting.

## PDF and DOCX Fixtures

Use real binary uploads for indexing or conversion. For conversion preview:

```bash
curl -X POST "$KHOJ_URL/api/content/convert?client=my-client" \
  -H "Authorization: Bearer $KHOJ_API_KEY" \
  -F 'files=@brief.pdf;type=application/pdf' \
  -F 'files=@notes.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document'
```

Expected behavior:

- Conversion returns JSON objects with `name`, extracted `content`, `file_type`, and byte `size`.
- PDF extraction is page-oriented through PyMuPDF.
- DOCX extraction uses a docx-to-text loader.
- Parser entries prefix compiled text with the source filename.
- Extraction can be empty or partial for scanned PDFs, malformed files, encrypted PDFs, or unsupported DOCX features.

## Image OCR Fixture

Use small `.png`, `.jpg`/`.jpeg`, or `.webp` images with MIME `image/png`, `image/jpeg`, or `image/webp`.

Expected behavior:

- OCR runs only if `rapidocr_onnxruntime` is importable.
- Extracted OCR snippets are joined with spaces into one raw string per image.
- Unsupported image extensions are skipped even if bytes are image-like.
- Temporary image files are removed after parsing.

## GitHub Remote Source Shape

Store config through `/api/content/github`:

```json
{
  "pat_token": "optional_for_public_repos",
  "repos": [
    {"owner": "octo-org", "name": "notes", "branch": "main"},
    {"owner": "octo-org", "name": "wiki", "branch": "master"}
  ]
}
```

Expected behavior:

- Repository files are fetched from the Git tree recursively.
- Markdown and Org files are parsed by their native parsers.
- Other blobs are passed through Magika and text/code blobs become plaintext entries.
- Entry file values are GitHub blob URLs, not local paths.
- Missing PAT can work for public repos but causes private-repo failures and lower rate limits.

## Notion Remote Source Shape

Store config through `/api/content/notion`:

```json
{"token": "secret_notion_integration_token"}
```

Expected behavior:

- The token must belong to a Notion integration shared with target pages/workspaces.
- Khoj searches accessible pages, reads page block children, and extracts supported text blocks.
- Some blocks are skipped or flattened; databases are not deeply indexed by the current processor path.
- Page title detection looks for common title fields including `title`, `Title`, `Name`, `Page`, and `Event`.

## IndexerInput Shape

The server builds an internal `IndexerInput` object after reading multipart files:

```json
{
  "org": {"journal.org": "* Heading\nBody"},
  "markdown": {"notes.md": "# Heading\nBody"},
  "pdf": {"paper.pdf": "<bytes>"},
  "plaintext": {"notes.txt": "Body"},
  "image": {"scan.png": "<bytes>"},
  "docx": {"brief.docx": "<bytes>"}
}
```

Client code should not send this JSON shape to `/api/content`; it is the server-side representation created from multipart uploads. Remote source processors do not use this shape directly.

## Tiny Parser-Only Checks

Use the bundled helper for self-contained parser checks:

```bash
python skills/khoj/sub-skills/content-indexing/scripts/parse_content_fixture.py --type markdown --name notes.md --text '# A\nBody\n## B\nMore' --max-tokens 4
python skills/khoj/sub-skills/content-indexing/scripts/parse_content_fixture.py --type org --name todo.org --text '* A\nBody\n** B\nMore' --max-tokens 4
python skills/khoj/sub-skills/content-indexing/scripts/parse_content_fixture.py --type plaintext --name notes.txt --text 'plain words here'
```

The output JSON is a list of entries with `raw`, `compiled`, `heading`, `file`, `uri`, and `corpus_id` fields. It does not create embeddings, touch file objects, or write to the database.
