# APOD API shared troubleshooting

Read this guide when a failure crosses endpoint, parser, and deployment
boundaries. First classify it as **package/import**, **local service/assets**,
**input validation**, **upstream network/HTML**, or **credential/load
operations**.

## Package and import failures

- The declared runtime is Python `>=3.12`. Verify the active interpreter with
  `python --version`, then check `import flask, requests, bs4, PIL`.
- The repository's current flat layout is not editable-installable with default
  setuptools discovery: `apod`, `apod_parser`, `static`, `templates`, and
  `skills` are all visible top-level directories. If `pip install -e .` fails
  with “Multiple top-level packages discovered”, install the declared runtime
  dependencies without editable-installing the project and run from a checkout
  with its root on `PYTHONPATH`. See the deployment installation reference for
  the exact public dependency path.
- `ModuleNotFoundError: application` usually means the process was started
  outside the application checkout or without its root on the import path. It
  is different from a missing Flask dependency.
- Do not copy a local virtualenv, Conda prefix, or editable-install path into a
  public command or skill file.

## Local service and assets

- The service's canonical endpoint is `/v1/apod/` with a trailing slash. A
  no-slash client may see a redirect; clients that do not follow redirects
  should use the exact slash form.
- The root page and `/static/default_apod_object.json` are bounded local checks
  for Flask startup, templates, and static assets. They do not prove that the
  APOD scraper can reach NASA.
- `TemplateNotFound` or a static 404 means the process working directory or
  container image omitted `templates/` or `static/`. Preserve those assets in
  the service runtime and keep relative asset lookups rooted correctly.
- A port bind error is local resource contention. Choose an explicit unused
  host port or stop the approved conflicting process; do not retry blindly.

## Query and response errors

- A `400` with an allowed-field message means an unknown query name, invalid
  boolean, or invalid field combination. The Flask service does not accept
  `api_key`; that parameter belongs to NASA's separate JSON API helper.
- Use `YYYY-MM-DD`, dates from `1995-06-16` through the service's current date,
  `1 <= count <= 100`, and never combine `count` with date/range fields.
- A `404` can mean an unmapped route, missing static asset, or no usable data
  for a single requested date. Inspect the JSON `msg` and `code` rather than
  treating every 404 as the same failure.
- A `500` after valid input usually points to an upstream request failure,
  APOD HTML schema drift, or the optional concept-tag request. Retry a known
  historical date with `concept_tags=false` and a short client timeout before
  changing query syntax.

## External services and credentials

- `apod.utility.parse_apod` scrapes APOD HTML with Requests, urllib3, and
  BeautifulSoup. DNS/TLS failures, rate limits, APOD downtime, or markup
  changes can make it fail; source-level behavior cannot guarantee live uptime.
- `apod_object_parser.get_data(api_key)` uses NASA's JSON endpoint and needs a
  protected API key. Do not put that key in shell history, fixtures, images, or
  review output.
- `concept_tags=true` in the Flask service is an optional legacy Alchemy path.
  Without the local credential, the service returns a disabled message in the
  `concepts` field. This is expected; retry with `concept_tags=false` when
  isolating APOD scraping.
- Image downloads and Locust runs are network-affecting. Use the bundled safe
  downloader's timeout/dry-run controls and only run Locust with an explicit
  target, finite users, spawn rate, and run time.

## Freshness check

If implementation, templates, query fields, dependency metadata, or parser
signatures differ from the provenance snapshot, stop using this graph as an
exact API authority and request a refresh before relying on its details.
