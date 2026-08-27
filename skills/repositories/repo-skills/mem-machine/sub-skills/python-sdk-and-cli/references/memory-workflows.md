# Memory Workflows

This reference covers Python SDK workflows. For raw REST payload mapping, also
read the root REST API and data-model reference.

## 1. Build A Client And Project

```python
from memmachine_client import MemMachineClient

client = MemMachineClient(base_url="http://localhost:8080", api_key=None)
project = client.get_or_create_project(
    org_id="my-org",
    project_id="my-project",
    description="Agent memory project",
)
```

If the project must use a non-default long-term-memory backend, pass the server
resource IDs at creation time only after the server config is known:

```python
project = client.create_project(
    org_id="my-org",
    project_id="event-backend-project",
    backend="event",
    embedder="openai_embedder",
    reranker="my_reranker_id",
    vector_store="event_vector_store",
    segment_store="profile_storage",
    properties_schema={"category": "str", "source_role": "str"},
)
```

Use the server sub-skill to validate those resource IDs.

## 2. Create Memory Context

```python
memory = project.memory(
    metadata={
        "user_id": "alice",
        "agent_id": "travel-agent",
        "group_id": "default",
        "session_id": "session-001",
    }
)
```

Use consistent metadata keys across add/search/list calls. If a search does not
find expected memories, first confirm the project and metadata context match the
original add call.

## 3. Add Memories

```python
from memmachine_common.api import EpisodeType, MemoryType

added = memory.add(
    "Alice prefers aisle seats on flights.",
    role="user",
    episode_type=EpisodeType.Message,
    memory_types=[MemoryType.Episodic, MemoryType.Semantic],
    metadata={"category": "travel"},
)
```

Validation checklist:

- Store stable, useful memories rather than transient scratch text.
- Use metadata for later filtering, not for secrets.
- Do not log full memory contents if they may contain private user data.
- Inspect returned IDs before delete/update workflows.

## 4. Search Memories

Simple search:

```python
result = memory.search("What travel seating does Alice prefer?", limit=5)
```

Search with context and filters:

```python
result = memory.search(
    "travel preferences",
    limit=10,
    filter="metadata.category = 'travel'",
    set_metadata={"user_id": "alice"},
    expand_context=1,
    score_threshold=0.2,
)
```

Richer retrieval-agent mode:

```python
result = memory.search("What should the travel agent remember?", agent_mode=True)
```

Use `agent_mode=True` only when server-side retrieval-agent resources are ready.
If ordinary search can answer the question, prefer ordinary search.

## 5. Filter Correctly

Modern filter strings support predicates and boolean logic:

```text
metadata.category = 'travel'
category = 'travel' AND priority = HIGH
set_id in ('user-88') AND tag in ('writing_style')
created_at < date('2026-01-19T01:56:41.513342Z')
```

Avoid `==`; use `=`. For very simple equality filters, legacy `filter_dict` can
still be useful:

```python
result = memory.search("travel", filter_dict={"category": "travel"})
```

If a user supplies both `filter` and `filter_dict`, prefer `filter` for complex
logic and explain which one will actually be sent in the chosen SDK version.

## 6. List And Delete

List paginated memories:

```python
from memmachine_common.api import MemoryType

page = memory.list(memory_type=MemoryType.Episodic, page_size=20, page_num=0)
```

Delete by explicit IDs only:

```python
memory.delete_episodic(episodic_id="episode-id")
memory.delete_semantic(semantic_id="semantic-id")
```

Ask before deletion. Distinguish episodic IDs from semantic IDs.

## 7. Semantic/Profile Memory Workflows

Create a semantic set type and category when the server's semantic memory is
enabled:

```python
set_type_id = memory.create_semantic_set_type(
    metadata_tags=["user_id"],
    name="User profile",
    description="Profile facts keyed by user_id",
)
set_id = memory.get_semantic_set_id(
    metadata_tags=["user_id"],
    set_metadata={"user_id": "alice"},
)
category_id = memory.add_semantic_category(
    set_id=set_id,
    category_name="travel_preferences",
    prompt="Extract stable travel preferences.",
)
feature_id = memory.add_feature(
    set_id=set_id,
    category_name="travel_preferences",
    tag="seating",
    feature="preferred_seat",
    value="aisle",
)
```

If these calls fail, inspect server semantic memory config and resource status.
They are not purely client-side operations.

## 8. Formatting Helpers

The SDK exports formatting helpers for presentation:

```python
from memmachine_client import format_search_result

print(format_search_result(result))
```

Use formatting helpers for human-readable output, but preserve raw Pydantic
models when assertions or downstream programmatic checks are needed.

## 9. LangGraph Tools

```python
from memmachine_client.langgraph import MemMachineTools, create_search_memory_tool

tools = MemMachineTools(base_url="http://localhost:8080", api_key=None)
search_tool = create_search_memory_tool(tools)
response = search_tool("travel preferences", "alice", 5)
```

Confirm the installed LangGraph integration's constructor details before using
it in a production graph. Framework dependencies are optional and should be
installed explicitly by the application.
