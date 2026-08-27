# Cross-Cutting Troubleshooting

## Missing spaCy model

**Symptoms**

- `OSError: [E050] Can't find model ...`
- ChatterBot raises a setup error saying the spaCy model for a language is missing.

**Cause**

The default `PosLemmaTagger` loads a language-specific spaCy model such as `en_core_web_sm`.

**Recovery**

1. Identify the language being used by `tagger_language`.
2. Install the matching model, for example:

   ```bash
   python -m spacy download en_core_web_sm
   ```

3. Rerun `python scripts/check_chatterbot_environment.py --check-spacy-model en_core_web_sm`.

For Redis vector storage, the storage adapter prefers `NoOpTagger`, but normal SQL/BestMatch workflows still need the spaCy model.

## Optional dependency import errors

**Symptoms**

- `Unable to import "pint"` from `UnitConversion`.
- `Unable to import "yaml"` from corpus loading.
- `ModuleNotFoundError: No module named 'pymongo'`, `redis`, `langchain_redis`, `ollama`, or `openai`.

**Recovery**

Install the smallest needed dependency:

```bash
python -m pip install pint                 # UnitConversion
python -m pip install pyyaml chatterbot-corpus
python -m pip install "chatterbot[mongodb]"
python -m pip install "chatterbot[redis]"
python -m pip install ollama openai        # LLM adapter clients, if needed
```

Do not install Redis, MongoDB, or LLM dependencies for ordinary SQL/list-training workflows.

## `ChatBot.get_response()` missing input

**Symptoms**

- `Either a statement object or a "text" keyword argument is required.`

**Cause**

`get_response()` accepts a string, a dict with `text`, a `Statement`, or `text=` keyword. It raises if neither is provided.

**Recovery**

Use one of:

```python
bot.get_response("Hello")
bot.get_response(text="Hello", conversation="session")
bot.get_response({"text": "Hello", "tags": ["greeting"]})
```

## Adapter validation failures

**Symptoms**

- `... must be a subclass of StorageAdapter`.
- `... must be a subclass of LogicAdapter`.
- A dictionary adapter config fails because it lacks `import_path`.

**Recovery**

Use a string import path or a dict with `import_path`:

```python
ChatBot(
    "Bot",
    storage_adapter="chatterbot.storage.SQLStorageAdapter",
    logic_adapters=[
        {"import_path": "chatterbot.logic.BestMatch"}
    ]
)
```

Do not pass a logic adapter where a storage adapter is expected, or vice versa.

## Service backend unavailable

**MongoDB symptoms**

- PyMongo server selection timeouts.
- Connection or authentication errors.

Check the URI, service status, credentials, TLS options, and whether the task actually needs MongoDB. For local development, the docs show a Docker `mongo:8.0` service.

**Redis symptoms**

- Redis connection failures.
- Missing vector index or embedding package errors.
- First run downloads a HuggingFace embedding model.

Confirm Redis Stack/vector-search support, `database_uri`, embedding provider packages, and model/provider credentials if using OpenAI or Cohere embeddings.

**LLM adapter symptoms**

- `Ollama library not installed`, connection refused, or missing model.
- OpenAI authentication/base URL errors.
- `ValueError: LLM logic adapters require a 'model' parameter`.

Install the client, provide `model`, and verify service/credentials before using LLM adapters. Keep LLM adapter examples out of offline smoke tests unless credentials and a model server are intentionally available.

## Training data problems

**Symptoms**

- `KeyError` mentioning `field_map`.
- No files detected for `CsvFileTrainer` or `JsonFileTrainer`.
- Corpus paths fail to load.

**Recovery**

- For CSV/TSV, match `field_map` values to headers or integer columns.
- For JSON, ensure the root has a `conversation` list and field names match `JsonFileTrainer.DEFAULT_STATEMENT_TO_KEY_MAPPING` or your custom mapping.
- For `ChatterBotCorpusTrainer`, install `pyyaml` and `chatterbot-corpus`, then use paths such as `chatterbot.corpus.english.greetings`.
- Use the training sub-skill scripts to generate tiny fixtures before running large corpora.

## Django settings not configured

**Symptoms**

- `django.core.exceptions.ImproperlyConfigured: Requested setting INSTALLED_APPS, but settings are not configured.`

**Cause**

The Django model module was imported before Django settings were configured.

**Recovery**

Set `DJANGO_SETTINGS_MODULE` or call `settings.configure(...)` and `django.setup()` before importing `chatterbot.ext.django_chatterbot.models`. In a real project, add `chatterbot.ext.django_chatterbot` to `INSTALLED_APPS` and run migrations.

## Avoid unsafe examples by default

- `terminal_example.py`, `learning_feedback_example.py`, `ollama_example.py`, and `openai_example.py` contain interactive loops, credentials, network calls, or service dependencies.
- `UbuntuCorpusTrainer` can download and process a large corpus. Use a tiny fixture or explicit `limit` for tests.
- Prefer bundled helper scripts in this skill for deterministic smoke checks.
