# Chunking for RAG

Docling chunkers operate directly on a `DoclingDocument`. Use them when you need chunks with document-aware metadata instead of chunking exported Markdown yourself.

## Built-In Chunkers

`docling.chunking` re-exports these chunking types from `docling-core`:

```python
from docling.chunking import BaseChunk, BaseChunker, BaseMeta
from docling.chunking import DocChunk, DocMeta, HierarchicalChunker, HybridChunker
```

The base chunker contract is:

- `chunk(dl_doc, **kwargs)`: yield chunk objects for a `DoclingDocument`.
- `contextualize(chunk)`: return the metadata-enriched text that should usually be embedded or sent to a model.

## HybridChunker Recipe

`HybridChunker` starts from document hierarchy, then applies tokenizer-aware splitting and optional merging. It is the usual choice for retrieval-augmented generation.

```python
from docling.chunking import HybridChunker

# result is a ConversionResult; conversion setup belongs to another sub-skill.
doc = result.document

chunker = HybridChunker(
    tokenizer="sentence-transformers/all-MiniLM-L6-v2",
    merge_peers=True,
    repeat_table_header=True,
    omit_header_on_overflow=False,
)

records = []
for index, chunk in enumerate(chunker.chunk(dl_doc=doc), start=1):
    text = chunker.contextualize(chunk)
    records.append(
        {
            "id": f"chunk-{index}",
            "text": text,
            "raw_text": getattr(chunk, "text", text),
            "meta": getattr(chunk, "meta", None),
        }
    )
```

Installed Docling exposes `HybridChunker` with options including `repeat_table_header`, `merge_peers`, and `omit_header_on_overflow`. Use the tokenizer aligned to the embedding model whenever possible.

## Table Header Controls

Tables often split across chunks. Configure header behavior before post-processing chunks:

- `repeat_table_header=True`: repeat table headers at the start of each table chunk so standalone chunks retain column meaning.
- `omit_header_on_overflow=True`: when a row fits the token limit without the repeated header but not with it, omit the header for that row instead of forcing a worse split.
- `merge_peers=True`: merge undersized successive chunks with the same headings/captions. Disable when you need one chunk per nearby document element.

For RAG over wide tables, start with `repeat_table_header=True`, inspect the longest contextualized chunks, then enable `omit_header_on_overflow=True` only if repeated headers cause overflow.

## Hierarchical Chunker

`HierarchicalChunker` uses document structure and metadata and avoids tokenizer-aware splitting. It is useful when you want small semantic elements or when tokenizer dependencies are unavailable.

```python
from docling.chunking import HierarchicalChunker

chunker = HierarchicalChunker()
chunks = [chunker.contextualize(chunk) for chunk in chunker.chunk(dl_doc=result.document)]
```

Use this for deterministic document-element chunking. If chunks are too large for an embedding model, switch to `HybridChunker` instead of manually slicing strings.

## Line-Based Token Chunking

Docling also documents a line-based token chunker in `docling-core`. It preserves line boundaries, supports repeated prefixes, and can omit prefixes on overflow. Use it for structured text such as tables, logs, code blocks, and lists when preserving lines is more important than preserving full document hierarchy.

Import path when using `docling-core` directly:

```python
from docling_core.transforms.chunker.line_chunker import LineBasedTokenChunker
```

If only the `docling` package is available, prefer `HybridChunker` or import from `docling-core` only after confirming the installed extras.

## Chunk Records for Vector Stores

A robust vector-store record should include contextualized text, stable IDs, and useful metadata that remains JSON-serializable:

```python
from dataclasses import asdict, is_dataclass

from docling.chunking import HybridChunker

chunker = HybridChunker(tokenizer="sentence-transformers/all-MiniLM-L6-v2")

records = []
for index, chunk in enumerate(chunker.chunk(dl_doc=result.document), start=1):
    meta = getattr(chunk, "meta", None)
    if is_dataclass(meta):
        meta = asdict(meta)
    elif hasattr(meta, "model_dump"):
        meta = meta.model_dump(mode="json")

    records.append(
        {
            "id": f"{result.document.name or 'doc'}-{index}",
            "text": chunker.contextualize(chunk),
            "metadata": meta or {},
        }
    )
```

Avoid storing Python objects such as tokenizer instances or document elements directly in vector metadata. Convert metadata to plain JSON-compatible values.

## Markdown-First Alternative

Docling also supports exporting Markdown and using external chunkers. Use that approach when:

- the vector framework already has a required Markdown splitter,
- exact Docling hierarchy/provenance is not required,
- installation cannot include tokenizer extras,
- or chunks must match an existing Markdown-based corpus.

For Docling-native RAG, prefer `HybridChunker` because it can preserve headings, captions, and table semantics before token splitting.
