# Django Integration Workflows

## Add ChatterBot to a Django project

Install dependencies:

```bash
python -m pip install django chatterbot
```

Add the app to settings:

```python
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "chatterbot.ext.django_chatterbot",
]
```

Run migrations:

```bash
python manage.py migrate django_chatterbot
```

Configure a bot:

```python
CHATTERBOT = {
    "name": "Django ChatterBot",
    "storage_adapter": "chatterbot.storage.DjangoStorageAdapter",
    "logic_adapters": [
        {"import_path": "chatterbot.logic.BestMatch"},
        {"import_path": "chatterbot.logic.MathematicalEvaluation"},
    ],
}
```

Use it in application code after Django settings are configured:

```python
from django.conf import settings
from chatterbot import ChatBot

bot = ChatBot(**settings.CHATTERBOT)
response = bot.get_response("Hello", conversation="web-session")
```

## Minimal settings smoke outside a project

For diagnostics only, configure settings in memory before importing models:

```python
from django.conf import settings

settings.configure(
    INSTALLED_APPS=["django.contrib.contenttypes", "chatterbot.ext.django_chatterbot"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    SECRET_KEY="diagnostic",
    USE_TZ=True,
)

import django
django.setup()

from chatterbot.ext.django_chatterbot.models import Statement
print(Statement)
```

Run the bundled smoke helper:

```bash
python sub-skills/django-integration/scripts/django_config_smoke.py
```

## Use a database alias

`DjangoStorageAdapter` accepts a `database` alias:

```python
bot = ChatBot(
    "Secondary DB Bot",
    storage_adapter="chatterbot.storage.DjangoStorageAdapter",
    database="default",
)
```

If using multiple databases, ensure migrations have run on the selected alias and your routers allow the ChatterBot models there.

## Custom statement/tag models

Prefer defaults unless you need additional fields or app-level model ownership. If customizing:

```python
CHATTERBOT_STATEMENT_MODEL = "myapp.CustomStatement"
CHATTERBOT_TAG_MODEL = "myapp.CustomTag"
```

Your models should inherit or match the behavior of `AbstractBaseStatement` and `AbstractBaseTag`. Plan migrations carefully because Django swappable models must be in place before dependent migrations are created.

`DjangoStorageAdapter` also accepts explicit model paths:

```python
bot = ChatBot(
    "Custom Model Bot",
    storage_adapter="chatterbot.storage.DjangoStorageAdapter",
    statement_model="myapp.CustomStatement",
    tag_model="myapp.CustomTag",
)
```

## Example app pattern

The ChatterBot example app uses the standard Django workflow:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

For future agents, treat the example as a pattern, not as a runtime dependency. In a new project:

1. add the ChatterBot app to `INSTALLED_APPS`;
2. run migrations;
3. instantiate `ChatBot` from settings in views or service code;
4. pass a stable `conversation` value derived from the user session;
5. serialize `response.text` rather than the whole `Statement` object unless the API explicitly needs metadata.

## Training in Django storage

Once migrations are applied, trainers work with Django storage the same way as SQL storage:

```python
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer

bot = ChatBot(
    "Django Training Bot",
    storage_adapter="chatterbot.storage.DjangoStorageAdapter",
)
trainer = ListTrainer(bot, show_training_progress=False)
trainer.train(["Hello", "Hi there!"])
```

For corpus training, install `pyyaml` and `chatterbot-corpus` and make sure the Django database is ready before training.

## Views and APIs

A minimal view shape is:

```python
from django.http import JsonResponse
from django.conf import settings
from chatterbot import ChatBot

chatbot = ChatBot(**settings.CHATTERBOT)

def chat(request):
    text = request.GET.get("text", "")
    response = chatbot.get_response(text, conversation=request.session.session_key or "anonymous")
    return JsonResponse({"text": response.text, "confidence": response.confidence})
```

Add application-level validation, rate limiting, and security checks before production use, especially if LLM adapters or external services are configured.
