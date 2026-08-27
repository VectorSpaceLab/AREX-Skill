# Troubleshooting

This reference collects the most common backend-platform setup and safety issues.

## Environment and imports

| Symptom | Likely cause | What to check |
| --- | --- | --- |
| `ModuleNotFoundError`, import failure, or missing backend symbols | The checkout is not installed as a distribution by design, or the backend directory is not on the import path. | Use `uv run --frozen --no-default-groups --group backend` for the route helper, and pass the repo root so it can add the backend directory to `sys.path`. |
| `pip check` mentions `mitmproxy` / `pyopenssl` conflicts | Known `uv` override noise in this environment. | Treat it as a troubleshooting note, not as a claim that the backend package set is wrong. |
| Backend code imports but config reads fail | Missing environment values or optional service credentials. | Re-run with the expected env file or set the needed values before importing the app. |

## Services and logs

- If the API, web, or worker behavior looks wrong, inspect the service logs under `backend/log/`.
- Assume the core services are running, but verify the specific service you are depending on if a flow stalls.
- If a background job appears stuck, check the matching worker queue and the worker log before changing code.

## Database access

- Use the repo-standard PostgreSQL command with `psql` when you need to inspect state.
- A simple local form is:
  - `PGPASSWORD=... psql -h localhost -U postgres -c "<SQL>"`
- If the client is unavailable, use the containerized fallback:
  - `docker exec onyx-relational_db-1 psql -U postgres -c "<SQL>"`
- Keep ad hoc SQL out of route handlers; database work should stay in the DB helper layer.

## Auth, RBAC, and IDOR

- If a route reads or mutates user, chat, document, connector, or tenant data, confirm it has the right auth dependency.
- Missing tenant checks or ownership checks are security bugs, not cosmetic bugs.
- If a request returns data for the wrong tenant or user, treat it as an IDOR risk until proven otherwise.

## File store issues

- Verify the configured file-store backend, bucket or container name, and credentials.
- Remember that file-store initialization happens during startup.
- If a backend-specific object-store operation fails, the root cause is usually credentials, endpoint reachability, or a missing bucket/container.

## Unsafe maintenance helpers

- Do not use destructive maintenance scripts during routine debugging.
- The reset-index, reset-database, hard-delete-chat, and force-delete-connector helpers can wipe data or bypass normal safety rails.
- Use them only when you explicitly want that destructive behavior.

## Live backend calls

- When you are exercising the running app, call backend endpoints through the frontend proxy path instead of the raw backend port.
- Example pattern: use `http://localhost:3000/api/...` rather than a direct call to the backend service port.
