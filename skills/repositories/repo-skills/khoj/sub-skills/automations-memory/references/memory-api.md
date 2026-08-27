# Memory API and Settings

Khoj exposes memory management through `/api/memories` and uses memory adapters during chat to retrieve, create, and delete long-term user memories. Memory belongs to a user, may optionally be scoped to a non-default agent, and stores raw text plus embeddings.

## Endpoint Summary

| Method and path | Purpose | Inputs | Success response |
| --- | --- | --- | --- |
| `GET /api/memories` | List memories for the authenticated user. | Optional `client` query param is accepted but not used by the route logic. | JSON list of `{id, raw, created_at}`. |
| `DELETE /api/memories/{memory_id}` | Delete one memory owned by the authenticated user. | Path `memory_id`. | `204` with no body. |
| `PUT /api/memories/{memory_id}` | Replace one memory's raw text. | Path `memory_id`; JSON body `{"raw": "..."}`. | JSON `{id, raw}` for the newly created memory row. |

All routes require authentication and verify ownership by filtering on both `id` and the current user.

## Read Behavior

`GET /api/memories` lists all memory rows for the authenticated user and does not filter by agent. Each item contains only the database id, raw text, and ISO-formatted creation time. It does not include embeddings, search model details, agent id, or updated time.

## Delete Behavior

`DELETE /api/memories/{memory_id}` deletes the row only if it belongs to the authenticated user. If no matching row exists, it returns `404` with JSON `{"error": "Memory not found"}`. A successful delete returns `204` and no response body.

The lower-level memory adapter also exposes deletion by user plus memory id and returns a boolean instead of an HTTP response. Chat memory deletion uses that adapter path and expects memory ids, not raw memory text.

## Update Behavior

`PUT /api/memories/{memory_id}` is replacement, not in-place mutation:

1. It finds the existing memory by `id` and user.
2. It rejects missing rows with `404 {"error": "Memory not found"}`.
3. It rejects an empty `raw` value with `400 {"error": "Missing required field 'raw'"}`.
4. It deletes the old memory row.
5. It creates a new memory through the memory adapter using the new raw text.
6. It returns the new memory's id and raw text.

This means a user-visible memory edit changes the memory id. Any client cache or test assertion that expects stable ids across updates is wrong for current Khoj behavior.

## Memory Creation and Embeddings

Memory creation through the adapter embeds the raw memory text with the default search model and stores the resulting vector. If a non-default agent is provided, the new row is scoped to that agent. If no agent is provided, or the provided agent is Khoj's default agent, the memory is stored without an agent scope.

Memory extraction during chat follows this shape:

- Khoj first checks whether memory is enabled for the user.
- If enabled, it asks the model to identify facts to create and facts to delete from the recent conversation and existing facts.
- Facts in the `create` list are saved as new memory rows.
- IDs in the `delete` list are deleted through the memory adapter.

## Memory Settings

Memory is controlled by a server-level mode and a per-user preference.

Server modes:

- `disabled`: memory is off for every user and overrides user preference.
- `enabled_default_off`: memory is off unless the user's `enable_memory` preference is set to true.
- `enabled_default_on`: memory is on unless the user's `enable_memory` preference is set to false.

If no server settings row exists, Khoj behaves like default-on memory: memory is enabled unless the user's `enable_memory` preference is explicitly false.

User configuration responses expose both `enable_memory` and `server_memory_mode`; when no server settings row exists, `server_memory_mode` is reported as `enabled_default_on`.

## User and Agent Scoping

Memory rows are always isolated by user. A user cannot read, update, delete, pull, or search another user's memories through the normal route and adapter paths.

Agent scoping applies to adapter-based memory pull/search and save behavior:

- Default agent or `agent=None`: sees all memories for the user, including unscoped memories and memories created by custom agents.
- Non-default custom agent: sees only memories for the same user and same custom agent.
- Saving with default agent or `agent=None`: stores the memory with no agent scope.
- Saving with a non-default custom agent: stores the memory with that custom agent scope.

This is why a custom agent may not see memories visible to the default Khoj agent. It is also why a default-agent memory may appear unscoped in the database.

## Memory Recency and Search

`pull_memories` retrieves recent memories updated within a default seven-day window, ordered newest first, with a default limit of 10. `search_memories` embeds the query, filters by user and agent scope, applies the configured search model confidence threshold as a maximum vector distance when present, and returns nearest memories up to the requested limit.

Use `search-retrieval` for vector search model and threshold troubleshooting; use this sub-skill for memory ownership, setting, and agent-scope questions.
