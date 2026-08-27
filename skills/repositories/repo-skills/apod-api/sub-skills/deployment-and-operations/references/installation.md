# Installation and environment

## Runtime contract

The repository declares package metadata version `1.1.0`, Python `>=3.12`, and
these public runtime dependencies:

- Flask
- Flask-CORS
- Gunicorn
- Jinja2
- Pillow
- Requests
- urllib3
- BeautifulSoup4
- Werkzeug

`locust`, `memory-profiler`, `pytest`, `pytest-cov`, and `ruff` are in the
`dev` dependency group. Locust is not required to import or serve the API.

## Recommended uv path

Run uv from a real checkout containing both `pyproject.toml` and `uv.lock`.
The lock file is the reproducible dependency input used by the repository's
Dockerfile.

```bash
cd <repo-root>
uv sync
uv run python application.py
```

For a production-like environment without development tools:

```bash
cd <repo-root>
uv sync --frozen --no-dev
uv run gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile - application:app
```

If uv reports a project-install/build-discovery error, keep the checkout on
`PYTHONPATH` and sync dependencies without trying to install the project itself:

```bash
cd <repo-root>
uv sync --frozen --no-dev --no-install-project
PYTHONPATH="$PWD" uv run python -c "from application import app; print(app.url_map)"
```

Do not run `uv sync` from the generated skill directory: it must resolve the
application's own `pyproject.toml` and lock file from the real checkout.

## Public pip-only alternative

There is no generated requirements file in the repository. A clean virtual
environment can install the public runtime packages directly:

```bash
cd <repo-root>
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install \
  "beautifulsoup4>=4.14.3" \
  "Flask>=3.1.2" \
  "Flask-CORS>=6.0.2" \
  "Gunicorn>=23.0.0" \
  "Jinja2>=3.1.6" \
  "Pillow>=12.2.0" \
  "Requests>=2.33.0" \
  "urllib3>=2.7.0" \
  "Werkzeug>=3.1.5"
```

Then run the import check with the checkout as the module root:

```bash
PYTHONPATH="$PWD" python -c "from application import app; print(app.url_map)"
```

Use an approved internal mirror or normal public PyPI configuration as
appropriate; this skill does not prescribe credentials or a private index.

## Important editable-install caveat

The current `pyproject.toml` does **not** declare a package layout, and default
setuptools flat-layout discovery sees the top-level `apod`, `apod_parser`,
`static`, `templates`, and `skills` directories as ambiguous. Consequently,
`python -m pip install -e .` is not a supported setup path and may fail with a
multiple-top-level-package discovery error. Do not hide or “fix” that fact by
inventing package configuration in an operations run.

When editable installation fails, use the dependency-only pip commands above
and inspect/run from the checkout with `PYTHONPATH="$PWD"`. With uv, prefer
`uv sync --frozen --no-dev --no-install-project` for the same dependency-only
inspection workaround. A non-editable package build is not a substitute for
this workaround unless the project packaging is intentionally changed and
verified separately.

## Assets and optional concept tagging

`application.py` renders `templates/home.html` and serves files from `static/`.
Keep those directories in the process working tree or image. At import time the
application attempts to read `alchemy_api.key` from the working directory; the
missing-file path is expected and logs that concept tagging is disabled. Treat
that file as a secret-bearing deployment input, not as a package or test
fixture.
