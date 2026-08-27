# Persistence, RAG, Workspace, and Monitoring Troubleshooting

## Migration Fails

- Confirm whether the failure is legacy baseline, Alembic revision, SQLite, or
  PostgreSQL-specific.
- Check the current Alembic head and generated metadata.
- Run SQLite migration tests first; add PostgreSQL DSN-backed tests for
  Postgres-only behavior.
- Do not fix by adding a legacy `dbmXXX` migration.

## Tenant Resource Leakage

Symptoms include resources visible across Workspaces or API-key requests using
unexpected Workspace ids. Inspect `RequestContext` construction, tenant scopes,
service method signatures, and permission checks. API-key Workspace identity
must come from the key, not from a selector header.

## Vector Retrieval Fails

- Check selected backend under `vdb.use`.
- Verify service endpoint/API key/timeout only for service-backed stores.
- Confirm embedding dimensions match vector index dimensions.
- Use unit filter conversion tests before service-backed tests when debugging
  query shape.

## File Upload or Knowledge Ingestion Fails

- Check max file size, allowed content type, parser availability, storage
  provider path traversal checks, and Workspace scoping.
- Plugin-provided parser/engine failures may need Plugin Runtime diagnosis.

## Monitoring Export Fails

- Confirm `DATA_EXPORT` permission for export routes.
- Check configured row limits, max offset, and cleanup retention.
- Avoid logging raw tokens, provider keys, or private document content while
  diagnosing export failures.
