# Core Memory Workflows

Read this when you need the simplest way to store, improve, and query memory in Cognee.

## Two supported mental models

### 1) Memory-first flow

Use this when the user says things like “remember this,” “store this for later,” or “let the agent learn over time.”

```python
import cognee

await cognee.remember("Cognee turns documents into AI memory.")
results = await cognee.recall("What does Cognee do?")
```

Best for:
- session memory
- quick permanent memory storage
- single-call workflows
- background improvement after session storage

### 2) Pipeline-first flow

Use this when the user wants the pipeline stages explicitly.

```python
import cognee

await cognee.add("notes.txt", dataset_name="research")
await cognee.cognify(datasets="research")
results = await cognee.search("What are the main ideas?", datasets="research")
```

Best for:
- advanced users
- custom ingestion and graph-building stages
- explicit control over datasets and graph build timing

## Decision table

| User intent | Recommended call | Why |
| --- | --- | --- |
| Store one piece of knowledge and be done | `remember(...)` | Combines ingestion and graph build. |
| Store session chat, answer, or feedback | `remember(..., session_id=...)` | Writes to session cache first. |
| Estimate cost before running | `remember(..., dry_run=True)` or `cognify(..., dry_run=True)` | Produces an estimate without the expensive call path. |
| Split ingestion and graph build | `add(...)` then `cognify(...)` | Better when the user wants pipeline control. |
| Ask a question about stored content | `recall(...)` or `search(...)` | `recall` is session-aware; `search` is the lower-level query surface. |
| Bridge session memory into the graph | `improve(...)` | Enriches persistent memory with session-derived context. |
| Delete stored content | `forget(...)` | Removes graph or session-backed content depending on arguments. |

## Inputs that matter most

- `dataset_name`: default dataset label used by many flows.
- `dataset_id`: use when the user already has a concrete UUID.
- `session_id`: required for session-backed memory.
- `node_set`: logical tags for scoping and retrieval.
- `run_in_background`: returns a promise-like result object for long jobs.
- `self_improvement`: when true, `remember` may launch improvement work after the main graph update.

## Return shapes to explain

- `remember(...)` returns a `RememberResult` wrapper, not a plain dict.
- `recall(...)` and `search(...)` return lists of result entries.
- Background runs can be awaited later; they do not complete immediately.

## When to stop and route elsewhere

If the user asks *why* a certain search mode was chosen, or how to tune temporal/code/agentic retrieval, stop and route to [search-retrieval](../../search-retrieval/SKILL.md).

If the user asks why a provider, path, or database backend failed, stop and route to [configuration-backends](../../configuration-backends/SKILL.md).
