# Gerev source and container runtime

This reference distills the runtime path for starting Gerev from source or via Docker.

## Source-start command sequence

The documented source path is backend-first:

```bash
cd app
alembic upgrade head
uvicorn main:app --host 0.0.0.0 --port 80
```

The development variant in `app/README.md` is:

```bash
uvicorn main:app --env-file .env --reload
```

`run.sh` performs the same essential work: run Alembic, then start Uvicorn.

## Docker build and compose

- `Dockerfile` starts from `python:3.9`.
- It installs `torch` first, then the backend requirements from `app/requirements.txt`.
- It runs `python3 /tmp/models.py` during the image build to pre-cache the model stack; `/tmp/models.py` is a temporary container build-time script, distinct from the repository source module `app/models.py`.
- It copies `app/` into `/app` and a built `ui/build` directory into `/ui`.
- `docker-compose.yaml` builds from the local context, maps port `80:80`, mounts `~/.gerev/storage:/opt/storage`, and includes an NVIDIA GPU reservation example.

## Storage and path selection

`app/paths.py` chooses runtime paths by mode:

- Docker-like mode: `/opt/storage/`
- Local source mode: `~/.gerev/storage/`

Important files in the storage tree:

| File | Purpose |
| --- | --- |
| `db.sqlite3` | Main SQLAlchemy database |
| `tasks.sqlite3` | task queue |
| `indexing.sqlite3` | indexing queue |
| `faiss_index.bin` | vector index |
| `bm25_index.bin` | lexical index |
| `.uuid` | telemetry identifier |

Keep those files together. Mixing data from different storage roots creates confusing empty-search behavior.

## UI build and serving

- `ui/package.json` defines `start`, `build`, `test`, and `magic` scripts.
- In Docker mode, the backend serves the built UI from `/ui`.
- In local source mode, the backend expects the UI build output in `../ui/build/`.
- If the build output is missing, the backend may still start as an API but will not serve the full UI correctly.

## Runtime order that matters

On startup, `main.py`:

1. warns if CUDA is unavailable,
2. creates the Faiss and BM25 singletons,
3. initializes data-source discovery,
4. starts the background indexer,
5. starts task workers,
6. exposes the API and UI routes.

That order explains `Index is not initialized`, empty status counters, and stale queue behavior during boot troubleshooting.
