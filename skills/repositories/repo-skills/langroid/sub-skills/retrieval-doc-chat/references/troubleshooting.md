# Troubleshooting

## Quick diagnosis table

| Symptom | Likely layer | What to check |
| --- | --- | --- |
| Import error for a parser backend | Optional parser extra | Use the parser choice that matches the installed extra, or install the missing backend package |
| PDF output is empty or badly structured | PDF parser choice | Try `pypdfium2` first, then `pymupdf4llm`, `docling`, `marker`, or `pdf2image` depending on layout and OCR needs |
| Image-based PDF has no text | OCR path | `pdf2image` needs `pdftoppm` / poppler and `pytesseract` |
| DOCX / XLSX / PPTX parsing fails | Office parser choice | Use `markitdown` or `unstructured`-based parsers and confirm those extras are installed |
| URL crawl returns nothing | URL loader / crawler | Confirm the URL type, crawler config, and whether the page is a document URL or a web page |
| Retrieval is empty | Ingest, filter, chunking, embeddings | Confirm the collection exists, ingestion ran, filters are not excluding everything, and chunks were not discarded |
| Qdrant local store refuses to open | Cleanup | A previous local client likely still holds the lock |
| Lance RAG answer is wrong but retrieval looks close | Query planner / dataframe calc | Check the rephrased query, filter, and single-line dataframe calculation |
| A vector store needs credentials or a running service | Backend setup | Confirm env vars, cloud endpoints, and local service startup |
| Code-execution risk is a concern | `full_eval` | Keep `full_eval=False` for untrusted dataframe calculations |

## Parser and format issues

### Missing optional parser deps

Common missing modules and what they usually mean:

- `fitz` / `pymupdf4llm` / `docling` / `pypdf` / `pypdfium2`
  - PDF parser backends are not installed
- `pdf2image` / `pytesseract`
  - OCR path is incomplete
- `unstructured`
  - DOC / DOCX parsing path is incomplete
- `markitdown`
  - Office-to-markdown path is incomplete
- `marker`
  - Marker PDF parser path is incomplete or version-sensitive
- `crawl4ai`, `firecrawl`, `exa_py`
  - Optional URL-crawling backends are missing

### OCR and PDF constraints

- `pypdfium2` is the safest default
- `pdf2image` usually needs poppler binaries plus Tesseract for OCR
- `marker` and `docling` are heavier and can be version-sensitive
- `llm-pdf-parser` is slow by design and depends on a multimodal model configuration

### Office-document constraints

- DOCX: choose `python-docx`, `unstructured`, or `markitdown-docx`
- XLS/XLSX/PPTX: `markitdown` is the dedicated path here
- If a file looks like it parses but returns little text, try a different library choice before changing retrieval settings

## Retrieval issues

### Empty retrieval

Check these in order:

1. The collection exists and contains documents
2. The input was actually ingested
3. The filter is not too restrictive
4. The chunking settings did not split away the useful text
5. The embedding backend matches the vector dimension and model choice
6. `n_similar_chunks` and `n_relevant_chunks` are large enough
7. BM25 and fuzzy search are not both off when you expect lexical recovery
8. `relevance_extractor_config` is not stripping useful context too aggressively

### Retrieval is close but not good enough

Try one change at a time:

- increase `n_similar_chunks`
- enable or tune `n_neighbor_chunks`
- switch chunking strategy
- add `chunk_enrichment_config`
- enable cross-encoder reranking if sentence-transformers is available
- enable reciprocal rank fusion when using multiple retrieval methods
- keep `rerank_periphery` on unless you are debugging ordering

## Vector-store issues

### Qdrant cleanup

Local Qdrant stores keep a file lock.
If a store fails to reopen, call `close()` or use a context manager.
If the lock persists after a crash, create a new local storage path rather than forcing a shared lock.

### LanceDB storage errors

If LanceDB complains about a table or storage problem, recreate the local storage directory.
Also confirm the configured `document_class` and metadata fields still match what was ingested.

### Cloud or service-backed store errors

For Postgres, Weaviate, Pinecone, MeiliSearch, Firecrawl, and Exa, a failure is often a service or credential problem rather than a retrieval bug.
Check the relevant env vars, endpoints, and local service process before changing retrieval logic.

## Lance RAG-specific issues

- `dataframe_calc` must be one line
- use `filter` only when the query explicitly needs field-based restriction
- the rephrased query should not mention filter-only fields
- the planner may need a retry if the critic reports that the plan answers the wrong thing

## Security note

`VectorStore.compute_from_docs(...)` sanitizes calculations unless `full_eval=True`.
Never enable `full_eval` for untrusted input.

## When the issue is not here

If the failure is about model choice, API keys, provider routing, or tool-calling behavior, hand it to the sibling model/provider or generic agent sub-skill instead of chasing it here.
