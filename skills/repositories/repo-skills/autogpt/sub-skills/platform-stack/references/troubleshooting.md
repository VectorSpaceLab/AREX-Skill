# Platform Stack Troubleshooting

## Docker or Compose is unavailable

**Symptom:** `docker compose` or `make start-core` fails before containers are
created.

**Recovery:** Run the preflight script, confirm Docker Desktop/daemon is ready,
then run `docker compose config` from `autogpt_platform/`. Do not install a
second Compose implementation over an existing Docker Compose v2 setup.

## Frontend starts but API/auth calls fail

**Likely causes:** missing frontend `.env`, stale generated API config, backend
not healthy, wrong backend port, or `BETTER_AUTH_SECRET`/`DATABASE_URL` not
present for the embedded auth service.

**Recovery:** Run `make init-env`, inspect `docker compose ps` and backend logs,
confirm the backend API is reachable, then regenerate the frontend API client
only after the backend OpenAPI endpoint is correct.

## Existing `.env` is missing new variables

`make init-env` uses a no-clobber copy and does not merge defaults. Diff the
existing file against the current default and add only the intended keys. Do
not replace a production-like file wholesale.

## Database or migration failure

Check the selected `DATABASE_URL`, container logs, and Prisma schema/migration
state. Use the isolated test database path for test runs. `make reset-db` deletes
local database data and is not a general migration fix. For old Supabase data,
back up first and prefer dump/restore when copied data references unavailable
extensions, roles, or preload libraries.

## Port conflict

**Symptom:** frontend moves to another port or a backend service cannot bind.

Find the process/container owning the port, stop only the conflicting process,
or update the explicit local configuration and dependent base URLs. Do not
change credentials or reset the database for a port-only failure.

## Local AutoPilot returns incoherent output

Confirm `CHAT_BASE_URL` is reachable from the backend container, the model name
is valid for the local server, `CHAT_API_KEY` is explicitly set, and the model
context window is large enough for tool schemas. Local transport is not the
same as the graph-layer LLM block configuration; configuring one does not
configure the other.

## Full-stack tests hang

Stop and inspect the first unhealthy container, database readiness, seeded test
accounts, and browser auth state. Full Playwright/build suites are optional
expensive checks, not a replacement for focused backend/frontend tests.
