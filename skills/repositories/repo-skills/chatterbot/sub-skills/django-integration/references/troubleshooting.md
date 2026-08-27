# Django Integration Troubleshooting

## `ImproperlyConfigured: Requested setting INSTALLED_APPS`

**Symptom**

Importing `chatterbot.ext.django_chatterbot.models` raises:

```text
django.core.exceptions.ImproperlyConfigured: Requested setting INSTALLED_APPS, but settings are not configured.
```

**Cause**

Django settings were not configured before importing model classes.

**Fix**

In a real Django project, set `DJANGO_SETTINGS_MODULE` and run inside Django. In a diagnostic script, configure settings and call `django.setup()` first:

```python
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["django.contrib.contenttypes", "chatterbot.ext.django_chatterbot"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    SECRET_KEY="diagnostic",
)
import django
django.setup()
```

Then import the models.

## App not installed or migrations missing

**Symptoms**

- `LookupError` from `apps.get_model`.
- Database table missing errors for `django_chatterbot_statement` or tags.
- `DjangoStorageAdapter` cannot create/filter statements.

**Fix**

1. Add `chatterbot.ext.django_chatterbot` to `INSTALLED_APPS`.
2. Run:

   ```bash
   python manage.py migrate django_chatterbot
   ```

3. If using multiple databases, migrate the database alias selected by `DjangoStorageAdapter(database=...)`.

## `CHATTERBOT` settings overwritten unexpectedly

The extension's settings module merges defaults into `CHATTERBOT`. Ensure your project settings are loaded before constructing `ChatBot`, and verify the final dict:

```python
from django.conf import settings
print(settings.CHATTERBOT)
```

Keep `storage_adapter` as `chatterbot.storage.DjangoStorageAdapter` for Django ORM tables.

## Custom swappable model mismatch

**Symptoms**

- `apps.get_model` cannot locate the configured model.
- Migrations create default models when custom models were expected.
- Tags many-to-many relation points to the wrong model.

**Fix**

- Define `CHATTERBOT_STATEMENT_MODEL` and `CHATTERBOT_TAG_MODEL` before migrations that depend on them.
- Ensure the custom models inherit or match `AbstractBaseStatement` and `AbstractBaseTag` fields/methods.
- Prefer defaults unless a custom model is required.
- If passing `statement_model` or `tag_model` kwargs to `DjangoStorageAdapter`, use valid `app_label.ModelName` strings.

## Database alias confusion

`DjangoStorageAdapter` defaults to `database="default"`. If a project uses multiple databases:

```python
ChatBot(
    "Bot",
    storage_adapter="chatterbot.storage.DjangoStorageAdapter",
    database="chatbot_db",
)
```

Make sure migrations ran on that alias and routers allow reads/writes for ChatterBot models.

## spaCy model missing inside Django

Django storage does not remove the default tagger requirement. If `ChatBot(**settings.CHATTERBOT)` fails with a spaCy model error, install the model for the configured language:

```bash
python -m spacy download en_core_web_sm
```

## View/API safety

Do not expose raw unbounded chatbot endpoints in production without application-level controls. Add validation, rate limiting, authentication if needed, and security scanning if experimental LLM adapters are enabled. ChatterBot does not include built-in prompt-injection or PII scanning.
