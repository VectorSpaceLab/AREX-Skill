# Core Workflows

Use these recipes when a caller wants to operate M-flow from Python or the CLI.
They avoid service startup and focus on in-process package APIs.

## Prerequisites

```bash
python -c "import m_flow; print(m_flow.__version__)"
mflow --version
```

For live add/memorize/search, configure an LLM provider and API key or a working
local LLM setup. The common environment variable is `LLM_API_KEY`. Search modes
that produce LLM answers, especially triplet completion, require credentials.

## Novice quickstart: add, memorize, query

```python
import asyncio
from datetime import datetime, timezone

import m_flow


async def main():
    dataset = "agent_notes"

    await m_flow.add(
        "M-flow builds persistent memory for AI agents.",
        dataset_name=dataset,
        created_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
    )

    await m_flow.memorize(
        datasets=[dataset],
        content_type=m_flow.ContentType.TEXT,
    )

    result = await m_flow.query(
        "How does M-flow work?",
        datasets=dataset,
        mode="episodic",
        top_k=5,
    )

    if result.is_empty():
        print("No context returned; check dataset name and memorize status.")
    else:
        for item in result.context:
            print(item)


asyncio.run(main())
```

Equivalent CLI sequence:

```bash
mflow add "M-flow builds persistent memory for AI agents." -d agent_notes
mflow memorize -d agent_notes --content-type text
mflow search "How does M-flow work?" -d agent_notes --query-type EPISODIC
```

## One-step ingest workflow

Use `ingest()` when the task is simply "add this and make it queryable".

```python
import asyncio
import m_flow


async def main():
    result = await m_flow.ingest(
        "Release notes: feature A shipped after beta feedback.",
        dataset_name="release_notes",
        run_in_background=False,
    )

    print(result.to_dict())
    if result.needs_retry():
        raise RuntimeError(result.error_message)

    answer = await m_flow.query(
        "What shipped after beta feedback?",
        datasets="release_notes",
        mode="episodic",
    )
    print(answer.context)


asyncio.run(main())
```

Important `ingest()` behavior:

- `skip_memorize=True` means the data is not queryable yet.
- `run_in_background=True` returns `IngestStatus.BACKGROUND_STARTED`; wait before
  querying.
- Unknown keyword arguments raise `TypeError`; see
  [troubleshooting](troubleshooting.md#invalid-ingest-kwargs).
- `datasets=` is ignored by `ingest()` because it always memorizes the data just
  added. Use `memorize()` directly for existing datasets.

## Background memorize or ingest

Use background mode only when the caller accepts eventual completion and can
poll by dataset ID.

```python
import asyncio
import m_flow


async def main():
    result = await m_flow.ingest(
        "Large content batch...",
        dataset_name="large_batch",
        run_in_background=True,
    )

    if result.is_background():
        status = await m_flow.datasets.get_status([result.dataset_id])
        print(status)
        print("Wait for memorize_pipeline completion before querying.")


asyncio.run(main())
```

For CLI background processing:

```bash
mflow add large_document.md -d large_batch
mflow memorize -d large_batch --background --verbose
```

## Dataset naming and identity

- Keep `dataset_name` stable across add/ingest, memorize, query/search, and data
  management calls.
- Prefer lowercase names with underscores for scripts: `customer_notes_2026q1`,
  `agent_memory_smoke`, `meeting_logs`.
- Use `dataset_id` only when the task already has the UUID and must avoid name
  ambiguity.
- If a query returns no data, verify that the query targets the same dataset name
  and that background memorization has completed.

## Historical imports with `created_at`

```python
from datetime import datetime, timezone

await m_flow.add(
    "2023 meeting: deadline moved to May 8.",
    dataset_name="meeting_history",
    created_at=datetime(2023, 5, 8, 9, 30, tzinfo=timezone.utc),
)
```

`created_at` can be an integer Unix timestamp in milliseconds or a `datetime`.
Naive datetimes are treated as UTC by the API. This is useful for chat history,
incident logs, and dated documents where temporal recall matters.

## Loader preference handoff

The core API accepts `preferred_loaders` on `add()` and `update()`:

```python
await m_flow.add(
    ["report.pdf", "notes.md"],
    dataset_name="documents",
    preferred_loaders=[{"name": "pdf", "config": {}}],
)
```

Do not invent loader names or loader configs from this sub-skill. Route the
choice of loader names, optional parser dependencies, content routing, and custom
pipeline stages to `../../ingestion-pipelines/SKILL.md`.

## Triplet answer versus context retrieval

For natural-language answers with graph context:

```python
result = await m_flow.query("Summarize the project status", datasets="notes", mode="triplet")
print(result.answer)
```

If no LLM key is configured, or the user wants retrieved evidence rather than a
model-written answer, use context-first modes:

```python
result = await m_flow.query("project status", datasets="notes", mode="episodic")
for ctx in result.context:
    print(ctx)
```

Advanced `RecallMode`, ranking, and output controls belong in
`../../retrieval-graph-search/SKILL.md`.

## Manual episode insertion

Use manual insertion when the caller already has curated memory structure and
wants to bypass LLM extraction:

```python
import asyncio
import m_flow


async def main():
    result = await m_flow.manual_add_episode(
        name="Roadmap decision",
        summary="The team chose staged rollout to reduce migration risk.",
        facets=[
            {
                "facet_type": "decision",
                "search_text": "Use staged rollout",
                "description": "Roll out by tenant group before global release.",
            }
        ],
        entities=[
            {
                "name": "staged rollout",
                "description": "Deployment strategy selected for the roadmap",
            }
        ],
        dataset_name="manual_memory",
    )
    print(result)


asyncio.run(main())
```

Manual APIs still persist graph/vector data. Confirm dataset scope before use.

## Configuration workflow

Read masked config safely:

```python
import m_flow

print(m_flow.config.show("llm"))
print(m_flow.config.env_categories())
```

Set process-local config before running a workflow:

```python
m_flow.config.set_llm_provider("openai")
m_flow.config.set_llm_model("gpt-4o-mini")
m_flow.config.set_llm_api_key("...")
m_flow.config.clear_caches()
```

For persistent environment variables, secrets, and service deployments, route to
root configuration guidance (`../../../references/configuration.md`) or
`../../service-integrations/SKILL.md`.

## Update, delete, and prune workflow cautions

Data-management APIs can remove or rebuild stored state:

```python
# Delete one data item from one dataset.
await m_flow.delete(data_id, dataset_id, mode="soft")

# Replace one data item and re-run memorization for the dataset.
await m_flow.update(data_id, "replacement text", dataset_id)

# Development/test cleanup only: clears all M-flow data stores.
await m_flow.prune.all()
```

Before using them, get explicit user confirmation for the target dataset/item,
backup expectations, and whether the operation may affect shared local DB files.
Never call `prune.all()` as part of a default smoke test.
