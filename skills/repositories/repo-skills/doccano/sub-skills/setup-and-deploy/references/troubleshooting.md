# Setup and deploy troubleshooting

## Install and import failures

- If `doccano` is missing, confirm the package is installed in the active environment and that `python -m pip check` passes.
- If editable install or package import fails, check for mixed interpreters and reinstall in the same environment.
- If the build path expects Poetry or Yarn and one of them is missing, install the missing tool before retrying the package build.

## Database and startup failures

- `OperationalError` or "database unavailable" usually means the database service is not running or `DATABASE_URL` is wrong.
- `JSON_VALID` errors on SQLite mean the Python/SQLite build lacks JSON1 support.
- If `createuser` complains about a duplicate user or missing username/password, correct the CLI arguments and retry.

## Web and deployment failures

- Port conflicts are fixed by changing `--port` or the container port mapping.
- CSRF errors almost always mean the frontend origin is missing from `CSRF_TRUSTED_ORIGINS`.
- Missing bootstrap variables in container or cloud deployments are fixed by setting `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `ADMIN_EMAIL`.
- If Docker Compose starts but the UI cannot reach the backend, confirm the backend, broker, and database settings in the `.env` file.

## Package build failures

- Frontend build failures usually mean Node, Yarn, or the frontend dependencies are incomplete.
- Backend packaging failures usually mean Poetry could not find the expected temporary `pyproject.toml` layout or a dependency was not installed in the build environment.
- Static-file collection must run before the package build completes.
