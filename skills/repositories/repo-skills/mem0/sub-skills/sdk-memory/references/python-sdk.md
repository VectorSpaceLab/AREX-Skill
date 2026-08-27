# Python SDK Reference

Mem0's Python distribution is `mem0ai`. Verified package facts for version 2.0.7 include public exports `Memory`, `AsyncMemory`, `MemoryClient`, and `AsyncMemoryClient` from `mem0`.

## Imports and Modes

| Mode | Import | Use when | Credentials/config |
| --- | --- | --- | --- |
| Hosted Platform sync | `from mem0 import MemoryClient` | Production apps using Mem0 Platform APIs | `MEM0_API_KEY` or constructor `api_key` |
| Hosted Platform async | `from mem0 import AsyncMemoryClient` | Async Python services using Mem0 Platform APIs | `MEM0_API_KEY` or constructor `api_key` |
| OSS sync | `from mem0 import Memory` | Local/self-managed memory pipeline in-process | Provider config; defaults use OpenAI + local Qdrant path |
| OSS async | `from mem0 import AsyncMemory` | Async local/self-managed memory pipeline | Provider config; defaults use OpenAI + local Qdrant path |

Use `provider-configuration` for provider selection, Qdrant/pgvector/graph/reranker setup, and optional dependency details. This reference focuses on call-site SDK usage.

## Hosted Platform Clients

Current signatures:

| Method | Shape |
| --- | --- |
| `MemoryClient(api_key=None, host=None, client=None)` | API key from argument or `MEM0_API_KEY`; default host `https://api.mem0.ai` |
| `add(messages, options=None, **kwargs)` | accepts string, one message dict, or list of message dicts |
| `search(query, options=None, **kwargs)` | returns `{"results": [...]}`; rejects blank query and top-level entity parameters |
| `get(memory_id)` | returns one memory dict |
| `get_all(options=None, **kwargs)` | returns paginated dict with `count`, `next`, `previous`, `results`; rejects top-level entity parameters |
| `update(memory_id, options=None, **kwargs)` | requires at least one of `text`, `metadata`, `timestamp` |
| `delete(memory_id, delete_linked=False)` | deletes one memory; `delete_linked=True` also deletes superseded linked memories |
| `delete_all(options=None, **kwargs)` | scoped delete through query parameters; treat as destructive |
| `history(memory_id)` | returns change history list |
| `batch_update(memories)` / `batch_delete(memories)` | Platform-only batch operations |
| `create_memory_export(schema, **kwargs)` / `get_memory_export(**kwargs)` | Platform-only export flow |
| `feedback(memory_id, feedback=None, feedback_reason=None)` | feedback values are `POSITIVE`, `NEGATIVE`, `VERY_NEGATIVE`, or `None` |

Typed option models are available from `mem0.client.types`: `AddMemoryOptions`, `SearchMemoryOptions`, `GetAllMemoryOptions`, `UpdateMemoryOptions`, and `DeleteAllMemoryOptions`. Methods also accept keyword args for backward compatibility.

### Platform Add

`add` accepts a string, dict, or list of OpenAI-style messages. Current migration docs keep entity IDs as top-level kwargs for `add()` and `delete_all()`, while `search()` and `get_all()` require `filters`.

```python
from mem0 import MemoryClient

client = MemoryClient(api_key=os.environ["MEM0_API_KEY"])

response = client.add(
    messages=[
        {"role": "user", "content": "I am allergic to walnuts."},
        {"role": "assistant", "content": "I will avoid walnut suggestions."},
    ],
    user_id="alice",
    metadata={"source": "support-chat"},
    infer=True,
)
```

Useful add options include `filters`, `metadata`, `infer`, `custom_categories`, `custom_instructions`, `timestamp`, and `structured_data_schema`.

### Platform Search and List

For hosted `search` and `get_all`, entity scope must be inside `filters`; top-level `user_id`, `agent_id`, `app_id`, and `run_id` raise `ValueError`.

```python
results = client.search(
    "What dietary restrictions should I remember?",
    filters={"user_id": "alice"},
    top_k=5,
    threshold=0.1,
    rerank=False,
)

page = client.get_all(filters={"user_id": "alice"}, page=1, page_size=50)
```

Nested filters are passed through for Platform search, including `AND`, `OR`, `NOT`, date comparisons, category filters, and field operators such as `in`, `gte`, and `contains`.

### Platform Update, Delete, Export, Feedback

```python
client.update(
    "memory-id",
    text="Alice prefers decaf coffee after noon.",
    metadata={"category": "preference"},
)

client.delete("memory-id")
client.delete("memory-id", delete_linked=True)
client.delete_all(user_id="alice")

client.batch_update([{"memory_id": "id1", "text": "Updated fact"}])
client.batch_delete([{"memory_id": "id1"}, {"memory_id": "id2"}])

client.feedback("memory-id", feedback="positive", feedback_reason="Useful personalization")
export_job = client.create_memory_export(
    schema='{"type":"object","properties":{"memory":{"type":"string"}}}',
    filters={"user_id": "alice"},
)
export_data = client.get_memory_export(filters={"user_id": "alice"})
```

`delete_all`, wildcard deletes, and `reset` can remove many records. Confirm project, environment, and filters before executing.

## Async Hosted Client

`AsyncMemoryClient` mirrors `MemoryClient` but every network operation is awaited and uses `httpx.AsyncClient` when a custom client is supplied.

```python
import asyncio
from mem0 import AsyncMemoryClient

async def main() -> None:
    client = AsyncMemoryClient()
    await client.add("User likes sci-fi movies", filters={"user_id": "alice"})
    results = await client.search("movie preferences", filters={"user_id": "alice"})
    await client.feedback(results["results"][0]["id"], feedback="POSITIVE")

asyncio.run(main())
```

## OSS Memory

Current sync signatures:

| Method | Shape |
| --- | --- |
| `Memory(config=MemoryConfig(...), history_db_path=..., version="v1.1", custom_instructions=None)` | in-process memory pipeline |
| `add(messages, *, user_id=None, agent_id=None, run_id=None, metadata=None, timestamp=None, infer=True, memory_type=None, prompt=None)` | one of `user_id`, `agent_id`, or `run_id` is required |
| `search(query, *, top_k=20, filters=None, threshold=0.1, rerank=False, explain=False, reference_date=None, **kwargs)` | entity IDs go in `filters`; top-level entity params are rejected |
| `get_all(*, filters=None, top_k=20, **kwargs)` | entity IDs go in `filters`; at least one is required |
| `update(memory_id, data, metadata=None)` | replaces text and optionally metadata |
| `delete(memory_id)` | deletes one memory |
| `delete_all(user_id=None, agent_id=None, run_id=None)` | requires at least one top-level scope arg |
| `history(memory_id)` | returns local history |
| `reset()` | clears local memory/history collections |

```python
from mem0 import Memory

memory = Memory()

added = memory.add(
    "Alice dislikes thrillers but loves sci-fi.",
    user_id="alice",
    metadata={"category": "movie_recommendations"},
)

results = memory.search(
    "What movies should I recommend?",
    filters={"user_id": "alice", "category": "movie_recommendations"},
    top_k=5,
    explain=True,
)

memory.update(added["results"][0]["id"], "Alice prefers optimistic sci-fi movies.")
memory.delete_all(user_id="alice")
```

OSS `add` accepts top-level `user_id`, `agent_id`, and `run_id`, then stores those scope values into metadata/filters. OSS `search` and `get_all` require scope in `filters`. Passing `timestamp` to OSS `add` or `reference_date` to OSS `search` raises a Platform-only temporal feature error.

## Async OSS Memory

`AsyncMemory` mirrors `Memory`; await each operation. Its `add` additionally accepts an optional `llm` override in the live signature.

```python
from mem0 import AsyncMemory

memory = AsyncMemory()
await memory.add("Alice is learning Japanese", user_id="alice", infer=True)
results = await memory.search("language goals", filters={"user_id": "alice"}, top_k=3)
```

## Migration-Sensitive Differences

| Concern | Hosted Platform Python | OSS Python |
| --- | --- | --- |
| Client initialization | Validates API key with `/v1/ping/` | Initializes local providers/vector store |
| Entity scope on `add` | top-level `user_id`/`agent_id`/`app_id`/`run_id` in current SDK behavior | top-level `user_id`/`agent_id`/`run_id` |
| Entity scope on `search`/`get_all` | `filters={...}` only | `filters={...}` only |
| Delete all | Platform method accepts options/kwargs; confirm filter behavior | requires top-level `user_id`, `agent_id`, or `run_id`; use `reset()` for full local wipe |
| Update text field | `text="..."` | `data="..."` or positional second arg |
| Batch/export/feedback | Platform client supports these | not available on local `Memory` |
| Temporal parameters | Platform supports request-level timestamp/export/date features | temporal request parameters raise guidance errors |
| Return casing | Python returns snake_case API payloads | OSS returns dicts from local storage with `results` |

## Minimal Import and Version Check

Use the bundled script for read-only inspection:

```bash
python scripts/inspect_mem0_sdk.py --json
```

If using a package inside an app, a minimal direct check is:

```python
import mem0
from mem0 import AsyncMemory, AsyncMemoryClient, Memory, MemoryClient

print(mem0.__version__)
```
