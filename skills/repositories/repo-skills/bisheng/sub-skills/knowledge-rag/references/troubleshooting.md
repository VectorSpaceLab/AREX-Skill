# Knowledge and RAG Troubleshooting

## Parser or loader failures

Symptoms:
- File status moves to FAILED or TIMEOUT.
- PDFs parse locally but scanned images fail.
- External parser returns timeout or auth errors.

Likely causes:
- `knowledge.loader_provider` points to an unavailable service.
- Provider URL/token/header config is missing or wrong.
- Image OCR requires an external parser; local PDF fallback is not a full image OCR substitute.
- File extension routing selected an unexpected loader.

Recovery:
- Run the bundled config checker to verify key presence.
- Confirm provider URL reachability from backend/worker host before changing pipeline code.
- Reproduce with a tiny fixture if possible.
- Keep network/parser-service checks separate from unit tests.

## MinIO or preview failures

Symptoms:
- Original file uploads but preview, bbox, thumbnail, or extracted images are missing.
- Frontend preview URLs return 403.

Likely causes:
- MinIO endpoint/sharepoint mismatch.
- Transform stage failed after loader success.
- Object name or tenant prefix is wrong.

Recovery:
- Distinguish source object upload from derived preview/bbox/thumbnail objects.
- Check object-storage config and frontend proxy host matching.
- Route tenant prefix problems to `identity-permissions-tenancy`.

## Vector or search index failures

Symptoms:
- File status is SUCCESS but retrieval returns no results.
- Keyword search works but semantic search does not, or the reverse.
- Rebuild after embedding model change fails.

Likely causes:
- Milvus collection missing or stale.
- Elasticsearch index missing or stale.
- Embedding model configuration invalid.
- Metadata field schema mismatch between DB, Milvus, and ES.

Recovery:
- Identify which channel failed: dense Milvus or sparse Elasticsearch.
- Use existing diagnostic scripts such as Milvus schema inspectors only under `deployment-maintenance` rules; many require live services.
- Rebuild logic should preserve ES data when only embeddings change, according to documented worker behavior.

## Worker and queue failures

Symptoms:
- Files remain WAITING or PROCESSING.
- Retry does not change status.
- Copy/rebuild tasks stall.

Likely causes:
- `knowledge_celery` worker not running or wrong config.
- Redis broker mismatch between API and worker.
- Worker lacks storage/vector/search connectivity.
- Tenant context not propagated into worker.

Recovery:
- Start the correct queue from `src/backend`.
- Verify API and worker share the same `config` env value.
- Route tenant header/context issues to `identity-permissions-tenancy`.

## Permission-related empty results

Symptoms:
- Ingestion succeeded, but a user cannot see a knowledge space or file.
- API list results differ by tenant/admin state.

Recovery:
- Do not patch retrieval first. Check ReBAC/OpenFGA/approval and tenant visibility via `identity-permissions-tenancy`.
- Cursor list behavior may intentionally scan extra DB rows to fill visible pages after permission filtering.

## Test environment overreach

Avoid:
- Running large OCR/model/parser service tests as unit checks.
- Treating a skipped external service test as a pass.
- Hardcoding parser endpoints, object storage credentials, or model IDs in tests.
