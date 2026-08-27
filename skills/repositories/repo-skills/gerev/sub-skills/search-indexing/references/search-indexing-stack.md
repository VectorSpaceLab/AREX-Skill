# Gerev search, indexing, parser, queue, and status stack

This reference is distilled from the Gerev backend source so future agents can reason about the search/index runtime without reopening the original checkout. Source evidence paths are named for provenance, but runtime links in this sub-skill stay inside the generated skill tree.

## Import-time model and tokenizer behavior

`app/models.py` creates all neural ranking objects at module import time:

| Object | Model id / role | Used by |
| --- | --- | --- |
| `bi_encoder` | `multi-qa-MiniLM-L6-cos-v1` SentenceTransformer | Embeds queries and indexed paragraphs for Faiss vector search. |
| `cross_encoder_small` | `cross-encoder/ms-marco-TinyBERT-L-2-v2` CrossEncoder | First reranking pass over merged BM25/Faiss candidates. |
| `cross_encoder_large` | `cross-encoder/ms-marco-MiniLM-L-6-v2` CrossEncoder | Final reranking pass before/after answer extraction. |
| `qa_model` | Transformers question-answering pipeline, `deepset/roberta-base-squad2` | Finds answer spans inside top candidate paragraphs. |

Construction evidence verified that the current import-time QA/reranker stack requires `transformers<5` and `sentence-transformers<4`. First import on a cold host may download Hugging Face assets unless the cache is already populated. Torch can use CUDA when available; CPU fallback is expected and documented by the app, but it is slower.

`app/search_logic.py` also calls `nltk.download('punkt')` during import. Tokenization needs both `punkt` and, with newer NLTK releases, `punkt_tab`. A proxied downloader warning can be harmless if local tokenizer data is already installed; missing tokenizer data affects BM25 update/search.

The search candidate budgets depend on `torch.cuda.is_available()` at import time:

| Budget | CUDA available | CPU fallback |
| --- | ---: | ---: |
| BM25 candidates | 100 | 20 |
| bi-encoder/Faiss candidates | 60 | 20 |
| small cross-encoder candidates constant | 30 | 10 |

## Search query flow

The public route is `GET /api/v1/search?query=<text>&top_k=<n>`. `app/api/search.py` increments telemetry from the optional `uuid` request header and calls `search_documents(query, top_k)`.

`search_documents()` performs this pipeline:

1. Encode the query with `bi_encoder.encode(query, convert_to_tensor=True, show_progress_bar=False)`.
2. Read the singleton `FaissIndex` and search vector ids up to `BI_ENCODER_CANDIDATES`; filter out `-1` empty ids.
3. Read the singleton `Bm25Index` and append BM25 paragraph ids up to `BM_25_CANDIDATES`.
4. Query SQLite via SQLAlchemy for `Paragraph.id.in_(candidate_ids)`. If no paragraphs are returned, search returns `[]`.
5. Build `Candidate` objects containing paragraph content, the related `Document`, and a mutable score.
6. Rerank all candidates using the small cross-encoder, with each paragraph concatenated to the document title using `[SEP]`.
7. Rerank the remaining candidates using the large cross-encoder and keep `top_k`.
8. Run the QA pipeline on the top contexts. The answer text is expanded to a sentence-like span using punctuation/quote/parenthesis splitting, and `answer_start`/`answer_end` are saved on each candidate.
9. Rerank again with the large cross-encoder, this time using only the assigned answer span plus title.
10. If a candidate's document has a parent document that is also in the candidate list, make the child nested under the parent result and remove the duplicate parent candidate from the top-level list. If the parent was not in the list, a parent result is synthesized from the ORM relationship.
11. Convert candidates concurrently to `SearchResult` dataclasses. Scores are rescaled with `(raw_score + 12) / 24 * 100`. Result URLs gain a browser text-fragment anchor derived from the highlighted answer.

Practical implications:

- Importing the search route can be expensive because models load immediately.
- Direct `search_documents()` calls require `FaissIndex.create()` and `Bm25Index.create()` to have run first.
- Search over an empty database or empty indexes returns `[]`; it is not necessarily an error.
- Result ordering is determined by neural rerank scores, not by BM25/Faiss retrieval order.
- Confluence author images may trigger an additional data-source token lookup when converting results.

## Index creation and document ingestion

`app/main.py` startup calls `FaissIndex.create()` and `Bm25Index.create()`, initializes data-source discovery, starts the background indexer, and starts task workers.

`Indexer.index_documents(documents)` is the central ingestion function:

1. Compute each incoming `BasicDocument.id_in_data_source` as `<data_source_id>_<source_document_id>`.
2. Delete any existing `Document` rows with matching `id_in_data_source`, remove their paragraph ids from Faiss, rebuild BM25, and delete DB rows.
3. Convert each `BasicDocument` to a SQLAlchemy `Document` plus `Paragraph` children. Child documents are attached through `Document.parent` / `parent_id`.
4. Split source text into paragraphs by blank-line boundaries. Small paragraphs are batched until the current paragraph is longer than roughly 256 characters. `None` content produces no paragraphs.
5. Save documents and paragraphs in SQLite.
6. Rebuild BM25 from all persisted paragraphs.
7. Encode paragraph text plus title metadata using the bi-encoder.
8. Add embeddings to the Faiss `IndexIDMap` with paragraph ids.

There is a source-level defect at import time: `indexing/index_documents.py` imports `split_PDF_into_paragraphs` from `parsers/pdf.py`, but that function is not defined. The imported name is not used in the visible indexing logic, yet it blocks `api.data_source` and full `main.py` import until fixed or shimmed.

## BM25 index behavior

`Bm25Index` is a process singleton:

- `create()` loads a pickled index from `BM25_INDEX_PATH` when it exists; otherwise it starts empty.
- `get()` raises `RuntimeError("Index is not initialized")` if startup has not called `create()`.
- `update()` rebuilds from every `Paragraph` row in the database. Each paragraph is tokenized with `nltk.word_tokenize()` after appending title, author, and data-source type name metadata when available.
- `search(query, top_k)` tokenizes the query, scores with `rank_bm25.BM25Okapi`, sorts the best ids, and returns paragraph ids.
- `clear()` resets in memory and saves the empty pickle.

If the database contains zero paragraphs, BM25 has `index = None` and `search()` returns an empty list. Because the saved file is a Python pickle, version or class-layout changes can make old files fail to load.

## Faiss index behavior

`FaissIndex` is also a process singleton:

- `create()` constructs a `FaissIndex`; it raises if an instance already exists.
- The constructor loads `FAISS_INDEX_PATH` when present; otherwise it creates `faiss.IndexFlatIP(384)` wrapped in `faiss.IndexIDMap`.
- `MODEL_DIM` is fixed at `384`, matching the MiniLM bi-encoder output dimension.
- `update(ids, embeddings)` stores embeddings on CPU and writes the Faiss index file.
- `remove(ids)` removes ids and rewrites the file.
- `search(queries, top_k)` unsqueezes a single query vector and returns ids.
- `clear()` resets the index and rewrites the file.

Dimension mismatch or corrupted Faiss files usually appears during startup load or update. A stale vector index can disagree with the SQLite paragraph table if files were copied independently or storage paths changed.

## SQLite storage and queues

`app/paths.py` creates the storage directory when imported. In Docker-like mode (`DOCKER_DEPLOYMENT` set), storage is `/opt/storage`. Otherwise the source computes a home storage directory under the login user's home. The important files are:

| Logical store | Filename |
| --- | --- |
| Main SQLAlchemy database | `db.sqlite3` |
| Task queue | `tasks.sqlite3` |
| Indexing queue | `indexing.sqlite3` |
| Faiss vector index | `faiss_index.bin` |
| BM25 pickle | `bm25_index.bin` |
| Instance uuid | `.uuid` |

`IndexQueue` wraps `persistqueue.SQLiteAckQueue` at the indexing queue path with queue name `index` and `multithreading=True`. `put()` appends `BasicDocument` objects and notifies a condition variable. `consume_all(max_docs=5000, timeout=1)` waits briefly, drains raw queue items up to the limit, and returns `IndexQueueItem(queue_item_id, doc)` values. `BackgroundIndexer` acks each item only after the whole chunk indexes successfully.

`TaskQueue` wraps another `SQLiteAckQueue` at the tasks path with queue name `task`. `Workers` starts 20 threads. Each worker obtains one task, resolves the data-source instance, calls `run_task(function_name, **kwargs)`, and acks on success. On failure, `attempts` is decremented from its default of 3; unfinished tasks are updated and nacked, and zero-attempt tasks are `ack_failed()`.

## Startup, shutdown, and status routes

Search readiness depends on FastAPI startup events:

- Every 60 seconds after startup, `check_for_new_documents()` scans all data sources and calls their `index(force=False)` method if the source has not been indexed in the last hour.
- Startup telemetry and daily telemetry are best-effort and exceptions are ignored.
- The main startup event warns when CUDA is unavailable, creates both indexes, initializes data-source classes, starts the background indexer, and starts task workers.
- Shutdown stops workers and the background indexer.

Search/status-relevant routes:

| Route | Behavior |
| --- | --- |
| `GET /api/v1/search` | Runs the full search/ranking/QA flow. |
| `GET /api/v1/status` | Returns `docs_in_indexing`, `docs_left_to_index`, and `docs_indexed`. |
| `POST /clear-index` | Clears Faiss and BM25, then deletes all `Document` and `Paragraph` rows. Destructive. |
| `POST /check-for-new-documents` | Forces data-source indexing checks. Potentially network/connector side effects. |

Status semantics:

- `docs_in_indexing` is the current in-process background chunk size.
- `docs_left_to_index` is `IndexQueue.qsize() + TaskQueue.qsize()`.
- `docs_indexed` is an in-memory process counter reset on process start or `BackgroundIndexer.reset_indexed_count()`.
- Status counters do not prove that Faiss/BM25 files and SQLite rows are mutually consistent.

## Parser helpers

Parser helpers are simple utility functions used by connector/document ingestion paths:

| Parser file | Function(s) | Behavior |
| --- | --- | --- |
| `parsers/txt.py` | `txt_to_string(path)` | Reads UTF-8 text files. |
| `parsers/html.py` | `html_to_text(html)` | Adds `: ` before heading close tags, extracts text with BeautifulSoup using blank-line separators, and removes whitespace before punctuation. |
| `parsers/docx.py` | `docx_to_html(path)` | Uses Mammoth to convert DOCX to HTML; pair with `html_to_text()` when plain text is needed. |
| `parsers/pptx.py` | `pptx_to_text(path, slides_seperator="\n\n")` | Extracts text from shapes, adds `:` after slide titles, and separates slides. The parameter name is misspelled in source. |
| `parsers/pdf.py` | `pdf_to_text(path)`, `pdf_to_textV2(path)` | `pdf_to_text` concatenates PyPDF2 extracted page text. `pdf_to_textV2` uses LangChain `PyPDFLoader` and a 256-character `CharacterTextSplitter`, then joins chunks with blank lines. |

Remember: `split_PDF_into_paragraphs` is not present in `parsers/pdf.py` even though `index_documents.py` imports it.
