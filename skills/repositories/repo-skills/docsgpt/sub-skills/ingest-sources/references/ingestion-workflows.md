# Ingestion Workflows

## File source

1. Select files and any advanced source configuration.
2. Upload through the source upload surface.
3. Capture the task id and poll `GET /api/task_status?task_id=...`.
4. On success, record the source id/result rather than only the task id.
5. Inspect source files/chunks and run one retrieval query.

For bulk uploads, isolate one failing file by retrying a tiny representative input. Avoid repeatedly enqueueing the same large source while a worker is still active.

## Remote source

1. Choose one registered loader and validate the URL/config shape.
2. Bound network scope and provide credentials only when required.
3. Enqueue the remote source.
4. Poll task state; capture loader/parser errors separately.
5. Verify resulting source metadata and chunks.
6. Use source sync only after understanding whether it replaces, appends, or reconciles content for that loader.

## Connector source

1. Establish OAuth/session state for the current user.
2. List connector files and select explicit resources.
3. Enqueue ingestion with source-level configuration.
4. Verify callback/session expiry and worker access to encrypted credentials.
5. Poll completion and check ownership/team access.
6. Schedule or trigger sync only after a manual bounded sync passes.

## Audio source

- Cloud path: configure `STT_PROVIDER=openai`, model/key, language and file limit.
- Local path: install/configure optional `faster_whisper`; CPU can be slow and GPU/model availability must be proven separately.
- Timestamp/diarization settings may be provider-dependent; do not promise diarization when the selected provider ignores it.
- The transcript enters the normal parser/chunk/embed/index path. Inspect transcript quality before blaming retrieval.

## Re-ingestion decision

Re-ingest when changing:

- chunking strategy, max/min tokens, or duplicate-header behavior;
- embedding model, endpoint, or vector dimension;
- parser/OCR behavior that changes extracted text;
- source content after a sync that does not update existing chunks automatically;
- GraphRAG enable/rebuild or graph extraction inputs.

Re-ingestion is generally not required for query-time fields such as retriever, exposure, chunks, score threshold, query rephrasing, or pre-screening.

## Wiki and GraphRAG conversions

The generic source config endpoint cannot mutate `kind`. Use dedicated endpoints/actions:

- Wiki conversion and page endpoints for living, agent-editable source content.
- `POST /api/sources/<source_id>/graphrag/enable` for GraphRAG. It enqueues a rebuild and requires pgvector plus the feature flag.

## Completion evidence

A complete ingestion check includes:

```text
input accepted -> task terminal success -> source row visible -> chunks present
-> embedding/vector write succeeded -> one expected citation retrieved
```

If any arrow fails, diagnose that layer rather than rerunning the whole pipeline blindly.
