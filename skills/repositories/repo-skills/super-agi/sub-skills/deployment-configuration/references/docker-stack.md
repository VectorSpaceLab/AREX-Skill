# Docker and Compose Stack

## When to Read

Read this when you need to start, inspect, or troubleshoot the default or GPU
SuperAGI runtime stack.

## Default Stack

The default compose file defines these services:

- `backend`: builds the root Dockerfile, waits for PostgreSQL, then starts the
  app entrypoint.
- `celery`: builds the same image and starts the Celery worker entrypoint.
- `gui`: builds the Next.js frontend from `./gui`.
- `super__redis`: Redis stack server image.
- `super__postgres`: PostgreSQL 15 image with the default SuperAGI database
  user/password/db name.
- `proxy`: nginx on host port `3000`, forwarding to backend and GUI.

The backend container expects the app to run on port `8001` inside the stack.

## GPU / Local LLM Stack

The GPU compose file uses `Dockerfile-gpu` and reserves NVIDIA devices. It also
installs `llama-cpp-python==0.2.7` with CUDA build flags. Treat this as an
optional branch for local model serving, not a requirement for ordinary hosted
provider workflows.

## Startup Order

The container entrypoint path is intentionally sequential:

1. Tool import/download step.
2. Tool dependency installation.
3. Alembic migrations.
4. Backend server startup.

The Celery entrypoint follows the same tool import and dependency installation
pattern before starting the worker.

## Practical Notes

- The compose files and Dockerfiles encode Python 3.10, apt packages, and NLTK
  downloads. They are better sources of runtime truth than a manual ad hoc
  startup sequence.
- `run.sh` and `run_gui.sh` are host-local helper scripts, but they are
  side-effectful and interactive. Prefer Docker Compose when possible.
- The GUI build uses the `./gui` package and Next.js scripts; the repo also has a
  small `gui/README.md` that mirrors standard Next.js usage.
- Full `docker compose up` was not run during skill creation because it is
  long-running and mutates volumes. Use it only when the downstream task needs a
  real running stack.
