# Data Workflows

This reference covers ingestion, loader choice, datahub access, dataset helpers, and validation steps for memory/RAG work.

## Loader Selection

| Source | CAMEL API | Best Use | Runtime Notes |
| --- | --- | --- | --- |
| Raw bytes for PDF/DOCX/TXT/JSON/HTML | `create_file_from_raw_bytes` | Deterministic local parsing and tests | Requires per-format packages such as PyMuPDF or docx2txt for PDF/DOCX |
| Local files or URLs into unstructured elements | `UnstructuredIO.parse_file_or_url` | RAG chunking pipeline with metadata | URL mode is networked; `unstructured` is Python `<3.13` in CAMEL extras |
| In-memory text fixtures | `UnstructuredIO.create_element_from_text` | CI-safe vector retriever tests | Requires `unstructured` package but no network |
| Markdown conversion from many file types | `MarkItDownLoader` | Python 3.13+ document conversion paths | Optional dependency; validate supported extension and file existence |
| Web scraping/API loaders | `Apify`, `Firecrawl`, `JinaURLReader`, `Crawl4AI`, `ScrapeGraphAI` | Authorized web data collection | Network, credentials, rate limits, external service failures |
| OCR/document APIs | `MistralReader`, `MinerU`, `ChunkrReader` | OCR, scanned PDFs, segmentation | API keys and service availability required |
| Hugging Face datasets | `HuggingFaceDatasetManager` | Hub datasets and authenticated data flows | Token/cache/network concerns |
| Fixed examples | `StaticDataset` | Deterministic eval/test fixtures | Keep data schema explicit |
| Synthetic examples | `FewShotGenerator`, `SelfInstructGenerator` | Data generation from seeds | Cross-link to datagen/evaluation sub-skill for full pipelines |

## BaseIO Pattern For Local Files

`create_file_from_raw_bytes(raw_bytes, filename)` returns a `File` object with `docs`, `metadata`, `file_id`, and `raw_bytes`.

```python
from camel.loaders import create_file_from_raw_bytes

raw_bytes = b"Hello CAMEL"
file_obj = create_file_from_raw_bytes(raw_bytes, "note.txt")
text = file_obj.docs[0]["page_content"]
```

Validate:

- Extension is one of the supported file types for the installed optional packages.
- `file_obj.docs` is non-empty.
- Each doc has `page_content` and optional metadata such as page number.
- Large or binary files are not accidentally serialized into prompts.

## UnstructuredIO Pattern For RAG

Use `UnstructuredIO` when you want elements, cleaning, extraction, chunking, and staging. `VectorRetriever.process` uses `UnstructuredIO` internally unless you pass a custom chunker or in-memory `Element`.

```python
from camel.loaders import UnstructuredIO

uio = UnstructuredIO()
element = uio.create_element_from_text(
    text="CAMEL supports memory, tools, models, and multi-agent workflows.",
    filename="fixture.txt",
)
chunks = uio.chunk_elements([element], chunk_type="chunk_by_title")
```

Practical steps:

1. Parse bytes or files into elements.
2. Clean noisy text with `clean_text_data` only when it does not remove task-critical symbols.
3. Chunk with a size that preserves semantic units.
4. Store metadata: filename, page, section, source URL, content hash, and chunk index.
5. Embed chunk text and store with `VectorRecord(payload={...})` or use `VectorRetriever.process`.

## MarkItDown Pattern

Use `MarkItDownLoader` for file-to-Markdown conversion, especially on Python versions where `unstructured` is unavailable.

```python
from camel.loaders import MarkItDownLoader

loader = MarkItDownLoader()
markdown_by_file = loader.convert_files(
    ["report.pdf", "notes.md"],
    parallel=False,
    skip_failed=True,
)
```

Check:

- File exists before conversion.
- Extension is supported by `MarkItDownLoader.SUPPORTED_FORMATS`.
- `skip_failed=True` is appropriate for batch ingestion when partial success is acceptable.
- Converted text is reviewed before embedding if documents may contain boilerplate or sensitive data.

## API-Backed Loader Guidance

Network/credential loaders should be reference-only in offline skill examples. Use them when the user explicitly has the API key and accepts network access.

- `JinaURLReader(api_key=None, return_format='markdown', json_response=False, timeout=..., **kwargs)`: clean URL extraction; empty or HTTP-error responses should be treated as ingestion failures.
- `Firecrawl(api_key=None, api_url=None)`: web crawl/scrape workflows; validate domain permissions.
- `Apify(api_key)`: actor/dataset workflows; validate actor input and dataset IDs.
- `ChunkrReader(api_key=None, url=None)`: document chunking/OCR service; validate task completion and chunk metadata.
- `MistralReader(api_key=None, model=...)`: OCR service; keep model and file types explicit.
- `MinerU(...)`: OCR/layout extraction; note Python and optional dependency constraints.
- `Crawl4AI()` and `ScrapeGraphAI(api_key)`: browser/graph scraping paths; isolate side effects and close clients when needed.

## Build A Loader-To-Retriever Pipeline

```python
from camel.retrievers import VectorRetriever

retriever = VectorRetriever(embedding_model=embedding, storage=storage)
retriever.process(
    content="Local text for tests",
    should_chunk=False,
    extra_info={"dataset": "unit-fixtures", "version": "v1"},
    metadata_filename="fixture.txt",
)
results = retriever.query("What is in the fixture?", top_k=3, similarity_threshold=0.0)
```

If using explicit records instead of `VectorRetriever.process`, use this payload shape:

```python
payload = {
    "text": "Chunk text shown to the agent",
    "metadata": {"source": "fixture.txt", "piece_num": 1},
    "extra_info": {"dataset": "unit-fixtures"},
    "content path": "fixture.txt",
}
```

## Datahub And Dataset Patterns

Use `HuggingFaceDatasetManager` only for authorized hub access and make cache/network behavior explicit. For deterministic tests, prefer `StaticDataset` or local JSON/CSV fixtures loaded through BaseIO.

For generation surfaces:

- `StaticDataset` wraps fixed rows and can enforce minimum sample behavior.
- `FewShotGenerator` and `SelfInstructGenerator` combine seed data, verifiers, and models/agents; route full datagen design and evaluation to the sibling datagen/evaluation sub-skill.
- Always define row schema, required fields, expected types, and verifier behavior before generating new samples.

## Data Validation Checklist

Before retrieval:

- Confirm loader output is non-empty.
- Normalize encodings and whitespace only as much as needed.
- Preserve source metadata in structured fields.
- Check chunk count, average chunk length, and first/last chunk content.
- Check embedding batch size against provider limits.

After retrieval:

- Confirm vector store `status().vector_count` is positive.
- Query with a known phrase from the fixture and expect the matching chunk.
- Lower `similarity_threshold` only for diagnosis, then tune back up.
- Print/log retrieved metadata, not only text.
- Deduplicate overlapping chunks before sending context to the model.

## Evidence Coverage

The patterns above distill CAMEL's loader, MarkItDown, API-backed reader, Hugging Face datahub, static dataset, few-shot dataset, self-instruct dataset, and loader error-handling examples into self-contained guidance. They do not require access to the original repository examples or tests at runtime.
