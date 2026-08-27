# Test Selection

## By Change Surface

| Change surface | First checks | Expand when |
|---|---|---|
| Boot/config/health | `tests/e2e` startup or core boot unit tests | Deployment/runtime flags changed. |
| HTTP API/auth | authz/API-key/service/controller unit tests | Route/service/MCP contract changes. |
| MCP server | MCP controller/mount/service tests, manual MCP smoke | Transport/auth/tool registration changed. |
| Pipeline/stage | stage unit tests, fake message smoke, pipeline full-flow | Multiple stages or query scheduling changed. |
| Platform adapter | adapter-specific unit tests, webhook/signature tests | Live platform behavior or credentials are in scope. |
| Provider/runner/tool | provider/runner/tool manager unit tests | Real provider integration is requested. |
| Plugin Runtime | plugin connector/handler tests | SDK protocol/runtime changes. |
| Box/native/stdio MCP | Box service/connector tests | Real sandbox/container lifecycle changes. |
| Persistence/schema | SQLite migration tests, persistence unit tests | Postgres/pgvector/cloud migration behavior changed. |
| RAG/vector/storage | RAG/storage/vector unit tests | Live vector/storage service behavior changed. |
| Frontend | `pnpm lint` and focused unit/e2e | User path, routing, browser state, or mock API contract changed. |
| Skills assets | `bin/lbs validate`, `bin/lbs index --check` | Cases/suites/fixtures/troubleshooting changed. |

## Layered Gates

- Quick: `bash scripts/test-quick.sh`.
- Fast integration: `bash scripts/test-integration-fast.sh`.
- Coverage: `bash scripts/test-coverage.sh` when coverage risk matters.
- Full local: `make test-all-local` before major or release-like changes.
- Box integration: requires Docker/Podman.
- PostgreSQL tests: require `TEST_POSTGRES_URL`.
- Frontend e2e: requires Node/pnpm/browser setup.

## Skips

A skip is useful evidence only when it names the missing prerequisite. Do not
claim service-backed behavior is verified when the service was absent.
