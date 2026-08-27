---
name: storage-adapters
description: "Use ChatterBot SQL, MongoDB, Redis vector, and custom storage
  adapters, including database_uri, filters, tags, and optional backend
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Storage Adapters

Use this sub-skill when a task asks how ChatterBot stores statements, chooses SQL vs MongoDB vs Redis vector storage, configures `database_uri`, writes or filters statement records, debugs service backends, or implements a custom storage adapter.

## Quick route

1. Read [references/storage-api.md](references/storage-api.md) for storage adapter classes, methods, filter kwargs, and backend-specific configuration.
2. Read [references/workflows.md](references/workflows.md) for SQL, MongoDB, Redis vector, tag filtering, custom adapter, and service setup recipes.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for SQLite file confusion, MongoDB service timeouts, Redis vector dependencies, missing optional packages, and search mismatch issues.
4. Run [scripts/sql_storage_smoke.py](scripts/sql_storage_smoke.py) for a deterministic SQL storage CRUD/filter smoke test.
5. Run [scripts/storage_dependency_check.py](scripts/storage_dependency_check.py) before selecting MongoDB or Redis vector storage.

## Built-in storage choices

| Adapter | Best for | Prerequisites |
| --- | --- | --- |
| `SQLStorageAdapter` | default storage, SQLite, SQLAlchemy-supported databases, exact/indexed text matching | base package; database driver for non-SQLite URIs |
| `MongoDatabaseAdapter` | flexible NoSQL statement documents | `pymongo`, reachable MongoDB service |
| `RedisVectorStorageAdapter` | experimental semantic vector search with embeddings | `chatterbot[redis]`, Redis Stack/vector search service, embedding model/provider |
| `DjangoStorageAdapter` | Django ORM integration | route to [django-integration](../django-integration/SKILL.md) |

## Default SQL behavior

```python
from chatterbot import ChatBot

bot = ChatBot(
    "SQL Bot",
    storage_adapter="chatterbot.storage.SQLStorageAdapter",
    database_uri=None,  # in-memory sqlite smoke
)
```

For a persistent SQLite file:

```python
bot = ChatBot("SQL Bot", database_uri="sqlite:///db.sqlite3")
```

For non-SQLite databases, pass a SQLAlchemy URI and any supported pool kwargs such as `pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`, and `pool_pre_ping`.

## Statement filtering

Storage adapters expose common `filter(**kwargs)` options such as `text`, `in_response_to`, `conversation`, `tags`, `exclude_text`, `exclude_text_words`, `persona_not_startswith`, `search_text_contains`, `search_in_response_to_contains`, `order_by`, and `page_size`. See the API reference before assuming a filter works identically across SQL, MongoDB, and Redis vector storage.

## Boundaries

- For `ChatBot` response lifecycle, route to [core-chatbot](../core-chatbot/SKILL.md).
- For training data that creates storage records, route to [training](../training/SKILL.md).
- For logic/search behavior that consumes storage, route to [logic-adapters](../logic-adapters/SKILL.md).
- For Django ORM setup and migrations, route to [django-integration](../django-integration/SKILL.md).
