# Django Integration API Reference

## When to read

Read this before importing ChatterBot Django models, configuring `DjangoStorageAdapter`, adding migrations, or customizing statement/tag models.

## App and settings

The Django app module is:

```python
"chatterbot.ext.django_chatterbot"
```

Default ChatterBot Django settings merge these values into `CHATTERBOT`:

```python
{
    "name": "ChatterBot",
    "storage_adapter": "chatterbot.storage.DjangoStorageAdapter",
    "django_app_name": "django_chatterbot",
}
```

In a Django project, set `CHATTERBOT` in settings when you need custom logic adapters, name, database alias, or storage options.

## `DjangoStorageAdapter`

Constructor:

```python
DjangoStorageAdapter(**kwargs)
```

Important kwargs:

| Keyword | Meaning |
| --- | --- |
| `django_app_name` | app label used to locate default models; defaults to `django_chatterbot` |
| `database` | Django database alias; defaults to `default` |
| `statement_model` | dotted app/model path; defaults from `CHATTERBOT_STATEMENT_MODEL` setting or `<app>.Statement` |
| `tag_model` | dotted app/model path; defaults from `CHATTERBOT_TAG_MODEL` setting or `<app>.Tag` |

The adapter implements the common storage interface: `count`, `filter`, `create`, `create_many`, `update`, `get_random`, `remove`, and `drop`.

## Models

Default model classes:

```python
from chatterbot.ext.django_chatterbot.models import Statement, Tag
```

They inherit abstract base classes:

- `AbstractBaseStatement`
- `AbstractBaseTag`

`Statement` is swappable through `CHATTERBOT_STATEMENT_MODEL`. `Tag` is swappable through `CHATTERBOT_TAG_MODEL`.

Default `Statement` fields include:

- `text`
- `search_text`
- `conversation`
- `created_at`
- `in_response_to`
- `search_in_response_to`
- `persona`
- many-to-many `tags`

The abstract model defines indexes on `search_text` and `search_in_response_to` with names `idx_cb_search_text` and `idx_cb_search_in_response_to`.

## Migrations and admin

The package includes migrations under the Django app. Add the app to `INSTALLED_APPS`, then run:

```bash
python manage.py migrate django_chatterbot
```

Admin registration is provided for default `Statement` and `Tag` models through `chatterbot.ext.django_chatterbot.admin`.

## Model import rule

Do not import `chatterbot.ext.django_chatterbot.models` before Django settings are configured. This is normal Django behavior. Either run inside a configured Django process or explicitly configure settings and call `django.setup()` for diagnostics.

## Test-backed behavior

Repo tests cover:

- basic Django storage CRUD and filtering;
- ChatBot response flow with Django storage;
- corpus training through Django storage;
- `database` alias acceptance;
- custom model and settings behavior;
- settings defaults.

Use these as native verification anchors only in a prepared Django test environment.
