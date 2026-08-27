# Search and indexing troubleshooting

Use this reference with the read-only helper in `../scripts/inspect_search_indexing.py`. Prefer non-mutating diagnosis first: inspect source shape, storage files, queue sizes, and logs before clearing indexes or forcing connector work.

## Fast triage order

1. **Can the app import/start?** If full startup fails before routes load, check the known `split_PDF_into_paragraphs` defect first.
2. **Are model caches available?** Search route import loads SentenceTransformer, CrossEncoder, and Transformers QA models immediately.
3. **Is NLTK tokenizer data present?** BM25 update/search needs tokenizers even when neural models are healthy.
4. **Did startup initialize indexes?** `FaissIndex.get()` and `Bm25Index.get()` fail until startup has called `create()`.
5. **Is storage the expected storage?** Verify Docker versus home storage, permissions, and that SQLite/index files are from the same run.
6. **Are queues moving?** Compare `/api/v1/status`, queue database contents, and logs from `BackgroundIndexer`/`Workers`.

## Symptom matrix

| Symptom | Likely cause | What to inspect | Safe next action |
| --- | --- | --- | --- |
| `ImportError: cannot import name 'split_PDF_into_paragraphs' from 'parsers.pdf'` | Source defect in `indexing/index_documents.py`; `parsers/pdf.py` does not define the imported symbol. | Run `python sub-skills/search-indexing/scripts/inspect_search_indexing.py --app-dir ./app --strict` from the generated skill tree root. Confirm `index_documents.py` imports the missing name. | Document the blocker. If the user authorizes source changes, add a compatible helper/alias or remove the unused import, then retest import/startup. |
| First import hangs, downloads, or fails offline | `models.py` loads four Hugging Face model assets at import time. | Check logs for model ids: `multi-qa-MiniLM-L6-cos-v1`, `cross-encoder/ms-marco-TinyBERT-L-2-v2`, `cross-encoder/ms-marco-MiniLM-L-6-v2`, `deepset/roberta-base-squad2`. | Pre-seed the model cache or run once with network/proxy access. Keep `transformers<5` and `sentence-transformers<4` for the current stack. |
| `nltk.download('punkt')` emits a proxy/index warning | Import-time downloader checks remote state even when local data is present. | Use the helper's NLTK section or a direct `nltk.data.find()` check for `punkt` and `punkt_tab`. | If tokenizers exist, treat the warning as nonfatal. If missing, download or pre-seed both `punkt` and `punkt_tab` in the runtime NLTK data path. |
| BM25 update/search fails with tokenizer lookup | Missing NLTK `punkt` or `punkt_tab`; incompatible NLTK data path. | Stack trace mentions `LookupError` from `nltk.word_tokenize`. | Install/pre-seed tokenizer data. Avoid relying only on `nltk.download('punkt')` with newer NLTK; verify `punkt_tab` too. |
| Startup logs `CUDA is not available, using CPU...` | Torch cannot see CUDA. This is expected on CPU hosts. | `torch.cuda.is_available()`, container GPU runtime, driver visibility if acceleration is expected. | For correctness, continue on CPU. For performance, fix GPU runtime or reduce query/indexing load while accepting slower search. |
| Search raises `RuntimeError: Index is not initialized` | `FaissIndex.create()` or `Bm25Index.create()` did not run in this process. | Did the caller bypass FastAPI startup and call `search_documents()` directly? | Run through normal app startup, or initialize both singleton indexes in a controlled test harness before calling search. |
| Startup/test raises `RuntimeError: Index is already initialized` | Startup/create called twice in one process without resetting singleton state. | Test fixtures, reload behavior, or repeated manual `create()` calls. | Use a fresh process for integration checks or explicitly reset singleton class attributes only in isolated tests. |
| Empty search results despite documents existing | No paragraphs were indexed, indexes are empty/stale, query path reads a different storage directory, or model/index IDs disagree with DB rows. | Count `document` and `paragraph` rows; inspect `faiss_index.bin` and `bm25_index.bin`; confirm storage mode. | Rebuild indexes from the intended database after confirming storage, but do not use `/clear-index` unless destructive deletion is intended. |
| `GET /api/v1/status` shows growing `docs_left_to_index` | IndexQueue or TaskQueue is filling faster than workers/indexer complete, or a chunk repeatedly fails before ack. | Background logs for `Error while indexing documents...`; queue database table sizes; `docs_in_indexing`. | Fix the underlying exception first. Unacked items are expected to remain until successful ack or failure handling. |
| `docs_indexed` resets to zero after restart | Counter is in-memory only. | Process restart history. | Use DB/index counts for persistent progress; do not treat the status counter as historical truth. |
| Storage files missing or permission denied | Wrong `DOCKER_DEPLOYMENT` setting, different service user, missing mount, or unwritable storage directory. | Effective storage mode; `/opt/storage` for Docker-like mode; home storage directory otherwise; ownership and free disk space. | Create/fix the intended storage directory before import/startup. Keep DB, queue, Faiss, and BM25 files together. |
| Faiss load/update fails | Corrupted/stale `faiss_index.bin`, model dimension mismatch, incompatible faiss build, or id array type issue in an edited runtime. | Verify MiniLM embedding dimension is 384; inspect whether DB paragraph ids match index ids; check faiss package variant. | Regenerate Faiss from the database after backing up storage. Do not copy Faiss files without the matching SQLite DB. |
| BM25 pickle load fails | Pickle produced by incompatible code/package version or corrupted file. | Error during `Bm25Index.create()` opening `bm25_index.bin`. | Back up/remove the BM25 pickle and let the app rebuild from SQLite paragraphs. |
| `/clear-index` unexpectedly removes documents | Route clears both indexes and deletes `Document`/`Paragraph` rows. | Route caller, logs, backups. | Treat as destructive. Prefer storage inspection and controlled rebuilds before invoking it. |
| `/check-for-new-documents` triggers external activity | It forces data-source indexing checks. | Data-source configs and connector logs. | Avoid unless connector credentials/network side effects are acceptable. |

## Known source defect: missing PDF split helper

The import chain is:

```text
main.py -> api.data_source / background_indexer -> indexing.index_documents -> parsers.pdf.split_PDF_into_paragraphs
```

`parsers/pdf.py` defines `pdf_to_text()` and `pdf_to_textV2()`, not `split_PDF_into_paragraphs`. The missing import currently blocks full app import/startup even though the visible `Indexer` code does not call that name.

Do not silently claim clean startup while this remains. If code changes are in scope, likely remedies are either removing the unused import or adding a wrapper with the expected name that delegates to existing PDF text/splitting behavior. Retest at least `api.data_source` and `main.py` import after any fix.

## Storage consistency checklist

For a healthy search index snapshot, the following should refer to the same storage root:

- `db.sqlite3` with `document` and `paragraph` rows.
- `faiss_index.bin` built with paragraph ids from that DB.
- `bm25_index.bin` built from that DB's paragraphs and metadata.
- `indexing.sqlite3` and `tasks.sqlite3` queues that are not unexpectedly accumulating unacked work.

A common failure pattern is running one process with Docker-like storage and another with home storage; both can start successfully but see different data. Another is copying only `db.sqlite3` without regenerating Faiss/BM25 files.
