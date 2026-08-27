# Storage Adapter API Reference

## When to read

Read this before choosing SQL, MongoDB, Redis vector, or custom storage for a ChatterBot workflow.

## Built-in adapter classes

ChatterBot 1.2.14 exposes these storage classes:

```python
from chatterbot.storage import (
    StorageAdapter,
    SQLStorageAdapter,
    MongoDatabaseAdapter,
    RedisVectorStorageAdapter,
    DjangoStorageAdapter,
)
```

`DjangoStorageAdapter` is covered in the Django sub-skill because it requires Django settings and migrations.

## Common storage interface

The abstract `StorageAdapter` defines the common methods:

```python
count() -> int
filter(**kwargs)
create(**kwargs)
create_many(statements)
update(statement)
get_random()
remove(statement_text)
drop()
close()
get_preferred_tagger()
get_preferred_search_algorithm()
```

`filter` accepts common query kwargs:

| Kwarg | Meaning |
| --- | --- |
| `page_size` | maximum batch/page size for iteration |
| `order_by` | field names for ordering, e.g. `['created_at']` or `['text']` |
| `tags` | one tag string or list of tags |
| `exclude_text` | exact response texts to exclude |
| `exclude_text_words` | substrings/words that should not appear in returned text |
| `persona_not_startswith` | exclude statements whose persona starts with a value, normally `bot:` |
| `search_text_contains` | match indexed/search text terms |
| `search_in_response_to_contains` | match indexed response-to terms |

Adapters also accept model fields such as `text`, `in_response_to`, `conversation`, and `persona`.

## SQL storage

Class:

```python
SQLStorageAdapter(**kwargs)
```

Important kwargs:

- `database_uri`: SQLAlchemy URI. `None` means in-memory SQLite (`sqlite://`). Omitted/false means `sqlite:///db.sqlite3`.
- `pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`, `pool_pre_ping`: applied only for non-SQLite QueuePool engines.
- `raise_on_missing_search_text`: common storage adapter flag used by tests and diagnostics.

SQL storage creates tables if needed and adds indexes named `idx_cb_search_text` and `idx_cb_search_in_response_to` on the statement model. SQLite connections are configured with WAL and `synchronous=NORMAL` when possible.

## MongoDB storage

Class:

```python
MongoDatabaseAdapter(**kwargs)
```

Important kwargs:

- `database_uri`: defaults to `mongodb://localhost:27017/chatterbot-database`.
- `mongodb_client_kwargs`: passed to `pymongo.MongoClient`, useful for TLS, timeouts, pool settings, or DocumentDB/Atlas configuration.

Mongo storage writes statement documents to the `statements` collection. It uses regex-based matching for `search_text_contains` and `search_in_response_to_contains`.

## Redis vector storage

Class:

```python
RedisVectorStorageAdapter(**kwargs)
```

Important kwargs:

- `database_uri`: defaults to `redis://localhost:6379/0`.
- `embedding_provider`: `huggingface` by default; also supports `openai` and `cohere` when provider packages and credentials exist.
- `embedding_model`: defaults to `sentence-transformers/all-mpnet-base-v2`.
- `embedding_kwargs`: passed to the provider, e.g. HuggingFace `model_kwargs` or `encode_kwargs`.

Redis vector storage differs from SQL:

- It stores `in_response_to` as the vector content field.
- It prefers `NoOpTagger` because vector embeddings do not need POS/lemma search text.
- It prefers `semantic_vector_search`.
- Confidence is derived from vector distance.

Default model choices documented by the repo include:

| Use case | Model |
| --- | --- |
| balanced default | `sentence-transformers/all-mpnet-base-v2` |
| faster/smaller | `all-MiniLM-L6-v2` |
| Q&A optimized | `multi-qa-mpnet-base-dot-v1` |
| multilingual | `paraphrase-multilingual-mpnet-base-v2` |

Cloud embedding providers require additional packages such as `langchain-openai` or `langchain-cohere` plus provider credentials.

## Statement tags

Storage adapters deduplicate tags during create/update. Use:

```python
statement.add_tags("support", "faq")
storage.update(statement)
list(storage.filter(tags=["support"]))
```

In SQL and Django storage, tags are separate related models/tables. In Mongo and Redis storage, tags are document metadata.

## Custom storage adapters

Subclass `StorageAdapter` and implement the interface methods. Override `get_preferred_tagger` and `get_preferred_search_algorithm` when the backend needs a different text pipeline, as Redis does:

```python
def get_preferred_tagger(self):
    from chatterbot.tagging import NoOpTagger
    return NoOpTagger

def get_preferred_search_algorithm(self):
    return "semantic_vector_search"
```

A custom adapter must provide a statement model/object compatible with `chatterbot.conversation.Statement` fields.
