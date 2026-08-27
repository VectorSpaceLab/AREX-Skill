# Deployment troubleshooting

Start with the cheapest distinction: dependency/import, listener/port,
static/template files, container build, or external APOD network. Keep live
network and credential-bound checks separate from local startup checks.

| Symptom | First check | Likely cause or route |
|---|---|---|
| `pip install -e .` reports multiple top-level packages | Inspect the project layout and packaging metadata | Expected flat-layout setuptools discovery ambiguity; use the dependency-only `venv` + `pip install` workaround in [installation](installation.md), not an invented editable install |
| `uv sync` tries to build/install the project and fails | Run `uv sync --frozen --no-dev --no-install-project` from a real checkout | The dependencies can be inspected without installing the ambiguous project; keep `PYTHONPATH` set to the checkout |
| `ModuleNotFoundError: flask` or `gunicorn` | Check `python -c 'import flask, gunicorn'` in the active environment | Wrong interpreter or dependencies not installed; use uv's environment or the public pip list |
| `from application import app` fails | Run from the checkout with `PYTHONPATH="$PWD"` | Wrong current directory, missing dependency, or source import error; do not debug endpoint semantics here |
| Import logs missing `alchemy_api.key` | Confirm whether concept tagging was actually required | Expected credential-bound behavior: concept tagging is disabled without the key; do not copy a secret into the skill or image |
| `TemplateNotFound` or a static 404 | Confirm `templates/` and `static/` are present and process cwd is the checkout/image workdir | Assets were omitted, copied to the wrong image path, or the process was launched from the wrong directory |
| Port 5000 is already in use | `ss -ltnp 'sport = :5000'` or choose an explicit host-port mapping | Stop the approved conflicting process or map another host port while keeping the container port at 5000 |
| Curl `/` fails but process appears alive | Check the Gunicorn/Flask logs, binding address, and host mapping | Service not ready, bound only elsewhere, crashed during import, or Docker port not published |
| Compose cannot find the build context | Inspect `APOD_API_BUILD_CONTEXT` and `--project-directory` | The adapted template is stored with the skill; point its build context at a real APOD checkout |
| Docker build fails during `uv sync --frozen` | Check `pyproject.toml`/`uv.lock` are in build context and inspect the exact uv error | Missing lock/project files or a dependency/network failure; do not silently drop `--frozen` for reproducibility |
| Container starts but `/` is fine and `/v1/apod` fails | Check outbound DNS/HTTPS from the container and upstream response | Live APOD scraping requires external network access; route query/response details to [api-service](../../api-service/SKILL.md) |
| Locust cannot import `locust` | Check that the dev dependency group was installed | Optional tool is not part of the minimum environment; use `uv sync --frozen --group dev --no-install-project` only for an approved bounded run |
| Locust starts against an unintended target | Stop immediately and inspect `APOD_API_HOST`/`--host` | Every run needs an explicit finite target and duration; never run unbounded load against production |
| Concept tagging is unexpectedly unavailable | Check the protected deployment secret/file mechanism | `alchemy_api.key` is optional and credential-bound; absence deliberately disables tagging |

## Compose port/template diagnostic

For a synthetic deployment check, verify all of the following before starting
anything:

1. The Compose file is passed by an explicit `-f` path.
2. `APOD_API_BUILD_CONTEXT` points to a real checkout containing the Dockerfile
   and lock/project files.
3. `--project-directory` is the real checkout when relative Docker paths or
   environment files are involved.
4. The rendered service maps `${APOD_API_HOST_PORT:-5000}:5000` and does not
   publish a credential.
5. A bounded `/` or static check is planned before any optional live endpoint
   or Locust request.

Use `docker compose ... config` as a read-only render check before `up`; it
need not start a container. If a host port is changed, the URL for local
checks must use that host port while the application remains on container port
`5000`.

## Required-backend and network limits

There is no accelerator-specific runtime requirement for this Flask service.
The difficult environment dependency is outbound access to NASA/APOD for live
scraping, plus any separately approved credential for concept tagging. Native
live-load checks are intentionally skipped-expensive. Keep unresolved DNS,
proxy, upstream availability, API-key policy, and container-registry access
explicit rather than claiming a fully verified deployment.
