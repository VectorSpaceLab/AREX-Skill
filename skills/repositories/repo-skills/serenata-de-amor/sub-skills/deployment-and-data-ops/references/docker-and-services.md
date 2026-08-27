# Docker and service operations

Jarbas is a Django service backed by PostgreSQL for full data/search behavior. Docker Compose is the easiest local orchestration path; a local install is possible but must respect the legacy dependency stack.

## Service topology

| Service | Role | Required for | Notes |
| --- | --- | --- | --- |
| `django` | Jarbas web/API process | web UI/API, management commands in containers | Development override runs `python manage.py runserver 0.0.0.0:8000`; base image command uses Gunicorn. |
| `postgres` | PostgreSQL database | migrations, data loads, full search-vector/API behavior | Present in the development override. CI used PostgreSQL 9.6; local Compose image is PostgreSQL 10.x-era. |
| `queue` | RabbitMQ broker | Celery worker/beat and async tasks | Needed for production-like Celery behavior. |
| `tasks` | Celery worker (`celery worker --app jarbas`) | async task execution | Uses Jarbas env and Django image. |
| `beat` | Celery beat (`celery beat --app jarbas`) | scheduled search-vector jobs | Optional for local manual runs. |
| `cache` | memcached | production-like Django cache middleware | Use dummy cache for tests/checks if memcached is unavailable. |
| `elm` | Node/Elm asset builder | development asset watch/build | Legacy Node/Elm stack; see `frontend-assets.md`. |
| `rosie` | Rosie container | generating suspicion outputs | Classifier details are owned by `rosie-suspicion-pipeline`; loading its output into Jarbas is covered here. |
| `nginx-proxy`, `nginx-letsencrypt`, `logging` | production reverse proxy/TLS/log shipping | production Compose profile | Reference-only unless operating an authorized production-like target. |

## Docker Compose local setup sequence

Use either `docker compose` (new plugin) or `docker-compose` (legacy binary), matching the host installation. Examples below use `docker compose`; replace with `docker-compose` if needed.

1. Create `.env` from the configuration reference and adjust local-only values.
2. Build/pull/start the support services:

   ```console
   $ docker compose up -d postgres queue cache elm tasks beat
   ```

   For a simple health check of the stack, `docker compose up` starts the default service set. For deterministic setup, start dependencies first, then run one-off commands.
3. Wait for PostgreSQL to accept connections. If migrations fail with connection errors, retry after checking the database container logs.
4. Apply migrations:

   ```console
   $ docker compose run --rm django python manage.py migrate
   ```

5. Load bundled sample data in the safe order:

   ```console
   $ docker compose run --rm django python manage.py reimbursements /mnt/data/reimbursements_sample.csv
   $ docker compose run --rm django python manage.py companies /mnt/data/companies_sample.xz
   $ docker compose run --rm django python manage.py suspicions /mnt/data/suspicions_sample.xz
   ```

6. Rebuild search vectors after reimbursements and optional receipt text are present:

   ```console
   $ docker compose run --rm django python manage.py searchvector
   ```

7. Optionally attach known Rosie tweet URLs if Twitter credentials are configured; missing credentials are non-fatal for `tweets`:

   ```console
   $ docker compose run --rm django python manage.py tweets
   ```

8. Start the web service:

   ```console
   $ docker compose up django
   ```

9. Validate from another shell:

   ```console
   $ docker compose run --rm django python manage.py check
   $ docker compose ps
   ```

API query examples and endpoint semantics are handled by the `jarbas-data-api` sub-skill; this sub-skill only ensures the service and data prerequisites are present.

## Local install sequence

Use a Python version compatible with the old stack. The project historically targeted Python 3.6, and inspection succeeded with Python 3.7 plus pinned dependencies. Modern Python versions may break old pins.

Prerequisites:

- Python 3.6/3.7-era interpreter with `lzma` support.
- PostgreSQL service and a database matching `DATABASE_URL` for migrations/data loads.
- Optional RabbitMQ for Celery worker/beat.
- Optional memcached, or set dummy cache.
- Optional Node 8 / Elm 0.18 for assets.

Sequence:

```console
$ python -m pip install -r requirements.txt
$ export SECRET_KEY=local-dev-only
$ export DATABASE_URL=postgres://<user>:<password>@localhost/<database>
$ export CACHE_BACKEND=django.core.cache.backends.dummy.DummyCache
$ export CELERY_BROKER_URL=amqp://guest:guest@localhost//
$ python manage.py check
$ python manage.py migrate
$ python manage.py reimbursements contrib/data/reimbursements_sample.csv
$ python manage.py companies contrib/data/companies_sample.xz
$ python manage.py suspicions contrib/data/suspicions_sample.xz
$ python manage.py searchvector
$ python manage.py runserver
```

If RabbitMQ is needed for async tasks:

```console
$ celery worker --app jarbas
$ celery beat --app jarbas
```

Run those in separate shells or process supervisors. Do not treat `memory://` as a multi-process broker.

## Static files in service setup

For production-like static serving or Docker image builds, collect static files after assets are generated or when the current static bundle is acceptable:

```console
$ python manage.py collectstatic --no-input
```

The Docker image build runs `collectstatic` during build. If static collection fails, diagnose the Python/Django settings first, then the optional Node/Elm asset build if `app.js` needs regeneration.

## Validation matrix

| Validation | Command | Requires | Good signal | Limit |
| --- | --- | --- | --- | --- |
| Import/config preflight | `python scripts/jarbas_manage_check.py --repo-root <checkout>` | Python deps only | `System check identified no issues` | Uses safe defaults when env vars missing; not full DB proof. |
| Django system check in configured env | `python manage.py check` | `SECRET_KEY`, importable deps | exits 0 | Does not run migrations or open every external service. |
| Migrations | `python manage.py migrate` | PostgreSQL DB | migrations apply | Can mutate DB schema. Confirm target DB first. |
| Sample load | `reimbursements`, `companies`, `suspicions` commands | migrated DB and sample files | increasing record counts / no uncaught errors | Sample data is tiny and not full production data. |
| Search-vector build | `python manage.py searchvector` | PostgreSQL, reimbursement rows | progress output or clean exit | PostgreSQL-specific; SQLite is not enough. |
| Web process | `python manage.py runserver` or Compose `django` | DB config and deps | local HTTP server | Endpoint correctness belongs to `jarbas-data-api`. |
| Docker stack | `docker compose ps` and container logs | Docker daemon/images | containers running | Old image/toolchain versions may require rebuild/pin repairs. |

## Docker/toolchain drift

The Dockerfiles pin old base images (`python:3.6` and Node 9-era image) and old Python/Node dependencies. If builds fail today:

- Check whether the base images are still available.
- Prefer rebuilding in a controlled legacy environment rather than upgrading pins opportunistically.
- Do not claim modern Python/Node compatibility without running native checks.
- If only management-command documentation is needed, use the local preflight helper and skip Docker image builds.
