---
name: deployment-and-operations
description: "Install, start, containerize, operate, and safely load-test the
  APOD Flask service."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Deployment and Operations

Use this sub-skill when the task is to install the public runtime dependencies,
start APOD locally, run the production Gunicorn server, build or compose the
container, perform a bounded startup check, or run the optional weighted
Locust profile. The service is Python `>=3.12` and the package metadata version
is `1.1.0`.

## Route here for

- `uv sync`, public dependency installation, or a failed `pip install -e .`
- `gunicorn application:app` and port `5000` startup
- Docker image builds, Compose port mappings, and container startup
- Static/template asset checks and bounded service smoke checks
- A deliberately short Locust run against an explicitly named target

## Route away

- APOD query parameters, response shapes, and endpoint semantics →
  [api-service](../api-service/SKILL.md)
- HTML scraping, media parsing, image handling, or parser behavior →
  [parser-and-media](../parser-and-media/SKILL.md)
- Cross-cutting failure triage → [root troubleshooting](../../references/troubleshooting.md)

## Read next

1. Read [installation](references/installation.md) for Python `>=3.12`, uv,
   public pip alternatives, and the flat-layout packaging caveat.
2. Read [container deployment](references/container-deployment.md) for the
   source Docker behavior and the adapted [Compose template](scripts/docker-compose.apod-api.yml).
3. Read [operations](references/operations.md) for bounded startup checks,
   Gunicorn, shutdown, and the optional [Locust profile](scripts/locustfile.py).
4. Read [troubleshooting](references/troubleshooting.md) for packaging,
   import, port, asset, Docker, network, and credential-bound failures.

## Safety boundaries

- External NASA APOD access is required for live `/v1/apod` scraping. Import,
  `/`, and static-asset checks are the default bounded checks; do not start a
  live load test as part of ordinary setup.
- Locust is a development-only optional group, not a minimum runtime
  dependency. Every load run must supply an explicit host and finite users,
  spawn rate, and run time.
- `alchemy_api.key` is credential-bound. Without that file, concept tagging is
  disabled by design; never bake credentials into an image, Compose asset, or
  command transcript.
- The application must run with its working directory at the checkout root so
  `templates/`, `static/`, and the optional key lookup resolve as intended.

## Canonical production command

From a real checkout after dependencies are available, the production entry
point is exactly:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - application:app
```

Use `uv run gunicorn ...` when uv owns the environment. The command starts a
long-running service; use the bounded checks in [operations](references/operations.md)
first when the request is only to validate installation.
