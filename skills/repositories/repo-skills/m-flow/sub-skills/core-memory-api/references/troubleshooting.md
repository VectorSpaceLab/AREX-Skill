# Core API and CLI Troubleshooting

Use this file for in-process Python API and `mflow` CLI failures. Route loader,
pipeline, retrieval-scoring, service, UI, MCP, or Docker issues to the sibling
sub-skills named in `SKILL.md`.

## Import or console entry point fails

Signals:

- `ModuleNotFoundError: No module named 'm_flow'`
- `mflow: command not found`
- `mflow --version` cannot import package modules

Checks:

```bash
python -c "import m_flow; print(m_flow.__version__)"
python -c "import shutil; print(shutil.which('mflow'))"
mflow --version
```

Fixes:

- Install the package into the active Python environment: `pip install mflow-ai`
  or an editable source install if developing the package.
- Ensure the shell running `mflow` uses the same environment as `python`.
- Run `python scripts/core_workflow_smoke.py` from this sub-skill for a safe
  import/export/config check.

## Coroutine or event-loop errors

Signals:

- `RuntimeWarning: coroutine ... was never awaited`
- `asyncio.run() cannot be called from a running event loop`

Fixes:

- In scripts: wrap the async workflow in `asyncio.run(main())`.
- In notebooks, async web handlers, or other running event loops: use `await
  m_flow.add(...)`, `await m_flow.memorize(...)`, and `await m_flow.query(...)`
  directly instead of nesting `asyncio.run()`.

## Add succeeded but query returns nothing

Likely causes:

1. `memorize()` has not run for the dataset.
2. `ingest(..., skip_memorize=True)` was used.
3. `run_in_background=True` returned before graph construction finished.
4. Query uses a different dataset name or inaccessible user context.
5. The wrong retrieval mode is being used for the question.

Checks:

```python
result = await m_flow.ingest("text", dataset_name="notes")
print(result.status)

# If you have a dataset UUID from an IngestResult:
print(await m_flow.datasets.get_status([result.dataset_id]))

qr = await m_flow.query("what is in notes?", datasets="notes", mode="episodic")
print(qr.to_dict())
```

Fixes:

- Run `await m_flow.memorize(datasets=["notes"], content_type=m_flow.ContentType.TEXT)`.
- Wait for background `memorize_pipeline` completion before querying.
- Verify the exact dataset name/UUID and user context.
- Route ranking and retrieval-mode tuning to `../../retrieval-graph-search/SKILL.md`.

## Invalid `ingest()` kwargs

Signal:

```text
ingest() got unexpected keyword argument(s): {...}. Valid params: [...]
```

Why it happens: `ingest()` dynamically inspects the current `add()` and
`memorize()` signatures, then splits `**kwargs` between the two calls. It rejects
unknown names. It also ignores `datasets=` because it always memorizes the data
it just added.

Fixes:

- Use only kwargs accepted by `add()` or `memorize()`.
- For add-only options: pass names such as `dataset_id`, `preferred_loaders`,
  `created_at`, `graph_scope`, `incremental_loading`, `enable_cache`,
  `items_per_batch`.
- For memorize options: pass names such as `run_in_background`, `chunker`,
  `chunk_size`, `chunks_per_batch`, `content_type`, `enable_content_routing`,
  `enable_episode_routing`, `enable_procedural`, `precise_mode`.
- Use `memorize_incremental_loading=` when you specifically need to override the
  memorize phase's incremental behavior; plain `incremental_loading` applies to
  `add()` and `ingest()` defaults memorize incremental loading to true.
- If the desired option concerns loader internals, content routing, chunking, or
  custom stages, route to `../../ingestion-pipelines/SKILL.md`.
- When in doubt, call `add()` then `memorize()` explicitly instead of `ingest()`.

## Triplet answer mode lacks credentials

Signals:

- Errors mentioning missing LLM/API key/provider.
- `mflow search ... --query-type TRIPLET_COMPLETION` fails before producing an
  answer.
- `query(..., mode="triplet")` returns no answer or raises provider setup errors.

Fixes:

```bash
export LLM_API_KEY="..."
```

or process-local Python setup:

```python
m_flow.config.set_llm_provider("openai")
m_flow.config.set_llm_model("gpt-4o-mini")
m_flow.config.set_llm_api_key("...")
m_flow.config.clear_caches()
```

If the task only needs retrieved context, avoid answer generation:

```python
result = await m_flow.query("deadline decision", datasets="notes", mode="episodic")
print(result.context)
```

or CLI:

```bash
mflow search "deadline decision" -d notes --query-type EPISODIC
```

## Background processing queried too early

Signals:

- `IngestStatus.BACKGROUND_STARTED` but query is empty.
- CLI prints "Memorization started in background" and a follow-up search returns
  no results.

Fixes:

- Poll `m_flow.datasets.get_status([dataset_uuid])` if a UUID is available.
- For simple scripts, use blocking mode (`run_in_background=False`) unless data
  size requires background processing.
- Do not treat a background-started status as queryable completion.

## Concurrent memorize conflict

Signals:

- Warnings about active memorize runs on the same dataset.
- A `ConcurrentMemorizeError` when `conflict_mode="error"` is used.

Fixes:

- Run only one memorize operation per dataset at a time.
- Use `conflict_mode="warn"` for default warning behavior, `"error"` for
  strict automation, or `"ignore"` only if the caller understands duplicate
  processing risks.

## Destructive delete/update/prune mistakes

Rules:

- `delete(data_id, dataset_id, mode="soft")` affects one data item.
- `delete(..., mode="hard")` can prune orphan entity nodes.
- `update(data_id, data, dataset_id, ...)` deletes the old item, adds new
  content, and re-runs memorization.
- `datasets.delete_dataset(dataset_id)` removes an entire dataset.
- `prune.all()` clears file storage, relational metadata, graph, vector, and
  cache state.

Before running any destructive call:

1. Confirm exact target: dataset name/UUID, data item UUID, or all stores.
2. Confirm whether local DB/vector/graph data can be removed.
3. Prefer `mode="soft"` unless the user asked to remove orphan graph nodes.
4. Never use `prune.all()` as a default setup or smoke-test step.

## `mflow delete` calls a missing `remove` alias

Signal:

```text
Deletion failed: module 'm_flow' has no attribute 'remove'
```

The CLI delete implementation may call a legacy `m_flow.remove(...)` alias, while
the current public package exports `delete`, `datasets.delete_dataset`, and
`prune`. Do not assume data was removed after this error. Use Python APIs for
version-safe deletion until the CLI alias is available:

```python
await m_flow.datasets.delete_dataset(dataset_id)
# or
await m_flow.delete(data_id, dataset_id, mode="soft")
```

## `mflow config get/set` method mismatch

Signals:

- `config.get() not available`
- `config.get_all() not available`
- `Failed to set 'key': ...` for a key that exists in `mflow config list`

The CLI config command may expect legacy `m_flow.config.get`, `get_all`, or
`set` methods. The current public facade provides explicit static methods such
as `show`, `set_llm_api_key`, `set_llm_model`, `set_graph_database_provider`,
`set_vector_db_provider`, and `clear_caches`.

Fix:

```python
print(m_flow.config.show(as_dict=True))
m_flow.config.set_llm_api_key("...")
m_flow.config.set_chunk_size(1500)
m_flow.config.clear_caches()
```

Use `mflow config list` for a quick registry display, but prefer Python config
calls for automation.

## Loader, retrieval, or service issue is out of scope

Route these cases away from this sub-skill:

- Unsupported file type, `preferred_loaders`, parser extras, chunker behavior,
  content routing, procedural toggles, or `run_custom_pipeline`: use
  `../../ingestion-pipelines/SKILL.md`.
- Empty/noisy search despite memorized data, RecallMode choice, scoring,
  episodic tuning knobs, Cypher, graph/vector provider tuning: use
  `../../retrieval-graph-search/SKILL.md`.
- FastAPI auth, HTTP routers, UI startup, MCP tools/transports, Docker Compose,
  ports, workers, or deployment secrets: use `../../service-integrations/SKILL.md`.
