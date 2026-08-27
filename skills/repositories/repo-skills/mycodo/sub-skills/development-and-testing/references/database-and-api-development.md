# Database And API Development

Read this for source changes involving Mycodo's settings database, Alembic migrations, Flask API resources, schemas, or forms.

## Settings database and migrations

- The settings database is SQLite in the installed layout and is represented by SQLAlchemy models under `mycodo/databases/models`.
- Alembic migration files and environment live under `alembic_db/`.
- The inspected config reports an Alembic version constant; future changes must keep config, migration scripts, and upgrade behavior aligned.
- Post-upgrade hooks exist for data transformations that are not pure schema migrations.

When changing a model:

1. Identify the model and all Flask forms/API schemas/controllers that read/write it.
2. Add or update an Alembic migration.
3. Consider backup/restore/import/export compatibility.
4. Add focused tests or fixtures for default values and upgrade behavior.
5. Update docs if the setting is user-facing.

## Flask API development

API resources live under `mycodo/mycodo_flask/api`. Mycodo uses versioned REST media types; API v1 examples use `Accept: application/vnd.mycodo.v1+json`. Installed API docs are served at `/api`.

When editing an endpoint:

1. Locate the namespace/resource class and route decorators.
2. Confirm method(s): `GET`, `POST`, `PUT`, `PATCH`, `DELETE`.
3. Update request/response models, schema fields, permissions, and error codes.
4. Add focused tests under software tests.
5. Update API references and multi-channel docs when public behavior changes.
6. Route automation usage guidance to `api-and-automation`.

## Multi-channel API changes

Multi-channel endpoints improve clients that need several measurement channels in one request. Preserve:

- channel IDs and measurement IDs,
- request shape and status codes,
- response grouping and missing-channel errors,
- backward compatibility for single-channel clients when possible.

## Forms/templates/static changes

Flask forms live under `mycodo/mycodo_flask/forms`; templates and static assets live under `templates` and `static`. For user-visible text, check translation implications. For dashboard/widget changes, verify browser-side behavior and server endpoints.

## Database/API troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Test app creation fails | missing dependency, config import side effect, model initialization error | run import smoke; isolate the changed model/form/API import |
| API route returns 406/unsupported media | wrong `Accept` header or version negotiation | use v1 media type and endpoint docs |
| API 4xx after model change | schema/model mismatch or missing required field | inspect request parser/model, SQLAlchemy defaults, and tests |
| Alembic version mismatch | migration not applied or config constant stale | review migration head and upgrade logs |
| Import/export loses settings | model field not included or version compatibility missed | test settings export/import path and update docs |
