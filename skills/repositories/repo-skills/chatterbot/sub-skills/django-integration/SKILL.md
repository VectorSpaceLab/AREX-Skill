---
name: django-integration
description: "Use ChatterBot Django app integration, DjangoStorageAdapter,
  CHATTERBOT settings, migrations, swappable models, admin, views, and example
  project workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Django Integration

Use this sub-skill when a task asks how to add ChatterBot to a Django project, configure `chatterbot.ext.django_chatterbot`, run migrations, use `DjangoStorageAdapter`, customize statement/tag models, debug Django settings, or adapt the ChatterBot Django example app.

## Quick route

1. Read [references/django-api.md](references/django-api.md) for adapter, settings, models, and migration facts.
2. Read [references/workflows.md](references/workflows.md) for project setup, minimal settings, custom models, view/API wiring, and example app smoke checks.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for `ImproperlyConfigured`, missing apps, migrations, database aliases, and swappable model issues.
4. Run [scripts/django_config_smoke.py](scripts/django_config_smoke.py) for a safe in-memory Django configuration check.

## Required setup

A Django project must install both Django and ChatterBot:

```bash
python -m pip install django chatterbot
```

Add the app:

```python
INSTALLED_APPS = [
    # ...
    "chatterbot.ext.django_chatterbot",
]
```

Run migrations:

```bash
python manage.py migrate django_chatterbot
```

Then create a bot with Django storage:

```python
from chatterbot import ChatBot

bot = ChatBot(
    "Django Bot",
    storage_adapter="chatterbot.storage.DjangoStorageAdapter",
)
```

## ChatterBot Django settings

The extension provides default settings in `chatterbot.ext.django_chatterbot.settings`:

```python
CHATTERBOT = {
    "name": "ChatterBot",
    "storage_adapter": "chatterbot.storage.DjangoStorageAdapter",
    "django_app_name": "django_chatterbot",
}
```

In project settings, override `CHATTERBOT` as needed, but keep the Django storage adapter when using Django ORM tables.

## Swappable models

The default models are swappable:

- `CHATTERBOT_STATEMENT_MODEL`
- `CHATTERBOT_TAG_MODEL`

Use custom models only when you understand Django swappable model migration rules. For ordinary projects, prefer the default `Statement` and `Tag` models.

## Boundaries

- For raw SQL/Mongo/Redis storage, use [storage-adapters](../storage-adapters/SKILL.md).
- For core bot behavior and `get_response`, use [core-chatbot](../core-chatbot/SKILL.md).
- For training APIs, use [training](../training/SKILL.md).
- For logic adapter configuration, use [logic-adapters](../logic-adapters/SKILL.md).
