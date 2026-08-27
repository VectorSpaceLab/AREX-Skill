# Argilla cross-cutting troubleshooting

Use this for quick triage, then route to the nearest sub-skill for full details.

## Missing API key or default client errors

Symptoms:

- `Argilla SDK error: ArgillaError: Missing api_key. You must provide a valid API key.`
- Field/question constructors fail even before `dataset.create()`.

Likely cause: the SDK resource constructor tried to use a default `rg.Argilla()` client, but no `ARGILLA_API_KEY` or explicit client was available.

Recovery:

1. Build `client = rg.Argilla(api_url=..., api_key=...)` first.
2. Pass `client=client` to `rg.Dataset`, `rg.User`, `rg.Workspace`, and other resources that accept it.
3. For field/question constructors that do not expose `client`, ensure a valid default client exists first, or build them after the explicit client is active.
4. Read `sub-skills/python-sdk/references/troubleshooting.md` for SDK-specific patterns.

## API URL, private Space, or authentication failures

Symptoms:

- 401/403 from SDK calls.
- Browser URL differs from SDK API URL.
- Private Hugging Face Space is visible in browser but SDK cannot connect.

Recovery:

1. Use the direct Space URL pattern such as `https://<owner>-<space>.hf.space` when the Hub embeds the UI.
2. Keep `api_key` as the Argilla API key from the Argilla UI settings page.
3. For private Spaces, add the Hugging Face token as an HTTP header: `headers={"Authorization": f"Bearer {HF_TOKEN}"}`.
4. Check user role/workspace access in `python-sdk`; check OAuth/Spaces settings in `server-ops`.

## Server starts but search/filter/vector results are wrong or empty

Likely causes:

- Search engine URL/backend mismatch.
- Elasticsearch/OpenSearch version issue.
- Dataset indexes need reindexing after migration or configuration change.
- Redis/background worker not running for jobs that populate data.

Recovery:

1. Read `sub-skills/server-ops/references/troubleshooting.md`.
2. Confirm `ARGILLA_ELASTICSEARCH`, `ARGILLA_SEARCH_ENGINE`, and service logs.
3. Reindex intentionally with `REINDEX_DATASETS=1` at Docker startup or `python -m argilla_server search-engine reindex` after backup/approval.
4. For SDK vector/query syntax, also read `sub-skills/python-sdk/references/data-formats.md`.

## Docker, database, Redis, or persistent storage problems

Symptoms:

- UI does not load at port 6900.
- Data disappears after Space restart.
- Worker jobs stay pending.
- PostgreSQL/SQLite lock or connection errors.

Recovery:

1. Use `server-ops`; inspect Docker/Space logs before changing data.
2. Persist `ARGILLA_HOME_PATH` and database/search volumes.
3. Keep server and worker processes on the same `ARGILLA_DATABASE_URL`, `ARGILLA_REDIS_URL`, `ARGILLA_ELASTICSEARCH`, and `ARGILLA_HOME_PATH` values.
4. For Spaces beyond testing, enable persistent storage before creating important datasets.

## Legacy migration confusion

Symptoms:

- User mentions Rubrix, Argilla v1, `DatasetForTextClassification`, token/text2text legacy datasets, old training/monitoring APIs, or `argilla_v1`.
- Current Argilla 2.x server no longer displays legacy task datasets.

Recovery:

1. Route to `sub-skills/legacy-migration/SKILL.md`.
2. Export or snapshot source data before target writes.
3. Do not install old broad `argilla-v1` extras into the current server env; use a separate legacy environment if needed.
4. Route deployment/reindex mechanics back to `server-ops`.

## CLI dependency issue

Symptom:

```text
TypeError: Secondary flag is not valid for non-boolean flag.
```

Likely cause: `argilla_server` uses Typer command definitions with boolean flags such as `--access-log/--no-access-log`; incompatible Click/Typer versions can break help rendering.

Recovery:

1. Check `python -m argilla_server --help`.
2. Prefer package-resolved versions from a fresh install. If manually pinning, use a compatible Typer/Click pair such as Typer 0.9.x with Click 8.1.x for this snapshot.
3. Run `python sub-skills/server-ops/scripts/check_server_cli.py --group all` after adjusting dependencies.
