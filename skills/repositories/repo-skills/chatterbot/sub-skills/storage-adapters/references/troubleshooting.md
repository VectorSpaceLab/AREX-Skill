# Storage Adapter Troubleshooting

## SQLite file appears unexpectedly

**Symptom**

A `db.sqlite3` file appears after creating a bot.

**Cause**

For SQL storage, `database_uri=None` means in-memory SQLite, but an omitted/false `database_uri` defaults to `sqlite:///db.sqlite3`.

**Fix**

Use the intended URI explicitly:

```python
ChatBot("Memory", database_uri=None)                 # no persistent file
ChatBot("File", database_uri="sqlite:///bot.sqlite3")
```

## SQL search returns weak or no matches

**Likely causes**

- Statements were created directly without `search_text` or `search_in_response_to`.
- A different tagger was used for training than for querying.
- `additional_response_selection_parameters` or `excluded_words` filtered out responses.

**Fix**

When seeding storage directly, populate search fields with the bot's active tagger:

```python
statement.search_text = bot.tagger.get_text_index_string(statement.text)
statement.search_in_response_to = bot.tagger.get_text_index_string(statement.in_response_to)
bot.storage.update(statement)
```

Prefer ChatterBot trainers for normal training because they fill these fields.

## MongoDB connection timeout

**Symptoms**

- PyMongo server selection timeout.
- Authentication or TLS errors.

**Fix**

1. Confirm `pymongo` is installed: `python -c "import pymongo"`.
2. Confirm the MongoDB service is reachable from the same host.
3. Use a database URI with database name, e.g. `mongodb://localhost:27017/chatterbot-database`.
4. For TLS/Atlas/DocumentDB, pass `mongodb_client_kwargs` such as `tlsCAFile`, `serverSelectionTimeoutMS`, and `connectTimeoutMS`.
5. If no MongoDB service is available, do not use `MongoDatabaseAdapter` for smoke tests; use SQL storage.

## Redis vector storage fails at import

**Symptoms**

- Missing `redis`, `langchain_redis`, `langchain_huggingface`, `sentence_transformers`, or related packages.
- `redisvl`/Pydantic compatibility issues on a newer Python.

**Fix**

Install only if Redis vector storage is selected:

```bash
python -m pip install "chatterbot[redis]"
```

The repo tests skip Redis on Python 3.14+ because of a `redisvl` dependency compatibility note. Prefer Python 3.10-3.13 for Redis vector workflows until that ecosystem changes.

## Redis service or embedding model unavailable

**Symptoms**

- Redis connection refused.
- Vector index query errors.
- First initialization downloads a HuggingFace model and stalls or fails.
- OpenAI/Cohere embedding providers fail because credentials are missing.

**Fix**

1. Start a Redis Stack/vector-search capable service, not just an incompatible minimal Redis build.
2. Verify `database_uri`.
3. For HuggingFace embeddings, allow/cache the model download or choose a smaller model such as `all-MiniLM-L6-v2`.
4. For OpenAI/Cohere embeddings, install the provider package and set credentials outside code.
5. Do not claim Redis semantic behavior from SQL storage tests; Redis uses `NoOpTagger` and `semantic_vector_search`.

## Tags or filters behave differently across backends

SQL/Django represent tags as relational models, Mongo stores them in documents, and Redis stores metadata for vector documents. If a complex filter behaves differently, reduce it to a small create/filter smoke and check the backend-specific implementation.

Use:

```bash
python sub-skills/storage-adapters/scripts/sql_storage_smoke.py --json
```

for SQL behavior. For Mongo/Redis, use backend-specific service tests only after the service is intentionally available.

## Storage adapter cleanup

Call `storage.close()` when a SQL/Mongo storage adapter is no longer needed in a script or test. Use `drop()` only for disposable test databases because it deletes all data for the adapter.
