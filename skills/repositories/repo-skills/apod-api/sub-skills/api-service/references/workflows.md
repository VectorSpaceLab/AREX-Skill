# Service workflows

These workflows are intentionally bounded. Help and route inspection import the
Flask module but do not issue APOD requests. An actual API query does contact
the live APOD website and should be treated as external-network activity.

## 1. Prepare a local runtime

Use the public project dependency workflow from the project root:

```bash
uv sync
```

The project declares Flask, Flask-CORS, Gunicorn, Jinja2, Pillow, Requests,
urllib3, BeautifulSoup4, and Werkzeug as runtime dependencies. The application
is importable when those dependencies are available and the project root is on
Python's import path.

Do not paper over the packaging defect with `pip install -e .`. The current
metadata is not editable-installable through default setuptools flat-layout
discovery because the top-level `apod`, `apod_parser`, `static`, `templates`,
and `skills` directories are ambiguous package candidates. `uv sync` is the
supported dependency setup; alternatively, use an environment with the
runtime dependencies installed and run commands from the project root. This
sub-skill does not require `alchemy_api.key` for ordinary APOD requests.

## 2. Inspect the service without network access

From the project root, run the bundled launcher:

```bash
python skills/disco/apod-api/sub-skills/api-service/scripts/run_service.py --help
python skills/disco/apod-api/sub-skills/api-service/scripts/run_service.py --inspect-routes
```

The first command prints usage and exits. The second imports the application,
prints `service_version=v1`, and should list at least:

```text
GET /
GET /static/<asset_path>
GET /v1/apod/
```

The import reads the optional credential file if one happens to exist in the
process working directory, but it does not call APOD. Absence of that file is
expected and leaves concept tagging disabled. If imports fail, fix the runtime
environment before trying a live request.

## 3. Run a bounded development service

Choose the host and port explicitly and keep the launcher bounded:

```bash
python skills/disco/apod-api/sub-skills/api-service/scripts/run_service.py \
  --serve --host 127.0.0.1 --port 5000 --duration 30
```

The wrapper serves `application:app` for at most 30 seconds, then shuts down.
It does not issue an APOD request on startup. `--duration` is capped by the
wrapper; use a separate deployment/operations workflow for an intentionally
long-lived Gunicorn or container service. The wrapper's bound only covers the
server lifetime; give API clients their own request timeout because the
underlying scraper uses the external APOD request path.

## 4. Query one APOD object

While the bounded server is running, use the exact trailing-slash endpoint:

```bash
curl -i --max-time 15 \
  'http://127.0.0.1:5000/v1/apod/?date=2014-10-01&concept_tags=false'
```

Expected observations for a healthy upstream page are HTTP 200,
`Content-Type: application/json`, a JSON object with `date`, `title`,
`explanation`, `media_type`, `url` when available, and `service_version: "v1"`.
The result may also contain `hdurl`, `copyright`, or other media-specific
fields. Do not add NASA's `api_key` query parameter; this service scrapes the
APOD website directly and rejects that field.

For the current page, omit `date`:

```bash
curl -i --max-time 15 'http://127.0.0.1:5000/v1/apod/'
```

This is live and may fail if APOD is unavailable or its HTML has changed.

## 5. Query random and range arrays

Request a bounded random sample:

```bash
curl -i --max-time 30 \
  'http://127.0.0.1:5000/v1/apod/?count=3&thumbs=True'
```

Request an inclusive range:

```bash
curl -i --max-time 30 \
  'http://127.0.0.1:5000/v1/apod/?start_date=2017-07-08&end_date=2017-07-10'
```

Both successful forms return a JSON array. A range with no `end_date` runs to
the service's current date and can be slow and network-heavy; prefer a short
explicit range for smoke checks. `count` accepts 1 through 100 and cannot be
combined with any date or range selector.

## 6. Check HTML and static behavior

The home page is useful for confirming that templates are present:

```bash
curl -i --max-time 5 'http://127.0.0.1:5000/'
```

The static fixture is a local, offline check of the static route:

```bash
curl -i --max-time 5 \
  'http://127.0.0.1:5000/static/default_apod_object.json'
```

A successful fixture response is JSON describing a `Default Image`; it does
not prove that the live APOD scraper is healthy and is not automatically used
as the API response fallback.

## 7. Route adjacent work correctly

Use [parser-and-media](../../parser-and-media/SKILL.md) for accessors, JSON
field extraction, asset download, and Pillow conversion. Use
[deployment-and-operations](../../deployment-and-operations/SKILL.md) for
Gunicorn, Docker/Compose, and load-profile procedures. Use the shared
[troubleshooting guide](../../../references/troubleshooting.md) when the failure
crosses service, parser, and deployment boundaries.
