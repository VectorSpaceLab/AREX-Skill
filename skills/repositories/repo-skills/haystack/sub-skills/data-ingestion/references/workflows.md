# Ingestion Workflows

Use these patterns to transform raw local files, URLs, strings, and binary streams into validated Haystack `Document` or message content before indexing or generation.

## Convert Text, Markdown, and PDFs

For a single known file type, instantiate the matching converter and call `run()`.

```python
from pathlib import Path
from haystack.components.converters import TextFileToDocument, MarkdownToDocument, PyPDFToDocument

text_docs = TextFileToDocument(store_full_path=False).run(
    sources=[Path("notes.txt")],
    meta={"collection": "research"},
)["documents"]

markdown_docs = MarkdownToDocument(extract_frontmatter=True, progress_bar=False).run(
    sources=[Path("guide.md")],
    meta={"collection": "docs"},
)["documents"]

pdf_docs = PyPDFToDocument(extraction_mode="plain").run(
    sources=[Path("paper.pdf")],
    meta={"collection": "papers"},
)["documents"]
```

Converter behavior to remember:
- `TextFileToDocument` defaults to UTF-8 and can use a `ByteStream.meta["encoding"]` override.
- `MarkdownToDocument(extract_frontmatter=True)` removes YAML frontmatter from content and merges it into metadata when the frontmatter is a mapping.
- `PyPDFToDocument` requires the optional `pypdf` package; `PDFMinerToDocument` is an alternative PDF converter with different dependency and extraction characteristics.
- Most converters accept paths or `ByteStream` objects, plus either one metadata dictionary for all inputs or a list matching the number of sources.
- `store_full_path=False` stores only the basename in `file_path`; set it to `True` only when full paths are intentionally required and safe to expose.

## Convert Mixed File Types

Use `MultiFileConverter` when a user provides mixed supported files and you want a compact routing/conversion component.

```python
from pathlib import Path
from haystack.components.converters import MultiFileConverter

converter = MultiFileConverter(encoding="utf-8", json_content_key="content")
result = converter.run(
    sources=[Path("a.txt"), Path("b.md"), Path("c.pdf")],
    meta={"batch": "onboarding"},
)
documents = result["documents"]
unclassified = result.get("unclassified", [])
failed = result.get("failed", [])
```

Supported MIME categories include CSV, DOCX, HTML, JSON, Markdown, plain text, PDF, PPTX, and XLSX. Optional packages may still be required for specific formats. Always inspect `unclassified` and `failed` outputs before indexing.

For stricter control, route first and then call explicit converters:

```python
from haystack.components.routers import FileTypeRouter
from haystack.components.converters import TextFileToDocument, MarkdownToDocument

router = FileTypeRouter(mime_types=["text/plain", "text/markdown", "application/pdf"])
routed = router.run(sources=["a.txt", "b.md", "c.unknown"])

text_docs = TextFileToDocument().run(sources=routed.get("text/plain", []))["documents"]
markdown_docs = MarkdownToDocument(progress_bar=False).run(sources=routed.get("text/markdown", []))["documents"]
unsupported = routed.get("unclassified", [])
```

## Use ByteStreams for In-Memory or Fetched Data

`ByteStream` lets you avoid temporary files while preserving metadata.

```python
from haystack.dataclasses import ByteStream
from haystack.components.converters import TextFileToDocument

streams = [
    ByteStream.from_string(
        "Policy text",
        mime_type="text/plain",
        meta={"file_path": "policy.txt", "source": "inline"},
    )
]
documents = TextFileToDocument().run(sources=streams, meta={"tenant": "acme"})["documents"]
```

Metadata merge order in common converters is `ByteStream.meta` plus the explicit `meta` argument, with explicit `meta` overriding duplicate keys. Use this to add batch-level metadata while preserving source-level details.

## Fetch URL Content

`LinkContentFetcher` returns `ByteStream` objects with URL and content-type metadata. Convert the streams with a matching converter.

```python
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import HTMLToDocument

fetcher = LinkContentFetcher(raise_on_failure=False, retry_attempts=1, timeout=3)
streams = fetcher.run(urls=["https://example.com"])["streams"]
documents = HTMLToDocument().run(sources=streams, meta={"source_type": "web"})["documents"]
```

For deterministic tests and agent-generated examples, prefer local `ByteStream.from_string()` inputs over network calls. When network fetching is required, set bounded timeouts/retries and handle partial success.

## Clean and Split Documents

Clean before splitting when you want whitespace/noise removal to affect chunk boundaries. Split before cleaning when you want page or line positions from raw content to be preserved. `DocumentPreprocessor` uses split-then-clean.

```python
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter

cleaner = DocumentCleaner(
    remove_empty_lines=True,
    remove_extra_whitespaces=True,
    remove_regex=r"Confidential\s+Footer",
    unicode_normalization="NFC",
)
cleaned = cleaner.run(documents=documents)["documents"]

splitter = DocumentSplitter(split_by="word", split_length=120, split_overlap=20, split_threshold=20)
chunks = splitter.run(documents=cleaned)["documents"]
```

Splitter options:
- `split_by`: `word`, `sentence`, `page`, `passage`, `period`, `line`, or `function`.
- `split_length`: maximum units per chunk.
- `split_overlap`: overlap units; must be less than `split_length`.
- `split_threshold`: short trailing splits are merged into the previous split.
- `respect_sentence_boundary=True` works with `split_by="word"` and may need NLTK resources.
- `skip_empty_documents=True` drops empty-content documents; set `False` only when downstream components can handle them.

Chunk metadata includes the original document metadata plus traceability keys such as `source_id`, page number, and split position. Keep those keys through indexing so retrieval answers can cite the source.

## Route Converted Documents

Use document routers when conversion is complete but downstream preprocessing/indexing differs by metadata, MIME type, or content length.

```python
from haystack.components.routers import DocumentTypeRouter, MetadataRouter, DocumentLengthRouter

by_type = DocumentTypeRouter(
    mime_types=["text/plain", "text/markdown", "application/pdf"],
    mime_type_meta_field="mime_type",
    file_path_meta_field="file_path",
).run(documents=documents)

by_language = MetadataRouter(
    rules={"english": {"field": "meta.language", "operator": "==", "value": "en"}}
).run(documents=documents)

by_length = DocumentLengthRouter(threshold=50).run(documents=documents)
short_docs = by_length["short_documents"]
long_docs = by_length["long_documents"]
```

Routing outputs to validate:
- `DocumentTypeRouter`: MIME-type keys plus `unclassified`.
- `MetadataRouter`: rule-name keys plus `unmatched`.
- `DocumentLengthRouter`: `short_documents` and `long_documents`; `content is None` always routes to `short_documents`.

## Pipeline Pattern Before Indexing

Build ingestion pipelines from explicit components, then hand off resulting documents to retrieval/indexing components covered by `../../retrieval-and-rag/SKILL.md`.

```python
from haystack import Pipeline
from haystack.components.converters import TextFileToDocument
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter

pipeline = Pipeline()
pipeline.add_component("converter", TextFileToDocument())
pipeline.add_component("cleaner", DocumentCleaner(strip_whitespaces=True))
pipeline.add_component("splitter", DocumentSplitter(split_by="word", split_length=100, split_overlap=10))
pipeline.connect("converter.documents", "cleaner.documents")
pipeline.connect("cleaner.documents", "splitter.documents")

result = pipeline.run({"converter": {"sources": ["notes.txt"], "meta": {"source": "notes"}}})
chunks = result["splitter"]["documents"]
```

Add a `DocumentWriter`, embedder, retriever, or document store only after switching to the retrieval-and-RAG route.

## Fetch and Cache Basics

Haystack includes caching components for URL/content freshness checks in ingestion-adjacent workflows. Use them to avoid refetching unchanged sources, but keep cache persistence and indexing policy separate from conversion logic.

Practical approach:
- Use `LinkContentFetcher` for bounded fetches into `ByteStream` objects.
- Store source URL, content type, timestamp, and checksum in metadata if later steps need cache decisions.
- When using cache-checker components, inspect their `changed`/`unchanged` style outputs and assert that skipped URLs are explicitly accounted for.
- Do not make generated skills depend on a specific local cache directory; pass cache locations as user configuration when required.
