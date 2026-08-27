---
name: chatterbot
description: "Operate ChatterBot conversational dialog engine workflows,
  including chatbot setup, training, logic adapters, storage backends, Django
  integration, and optional LLM adapters."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# ChatterBot Repo Skill

Use this skill when a task involves the `ChatterBot` Python package, the `chatterbot` import, conversational dialog bots that learn from statements/responses, ChatterBot trainers, ChatterBot storage adapters, built-in logic adapters, the Django extension, or errors from those APIs.

ChatterBot is a Python conversational dialog engine. A `ChatBot` instance combines:

- storage adapters that persist `Statement` objects;
- logic adapters that choose responses and assign confidence scores;
- preprocessors, taggers, comparison functions, and search algorithms;
- trainers that load list, corpus, CSV/TSV, JSON, or Ubuntu corpus style data.

## Install

Public install commands:

```bash
python -m pip install chatterbot
python -m pip install -e .
```

Install optional groups only when the selected workflow needs them:

```bash
python -m pip install "chatterbot[dev]"       # Pint, PyYAML, chatterbot-corpus, Ollama/OpenAI clients
python -m pip install "chatterbot[redis]"     # Redis vector storage and embedding providers
python -m pip install "chatterbot[mongodb]"   # MongoDB storage
python -m pip install django                 # Django integration if you are not using a broader extra
```

The default `ChatBot("name")` path uses SQL storage plus the `PosLemmaTagger`, which requires a compatible spaCy language model such as `en_core_web_sm` for English. If a quick import-only check is enough, do not instantiate `ChatBot` until the model requirement is understood.

## First checks

For a package install, start with:

```bash
python - <<'PY'
import chatterbot
from chatterbot import ChatBot
print(chatterbot.__version__)
print(ChatBot)
PY
```

Run the bundled environment diagnostic when install/import behavior is unclear:

```bash
python scripts/check_chatterbot_environment.py --check-spacy-model en_core_web_sm
```

The only package CLI is a small module entry point:

```bash
python -m chatterbot --version
python -m chatterbot --help
```

Read [references/installation-and-extras.md](references/installation-and-extras.md) for public install commands, optional extras, spaCy model setup, and service-backend prerequisites. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting setup, model, optional dependency, and service failures. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a newer checkout.

## Route by task

### Core chatbot behavior

Use [core-chatbot](sub-skills/core-chatbot/SKILL.md) when the task is about:

- creating `ChatBot` or `Statement` objects;
- `get_response`, `generate_response`, `learn_response`, conversation IDs, `read_only`, or persistence behavior;
- preprocessors, taggers, language model selection, comparisons, search, response selection, and filters;
- core CLI/version checks or basic smoke tests.

### Training and corpora

Use [training](sub-skills/training/SKILL.md) when the task is about:

- `ListTrainer`, `ChatterBotCorpusTrainer`, `CsvFileTrainer`, `JsonFileTrainer`, or `UbuntuCorpusTrainer`;
- `chatterbot-corpus`, dotted corpus paths, custom YAML corpora, or corpus loading;
- CSV/TSV/JSON field maps, training data schemas, progress controls, or exporting learned pairs.

### Logic adapters and LLM/tool adapters

Use [logic-adapters](sub-skills/logic-adapters/SKILL.md) when the task is about:

- `BestMatch`, `SpecificResponseAdapter`, `MathematicalEvaluation`, `TimeLogicAdapter`, `UnitConversion`;
- `default_response`, `maximum_similarity_threshold`, `excluded_words`, comparison functions, and response selection methods;
- implementing custom logic adapters;
- experimental `OllamaLogicAdapter` / `OpenAILogicAdapter` and `logic_adapters_as_tools` MCP-style tool calling.

### Storage adapters and retrieval backends

Use [storage-adapters](sub-skills/storage-adapters/SKILL.md) when the task is about:

- `SQLStorageAdapter`, SQLite/SQLAlchemy configuration, SQL pool options, or CRUD/filter behavior;
- `MongoDatabaseAdapter`, MongoDB URIs, TLS kwargs, or unavailable MongoDB service errors;
- `RedisVectorStorageAdapter`, Redis vector search, embedding model/provider options, or semantic search behavior;
- writing a custom `StorageAdapter`.

### Django integration

Use [django-integration](sub-skills/django-integration/SKILL.md) when the task is about:

- `chatterbot.ext.django_chatterbot`, `INSTALLED_APPS`, migrations, or Django settings;
- `DjangoStorageAdapter`, database aliases, swappable `Statement`/`Tag` models;
- Django views/admin/API wiring or the ChatterBot Django example pattern.

## Important constraints

- Do not assume `ChatBot("name")` works before a spaCy model is installed. Missing model errors usually tell the user to run `python -m spacy download <model>`.
- Use `database_uri=None` for in-memory SQL smoke tests and `database_uri="sqlite:///file.sqlite3"` for a persistent SQLite file.
- The Redis, MongoDB, Ollama, and OpenAI paths need optional packages and external services or credentials. Treat them as optional unless the user explicitly chooses them.
- `UnitConversion` needs `pint`; corpus training needs `pyyaml` and usually `chatterbot-corpus`; Django workflows need `django`.
- Avoid running examples that open an infinite input loop, start services, download large corpora, call model providers, or require API keys unless the user explicitly asks.

## Bundled helpers

- `scripts/check_chatterbot_environment.py` checks imports, metadata, spaCy models, and optional dependency availability.
- Sub-skills include small smoke/demo helpers for core chat, training, logic adapters, SQL storage, optional-backend dependency checks, and Django configuration.

These helpers are self-contained and do not require the original repository checkout.
