# Python SDK Workflows

## Sync setup

```python
from r2r import R2RClient

client = R2RClient(base_url="http://localhost:7272")
client.set_api_key("r2r_api_key_here")
print(client.system.health().results)
```

## Async setup

```python
import asyncio
from r2r import R2RAsyncClient

async def main():
    async with R2RAsyncClient(base_url="http://localhost:7272") as client:
        client.set_api_key("r2r_api_key_here")
        health = await client.system.health()
        print(health.results)

asyncio.run(main())
```

## Login-token flow

```python
from r2r import R2RClient

client = R2RClient(base_url="http://localhost:7272")
login = client.users.login("user@example.com", "password")
print(login.results.access_token.token)
print(client.users.me().results)
```

## Pagination and downloads

- Use `offset` and `limit` on list methods.
- Page results arrive in `results`; total count arrives in `total_entries`.
- `documents.download()` returns a `BytesIO` object.
- `documents.download_zip()` can return a `BytesIO` object or write to an output path.

```python
docs = client.documents.list(limit=10, offset=0)
print(docs.total_entries)
print(len(docs.results))

blob = client.documents.download("document-id")
print(type(blob).__name__)
```

## Streaming consumption

- `retrieval.rag(...)` and `retrieval.agent(...)` may return event generators.
- Handle citation, tool, message, and final-answer events instead of assuming a single JSON payload.

```python
stream = client.retrieval.rag(
    query="What does the document say?",
    rag_generation_config={"stream": True},
)
for event in stream:
    print(type(event).__name__, event)
```

## When to route away

- If the work is about building ingestion payloads, switch to `../ingestion-documents/SKILL.md`.
- If the work is about search tuning, switch to `../retrieval-rag/SKILL.md`.
- If the work is about graph extraction or graph CRUD, switch to `../graph-workflows/SKILL.md`.
