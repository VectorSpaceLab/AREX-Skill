# Configuration reference

Jarbas reads configuration from environment variables, normally sourced from a local `.env` file. Use this reference to create a safe development/test configuration without exposing production secrets.

## Minimal development `.env` shape

Create a `.env` at the repository root or pass equivalent environment variables to the process/container. Do not commit or print real credentials.

```dotenv
ENVIRONMENT=development
LOG_LEVEL=debug
WEB_TIMEOUT=60
WEB_WORKERS=2
SECRET_KEY=replace-with-local-only-secret
ALLOWED_HOSTS=*
USE_X_FORWARDED_HOST=False
CACHE_BACKEND=django.core.cache.backends.dummy.DummyCache
CACHE_LOCATION=
DATABASE_URL=postgres://jarbas:mysecretpassword@postgres/jarbas
CELERY_BROKER_URL=amqp://guest:guest@queue/
SCHEDULE_SEARCHVECTOR=False
```

For a Docker Compose local stack, the Postgres host is usually the Compose service name `postgres`, RabbitMQ is `queue`, and memcached is `cache`. For a non-Docker local stack, use hostnames and ports that match the local services, for example `localhost`.

## Variable groups

| Group | Variables | Required for | Notes |
| --- | --- | --- | --- |
| Django runtime | `ENVIRONMENT`, `LOG_LEVEL`, `WEB_TIMEOUT`, `WEB_WORKERS`, `SECRET_KEY`, `ALLOWED_HOSTS`, `USE_X_FORWARDED_HOST`, `SECURE_PROXY_SSL_HEADER` | imports, web server, production deployment | `SECRET_KEY` is mandatory. `ENVIRONMENT=production` enables production middleware behavior. |
| Database | `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | migrations, data loads, API service, search vectors | Full Jarbas behavior expects PostgreSQL. SQLite is acceptable only for import/system-check style smoke checks. |
| Cache | `CACHE_BACKEND`, `CACHE_LOCATION` | web service cache middleware | Use `django.core.cache.backends.dummy.DummyCache` for tests/checks when memcached is unavailable. Memcached needs `CACHE_LOCATION`, usually `cache:11211` or `localhost:11211`. |
| Celery/broker | `CELERY_BROKER_URL` | async task workers, periodic tasks, some data/receipt workflows | RabbitMQ URLs are typical. `memory://` is suitable only for import/system-check preflights, not multi-process work. |
| Static/proxy/production | `VIRTUAL_HOST`, `VIRTUAL_PROTO`, `LETSENCRYPT_EMAIL`, `HTTPS_METHOD`, `STATICFILES_STORAGE` | reverse proxy, HTTPS, static files | Treat as deployment-specific. Do not reuse production host/email settings blindly. |
| Monitoring/storage | `NEW_RELIC_*`, `LOGGING_URL`, `AMAZON_*` | production telemetry and object storage | Credential-bearing or account-specific; leave blank unless explicitly needed. |
| External APIs | `GOOGLE_API_KEY`, `GOOGLE_STREET_VIEW_API_KEY`, `FOURSQUARE_CLIENT_ID`, `FOURSQUARE_CLIENT_SECRET`, `YELP_ACCESS_TOKEN`, `INBOX_PASSWORD` | research/data-acquisition scripts or optional views | Not needed for basic sample seeding. Never echo real values in logs. |
| Twitter | `TWITTER_CONSUMER_KEY`, `TWITTER_CONSUMER_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET` | `tweets` readback and `tweet` publishing | `tweets` warns and exits when missing credentials. `tweet` can publish to an account; use `--fake` for dry-run message generation. |
| Search schedule | `SCHEDULE_SEARCHVECTOR`, `SCHEDULE_SEARCHVECTOR_CRON_*` | Celery beat schedule for search-vector rebuilding | Optional. Manual `searchvector` is safer for local runs. |

## Safe preflight defaults

The bundled `scripts/jarbas_manage_check.py` injects these defaults only into its child `manage.py check` process when the caller has not already set them:

- `SECRET_KEY`: a local dummy value.
- `DATABASE_URL`: a local SQLite URL for Django import/system checks.
- `CACHE_BACKEND`: Django dummy cache.
- `CELERY_BROKER_URL`: in-memory broker URL.
- `DJANGO_SETTINGS_MODULE`: `jarbas.settings`.

These defaults are deliberately not a production or data-loading configuration. They are only for verifying that Django settings and installed dependencies import cleanly without starting PostgreSQL, RabbitMQ, memcached, migrations, or network services.

## Configuration checklist

Before running migrations or data loads:

1. Confirm `SECRET_KEY` exists and is not a real production key in shared logs.
2. Confirm `DATABASE_URL` points to the intended PostgreSQL database.
3. Confirm the database user can create/modify tables for migrations.
4. Decide whether cache should be dummy or memcached.
5. Decide whether Celery/RabbitMQ is needed for this task. Basic sample loads can often be run without a live worker, but receipt fetching, scheduled tasks, and production-like async behavior need the broker/worker stack.
6. Leave Twitter, DigitalOcean, New Relic, object storage, and research API credentials blank unless the task explicitly requires them and the user has authorized the side effects.

## Redaction rules

- In handoffs and logs, report variable names and service classes, not secret values.
- If a failure message includes a URL with embedded credentials, redact the password/token before pasting it.
- Prefer local throwaway credentials for Docker sample databases.
- Do not copy production `.env` content into skill files, test cases, issue comments, or generated examples.
