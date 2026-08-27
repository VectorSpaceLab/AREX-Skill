---
name: apod-api
description: "Use NASA's apod-api Flask service and standalone APOD parser for
  date, count, range, media, deployment, Docker, and troubleshooting workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# apod-api

Use this repo skill when a task involves NASA's Astronomy Picture of the Day
(APOD) service, its `/v1/apod/` Flask endpoint, the standalone
`apod_object_parser` helper, APOD HTML/media extraction, or running the service
locally or in Docker. This is an operating guide for the public `apod-api`
repository, not a replacement NASA API credential store.

## Route by task

- **Flask endpoint, query construction, response/error semantics, or service
  import:** read [api-service](sub-skills/api-service/SKILL.md).
- **NASA APOD JSON accessors, optional fields, asset download, or Pillow image
  conversion:** read [parser-and-media](sub-skills/parser-and-media/SKILL.md).
- **uv/dependency setup, Gunicorn, Docker/Compose, startup checks, or a bounded
  Locust profile:** read
  [deployment-and-operations](sub-skills/deployment-and-operations/SKILL.md).
- **Cross-cutting setup, upstream, packaging, credential, or asset failures:**
  read [root troubleshooting](references/troubleshooting.md), then follow the
  nearest sub-skill's more specific guide.

Keep the routes distinct: the Flask service scrapes APOD website HTML, while
`apod_object_parser.get_data(api_key)` calls NASA's separate JSON API. Do not
pass NASA JSON API parameters such as `api_key` to the Flask endpoint; the
implemented Flask handler rejects unknown fields.

## Public runtime facts

- Distribution metadata: `apod-api` version `1.1.0`, Python `>=3.12`.
- Runtime dependencies: Flask, Flask-CORS, Gunicorn, Jinja2, Pillow, Requests,
  urllib3, BeautifulSoup4, and Werkzeug.
- Primary endpoint: `GET /v1/apod/` with a trailing slash. It supports one
  date, a random `count` from 1–100, or an inclusive `start_date`/`end_date`
  range, plus `concept_tags`, `thumbs`, and legacy `hd` flags.
- The application has root and static routes, CORS configuration, a volatile
  process-local cache, and JSON error envelopes containing `service_version`,
  `msg`, and `code`.
- Live APOD results depend on outbound access to `https://apod.nasa.gov/apod/`.
  Concept tagging additionally depends on a protected `alchemy_api.key`; its
  absence is an expected degraded mode, not a reason to publish a secret.

## Minimal inspection

For a real repository checkout, install the declared runtime dependencies and
then run the bundled route inspector from this skill:

```bash
python sub-skills/api-service/scripts/run_service.py --help
python sub-skills/api-service/scripts/run_service.py --inspect-routes
```

The inspector imports the application and prints its routes without scraping
APOD. Keep the application working directory able to resolve its templates and
static assets. If the project metadata attempts an editable build and reports
multiple top-level packages, follow the dependency-only workaround in
[installation](sub-skills/deployment-and-operations/references/installation.md)
rather than claiming that `pip install -e .` succeeded.

## Freshness and provenance

Before applying this guide to a changed checkout, read
[repo provenance](references/repo-provenance.md). If the commit, package
version, dirty paths, or public entry points differ, use a refresh workflow
instead of assuming these facts remain current.

## Boundaries and safety

Do not put NASA keys, Alchemy credentials, or private deployment values in
commands, fixtures, Docker layers, or generated reports. Treat live endpoint
requests, image downloads, HTML scraping, and Locust as external-network
operations with explicit timeouts and bounded scope. Do not run a load test as
an ordinary startup check. The review/test artifacts for this skill live
outside this runtime tree and are not needed by a future Researcher.
