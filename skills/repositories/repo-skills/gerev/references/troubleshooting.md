# Cross-cutting troubleshooting

Use this page for problems that span multiple Gerev workflows. For connector-specific auth or setup failures, see `../sub-skills/data-source-connectors/references/troubleshooting.md`. For search/index problems, see `../sub-skills/search-indexing/references/troubleshooting.md`. For source/Docker boot problems, see `../sub-skills/deployment-runtime/references/troubleshooting.md`.

## 1. Dependency compatibility

The current codebase is sensitive to the older 2023-era ML stack.
If the latest resolver gives import errors, pin the runtime family to:

- `fastapi==0.95.2`
- `starlette==0.27.0`
- `pydantic<2`
- `transformers<5`
- `sentence-transformers<4`

Common symptoms of a too-new stack:

- `Unknown task question-answering` from Transformers pipeline construction.
- `Object of type HTMLInputType is not JSON serializable` when loading connector metadata.
- `ModuleNotFoundError` or route import failures caused by old/new API drift.

## 2. Model cache and first import

`app/models.py` creates the bi-encoder, cross-encoders, and QA pipeline at import time. On a cold host this can trigger Hugging Face downloads or appear to hang.

What to check:

- model ids: `multi-qa-MiniLM-L6-cos-v1`, `cross-encoder/ms-marco-TinyBERT-L-2-v2`, `cross-encoder/ms-marco-MiniLM-L-6-v2`, `deepset/roberta-base-squad2`
- network/proxy access for model caches
- whether the local cache already contains the needed assets

If the host is offline, treat model download failure as a cache-preseed problem rather than a code bug.

## 3. Tokenizer data

`search_logic.py` calls `nltk.download('punkt')` during import. Modern NLTK also wants `punkt_tab`.

Symptoms:

- proxied fetch warnings during import
- `LookupError` from `nltk.word_tokenize`

Recovery:

- preseed or install both `punkt` and `punkt_tab`
- confirm tokenization with a tiny smoke such as `nltk.word_tokenize('Hello world.')`

## 4. Full startup import defect

The current source contains a known blocker:

- `app/indexing/index_documents.py` imports `split_PDF_into_paragraphs` from `app/parsers/pdf.py`
- `app/parsers/pdf.py` does not define that symbol

This can block `api.data_source` and full `main.py` import/startup even though the visible indexing code does not use the missing symbol.

Do not silently claim a clean boot until that defect is fixed or explicitly documented. If source changes are allowed, the likely fix is to remove the unused import or add a compatible wrapper.

## 5. Storage and path mismatches

A healthy runtime needs the backend, SQLite database, queue files, and vector/lexical indexes to use the same storage root.

Common mistakes:

- running one process with Docker-like storage and another with home storage
- copying `db.sqlite3` without rebuilding `faiss_index.bin` and `bm25_index.bin`
- missing write permissions on the storage directory
- expecting `/opt/storage` to exist outside Docker-like mode

## 6. CUDA is optional here

The app warns when CUDA is unavailable and continues on CPU. That is expected.

- If you only need correctness, CPU fallback is fine.
- If you want accelerated search or indexing, verify that `torch.cuda.is_available()` is true and that the GPU runtime is actually visible inside the environment/container.

## 7. When the UI will not serve

If the backend starts but the browser sees missing assets or 404s for static files:

- build the frontend in `ui/`
- confirm the backend is serving from the correct UI path for the current mode
- check `ui/build` in local source mode or `/ui` in Docker mode
