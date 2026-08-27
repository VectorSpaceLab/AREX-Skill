# Deployment and runtime

This reference covers source startup, Docker/compose deployment, storage layout, and UI build/serve expectations.

## Source startup

The documented source entry point is the backend in `app/`:

```bash
cd app
alembic upgrade head
uvicorn main:app --host 0.0.0.0 --port 80
```

For development reload mode, the repository README also documents:

```bash
uvicorn main:app --env-file .env --reload
```

`run.sh` performs the same startup sequence: run migrations, then launch Uvicorn on port `80`.

## Docker and compose

- `Dockerfile` starts from `python:3.9`, installs `torch` and `app/requirements.txt`, pre-caches the model stack with the temporary container build-time script at `/tmp/models.py` (not the repository source module `app/models.py`), copies `app/`, copies the built UI into `/ui`, and then runs `run.sh`.
- `docker-compose.yaml` builds the local image, exposes port `80`, mounts `~/.gerev/storage:/opt/storage`, and reserves an NVIDIA GPU in the sample compose file.
- `deploy.sh` is a maintainer release helper that builds and pushes multi-architecture images; it is not a routine runtime command.

## Storage layout

`app/paths.py` selects storage based on the deployment mode:

- Docker-like mode (`DOCKER_DEPLOYMENT` set): `/opt/storage/`
- Local source mode: a home-directory `.gerev/storage/` path

The important runtime files are:

| File | Purpose |
| --- | --- |
| `db.sqlite3` | SQLAlchemy database |
| `tasks.sqlite3` | task queue |
| `indexing.sqlite3` | indexing queue |
| `faiss_index.bin` | vector index |
| `bm25_index.bin` | lexical index |
| `.uuid` | telemetry identifier |

Keep those files together. Copying only one of them often creates inconsistent search results.

## UI build and serving

- `ui/package.json` exposes `start`, `build`, `test`, and `magic` scripts.
- In Docker mode, the backend serves the built UI from `/ui`.
- In local source mode, the backend expects the frontend build output in `../ui/build/`.
- If static UI files are missing, rebuild the UI before trying to serve the backend as a full app.

## Runtime sequence

On startup, `main.py`:

1. warns if CUDA is unavailable,
2. creates the Faiss and BM25 singletons,
3. initializes data-source discovery and database-backed connector metadata,
4. starts the background indexer,
5. starts task workers,
6. serves the API and UI routes.

That order matters when troubleshooting empty indexes or `Index is not initialized` errors.
