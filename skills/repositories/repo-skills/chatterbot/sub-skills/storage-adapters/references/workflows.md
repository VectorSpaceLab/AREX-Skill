# Storage Adapter Workflows

## SQL in-memory smoke

Use in-memory SQL for tests and examples that should not write a database file:

```python
from chatterbot import ChatBot

bot = ChatBot(
    "SQL Smoke",
    storage_adapter="chatterbot.storage.SQLStorageAdapter",
    database_uri=None,
)
```

Run the bundled smoke helper:

```bash
python sub-skills/storage-adapters/scripts/sql_storage_smoke.py
```

## Persistent SQLite file

Use a SQLite file for local persistence:

```python
bot = ChatBot(
    "SQLite Bot",
    storage_adapter="chatterbot.storage.SQLStorageAdapter",
    database_uri="sqlite:///chatbot.sqlite3",
)
```

Be explicit about `database_uri`. For SQL storage, `None` means in-memory SQLite; omitted/false defaults to `sqlite:///db.sqlite3`.

## SQLAlchemy server database

For PostgreSQL/MySQL/etc., install the appropriate SQLAlchemy DBAPI driver and pass a URI:

```python
bot = ChatBot(
    "Server SQL Bot",
    storage_adapter="chatterbot.storage.SQLStorageAdapter",
    database_uri="postgresql+psycopg://user:password@host:5432/chatterbot",
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)
```

Do not pass pool settings expecting SQLite to use them; ChatterBot only applies QueuePool settings for non-SQLite URIs.

## Direct statement CRUD and tags

Use storage methods when seeding statements outside trainers:

```python
from chatterbot.conversation import Statement

bot.storage.create(text="Hello", tags=["greeting"])
statement = Statement(text="Hi there!", in_response_to="Hello", tags=["greeting"])
statement.search_text = bot.tagger.get_text_index_string(statement.text)
statement.search_in_response_to = bot.tagger.get_text_index_string(statement.in_response_to)
bot.storage.update(statement)

results = list(bot.storage.filter(tags=["greeting"]))
```

If using SQL indexed search, populate `search_text` and `search_in_response_to` when creating statements directly. Trainers do this automatically.

## Query filters

Common filters:

```python
list(bot.storage.filter(text="Hello"))
list(bot.storage.filter(conversation="support"))
list(bot.storage.filter(tags=["faq"]))
list(bot.storage.filter(exclude_text=["Bad response"]))
list(bot.storage.filter(exclude_text_words=["forbidden"]))
list(bot.storage.filter(search_text_contains="hello everyone"))
list(bot.storage.filter(search_in_response_to_contains="hello"))
list(bot.storage.filter(order_by=["created_at"], page_size=100))
```

Remember that Redis vector storage interprets search fields through vector/search metadata differently from SQL indexed text.

## MongoDB storage

Install the optional dependency and ensure a service is running:

```bash
python -m pip install "chatterbot[mongodb]"
```

Configure:

```python
bot = ChatBot(
    "Mongo Bot",
    storage_adapter="chatterbot.storage.MongoDatabaseAdapter",
    database_uri="mongodb://localhost:27017/chatterbot-database",
)
```

For TLS/DocumentDB/Atlas, pass PyMongo client options:

```python
bot = ChatBot(
    "Mongo TLS Bot",
    storage_adapter="chatterbot.storage.MongoDatabaseAdapter",
    database_uri="mongodb://USER:PASSWORD@cluster.example:27017/?ssl=true",
    mongodb_client_kwargs={"tlsCAFile": "global-bundle.pem", "serverSelectionTimeoutMS": 5000},
)
```

Do not run Mongo examples as offline smoke tests unless a MongoDB service is intentionally available.

## Redis vector storage

Install Redis dependencies and run a Redis Stack/vector-search capable service:

```bash
python -m pip install "chatterbot[redis]"
```

Configure the default HuggingFace embedding path:

```python
bot = ChatBot(
    "Redis Semantic Bot",
    storage_adapter="chatterbot.storage.RedisVectorStorageAdapter",
    database_uri="redis://localhost:6379/0",
)
```

For faster or multilingual embeddings:

```python
bot = ChatBot(
    "Redis Fast Bot",
    storage_adapter="chatterbot.storage.RedisVectorStorageAdapter",
    embedding_model="all-MiniLM-L6-v2",
)
```

Provider-backed embeddings need their provider packages and credentials:

```python
bot = ChatBot(
    "OpenAI Embedding Bot",
    storage_adapter="chatterbot.storage.RedisVectorStorageAdapter",
    embedding_provider="openai",
    embedding_model="text-embedding-3-small",
    embedding_kwargs={"dimensions": 1536},
)
```

Redis vector storage automatically prefers `NoOpTagger` and `semantic_vector_search`. This is expected and should not be overridden unless implementing a custom vector-search experiment.

## Optional dependency preflight

Run:

```bash
python sub-skills/storage-adapters/scripts/storage_dependency_check.py --backend redis
python sub-skills/storage-adapters/scripts/storage_dependency_check.py --backend mongodb
```

This checks Python imports only. It does not prove a service is running.
