# Core SDK API reference

This reference records the public SDK surface that the `core-sdk` route owns.
Use it alongside `workflows.md` when you need exact parameters or object names.

## `Graphiti`

Verified constructor signature:

```python
Graphiti(
    uri: str | None = None,
    user: str | None = None,
    password: str | None = None,
    llm_client: LLMClient | None = None,
    embedder: EmbedderClient | None = None,
    cross_encoder: CrossEncoderClient | None = None,
    store_raw_episode_content: bool = True,
    graph_driver: GraphDriver | None = None,
    max_coroutines: int | None = None,
    tracer: Tracer | None = None,
    trace_span_prefix: str = 'graphiti',
)
```

### Public methods

| Method | Purpose | Key notes |
| --- | --- | --- |
| `close()` | Close the graph driver | Always close the client when done. |
| `build_indices_and_constraints(delete_existing=False)` | Create backend indices/constraints | Run this before first ingest on a fresh graph. |
| `add_episode(...)` | Ingest one episode | Accepts text, JSON, or message-style content plus optional custom types and saga context. |
| `add_episode_bulk(...)` | Ingest a batch of `RawEpisode` items | Use for small batched imports when you already have a list of episodes. |
| `search(query, ...)` | Hybrid fact/edge search | Returns `EntityEdge` results. Useful for answer-bearing relationships. |
| `search_(query, config=...)` | Configurable node/fact/community search | Returns `SearchResults` with nodes, edges, episodes, and communities depending on the config. |
| `retrieve_episodes(reference_time, ...)` | Fetch recent episodic nodes | Helpful for time-aware ingestion or saga workflows. |
| `build_communities(group_ids=None, ...)` | Detect communities and summaries | More expensive than search; typically used after ingesting enough data. |
| `summarize_saga(saga_id)` | Refresh a saga summary | Use after saga-linked ingest or when the summary needs an update. |
| `add_triplet(source_node, edge, target_node)` | Add a single fact directly | Bypasses episode extraction and dedupes endpoint nodes. |
| `get_nodes_and_edges_by_episode(episode_uuids)` | Trace provenance | Returns the entities and facts created by one or more episodes. |
| `remove_episode(episode_uuid)` | Remove an episode | Use with care; it can cascade to objects only created by that episode. |

### Return objects

| Object | Meaning |
| --- | --- |
| `AddEpisodeResults` | One-episode ingest result with episode, episodic edges, nodes, edges, communities, and community edges. |
| `AddBulkEpisodeResults` | Batch-ingest result for a list of episodes. |
| `AddTripletResults` | Returned nodes and edges for a direct fact write. |
| `SearchResults` | Search result container for `search_()`. |

## Drivers

### `Neo4jDriver`

```python
Neo4jDriver(uri: str, user: str | None, password: str | None, database: str = 'neo4j')
```

Use this when the task is about the default Graphiti backend or the REST service.

### `FalkorDriver`

```python
FalkorDriver(
    host: str = 'localhost',
    port: int = 6379,
    username: str | None = None,
    password: str | None = None,
    falkor_db: FalkorDB | None = None,
    database: str = 'default_db',
)
```

Use this when the task is about the FalkorDB path, the MCP default backend, or
embedded FalkorDB Lite.

## Search recipes

| Recipe | What it does | Typical use |
| --- | --- | --- |
| `NODE_HYBRID_SEARCH_RRF` | Node search with BM25 + cosine similarity and reciprocal rank fusion | Best default for node lookup. |
| `EDGE_HYBRID_SEARCH_RRF` | Edge search with BM25 + cosine similarity and reciprocal rank fusion | Best default for fact lookup. |
| `EDGE_HYBRID_SEARCH_NODE_DISTANCE` | Edge search centered on graph distance | Use when you have a center node UUID. |
| `COMBINED_HYBRID_SEARCH_CROSS_ENCODER` | Search across edges, nodes, episodes, and communities with cross-encoder reranking | Use when you have a provider reranker or a local fallback. |

`SearchConfig` has the verified fields:

- `edge_config`
- `node_config`
- `episode_config`
- `community_config`
- `limit`
- `reranker_min_score`

## Provider clients

### `OpenAIClient`

Use the official OpenAI API path when the provider is OpenAI or Azure OpenAI.
The class is instantiated via `LLMConfig` or the service factories rather than by
hand in most tasks.

### `OpenAIGenericClient`

Verified constructor signature:

```python
OpenAIGenericClient(
    config: LLMConfig | None = None,
    cache: bool = False,
    client: Any = None,
    max_tokens: int = 16384,
    structured_output_mode: Literal['json_schema', 'json_object'] = 'json_schema',
)
```

Use this for OpenAI-compatible providers and local models. Switch to
`structured_output_mode='json_object'` when the provider accepts schema requests
but does not actually enforce them.

### `OpenAIEmbedder`

Verified constructor signature:

```python
OpenAIEmbedder(config: OpenAIEmbedderConfig | None = None, client: AsyncOpenAI | AsyncAzureOpenAI | None = None)
```

Use this for OpenAI-compatible embedding endpoints.

### Rerankers

- `OpenAIRerankerClient`
- `GeminiRerankerClient`
- local BGE fallback via `BGERerankerClient` when no provider reranker is available

## Common inputs

### `add_episode(...)`

Important arguments:

- `name`
- `episode_body`
- `source_description`
- `reference_time`
- `source`
- `group_id`
- `uuid`
- `update_communities`
- `entity_types`
- `excluded_entity_types`
- `previous_episode_uuids`
- `edge_types`
- `edge_type_map`
- `custom_extraction_instructions`
- `saga`
- `saga_previous_episode_uuid`

### `search_(...)`

Important arguments:

- `query`
- `config`
- `group_ids`
- `center_node_uuid`
- `bfs_origin_node_uuids`
- `search_filter`
- `driver`

## Practical reminder

If a workflow only needs the public SDK, stop here. If it needs endpoint paths,
request/response shapes, or queue semantics, switch to the REST or MCP sub-skill
instead of expanding this reference further.
