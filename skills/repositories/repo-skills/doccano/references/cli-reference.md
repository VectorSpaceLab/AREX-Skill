# CLI and environment reference

doccano exposes a single console entry point named `doccano`.

## Commands

| Command | Purpose | Common options |
| --- | --- | --- |
| `doccano init` | Waits for the database, runs migrations, and creates default roles. | None beyond the implicit database settings. |
| `doccano migrate` | Runs Django migrations. | None. |
| `doccano createuser` | Creates an admin user non-interactively. | `--username`, `--password`, `--email` |
| `doccano webserver` | Starts the web app. | `--port`, `--workers`, `--env_file` |
| `doccano task` | Starts the Celery worker for import/export and other background work. | `--concurrency`, `--env_file` |
| `doccano flower` | Starts Flower for Celery monitoring. | `--basic_auth`, `--env_file` |

## Help usage

Prefer `doccano <command> --help` for command-specific usage. The custom `doccano help <command>` subcommand exists, but direct `--help` is clearer and easier to verify.

## Important environment variables

| Variable | Meaning |
| --- | --- |
| `DOCCANO_HOME` | Base directory for standalone runtime files such as the SQLite database and media directory. |
| `DATABASE_URL` | Database connection string. SQLite is the default fallback. |
| `MEDIA_ROOT` | Location for uploaded media and stored files. |
| `SECRET_KEY` | Django secret key. Should be unique in production. |
| `DEBUG` | Enables debug mode and relaxed local-origin defaults. |
| `IMPORT_BATCH_SIZE` | Batch size used during dataset import. |
| `MAX_UPLOAD_SIZE` | Maximum upload size in bytes. |
| `ENABLE_FILE_TYPE_CHECK` | Turns MIME/type checking on or off during import. |
| `CELERY_BROKER_URL` | Celery broker URL; defaults to a SQLAlchemy-backed fallback when not set. |
| `CSRF_TRUSTED_ORIGINS` | Extra origins allowed for CSRF in local or deployed environments. |
| `HEADER_AUTH_USER_NAME`, `HEADER_AUTH_USER_GROUPS`, `HEADER_AUTH_ADMIN_GROUP_NAME`, `HEADER_AUTH_GROUPS_SEPERATOR` | Enable header-based auth integration. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` | Email verification and notification configuration. |
| `ROLE_PROJECT_ADMIN`, `ROLE_ANNOTATOR`, `ROLE_ANNOTATION_APPROVER` | Override the default role names if needed. |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL` | Container and cloud bootstrap variables used by repo helper scripts. |
| `PORT`, `WORKERS`, `CELERY_WORKERS`, `FLOWER_BASIC_AUTH` | Container runtime variables used by the deployment helper scripts. |

## Public install guidance

- Base install: `pip install doccano`
- PostgreSQL extra: `pip install 'doccano[postgresql]'`
- The package supports Python 3.10 and newer.

## Notes for deployment helpers

- The runtime helpers in `tools/` assume a container or repo checkout context, so treat them as wrappers around the commands above rather than as the only source of truth.
- If the local database is SQLite, remember that some deployments need the SQLite JSON1 extension.
