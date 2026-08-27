# Cross-Cutting Troubleshooting

Use this reference when a Serenata de Amor task fails before it clearly belongs to Rosie, Jarbas API, or service/data operations.

## Legacy dependency stack

Symptoms:

- Import errors in old dependencies such as Celery/Kombu, Django, scikit-learn, pandas, NumPy, or `serenata-toolbox`.
- Errors mentioning removed legacy names such as `np.str` or `np.int`.
- Old debugger/test dependencies failing to install because their setup metadata uses removed packaging fields.

Likely causes:

- The repository was tested with Python 3.6-era CI and pinned 2019 dependencies.
- Modern Python, NumPy, Django, or packaging-tool versions can break old code paths.

Recovery:

1. Prefer a legacy-compatible Python environment for inspection or maintenance.
2. Install the pinned runtime requirements before trying to run native commands.
3. Do not upgrade NumPy/Django/scikit-learn unless the task is explicitly modernization; if you modernize, refresh this skill after verifying behavior.
4. If Celery/Kombu entry-point loading fails, check the `importlib-metadata` version and pin to an older compatible release if needed.

## This repo is not a pip package

Symptoms:

- `pip install -e .` fails because there is no `setup.py` or `pyproject.toml`.
- `python -c "import jarbas"` or `python -c "import rosie"` works only from some directories.

Recovery:

- Treat `jarbas/` and `rosie/` as application source roots, not package distribution metadata.
- For a local checkout, add the repository root and the `rosie/` directory to the import path when running diagnostic scripts.
- Use the bundled [scripts/check_serenata_imports.py](../scripts/check_serenata_imports.py) with `--repo-root <serenata-checkout>` for a safe import preflight.

## Missing configuration

Symptoms:

- `SECRET_KEY` or `DATABASE_URL` errors during Django import/check.
- Django settings import succeeds in one shell but not another.

Recovery:

1. For real service use, prepare a proper `.env` from the public sample variables and never invent production secrets.
2. For read-only checks, the bundled preflight scripts can inject unsafe check-only defaults.
3. If the task involves actual data loading or serving, route to `sub-skills/deployment-and-data-ops/` before running migrations or management commands.

## Service boundaries

- Full Jarbas API/search behavior uses PostgreSQL-specific fields and `SearchVector`. SQLite system checks are not equivalent to production/search verification.
- RabbitMQ/Celery, memcached, Docker, Node/Elm, Twitter credentials, DigitalOcean credentials, and external dataset APIs are not required for safe import checks.
- Do not start services, download large datasets, publish tweets, or mutate infrastructure unless the user authorizes the exact action and target.

## Boundary routing

- If the failure is about `rosie.py`, classifier columns, model caches, data downloads, or `suspicions.xz`, use `sub-skills/rosie-suspicion-pipeline/`.
- If the failure is about API endpoints, query strings, serializer output, receipts, company lookups, or search results, use `sub-skills/jarbas-data-api/`.
- If the failure is about `.env`, Docker Compose, PostgreSQL, migrations, sample data loads, management commands, Celery/cache, static assets, or maintenance scripts, use `sub-skills/deployment-and-data-ops/`.
