---
name: ingestion-pipelines
description: "Operate M-flow ingestion, loader selection, memorization stages,
  procedural learning, and custom pipeline workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# M-flow ingestion pipelines

Use this sub-skill when the task is about getting data into M-flow memory or assembling ingestion/memorization pipelines:

- choose input shapes, loaders, `preferred_loaders`, chunking, and `content_type`;
- run one-step `ingest()`, staged `add()` then `memorize()`, or advanced `run_custom_pipeline()` workflows;
- configure memorization layers: episodic, procedural, content routing, episode routing, precise mode, and conflict handling;
- extract procedural memory later with `learn()` from already-built episodic memory.

Route elsewhere:

- basic CLI/API quickstarts, dataset CRUD, and first-time examples → `core-memory-api`;
- `RecallMode`, `search()`, `query()`, graph/vector adapter tuning, and retrieval ranking → `retrieval-graph-search`;
- running API servers, UI, MCP, Docker, and service integration topology → `service-integrations`.

## First decisions

1. **Separate ingestion from memorization when you need control.** Use `ingest()` for the common add+memorize path. Use `add()` then `memorize()` when you need to validate stored data first, use different loader/chunking settings, skip/query later, or recover from a failed memorize stage.
2. **Declare content shape before LLM routing.** With content routing enabled, pass `content_type=ContentType.TEXT` for articles/notes/code-like prose and `content_type=ContentType.DIALOG` for chats, interviews, meeting logs, or transcripts. For mixed article + transcript data, prefer separate calls/datasets per content type instead of one mixed call.
3. **Choose memory layers intentionally.** Episodic memory is enabled by default. Procedural extraction is opt-in during `memorize(enable_procedural=True)` or can be run later with `learn()`.
4. **Use `conflict_mode="error"` for production jobs.** It prevents accidental concurrent `memorize()` runs over the same dataset. Use `"warn"` for interactive work and `"ignore"` only when you accept duplicate/inconsistent graph risk.
5. **Inspect the runtime before advising.** Run [scripts/pipeline_stage_inspector.py](scripts/pipeline_stage_inspector.py) to list the installed loader registry and public signatures without executing a pipeline.

## Common recipes

### One-step ingestion with explicit routing

```python
import m_flow
from m_flow import ContentType

result = await m_flow.ingest(
    data=["meeting-notes.txt", "transcript.txt"],
    dataset_name="team-memory",
    content_type=ContentType.DIALOG,
    enable_content_routing=True,
    enable_procedural=True,
    conflict_mode="error",
)

if result.needs_retry():
    # add() succeeded but memorize() failed; retry only the dataset's memorize stage.
    await m_flow.memorize(datasets=[result.dataset_name], content_type=ContentType.DIALOG)
```

### Staged add then memorize

```python
import m_flow
from m_flow import ContentType

await m_flow.add(
    data=["docs/overview.md", "docs/reference.pdf"],
    dataset_name="docs",
    preferred_loaders=[
        {"advanced_pdf_loader": {"strategy": "hi_res"}},
        "pypdf_loader",
        "text_loader",
    ],
)

await m_flow.memorize(
    datasets=["docs"],
    chunk_size=1200,
    chunks_per_batch=20,
    content_type=ContentType.TEXT,
    enable_content_routing=True,
    precise_mode=True,
    conflict_mode="error",
)
```

### Learn procedures from existing episodic memory

```python
import m_flow

# Prefer dataset-wide learning for duplicate prevention: learn() skips Episodes
# that already have derived_procedure edges when it discovers Episodes itself.
summary = await m_flow.learn(datasets=["team-memory"])
print(summary)
```

`learn(run_in_background=True)` is accepted by the public signature but currently logs a warning and runs synchronously so it can create `derived_procedure` edges after procedure persistence.

## Reference map

- [references/data-formats.md](references/data-formats.md): accepted data shapes, loader registry, optional loader extras, `preferred_loaders`, and content-type decisions.
- [references/pipeline-reference.md](references/pipeline-reference.md): memorize stage order, toggles, `learn()`, `Stage`, `run_custom_pipeline()`, and validation commands.
- [references/troubleshooting.md](references/troubleshooting.md): loader, path, routing, concurrency, procedural, and custom-pipeline failure signals.
