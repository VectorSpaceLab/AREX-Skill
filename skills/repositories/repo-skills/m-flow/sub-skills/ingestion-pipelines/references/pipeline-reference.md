# Pipeline reference

This reference summarizes memorization order, stage composition, procedural learning, and custom pipeline assembly for M-flow ingestion workflows.

## Add, ingest, and memorize routing

| Need | API choice | Why |
| --- | --- | --- |
| Fast add + graph construction | `await m_flow.ingest(data, dataset_name=..., content_type=...)` | Calls `add()` then `memorize()` and returns `IngestResult` with add and memorize run IDs. |
| Stage data without graph construction | `await m_flow.ingest(..., skip_memorize=True)` or `await m_flow.add(...)` | Useful for validating loader behavior or batching before memory extraction. Data is not queryable until `memorize()` succeeds. |
| Fine loader/chunking/routing control | `await m_flow.add(...); await m_flow.memorize(...)` | Keeps loader choices, dataset state, and graph extraction settings separate. |
| Custom preprocessing or low-level workflow | `await m_flow.run_custom_pipeline(tasks=[Stage(...)], ...)` | Runs caller-supplied stages through the standard workflow executor. |
| Extract procedures after episodic memory already exists | `await m_flow.learn(datasets=[...])` | Converts existing Episodes/Facets into procedural memories and links procedures back to source Episodes. |

`ingest()` validates kwargs against the combined `add()` and `memorize()` parameter sets. Invalid keys raise `TypeError`. A supplied `datasets` kwarg is ignored by `ingest()` because it always memorizes the dataset just added.

## `IngestResult` statuses

| Status | Meaning | Follow-up |
| --- | --- | --- |
| `COMPLETED` / `"completed"` | `add()` and synchronous `memorize()` completed. | Data should be queryable, subject to backend writes and model quality. |
| `BACKGROUND_STARTED` / `"background_started"` | Add succeeded and memorize was scheduled in background. | Track run events/logs; do not assume immediate queryability. |
| `MEMORIZE_SKIPPED` / `"memorize_skipped"` | Add succeeded; graph construction skipped. | Run `memorize(datasets=[result.dataset_name], ...)`. |
| `MEMORIZE_FAILED` / `"memorize_failed"` | Add succeeded but memorize raised. | Retry `memorize()` with the same dataset after fixing config/backend issue. |

## Default memorize stage order

### Sentence-level content routing path

Used when `enable_content_routing=True` and episodic memory is enabled.

1. `detect_format`
2. `segment_documents(max_chunk_size=chunk_size or LLM max tokens, chunker=TextChunker)`
3. `route_content_v2(content_type=...)` — stores sentence classifications in chunk metadata.
4. `compress_text`
5. memory write task:
   - episodic only: `write_episodic_memories(precise_mode=...)`;
   - episodic + procedural: unified episodic/procedural write that collects procedural decisions during episodic summarization and writes procedures from those decisions.
6. `persist_memory_nodes(embed_triplets=...)`
7. `write_same_entity_edges`
8. `write_facet_entity_edges`

### Non-content-routing path

Used when content routing is disabled or episodic memory is disabled.

1. `detect_format`
2. `segment_documents(...)`
3. `compress_text`
4. memory write task:
   - episodic only: `write_episodic_memories(precise_mode=...)`;
   - procedural only: `write_procedural_memories`;
   - episodic + procedural: `execute_parallel([episodic Stage, procedural Stage], merge_results=True, deduplicate=True)`.
5. `persist_memory_nodes(embed_triplets=...)`
6. `write_same_entity_edges` and `write_facet_entity_edges` only when episodic memory is enabled.

Avoid disabling both episodic and procedural layers for normal workloads; the pipeline still performs earlier summarization/persistence stages but produces little useful memory.

## Memorize toggles

Keyword arguments override environment variables for the current call.

| Option | Default | Effect |
| --- | --- | --- |
| `enable_episodic` | env `MFLOW_EPISODIC_ENABLED`, default true | Enables Episode/Facet/Entity memory extraction. |
| `enable_procedural` | env `MFLOW_PROCEDURAL_ENABLED`, default false | Extracts reusable procedures/preferences. Higher LLM cost. |
| `enable_content_routing` | env `MFLOW_CONTENT_ROUTING`, default true | Adds sentence-level routing before summarization when episodic is enabled. |
| `content_type` | `ContentType.TEXT` if omitted by `ingest()` | Controls text vs dialog sentence splitting. Use explicit values for predictable behavior. |
| `precise_mode` | env `MFLOW_PRECISE_MODE`, default false | Uses more token-expensive summarization intended to preserve all factual details. |
| `chunk_size` | derived from LLM context | Max chunk token target for `segment_documents`. |
| `chunks_per_batch` | internal default 100 when omitted | Batch size for LLM-heavy stages. Lower it for rate limits or memory pressure. |
| `items_per_batch` | 20 | Workflow batch size for dataset item processing. |
| `incremental_loading` | true | Memorize only incrementally processed rows when possible. `ingest()` forces memorize incremental true unless `memorize_incremental_loading` is set. |
| `enable_cache` | true | Lets pipeline skip stages already marked complete. Disable for forced rebuilds. |
| `run_in_background` | false | Uses the background executor and returns run events immediately. |
| `conflict_mode` | `"warn"` | `"error"` raises on same-process concurrent memorize for the same dataset; `"warn"` logs; `"ignore"` registers no protection. |

Episode routing and facet-point options are passed through to episodic writing when supported:

- `enable_episode_routing` / env `MFLOW_EPISODIC_ENABLE_ROUTING`, default true;
- `enable_semantic_merge` / env `MFLOW_EPISODIC_ENABLE_SEMANTIC_MERGE`, default false;
- `semantic_merge_threshold` / env `MFLOW_EPISODIC_SEMANTIC_MERGE_THRESHOLD`, default `0.90`;
- `enable_facet_points` / env `MFLOW_EPISODIC_ENABLE_FACET_POINTS`, default true;
- `enable_llm_entity_for_routing` / env `MFLOW_EPISODIC_USE_LLM_ENTITY_FOR_ROUTING`, default true;
- `facet_points_prompt_file` / env `MFLOW_EPISODIC_FACET_POINTS_PROMPT`.

## Transcript vs article pattern

Do not feed unrelated article prose and dialog transcript text through one memorization call if they need different splitting behavior.

```python
from m_flow import ContentType

await m_flow.add(["docs/article.md"], dataset_name="mixed-source")
await m_flow.add(["calls/call-001.txt"], dataset_name="mixed-source")

# If the dataset now contains both types, create two ingestion passes when possible,
# or keep separate datasets and query both later.
await m_flow.memorize(
    datasets=["article-source"],
    content_type=ContentType.TEXT,
    enable_content_routing=True,
)
await m_flow.memorize(
    datasets=["dialog-source"],
    content_type=ContentType.DIALOG,
    enable_content_routing=True,
)
```

If operational constraints force one call over mixed text, keep `MFLOW_AUTO_DETECT_DIALOG=true` and inspect logs for `[sentence_routing] Auto-detected DIALOG`. If false positives happen on code/config text, set `MFLOW_AUTO_DETECT_DIALOG=false` and pass `ContentType.TEXT` explicitly.

## Procedural memory paths

### During memorize

```python
await m_flow.memorize(
    datasets=["runbooks"],
    content_type=ContentType.TEXT,
    enable_episodic=True,
    enable_procedural=True,
    enable_content_routing=True,
)
```

With content routing enabled, procedural candidates can be collected in the episodic summarization pass and written by a unified procedure stage. Without content routing, episodic and procedural writers can run in parallel with deduplication.

### After episodic memory exists

```python
summary = await m_flow.learn(datasets=["runbooks"])
```

`learn()` workflow:

1. fetch Episode nodes and associated Facets from the graph;
2. convert Episodes into virtual `ContentFragment` / `FragmentDigest` records;
3. run `write_procedural_memories`;
4. filter virtual digest nodes before persistence;
5. persist procedures;
6. create `derived_procedure` edges back to source Episodes.

Duplicate prevention: when `episode_ids` is omitted, `learn()` searches for Episodes without existing `derived_procedure` edges. If callers provide explicit `episode_ids`, pre-check for existing derived edges when duplicate prevention matters.

Background note: `learn(run_in_background=True)` currently logs that background execution is not supported and runs synchronously so it can create derived edges after persistence.

## `Stage` contract

Import either from `m_flow.pipeline` or `m_flow.pipeline.tasks`:

```python
from m_flow.pipeline import Stage
```

A `Stage` wraps a callable and exposes an async-iterable execution contract. The callable may be:

- a normal function;
- a coroutine function;
- a sync generator;
- an async generator.

Constructor shape:

```python
Stage(fn, *default_args, config=None, task_config=None, **default_kwargs)
```

Current behavior appends `default_args` after the runtime pipeline inputs when invoking `fn`, and merges `default_kwargs` with runtime kwargs. `task_config={"batch_size": N}` controls collection batch size for generator/async-generator stages. `config` is an alias; prefer `task_config` for consistency with M-flow examples.

Useful introspection properties:

- `stage.executable` — original callable;
- `stage.task_type` — function/coroutine/generator category;
- `stage.task_config` — batch config;
- `stage.default_params` — stored positional and keyword defaults.

## Custom pipeline patterns

### Replicate add pipeline

```python
import m_flow
from m_flow.auth.methods import get_seed_user
from m_flow.ingestion.pipeline_tasks import ingest_data, resolve_data_directories
from m_flow.pipeline import Stage

current_user = await get_seed_user()

ingestion_steps = [
    Stage(resolve_data_directories, include_subdirectories=True),
    Stage(ingest_data, "custom-dataset", current_user),
]

await m_flow.run_custom_pipeline(
    tasks=ingestion_steps,
    data=["docs/a.md", "docs/b.pdf"],
    dataset="custom-dataset",
    user=current_user,
    workflow_name="custom_add_pipeline",
)
```

### Replicate memorize pipeline with public default tasks

```python
from m_flow.api.v1.memorize.memorize import get_default_tasks
from m_flow import ContentType

graph_tasks = await get_default_tasks(
    user=current_user,
    chunk_size=1200,
    chunks_per_batch=20,
    enable_content_routing=True,
    content_type=ContentType.TEXT,
)

await m_flow.run_custom_pipeline(
    tasks=graph_tasks,
    dataset="custom-dataset",
    user=current_user,
    workflow_name="custom_memorize_pipeline",
)
```

### Add a safe custom preprocessing stage

```python
from m_flow.pipeline import Stage

async def normalize_lines(items):
    if not isinstance(items, list):
        items = [items]
    return [str(x).replace("\r\n", "\n").strip() for x in items]

steps = [
    Stage(normalize_lines),
    Stage(resolve_data_directories, include_subdirectories=True),
    Stage(ingest_data, "normalized-docs", current_user),
]
```

Custom stages should be deterministic, should return the shape expected by the next stage, and should avoid writing to graph/vector stores unless they intentionally produce/persist M-flow memory nodes.

## Validation commands

Inspect the installed runtime without running a pipeline:

```bash
python sub-skills/ingestion-pipelines/scripts/pipeline_stage_inspector.py
python sub-skills/ingestion-pipelines/scripts/pipeline_stage_inspector.py --json
```

Minimum smoke checks before a real ingestion run:

```python
import inspect, m_flow
from m_flow.pipeline import Stage

print(m_flow.__version__)
print(inspect.signature(m_flow.add))
print(inspect.signature(m_flow.memorize))
print(inspect.signature(m_flow.run_custom_pipeline))
print(Stage(lambda x: x).task_type)
```

For real data, first test one small text item with a disposable dataset, then scale to files/URLs and larger `items_per_batch` values.
