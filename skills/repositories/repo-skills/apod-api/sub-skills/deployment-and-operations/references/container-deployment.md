# Container and Compose deployment

## Source image behavior

The repository Dockerfile is based on `python:3.12-slim`, copies uv from the
pinned `ghcr.io/astral-sh/uv:0.9.26` image, installs the lockfile with
`uv sync --frozen --no-dev`, copies the application tree, exposes container port
`5000`, and starts:

```text
gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - application:app
```

The build must include `pyproject.toml`, `uv.lock`, `application.py`, the
`apod/` code, and the `templates/` and `static/` assets. The application import
uses relative working-directory lookups, so preserve the Dockerfile's
`WORKDIR` behavior rather than launching from an unrelated directory.

Build and run a single image from a real checkout:

```bash
cd <repo-root>
docker build -t apod-api:1.1.0 .
docker run --rm --name apod-api -p 5000:5000 \
  -e FLASK_ENV=production apod-api:1.1.0
```

The host mapping is `host:container`; the container listens on `5000`. A
published port does not make NASA APOD reachable if the container has no
outbound network route.

## Adapted Compose asset

[`scripts/docker-compose.apod-api.yml`](../scripts/docker-compose.apod-api.yml)
is an adapted skill asset, not a copy that assumes its own directory is the
application build context. It intentionally requires
`APOD_API_BUILD_CONTEXT`; set it to the real checkout and pass that checkout as
the Compose project directory:

```bash
APOD_API_BUILD_CONTEXT=<repo-root> \
  docker compose \
  -f <path-to-this-skill>/scripts/docker-compose.apod-api.yml \
  --project-directory <repo-root> up --build
```

The template maps `${APOD_API_HOST_PORT:-5000}:5000`, sets
`FLASK_ENV=${FLASK_ENV:-production}`, and deliberately does not mount or
materialize `alchemy_api.key`. Port `5000` is therefore the default public
host port and can be changed only by an explicit host-port override.

Inspect before starting and stop the foreground stack with `Ctrl-C`; for a
background stack, use the same explicit file and then:

```bash
docker compose -f <path-to-this-skill>/scripts/docker-compose.apod-api.yml \
  --project-directory <repo-root> ps
docker compose -f <path-to-this-skill>/scripts/docker-compose.apod-api.yml \
  --project-directory <repo-root> logs --tail=100 apod-api
docker compose -f <path-to-this-skill>/scripts/docker-compose.apod-api.yml \
  --project-directory <repo-root> down
```

Do not use `down -v` for this stateless service as a routine command, and do
not add credentials to the Compose YAML. If concept tagging is deliberately
enabled in an approved deployment, inject the credential through the platform's
secret/file mechanism and verify the process working directory separately.

## Bounded container check

After the service is listening, these checks do not invoke the external APOD
scraper:

```bash
curl --fail --max-time 5 http://127.0.0.1:5000/
curl --fail --max-time 5 http://127.0.0.1:5000/static/default_apod_object.json
```

Do not treat a successful `/` check as proof that `/v1/apod` can scrape NASA;
that route needs outbound APOD network access and may also need an API key for
the upstream request. Do not run a load test as an image or Compose smoke
check.
