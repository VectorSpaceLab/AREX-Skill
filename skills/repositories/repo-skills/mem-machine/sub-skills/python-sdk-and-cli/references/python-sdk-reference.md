# Python SDK Reference

The Python SDK is exposed by `memmachine-client` as `memmachine_client`. It is a
synchronous HTTP client built around `requests`; create and close clients
explicitly or use a context manager if available in the installed version.

## Imports

```python
from memmachine_client import (
    Config,
    MemMachineClient,
    Memory,
    Project,
    format_episodes,
    format_search_result,
    format_semantic_memories,
)
from memmachine_common.api import EpisodeType, MemoryType
```

## Client Object

Verified constructor and important methods:

```text
MemMachineClient(api_key: str | None = None,
                 base_url: str | None = None,
                 timeout: int = 30,
                 max_retries: int = 3,
                 **kwargs) -> None

create_project(org_id, project_id, description='', embedder='', reranker='',
               backend=None, vector_graph_store='', vector_store='',
               segment_store='', properties_schema=None, timeout=None) -> Project
get_project(org_id, project_id, timeout=None) -> Project
get_or_create_project(...same config fields...) -> Project
list_projects(timeout=None) -> list[Project]
health_check(timeout=None) -> dict[str, Any]
get_metrics(timeout=None) -> str
config() -> Config
close() -> None
```

`base_url` is required by current code. Pass it explicitly or load it from your
own environment configuration before constructing the client.

## Project And Memory Context

`Project.memory(metadata=None, **kwargs) -> Memory` creates a memory object
bound to the project. Use metadata to carry stable context such as:

```python
memory = project.memory(
    metadata={
        "user_id": "alice",
        "agent_id": "support-bot",
        "group_id": "default",
        "session_id": "session-001",
    }
)
```

The metadata becomes default context for memory operations. Per-call metadata is
merged into the request. Keep metadata values simple strings unless the method
explicitly accepts JSON-like values.

Project helpers:

```text
Project.delete(timeout=None) -> bool
Project.refresh(timeout=None) -> None
Project.get_episode_count(timeout=None) -> int
```

## Memory Methods

Core memory methods:

```text
Memory.add(content: str,
           role: str = '',
           producer: str | None = None,
           produced_for: str | None = None,
           episode_type: EpisodeType | None = None,
           memory_types: list[MemoryType] | None = None,
           metadata: dict[str, str] | None = None,
           timestamp: datetime | None = None,
           timeout: int | None = None) -> list[AddMemoryResult]

Memory.search(query: str,
              limit: int | None = None,
              expand_context: int = 0,
              score_threshold: float | None = None,
              filter_dict: dict[str, str] | None = None,
              timeout: int | None = None,
              *,
              filter: str | None = None,
              set_metadata: dict[str, JsonValue] | None = None,
              agent_mode: bool = False) -> SearchResult

Memory.list(memory_type: MemoryType = MemoryType.Episodic,
            page_size: int = 100,
            page_num: int = 0,
            filter_dict: dict[str, str] | None = None,
            filter: str | None = None,
            set_metadata: dict[str, JsonValue] | None = None,
            timeout: int | None = None) -> ListResult

Memory.delete_episodic(episodic_id='', episodic_ids=None, timeout=None) -> bool
Memory.delete_semantic(semantic_id='', semantic_ids=None, timeout=None) -> bool
```

Use `memory_types=[MemoryType.Episodic]`, `[MemoryType.Semantic]`, or both when
the server configuration and workflow require a specific target. If omitted,
consult the installed version's defaults and server behavior before assuming
both are used.

## Semantic/Profile Helpers

`Memory` also exposes semantic memory management helpers:

```text
add_feature(set_id, category_name, tag, feature, value, feature_metadata=None, citations=None)
get_feature(feature_id, load_citations=False)
update_feature(feature_id, category_name=None, feature=None, value=None, tag=None, metadata=None)
create_semantic_set_type(metadata_tags, is_org_level=False, name=None, description=None)
list_semantic_set_types()
delete_semantic_set_type(set_type_id)
get_semantic_set_id(metadata_tags, is_org_level=False, set_metadata=None)
list_semantic_set_ids(set_metadata=None)
configure_semantic_set(set_id, embedder_name=None, llm_name=None)
get_semantic_category(category_id)
add_semantic_category(set_id, category_name, prompt, description=None)
add_semantic_category_template(set_type_id, category_name, prompt, description=None)
list_semantic_category_templates(set_type_id)
disable_semantic_category(set_id, category_name)
get_semantic_category_set_ids(category_id)
delete_semantic_category(category_id)
add_semantic_tag(category_id, tag_name, tag_description)
delete_semantic_tag(tag_id)
get_episodic_memory_config()
configure_episodic_memory(enabled=None, long_term_memory_enabled=None, short_term_memory_enabled=None)
```

These calls require a server that has semantic/config APIs enabled and the
necessary resources configured. For missing resource or validation errors, route
to the server configuration sub-skill.

## Runtime Configuration Wrapper

`client.config()` returns a `Config` wrapper for server configuration APIs:

```text
get_config(), get_resources()
update_memory_config(episodic_memory=None, semantic_memory=None)
get_episodic_memory_config(), update_episodic_memory_config(...)
get_long_term_memory_config(), update_long_term_memory_config(...)
get_short_term_memory_config(), update_short_term_memory_config(...)
get_semantic_memory_config(), update_semantic_memory_config(...)
add_embedder(name, provider, config), add_language_model(name, provider, config)
delete_embedder(name), delete_language_model(name)
retry_embedder(name), retry_language_model(name), retry_reranker(name)
```

Provider config shapes are server-side concerns. Use the server sub-skill before
creating or mutating provider resources.

## LangGraph Tool Helpers

`memmachine_client.langgraph` provides `MemMachineTools` plus helper factories:

```text
MemMachineTools.get_memory(org_id=None, project_id=None, user_id=None,
                           agent_id=None, group_id=None, session_id=None) -> Memory
MemMachineTools.add_memory(content, role='user', ..., metadata=None, episode_type=None) -> dict
MemMachineTools.search_memory(query, ..., limit=20, score_threshold=None,
                              filter_dict=None, filter=None) -> dict
MemMachineTools.get_context(...) -> dict
create_add_memory_tool(tools) -> Callable
create_search_memory_tool(tools) -> Callable
```

Use these when a LangGraph graph or tool-calling layer wants callable memory
operations. The framework dependency is separate from MemMachine itself.
