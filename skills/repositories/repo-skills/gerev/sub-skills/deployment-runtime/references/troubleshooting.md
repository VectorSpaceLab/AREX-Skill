# Deployment/runtime troubleshooting

## Startup fails before the app is usable

Symptoms:

- `uvicorn main:app` fails during import
- the app starts partially but cannot serve `/search` or `/data-sources`
- logs stop in the indexing import chain

Likely causes:

- the known `split_PDF_into_paragraphs` import defect in `app/indexing/index_documents.py`
- missing model cache on a cold host
- incompatible dependency majors for FastAPI, Pydantic, Transformers, or Sentence-Transformers

Recovery:

1. Check `../../../references/troubleshooting.md` at the root for the compatibility family.
2. Confirm the missing PDF split helper is still the blocker before changing anything else.
3. If source changes are allowed, remove the unused import or provide a compatibility wrapper.

## Storage path problems

Symptoms:

- the app appears to have no documents even though data was indexed earlier
- status counters are nonzero but search is empty
- SQLite, Faiss, and BM25 files seem to disagree

Likely causes:

- Docker-like and local-source storage roots are not the same
- the storage directory is unwritable
- only part of the storage tree was copied

Recovery:

- verify whether `DOCKER_DEPLOYMENT` is set
- keep `db.sqlite3`, `faiss_index.bin`, and `bm25_index.bin` together
- make sure the same storage root is used by every process

## UI missing or not served

Symptoms:

- the backend API works but the browser gets 404s for static files
- the React shell does not appear when the backend starts

Likely causes:

- `ui/build` has not been created
- the runtime is in local source mode but the UI bundle is missing
- the Docker image was built before the UI bundle existed

Recovery:

- run the frontend build step in `ui/`
- rebuild the Docker image or restart the source server after the build

## CUDA or CPU warning confusion

The startup warning about CUDA being unavailable is not a failure by itself. The app is designed to continue on CPU, just more slowly. Treat this as a performance note unless the user explicitly requires GPU acceleration.
