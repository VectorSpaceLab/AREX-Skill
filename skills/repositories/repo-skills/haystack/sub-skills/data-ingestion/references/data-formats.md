# Data Formats

Haystack ingestion components exchange strongly typed data classes. Prefer public imports from `haystack` and `haystack.dataclasses`; avoid depending on source-tree internals.

## Document

Use `Document` for retrievable/indexable units.

```python
from haystack import Document

doc = Document(
    content="A concise passage about retrieval.",
    meta={"source": "handbook.md", "section": "intro", "language": "en"},
)
```

Important fields:
- `id`: if omitted, Haystack generates a SHA-256 hash from content, blob, metadata, embeddings, and sparse embedding. Set it explicitly when a stable external ID is required.
- `content`: text content; must be `str` or `None`.
- `blob`: optional `ByteStream` for binary data associated with the document.
- `meta`: custom JSON-serializable metadata. Keep values simple when they will be used by filters or document stores.
- `score`: retrieval/ranking score, usually assigned later.
- `embedding` and `sparse_embedding`: use for indexing/retrieval workflows, but choose embedding and store strategy in `../../retrieval-and-rag/SKILL.md`.

Serialization:
- `doc.to_dict()` flattens `meta` into top-level keys by default for Haystack 1.x compatibility.
- Use `doc.to_dict(flatten=False)` when you need a nested `meta` field.
- `Document.from_dict(data)` accepts either nested `meta` or flattened metadata, but not both at once.

Validation tips:
- `Document(content=123)` raises `ValueError`; convert non-text inputs before constructing a text document.
- `DocumentCleaner` leaves `content=None` documents unchanged with a warning, while `DocumentSplitter` raises `ValueError` unless the document has text content.
- Splitting adds metadata such as `source_id`, `page_number`, and split identifiers; assert these when preserving traceability.

## ByteStream

Use `ByteStream` for binary or text bytes that converters, file routers, fetchers, and multimodal helpers can consume.

```python
from pathlib import Path
from haystack.dataclasses import ByteStream

stream = ByteStream.from_file_path(
    Path("policy.md"),
    guess_mime_type=True,
    meta={"source": "policy", "tenant": "finance"},
)
text_stream = ByteStream.from_string("hello", mime_type="text/plain", meta={"source": "inline"})
```

Key behavior:
- `data` is raw `bytes`.
- `mime_type` is optional but important for `FileTypeRouter`, `MultiFileConverter`, and downstream handlers.
- `meta` travels with the stream and is merged into converter output metadata.
- `to_file(path)` writes only bytes; metadata is not preserved on disk.
- `to_dict()` serializes bytes as a list of integers; use this for JSON-safe exchange, not compact storage.

## ChatMessage Basics

Use `ChatMessage` only for basic message payload construction in this sub-skill. Route agent/tool-call orchestration to `../../agents-tools-and-hitl/SKILL.md` and generator prompt design to `../../generation-and-model-components/SKILL.md`.

Common helpers:

```python
from haystack.dataclasses import ChatMessage, FileContent, ImageContent

user_message = ChatMessage.from_user("Summarize the attached policy.")
file_part = FileContent.from_file_path("policy.pdf")
message_with_file = ChatMessage.from_user(content_parts=["Read this file", file_part])
```

Practical checks:
- Roles are represented by `ChatRole` values: `user`, `system`, `assistant`, and `tool`.
- Text content, file content, image content, reasoning, and tool-call parts serialize as structured content parts.
- `ChatMessage` content deserialization rejects unsupported part keys; valid content-part keys include `text`, `image`, `file`, `reasoning`, `tool_call`, and `tool_call_result`.

## FileContent

Use `FileContent` for file attachments inside chat messages or model requests, not for indexable text documents.

```python
from haystack.dataclasses import FileContent

attachment = FileContent.from_file_path("invoice.pdf", extra={"purpose": "summarization"})
```

Key behavior:
- Stores `base64_data`, optional `mime_type`, optional `filename`, and JSON-serializable `extra`.
- Constructor validation checks base64 and tries MIME detection when `mime_type` is omitted.
- `from_file_path()` guesses MIME type from the filename and skips expensive validation after encoding.
- `from_url()` downloads via `LinkContentFetcher`; set short timeouts/retries for deterministic tests.

## ImageContent

Use `ImageContent` for image parts in messages or multimodal workflows. For ingestion from image files, prefer converter components under `haystack.components.converters.image`, such as `FileToImageContent`, `FileToDocument`, `DocumentToImageContent`, and `PDFToImageContent`, depending on whether the target is a message image part or a `Document`.

General guidance:
- Keep image bytes/base64 out of logs and traces.
- Preserve filename, MIME type, page number, and source metadata alongside image-derived content.
- If OCR or image captioning is required, document the external backend dependency and route model/generator details to the generation sub-skill.

## Metadata and Filters

Metadata powers routing and later retrieval filters.

Recommended conventions:
- Include `file_path` or `source` for traceability.
- Include `mime_type` when you already know it; routers can infer from paths, but explicit metadata is safer for streams.
- Use scalar values, lists of scalars, and ISO-formatted strings for dates.
- Avoid non-JSON objects in `Document.meta`, `ByteStream.meta`, and content `extra` dictionaries.

Metadata filter shape used by `MetadataRouter` follows Haystack filter expressions:

```python
rules = {
    "english": {"field": "meta.language", "operator": "==", "value": "en"},
    "recent": {
        "operator": "AND",
        "conditions": [
            {"field": "meta.created_at", "operator": ">=", "value": "2024-01-01"},
            {"field": "meta.created_at", "operator": "<", "value": "2025-01-01"},
        ],
    },
}
```

If a routing rule lacks an `operator`, `MetadataRouter` raises a syntax `ValueError` during initialization.
