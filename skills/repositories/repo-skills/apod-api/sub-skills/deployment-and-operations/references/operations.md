# Local and production operations

## Bounded preflight

Run these from the real checkout. They import the application and render the
home page without calling the external APOD scraper:

```bash
cd <repo-root>
uv run python -c "from application import app; print(app.url_map)"
uv run python -c "from application import app; c=app.test_client(); r=c.get('/'); print(r.status_code); assert r.status_code == 200"
```

The import should expose `/`, `/static/<asset_path>`, `/v1/apod/`, and the
error handlers. A missing `alchemy_api.key` log is expected and means concept
tagging is disabled; it is not an import failure.

When a server is running, use short host-local checks:

```bash
curl --fail --max-time 5 http://127.0.0.1:5000/
curl --fail --max-time 5 http://127.0.0.1:5000/static/default_apod_image.jpg
```

These checks validate Flask startup, template/static availability, port
binding, and basic HTTP handling. The `/v1/apod` endpoint is intentionally not
a default health check because it scrapes NASA/APOD over the network.

## Development startup

The README's development command is:

```bash
cd <repo-root>
uv run python application.py
```

This uses the module's development server on `0.0.0.0:5000` and is suitable
for local iteration, not a production process manager. Stop it with `Ctrl-C`.
The Flask development server can be replaced for local inspection with:

```bash
uv run flask --app application:app run --host 0.0.0.0 --port 5000
```

Keep the working directory at the checkout root so the relative `templates/`,
`static/`, and optional `alchemy_api.key` lookups work.

## Production Gunicorn

Use four workers, bind all container/host interfaces on port `5000`, and send
access logs to stdout:

```bash
cd <repo-root>
uv run gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - application:app
```

The underlying command, when the environment is activated, is exactly:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - application:app
```

This is a long-running command. Run the import and local HTTP checks first;
stop it with `Ctrl-C` or the process supervisor's normal graceful-stop path.
Do not expose an unauthenticated development process directly to the Internet.

## Observability and live endpoint distinction

Gunicorn access logs show requests, including the bounded `/` and static checks.
A successful import or home-page response does not prove external APOD access.
For a deliberately approved single live request, use a short client timeout,
an appropriate upstream API key supplied through the caller's protected
mechanism, and no retry/load loop. Never put that key in this skill, an image
layer, Compose YAML, or a shell history transcript.

## Optional bounded Locust profile

The adapted [Locust file](../scripts/locustfile.py) preserves the source
weights: one ordinary dated request, three thumbnail requests, and five
requests without a date. It is an optional dev-group tool, not a minimum
installation. Its original dates are source-profile inputs; an upstream date
that is invalid or unavailable can produce an application error response.

Install/use the dev group only when the user explicitly requests a short load
profile:

```bash
cd <repo-root>
uv sync --frozen --group dev --no-install-project
APOD_API_HOST=http://127.0.0.1:5000 \
  uv run --group dev locust \
  -f <path-to-this-skill>/scripts/locustfile.py \
  --users 2 --spawn-rate 1 --run-time 30s --headless
```

The host can instead be supplied with Locust's `--host` option. A run is valid
only with an explicit target and explicit finite `--users`, `--spawn-rate`, and
`--run-time`; never use an unbounded interactive or production target by
accident. Do not run this profile during ordinary skill verification, and do
not use live credentials in its query strings.
