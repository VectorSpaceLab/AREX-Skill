# Testing and Verification

## Purpose

Use this reference before choosing Nexent native tests, static checks, or optional live-service checks.

## Safe default checks

- Static route inventory: backend route helper in `sub-skills/backend-services-api/scripts/`.
- SDK import/signature probe: SDK helper in `sub-skills/sdk-agent-runtime/scripts/`.
- Knowledge/data/memory import diagnostics: helper in `sub-skills/knowledge-data-memory/scripts/`.
- Frontend API-call extraction: helper in `sub-skills/frontend-integration/scripts/`.
- SQL/init migration presence: helper in `sub-skills/deployment-operations/scripts/`.

These helpers are deterministic, read-only, and do not start services.

## Native test selection

| Area | Start with | Avoid by default |
| --- | --- | --- |
| SDK runtime | Focused `test/sdk/core/*` and mocked agent runtime tests | Real provider/model/MCP/A2A calls. |
| Backend routes/services | Matching `test/backend/app/test_*_app.py` and `test/backend/services/test_*_service.py` | Live database, Redis, Elasticsearch, MinIO, model provider calls. |
| Data-process/knowledge/memory | Pure or mocked data-process, vector, storage, memory tests | Full Ray/Celery workers, OCR/model downloads, large documents. |
| Frontend | `npm run type-check`, `lint`, `format:check`, `build`, or `check-all` when dependencies exist | Installing Node deps just for a small backend change. |
| Deployment | Static shell/SQL tests when safe | Real deploy/uninstall, image build/push, registry or cluster operations without approval. |

## Optional live verification

Live verification may require credentials, external services, GPUs, Docker/Kubernetes, or large downloads. Ask for explicit target and approval before performing destructive or credentialed actions. Keep secrets out of reports.

## Schema-change verification

For database schema changes, verify all of:

1. Backend model/helper behavior.
2. Migration SQL.
3. Fresh-deploy init SQL copies for supported deployment paths.
4. App version/release references if required.
5. Frontend types/services when API payloads changed.

## Interpreting environment differences

Nexent's SDK and backend/data-process dependencies can require separate inspection environments because package metadata pins differ. Treat this as a verification planning detail, not a public runtime guarantee. Use focused checks in the environment variant that matches the code path being validated.
