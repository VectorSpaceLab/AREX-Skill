---
name: data-ingestion
description: "Build Haystack ingestion flows that construct data classes,
  convert files/streams into Documents or multimodal message content,
  clean/split text, route by file/type/metadata, and perform safe fetch/cache
  checks before indexing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data Ingestion

Use this sub-skill when the task is about preparing data before it is written to a document store: constructing Haystack data objects, converting local files or `ByteStream` payloads, cleaning/splitting documents, routing files/documents by MIME type or metadata, and fetching URL content for conversion.

Route away from this sub-skill when the task is mainly about:
- Writing, deduplicating, embedding, retrieving, or choosing document stores: use `../retrieval-and-rag/SKILL.md`.
- Prompt assembly, generators, or model-specific generation parameters: use `../generation-and-model-components/SKILL.md`.
- Agents, tools, human-in-the-loop flows, or tool-call message orchestration beyond basic `ChatMessage` data construction: use `../agents-tools-and-hitl/SKILL.md`.

## Fast Paths

- Create text documents with `from haystack import Document`; pass `content`, JSON-serializable `meta`, optional explicit `id`, `embedding`, `sparse_embedding`, `score`, or binary `blob`.
- Use `ByteStream.from_file_path(path, guess_mime_type=True, meta={...})` or `ByteStream.from_string(text, mime_type="text/plain", meta={...})` when a converter/router should carry bytes plus metadata.
- Convert common files with `TextFileToDocument`, `MarkdownToDocument`, `PyPDFToDocument`, `PDFMinerToDocument`, `HTMLToDocument`, `DOCXToDocument`, `PPTXToDocument`, `XLSXToDocument`, `CSVToDocument`, `JSONConverter`, or `MultiFileConverter`.
- Clean text with `DocumentCleaner`; split text with `DocumentSplitter`; use `DocumentPreprocessor` when a compact split-then-clean super-component is enough.
- Route files before conversion with `FileTypeRouter`; route converted documents with `DocumentTypeRouter`, `MetadataRouter`, or `DocumentLengthRouter`.
- Fetch URLs with `LinkContentFetcher` into `ByteStream` objects, then convert the returned streams with a matching converter such as `HTMLToDocument`.

## Reference Map

- Data class details, serialization, metadata, and multimodal content: `references/data-formats.md`.
- End-to-end ingestion recipes for files, streams, preprocessing, routing, fetching, and cache/fetch checks: `references/workflows.md`.
- Failure diagnosis for imports, optional dependencies, credentials/backends, API misuse, bad data/config, and workflow edge cases: `references/troubleshooting.md`.
- Smoke-check script for public API availability and basic ingestion behavior: `scripts/ingestion_smoke_check.py`.

## Minimum Validation Pattern

1. Assert every converter/preprocessor/router output key exists, commonly `"documents"`, `"streams"`, MIME-type keys, `"unclassified"`, `"failed"`, or `"unmatched"`.
2. Assert document counts at each step, not just pipeline success.
3. Check metadata preservation: `file_path`, `mime_type`, source-specific metadata, `source_id`, `page_number`, and `split_id` where applicable.
4. Check empty/unsupported cases explicitly: unclassified files, failed fetches, empty PDF extraction, `Document.content is None`, and metadata-filter syntax.

Run the bundled smoke check from the skill root after installing Haystack in any normal Python environment:

```bash
python sub-skills/data-ingestion/scripts/ingestion_smoke_check.py
```
