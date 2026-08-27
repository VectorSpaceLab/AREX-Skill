# MCP tools reference

The Graphiti MCP server exposes memory, search, provenance, and maintenance tools.
The exact server code can route through `stdio`, `http`, or `sse`, but the tool
names stay the same.

## Memory ingest

### `add_memory`

Primary tool for episode ingestion. It queues work and returns immediately.

Important arguments:

- `name`
- `episode_body`
- `group_id`
- `source` (`text`, `json`, or `message`)
- `source_description`
- `uuid`
- `reference_time`
- `excluded_entity_types`
- `custom_extraction_instructions`
- `previous_episode_uuids`
- `update_communities`
- `saga`
- `saga_previous_episode_uuid`

Notes:

- `episode_body` must be a JSON string when `source='json'`.
- The server parses `reference_time` before queueing so bad timestamps fail fast.
- Background processing means search may lag behind ingest.

### `add_triplet`

Directly writes one fact without episode extraction.

Important arguments:

- `source_node_name`
- `edge_name`
- `fact`
- `target_node_name`
- `group_id`
- `source_node_uuid`
- `target_node_uuid`

Use this when the relationship is already known and you do not need episode
extraction or background queueing.

## Search

### `search_nodes`

Searches entity nodes.

Important arguments:

- `query`
- `group_ids` (string or list)
- `max_nodes`
- `entity_types`
- `center_node_uuid`

### `search_memory_facts`

Searches facts/edges.

Important arguments:

- `query`
- `group_ids` (string or list)
- `max_facts`
- `edge_types`
- `valid_at_before` / `valid_at_after`
- `invalid_at_before` / `invalid_at_after`
- `center_node_uuid` in newer search paths when exposed by the server version

## Retrieval and provenance

### `get_episodes`

Returns episodic nodes by `group_ids` and `max_episodes`.
Use it to confirm queued ingest has completed.

### `get_entity_edge`

Retrieves one fact edge by UUID.

### `get_episode_entities`

Returns the nodes and edges created by a list of episode UUIDs.
Use it for provenance tracing.

## Maintenance and summaries

### `delete_episode`

Deletes an episodic node and its dependent data.

### `delete_entity_edge`

Deletes one fact edge.

### `clear_graph`

Clears graph data for one or more groups. Destructive.

### `build_communities`

Runs community detection and returns community summaries.

### `summarize_saga`

Rebuilds the summary for a saga identified by name and group.

## Diagnostics

### `get_status`

Checks that the MCP server is initialized and that the database connection still
works.

### `/health`

HTTP health route used by containers and load balancers.

## Response shapes

The server returns small typed responses:

- `SuccessResponse`
- `ErrorResponse`
- `NodeSearchResponse`
- `FactSearchResponse`
- `EpisodeSearchResponse`
- `BuildCommunitiesResponse`
- `SagaSummaryResponse`
- `TripletResponse`
- `EpisodeEntitiesResponse`
- `StatusResponse`

When using the official MCP client, the returned payload may arrive as a text
message that needs JSON parsing.
