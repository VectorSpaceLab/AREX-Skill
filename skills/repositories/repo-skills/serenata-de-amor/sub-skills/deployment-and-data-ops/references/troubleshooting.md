# Troubleshooting guide

Use this guide to diagnose setup, `manage.py check`, data loading, service, and maintenance failures. API-level behavior belongs to `jarbas-data-api`; classifier/pipeline behavior belongs to `rosie-suspicion-pipeline`.

## First diagnostic steps

1. Run the safe preflight wrapper:

   ```console
   $ python sub-skills/deployment-and-data-ops/scripts/jarbas_manage_check.py --repo-root <serenata-checkout> --no-run
   $ python sub-skills/deployment-and-data-ops/scripts/jarbas_manage_check.py --repo-root <serenata-checkout>
   ```

2. If the wrapper passes but service commands fail, inspect the real `.env`/service configuration; the wrapper uses safe check-time defaults only when values are missing.
3. Confirm whether the task needs PostgreSQL, RabbitMQ/Celery, memcached, Node/Elm, Docker, network, or credentials.
4. Before destructive commands, print or otherwise confirm the target database identity without exposing credentials.

## Common failures

### Missing `.env` or `SECRET_KEY`

Symptoms:

- `decouple.UndefinedValueError: SECRET_KEY not found`
- Django settings import fails before any command runs.

Fix:

- Create `.env` or export `SECRET_KEY`.
- For check-only diagnostics, use `jarbas_manage_check.py`; it injects a dummy `SECRET_KEY` only for the child process.
- Do not paste production secrets into logs.

### `DATABASE_URL` points nowhere or PostgreSQL is not ready

Symptoms:

- connection refused to `postgres` or `localhost:5432`;
- authentication/database does not exist errors;
- migrations or data loads fail while `manage.py check` passed.

Fix:

1. Confirm `DATABASE_URL` host matches the execution context (`postgres` inside Compose, often `localhost` outside Compose).
2. Start/wait for PostgreSQL.
3. Create the database/user if needed.
4. Re-run `python manage.py migrate` before data loads.
5. Remember that SQLite can pass import checks but does not validate PostgreSQL-specific search behavior.

### PostgreSQL-specific search vector errors

Symptoms:

- failures importing or updating `SearchVector`/`SearchVectorField`;
- `searchvector` fails on SQLite;
- search results empty after new receipt text or reimbursement loads.

Fix:

- Use PostgreSQL for full Jarbas data/search semantics.
- Run migrations first.
- Run `python manage.py searchvector` after reimbursements and receipt text are loaded.
- Use `--all` when rebuilding all vectors after significant data changes.

### `psycopg2` install/import failures

Symptoms:

- `Error: pg_config executable not found`;
- missing `libpq` shared library;
- import failure for `psycopg2`.

Fix:

- Prefer the pinned binary package where compatible.
- If building from source, install PostgreSQL client development headers and compiler tooling for the platform.
- In Alpine containers, ensure `libpq` runtime packages and build dependencies are present during install.
- Keep Python in the legacy supported range; modern interpreters may not have wheels for old pins.

### Python `lzma` missing

Symptoms:

- `ModuleNotFoundError: No module named '_lzma'`;
- `.xz` loaders fail for companies, suspicions, or receipt text.

Fix:

- Use a Python build compiled with XZ/LZMA support.
- On Linux, install XZ/LZMA development libraries before building Python.
- Recreate the virtual environment after fixing the interpreter; installing a Python package cannot add `_lzma` to an already-built interpreter.

### Celery/Kombu import or `importlib-metadata` failures

Symptoms:

- Celery/Kombu import stack traces before workers start;
- entry-point or metadata errors in a modern environment;
- worker crashes while Django `manage.py check` otherwise imports.

Fix:

- Use legacy-compatible dependency versions matching the pinned stack.
- A known compatibility repair is constraining `importlib-metadata` to a version compatible with Celery 4/Kombu 4.
- Do not upgrade Celery/Kombu opportunistically without running worker and management-command checks.
- For pure Django checks, use the preflight wrapper and avoid starting workers.

### RabbitMQ unavailable

Symptoms:

- Celery worker cannot connect;
- broker connection retries;
- async tasks do not execute.

Fix:

- Start RabbitMQ and set `CELERY_BROKER_URL` to the correct host for the execution context.
- In Compose, the broker host is usually `queue`.
- `memory://` is only for check/import scenarios; it is not a replacement for a multi-process worker setup.

### Memcached unavailable

Symptoms:

- cache backend connection errors;
- middleware failures in production-like settings.

Fix:

- Start memcached and set `CACHE_LOCATION` correctly, or use `django.core.cache.backends.dummy.DummyCache` for tests/checks.
- Do not use dummy cache to prove production cache performance or behavior.

### Sample data load order mistakes

Symptoms:

- `suspicions` reports zero/few updates;
- API/data checks show no suspicious reimbursements;
- search does not find receipt text.

Fix:

- Load reimbursements before suspicions.
- Load receipt text before rebuilding search vectors if text search is needed.
- Re-run `searchvector --all` after changing fields included in search vectors.
- Verify record counts after each load.

### Twitter credentials missing or unsafe publication

Symptoms:

- `tweets` logs a warning about missing credentials;
- `tweet` fails authentication;
- accidental concern about posting publicly.

Fix:

- Missing credentials are acceptable for local sample setup.
- Use `python manage.py tweet --fake` for dry-run message generation.
- Do not run `tweet` without `--fake` unless a human authorizes publication from the configured account.

### DigitalOcean/update automation hazards

Symptoms:

- scripts ask for `DO_API_TOKEN`, `DO_SSH_KEY_NAME`, or production `DATABASE_URL`;
- Ansible/Pipenv/Python 2 failures;
- cloud resource creation/deletion actions appear in logs.

Fix:

- Stop unless the user explicitly requested production update automation.
- Use local sample commands instead of the DigitalOcean update playbook.
- If production update is authorized, require backups, target account confirmation, cost/quota understanding, and cleanup/rollback plan.

### Docker image or base-toolchain drift

Symptoms:

- old Python/Node base image unavailable;
- package build failures for pinned dependencies;
- `npm install` or Gulp/Elm fails in modern Node.

Fix:

- Treat the stack as legacy: Python 3.6/3.7-era, Node 8/9-era, Elm 0.18.
- Prefer a controlled legacy runtime or the documented containers over ad hoc upgrades.
- Skip Docker/asset builds when the task is only data loading or Django command inspection.

### Node/Elm asset failures

Symptoms:

- `primordials is not defined`;
- missing `elm-package`;
- Elm version mismatch;
- Gulp task syntax errors.

Fix:

- Use Node 8/9-era tooling.
- Use Elm 0.18 and `elm-package`, not Elm 0.19 commands.
- If the dashboard bundle does not need regeneration, skip `npm run assets` and run Python service checks instead.

## Decision tree for `manage.py check` failures

1. **Fails before Django imports settings**: wrong working directory or Python cannot find `manage.py`; pass `--repo-root` to the wrapper.
2. **Fails with missing `SECRET_KEY`**: set env or use wrapper defaults.
3. **Fails with module import errors**: install pinned Python requirements in a legacy-compatible interpreter.
4. **Fails with Celery/Kombu metadata errors**: repair legacy dependency compatibility; avoid broad upgrades.
5. **Passes with wrapper, fails with real `.env`**: compare injected safe default keys with real variable names; likely DB/cache/broker/settings mismatch.
6. **Passes `check`, fails migrations/data loads**: service readiness or PostgreSQL permissions/schema issue, not a check failure.

## Escalation notes

When reporting a blocker, include:

- command run;
- safety class;
- whether it used wrapper defaults, Docker, or real `.env`;
- dependency versions if import-related;
- service status for PostgreSQL/RabbitMQ/memcached;
- redacted database/broker host and database name, never passwords/tokens;
- whether data had already been mutated and whether a backup exists.
