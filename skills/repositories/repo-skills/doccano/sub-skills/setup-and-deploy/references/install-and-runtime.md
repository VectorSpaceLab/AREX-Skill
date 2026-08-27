# Installation and runtime

doccano supports three common runtime paths: pip, Docker, and Docker Compose. The package also exposes a CLI that can initialize the database, create a user, start the webserver, and launch Celery or Flower.

## Pip install

```bash
pip install doccano
```

If you want PostgreSQL support, install the extra and point `DATABASE_URL` at the database:

```bash
pip install 'doccano[postgresql]'
```

The usual startup sequence is:

```bash
doccano init
doccano createuser --username admin --password pass
doccano webserver --port 8000
```

In another terminal:

```bash
doccano task
```

## Runtime defaults

- SQLite is the default database.
- The standalone CLI uses `DOCCANO_HOME` for its local data and media directory.
- `doccano webserver` defaults to port `8000`.
- `doccano task` starts the Celery worker used for file upload/download and other background jobs.
- `doccano flower` starts Flower for Celery monitoring.

## Docker and Compose

- The container image is published as `doccano/doccano`.
- The compose deployment uses `docker/docker-compose.prod.yml` together with an `.env` file modeled after `docker/.env.example`.
- The common bootstrap variables are `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `ADMIN_EMAIL`.
- Production runtime variables also include `PORT`, `WORKERS`, `CELERY_WORKERS`, and optionally `FLOWER_BASIC_AUTH`.

## Cloud deployment

- AWS deployment is driven by `cloud/aws/template.aws.yaml`.
- Heroku deployment is supported by the repo helper script and the Dockerfile variants.

## Readiness checks

- Run `python -m pip check` after installation.
- Use `doccano --help`, `doccano createuser --help`, and `doccano webserver --help` to confirm the entry points are healthy before trying a long-running start.
