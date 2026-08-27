# Knowledge/Data/Memory Troubleshooting

Start with the smallest failing boundary: upload, parse, split, forward/vectorize, search, storage, memory policy, retrieval pipeline, Dreaming, or live infrastructure. Do not start Redis, Elasticsearch, MinIO, Ray, Celery, LibreOffice, or provider APIs unless the user explicitly asks for a live check and has provided the environment.

## Safe Diagnostic Script

Run the bundled static/import diagnostic from the generated sub-skill directory:

```bash
python scripts/check_knowledge_stack.py --repo-root <repo-root> --json
```

It checks expected files, parses relevant backend config names, extracts route decorators, and attempts imports/signature inspection. Import failures are diagnostic signals, not proof that live services are down.

## PPTX Upload or Processing Failures

Use this decision tree for `.pptx` failures:

1. **Upload boundary**
   - Confirm request path: knowledge-base upload, storage upload, direct `/tasks/process_text_file`, or preview conversion.
   - Check active size limit. Product docs may mention a smaller user-facing limit than backend constants; verify the endpoint actually hit.
   - Confirm destination (`minio` or local), object key, original filename, and tenant/user upload isolation.
2. **Optional dependency boundary**
   - `DataProcessCore` import failure usually means data-process extras are missing.
   - PPTX parsing needs unstructured PPTX support; image extraction from PPTX needs `python-pptx`.
   - Excel/PDF/JSON/EPUB/Markdown split failures point to `openpyxl`, `pypdf`, `ijson`, `ebooklib`, or markdown splitter dependencies.
3. **Conversion boundary**
   - PPTX parsing itself is not the same as Office preview conversion. Preview conversion uses the data-process service and LibreOffice (`soffice`) to create cached PDFs.
   - Word splitting and Office-to-PDF conversion can fail from missing `soffice`, conversion timeout, invalid output header, too-small generated PDF, or failed upload back to storage.
   - Concurrent conversions are guarded by a semaphore. Saturation appears as slow/hung conversions rather than parser errors.
4. **Model-cache/image boundary**
   - Multimodal extraction activates `UniversalImageExtractor` when `model_type="multi_embedding"` and the extension qualifies.
   - PDF high-resolution image extraction requires table-transformer and unstructured model initialization paths. Missing parameters can produce no image metadata rather than a hard failure.
   - Image filtering needs a CLIP model only when image filtering is enabled; otherwise it falls back to size-only behavior.
5. **Task orchestration boundary**
   - Distinguish process failure from forward failure. `PROCESS_FAILED` means parsing/splitting/source fetch; `FORWARD_FAILED` means chunk forwarding/vectorization.
   - Redis keys hold progress, aggregated split chunks, ready flags, task errors, and cancellation state. Missing Redis can prevent status/progress and async split aggregation.
   - Ray/Celery issues surface as worker inspection failures, retry loops, async split timeout, or no task metadata.
6. **Vectorization boundary**
   - Embedding model mismatch or missing selected model causes vectorization/search failures.
   - Dimension mismatch should surface as `es_dim_mismatch`; other bulk failures as `es_bulk_failed`.
   - Text embedding intentionally skips image-metadata chunks. Use a multimodal embedding model if those chunks should be indexed.

## Common Symptom Matrix

| Symptom | Likely boundary | Checks | Typical fix direction |
| --- | --- | --- | --- |
| `Unsupported chunking strategy` | SDK validation | Strategy must be `basic`, `by_title`, or `none`. | Validate UI/API inputs before enqueueing. |
| `.pptx` parses in one path but preview fails | Conversion, not parsing | Does the failing path call Office-to-PDF conversion? Is LibreOffice available? | Fix conversion service/dependency, not `DataProcessCore`. |
| Empty image metadata | Multimodal/model-cache | Was `model_type="multi_embedding"` used? Are PDF model-cache params present? | Configure multimodal model/cache; text-only search can ignore images. |
| File stuck waiting | Redis/Celery/Ray | Check process and forward states separately; look for async split ready key timeout. | Repair workers/broker/result backend; do not reparse blindly. |
| `No chunks received for forwarding` | Process → forward handoff | Redis chunk key missing, empty split result, or process produced no chunks. | Inspect process result before vector service. |
| `es_dim_mismatch` | Embedding/index mismatch | Knowledge base embedding dimension differs from indexed vectors. | Recreate index or select compatible embedding model; do not mix dimensions. |
| Hybrid search says model config needed | Knowledge-base model config | Knowledge record has no valid embedding model id. | Require explicit model selection for that knowledge base. |
| Search returns no KB accessible | Permission filtering | Check `allowed_index_names`, group visibility, tenant, creator/read/edit permission. | Fix permissions or selected KBs; do not bypass whitelist. |
| MinIO file size is `0` | Storage not found or hidden error | Compare strict and non-strict size APIs; check object path and permissions. | Use strict size path for diagnostics; fix storage credentials/object key. |
| Memory search returns `[]` | Embedding missing or disabled | `SearchMemoryTool` returns empty list when embedding is not configured. | Configure tenant embedding or test with explicit embedding/mocks. |
| Agent cannot write memory | Policy | Agents can only write agent short-term memory. | Use long-term version endpoints for tenant/user memory. |
| Dreaming run skipped | Lock/schedule | Audit reason `lock_busy` or disabled schedule. | Wait for active run or adjust schedule/config. |
| Memory retrieval ordering unexpected | Pipeline scoring | Check fusion weights, created-at timestamps, duplicate threshold, token budget. | Use pure pipeline fixtures to reproduce deterministically. |

## Boundary-Specific Playbooks

### Data Process Import Failure

1. Run the diagnostic script and inspect failed imports.
2. If `nexent.data_process.core` fails, check data-process extras and transitive parser dependencies.
3. If only backend app/service imports fail, check backend dependency extras and centralized constants.
4. Do not conclude Redis/Elasticsearch/MinIO are down from an import failure unless the traceback shows an actual connection attempt.

### Knowledge-Base Index/Search Failure

1. Check knowledge-base record exists and current user has read/edit permission.
2. Resolve embedding model through the knowledge record, not a request override.
3. For document indexing, verify the vector DB index exists, content chunks are non-empty, and model dimensions match the index.
4. For `knowledge_base_search`, check display-name conversion, whitelist filtering, `document_paths`, search mode, rerank fallback, and observer side effects.
5. If live ES is unavailable, stop at mocked/static verification and mark live service as optional.

### Storage/MinIO Failure

1. Identify object name, bucket/default bucket, and whether the path is a source file, cached preview PDF, or user attachment.
2. Use strict file size logic for diagnostics when a `0` size could hide permission or service errors.
3. For source preservation/quota issues, check the storage ledger and quota compensation path.
4. For delete operations, distinguish source-only deletion from full document/knowledge-base deletion.
5. Escalate deployed MinIO credentials, buckets, TLS, and network to [deployment-operations](../../deployment-operations/SKILL.md).

### Memory Provider or Retrieval Failure

1. Confirm memory switch, Dreaming switch, disabled-agent list, and tenant embedding status.
2. For manual long-term memory, use `/memory/long-term/{tenant|user}` version endpoints. Do not call removed legacy routes.
3. For agent short-term memory, verify `agent_id`, `conversation_id`, idempotency key, embedding vector, ES index name, and policy.
4. If retrieval scores are suspect, test `RetrievalPipeline` directly with pure fixtures before investigating databases.
5. External provider failures should degrade or return empty results unless the task specifically requires provider integration.

## What Not To Do

- Do not add direct environment reads outside the backend constants module.
- Do not bypass `allowed_index_names` or group/tenant permission checks to make search pass.
- Do not treat a CPU import check as proof of live Redis/ES/MinIO/Ray/Celery/LibreOffice readiness.
- Do not run broad native tests, benchmarks, or real deployment scripts during sub-skill use unless the user explicitly authorizes that scope.
- Do not store full conversations, credentials, temporary calculations, or user-forget data as memory.
