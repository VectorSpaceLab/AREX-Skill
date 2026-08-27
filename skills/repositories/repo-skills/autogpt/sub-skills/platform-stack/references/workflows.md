# Platform Stack Workflows

## Fresh local setup

1. Install Git, Docker Compose v2, Node 24, and Corepack. Run the preflight
   helper before changing files or starting containers.
2. From `autogpt_platform/`, run `make init-env`. This creates missing root,
   backend, and frontend `.env` files from the matching defaults without
   overwriting an existing file.
3. Start the complete local stack only when the UI and all services are needed:

```bash
docker compose up -d --build
docker compose ps
```

4. Open the frontend on the configured local port, normally `http://localhost:3000`.
   Check service logs before treating a browser error as a frontend bug.

## Backend/frontend development split

For active code changes, avoid rebuilding the whole frontend container:

```bash
cd autogpt_platform
docker compose --profile local up deps_backend -d
cd backend && poetry run app
cd ../frontend && pnpm dev
```

The backend's local REST and WebSocket services use the ports in the active
Compose/default environment. The frontend may use a neighboring port when
another process owns 3000; resolve the conflict rather than assuming the API
base URL changed correctly.

## Core-only services

Use the Makefile route when backend or frontend code will run on the host:

```bash
cd autogpt_platform
make start-core
make logs-core
# in separate shells:
make run-backend
make run-frontend
```

Run `make migrate` after a schema change or a fresh database. It deploys Prisma
migrations, generates the client, and regenerates the Prisma type stub.

## Backend OpenAPI to frontend hooks

When a backend endpoint or schema changes:

1. Start the backend API with the correct environment.
2. From `frontend/`, use `pnpm generate:api` to fetch OpenAPI and regenerate
   Orval hooks, schemas, and MSW handlers.
3. Add or update the page-level integration test before broad browser tests.

Do not hand-edit generated API files as a substitute for correcting the backend
route or OpenAPI output.

## Upgrading an existing installation

Refresh each `.env` against the current `.env.default`; copying defaults over an
existing configuration can delete operator values. Older Supabase-backed
installations need a backup and an explicit data migration decision. The newer
plain Postgres/pgvector layout is not guaranteed to accept a copied Supabase
data directory because extensions, roles, and preload configuration can differ.
Prefer a same-major dump/restore when the fast path is not proven.

## Stop/reset boundaries

- `docker compose stop` preserves containers and data.
- `docker compose down` removes containers and networks but may preserve named
  volumes depending on the command and Compose file.
- `make reset-db` deletes the local database data directory and is destructive.
  Use only with an explicit disposable database decision.
- `docker compose logs -f <service>` is the first diagnostic step for a
  restart loop; do not immediately delete volumes.
