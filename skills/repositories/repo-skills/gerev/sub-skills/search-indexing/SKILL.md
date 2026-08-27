---
name: search-indexing
description: "Operate and troubleshoot Gerev search, indexing, parsers, SQLite
  queues, ranking, and startup/status behavior."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Gerev Search and Indexing

Use this sub-skill when a task involves Gerev's search API, index maintenance, ranking stack, document parser helpers, SQLite-backed queues, or the startup/status behavior that makes search usable.

## Best-fit tasks

- Explain or debug `GET /api/v1/search` results, empty result sets, slow ranking, answer snippets, parent/child result nesting, or score interpretation.
- Reason about BM25, Faiss, SentenceTransformer, CrossEncoder, and Transformers QA model interactions without opening the source checkout.
- Inspect index persistence, SQLite queues, database/index file placement, and status counters.
- Diagnose startup failures caused by model cache downloads, NLTK data, CUDA availability, storage permissions, singleton indexes, or the current PDF parser import defect.
- Understand safe parser helper behavior for TXT, HTML, DOCX, PPTX, and PDF text extraction.

## Start here

1. Read [`search-indexing-stack.md`](references/search-indexing-stack.md) for the end-to-end flow, data model, parser map, queue behavior, index persistence, and startup/status route semantics.
2. For failures, use [`troubleshooting.md`](references/troubleshooting.md) first. It covers cold Hugging Face caches, NLTK `punkt`/`punkt_tab`, CUDA fallback, storage path issues, stale indexes, queue stalls, and the known `split_PDF_into_paragraphs` import defect.
3. When you have access to a Gerev checkout or storage directory, run the bundled [`inspect_search_indexing.py`](scripts/inspect_search_indexing.py) read-only helper from this sub-skill directory or with the equivalent path to the bundled script:

   ```bash
   python scripts/inspect_search_indexing.py --app-dir <checkout>/app --storage-dir <storage-dir> --sqlite-details
   ```

   Omit `--storage-dir` to let the helper infer Docker versus home storage. Add `--json` for machine-readable output or `--strict` when a CI-style nonzero exit is useful.

## High-signal routing checks

- Search import/startup touches model loading at import time through `models.py`; do not import the full app casually on a cold or offline host unless model caches are expected to exist.
- `search_logic.py` calls `nltk.download('punkt')` at import time. A downloader warning can be nonfatal when tokenizer data is already present, but missing `punkt` or `punkt_tab` will break BM25 tokenization on modern NLTK.
- `app/main.py` startup must create `FaissIndex` and `Bm25Index` singletons before search is used; direct calls to `search_documents()` without startup can raise "Index is not initialized".
- The current source contains an app-startup blocker: `indexing/index_documents.py` imports `split_PDF_into_paragraphs` from `parsers/pdf.py`, but `pdf.py` defines only `pdf_to_text` and `pdf_to_textV2`. Treat this as a source defect to document or fix only when the user authorizes code changes.
- Search/index storage is under `/opt/storage` in Docker-like mode and under a user home storage directory otherwise. Mismatched environment, user, or permissions can make the app appear to have no documents or no indexes.

## Boundaries

Included here: search query flow, BM25/Faiss ranking, transformer model loading, NLTK data, parser helpers, SQLite index/task queues, indexing background loop, SQLAlchemy search schemas, and the search/status/startup parts of the FastAPI app.

Do not use this sub-skill for connector credential setup, connector-specific API behavior, Docker image build/release automation, or frontend UX changes except where those surfaces directly affect search/status interpretation.
