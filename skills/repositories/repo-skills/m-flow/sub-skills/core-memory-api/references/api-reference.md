# Core Python API Reference

This reference covers the public `m_flow` package surface owned by this
sub-skill. All core workflow functions are `async` unless noted. Use
`asyncio.run(...)` from scripts or `await ...` inside an existing event loop.

## Public exports to expect

`import m_flow` exposes these names for core API work:

| Area | Public names |
| --- | --- |
| Core memory | `add`, `memorize`, `ingest`, `learn`, `search`, `query` |
| Result/config types | `IngestResult`, `IngestStatus`, `RecallMode`, `QueryResult`, `SearchConfig`, `ContentType` |
| Data management | `datasets`, `delete`, `update`, `prune` |
| Manual memory | `manual_ingest`, `manual_add_episode`, `patch_node`, `ManualIngestRequest`, `ManualEpisodeInput`, `ManualFacetInput`, `ManualFacetPointInput`, `ManualConceptInput`, `PatchNodeRequest` |
| Config | `config` |
| Advanced pipeline | `run_custom_pipeline`, `pipelines` (route detailed pipeline design to `../../ingestion-pipelines/SKILL.md`) |

## Core workflow APIs

### `add()` — register raw data

```python
await m_flow.add(
    data,
    dataset_name="main_dataset",
    user=None,
    graph_scope=None,
    vector_db_config=None,
    graph_db_config=None,
    dataset_id=None,
    preferred_loaders=None,
    incremental_loading=True,
    enable_cache=True,
    items_per_batch=20,
    created_at=None,
)
```

Use for text, paths, URLs, binary streams, or lists of those inputs. The return
is a pipeline `RunEvent` with dataset/run metadata. `dataset_id` overrides
`dataset_name` when targeting an existing dataset by UUID. `created_at` accepts
Unix milliseconds or a `datetime`; use it for historical chats, logs, or records.
`preferred_loaders` selects loader behavior; route loader-specific decisions to
`../../ingestion-pipelines/SKILL.md`.

### `memorize()` — build memory graph from registered data

```python
await m_flow.memorize(
    datasets=None,
    user=None,
    chunker=TextChunker,
    chunk_size=None,
    chunks_per_batch=None,
    vector_db_config=None,
    graph_db_config=None,
    run_in_background=False,
    incremental_loading=True,
    enable_cache=True,
    items_per_batch=20,
    conflict_mode="warn",
    **kwargs,
)
```

`datasets` may be a dataset name, a list of names, UUIDs, or `None` for all data
visible to the user. Blocking mode returns a mapping of dataset id to `RunEvent`;
background mode returns immediately with run events/progress handles. Important
`**kwargs` include `content_type`, `enable_content_routing`,
`enable_episode_routing`, `enable_procedural`, `precise_mode`, and other
pipeline toggles; route detailed chunking/content-routing choices to the
`ingestion-pipelines` sub-skill. Use `conflict_mode="error"` to fail fast if a
same-dataset memorize run is already active.

### `ingest()` — one-step add plus memorize

```python
result = await m_flow.ingest(
    data,
    dataset_name=None,
    skip_memorize=False,
    **kwargs,
)
```

`ingest()` splits valid keyword arguments between `add()` and `memorize()` and
raises `TypeError` for unknown kwargs. `dataset_name=None` becomes
`"main_dataset"`. `skip_memorize=True` stores data but leaves it not queryable
until a later `memorize()` call.

`IngestResult` fields and helpers:

- `dataset_id`, `dataset_name`, `status`, `add_run_id`, `memorize_run_id`,
  `error_message`
- `is_complete()` / `is_completed()` for synchronous success
- `is_background()` for `run_in_background=True`
- `is_success()` for completed or background-started results
- `needs_retry()` for `MEMORIZE_FAILED`
- `to_dict()` for serializable logging

`IngestStatus` values: `COMPLETED`, `BACKGROUND_STARTED`, `MEMORIZE_SKIPPED`,
`MEMORIZE_FAILED`.

### `search()` — advanced retrieval

```python
await m_flow.search(
    query_text,
    query_type=m_flow.RecallMode.TRIPLET_COMPLETION,
    user=None,
    datasets=None,
    dataset_ids=None,
    system_prompt_path=None,
    system_prompt=None,
    top_k=10,
    node_type=MemorySpace,
    node_name=None,
    save_interaction=None,
    only_context=False,
    use_combined_context=None,
    session_id=None,
    wide_search_top_k=None,
    triplet_distance_penalty=None,
    verbose=None,
    enable_hybrid_search=None,
    enable_time_bonus=None,
    edge_miss_cost=None,
    hop_cost=None,
    full_number_match_bonus=None,
    enable_adaptive_weights=None,
    display_mode=None,
    max_facets_per_episode=None,
    max_points_per_facet=None,
    collections=None,
    config=None,
)
```

Verified `RecallMode` values: `CHUNKS_LEXICAL`, `TRIPLET_COMPLETION`, `CYPHER`,
`EPISODIC`, `PROCEDURAL`. `SearchConfig` can hold `system_prompt`,
`system_prompt_path`, `save_interaction`, `use_combined_context`,
`wide_search_top_k`, `triplet_distance_penalty`, and `verbose`; direct keyword
arguments override `config` values. For scoring, display, Cypher, or backend
analysis, route to `../../retrieval-graph-search/SKILL.md`.

### `query()` — simplified retrieval

```python
result = await m_flow.query(
    question,
    datasets=None,
    mode="episodic",
    top_k=10,
)
```

Mode strings map as follows: `"episodic" -> RecallMode.EPISODIC`,
`"triplet" -> TRIPLET_COMPLETION`, `"chunks" -> CHUNKS_LEXICAL`,
`"procedural" -> PROCEDURAL`, `"cypher" -> CYPHER`. Unknown modes warn and
fall back to `episodic`.

`QueryResult` contains `answer`, `context`, and `datasets`. `answer` is normally
available only for triplet/LLM answer mode; episodic, chunks, and procedural
modes mainly populate `context`. Use `result.to_dict()`, `result.has_answer()`,
and `result.is_empty()` for robust scripts.

### `learn()` — derive procedural memory

```python
await m_flow.learn(
    datasets=None,
    user=None,
    episode_ids=None,
    run_in_background=False,
)
```

`learn()` extracts procedural memories from existing episodes. It returns a dict
with status/counters such as `episodes_processed`, `procedures_created`, and
`edges_created`. Current behavior warns and runs synchronously even if
`run_in_background=True`; do not promise background execution for learn.

## Dataset and data-management APIs

### `datasets` static helper

```python
await m_flow.datasets.list_datasets()
m_flow.datasets.discover_datasets(directory_path)
await m_flow.datasets.list_data(dataset_id)
await m_flow.datasets.has_data(dataset_id)
await m_flow.datasets.get_status([dataset_uuid])
await m_flow.datasets.delete_dataset(dataset_id)
```

Use `get_status()` after background memorize/ingest if the caller has the dataset
UUID. `delete_dataset()` is destructive; require confirmation.

### `delete()` and `update()`

```python
await m_flow.delete(data_id, dataset_id, mode="soft", user=None)
await m_flow.update(
    data_id,
    data,
    dataset_id,
    user=None,
    graph_scope=None,
    vector_db_config=None,
    graph_db_config=None,
    preferred_loaders=None,
    incremental_loading=True,
    content_type=None,
)
```

`delete()` removes one data item from one dataset. `mode="soft"` removes data
and edges; `mode="hard"` additionally prunes orphan entity nodes. `update()` is
an atomic delete/add/memorize refresh for one data item and may reprocess graph
state. Treat both as destructive and dataset-scoped.

### `prune` administrative cleanup

```python
await m_flow.prune.all()
await m_flow.prune.prune_data()
await m_flow.prune.prune_system(graph=True, vector=True, metadata=False, cache=True)
```

`prune.all()` clears file storage, relational metadata, graph, vector, and cache
state. `prune_system(metadata=False)` may leave orphan relational records after
file cleanup; prefer `prune.all()` for development/test cleanup and avoid all
prune calls in production unless the user explicitly asks.

## Manual memory APIs

Use manual APIs when the caller already has structured episode/facet/entity data
and wants to bypass LLM extraction.

```python
await m_flow.manual_add_episode(
    name="Meeting Notes",
    summary="Decision and context summary",
    facets=[{"facet_type": "decision", "search_text": "Adopt design A"}],
    entities=[{"name": "Team Alpha", "description": "Responsible group"}],
    dataset_name="manual_notes",
    embed_triplets=False,
)
```

For batch control, build `ManualIngestRequest(episodes=[ManualEpisodeInput(...)],
dataset_name="...")` and call `manual_ingest(request)`. Models:

- `ManualEpisodeInput`: `name`, `summary`, optional `signature`, `status`,
  `memory_type`, `display_only`, `facets`, `entities`
- `ManualFacetInput`: `facet_type`, `search_text`, optional aliases,
  description, anchor text, display-only text, points
- `ManualFacetPointInput`: `search_text`, aliases, description, display-only text
- `ManualConceptInput`: `name`, `description`, optional canonical/type/display
- `PatchNodeRequest`: `node_id`, `node_type`, `display_only`; empty string clears

`patch_node()` currently supports updating `display_only` for existing graph
nodes.

## Process-local configuration facade

`m_flow.config` is a static facade. Common safe reads:

```python
print(m_flow.config.show())
print(m_flow.config.show("llm"))
settings = m_flow.config.show(as_dict=True)
vars_by_name = m_flow.config.env_vars()
categories = m_flow.config.env_categories()
```

Common setters:

```python
m_flow.config.set_llm_provider("openai")
m_flow.config.set_llm_model("gpt-4o-mini")
m_flow.config.set_llm_api_key("...")
m_flow.config.set_graph_database_provider("kuzu")
m_flow.config.set_vector_db_provider("lancedb")
m_flow.config.set_chunk_size(1500)
m_flow.config.clear_caches()
```

Config setters affect the current process and subsequent operations; after
changing environment variables in-process, call `clear_caches()` when needed.
For persistent environment and deployment configuration, route to root
configuration guidance once available (`../../../references/configuration.md`).
