# Memory Lifecycle

## Core flow

1. Create a `Memori` instance.
2. Set attribution with `mem.attribution(entity_id, process_id)`.
3. Use `new_session()` to start a fresh conversation thread when needed.
4. Use `set_session(session_id)` to resume an existing thread.
5. Call `recall(query, limit=None)` or the cloud agent methods as needed.
6. Call `augmentation.wait()` when the script ends immediately after a write.

## Important rules

- `entity_id` must be a non-empty string.
- `process_id`, when supplied, must also be a non-empty string.
- `recall(query, limit)` requires a non-empty query string.
- `delete_entity_memories(...)` only works in BYODB mode.
- Short scripts often need `augmentation.wait()` so the background write can
  settle before the process exits.

## Config values that affect recall

- `recall_facts_limit` defaults to `5`.
- `recall_embeddings_limit` defaults to `1000`.
- `recall_relevance_threshold` defaults to `0.1`.
- `session_timeout_minutes` defaults to `30`.

## Practical guidance

- Set attribution before expecting durable memories.
- Use the same entity/process pair consistently across a session.
- If recall is empty, check mode selection, attribution, wait behavior, and
  whether the storage backend actually has the tables built.
