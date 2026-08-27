# TaskingAI backend native testing notes

This reference summarizes source-backed backend native-test behavior and verified inspection constraints. It is intended for deciding what can be safely tested in a future task without depending on the source checkout.

## Verified inspection facts

- Backend package version evidence: `v0.3.0`.
- Python 3.10 can import backend components used by this sub-skill, including the FastAPI route aggregator, `APIRouter`, assistant/model/retrieval classes, model type values, and `TextSplitter`.
- Python 3.11 is unsuitable for backend inspection/development with the pinned backend dependency set because `aioredis==2.0.1` fails during import with a duplicate `TimeoutError` base-class error. Choose Python 3.10 when a backend inspection or development environment must import the backend app.
- Backend dependencies include FastAPI/Uvicorn, asyncpg/Postgres, aioredis/Redis, tiktoken, aioboto3/object storage, OpenAPI schema validation, document loaders, and retrieval content loaders.

Do not include private environment names, executable paths, or local checkout paths in user-facing runtime guidance.

## Native service test candidates and prerequisites

The source evidence includes two backend native service-test wrappers:

| Candidate behavior | Source-backed mode | What it checks | Prerequisites | Safe default |
| --- | --- | --- | --- | --- |
| API-mode backend tests | API service mode | Backend service/client tests marked for API mode. | Running backend API service with correct API env, Postgres, Redis, inference service URL, plugin service URL, object storage settings, and test dependencies. | Skip unless services are already provided or user authorizes service startup/configuration. |
| Web-mode backend tests | Web service mode | Backend service tests marked for web/admin mode plus API-mode coverage. | Running backend web service with admin auth env, Postgres, Redis, inference/plugin service URLs, object storage settings, and test dependencies. | Skip unless services are already provided or user authorizes service startup/configuration. |

These candidates are **alternative native checks**, not mandatory for every backend API task. They may start or depend on system services, mutate databases, require credentials or network-reachable internal services, and can fail for deployment reasons unrelated to backend API semantics.

## Safe skip criteria

Skip original native service tests and use static or synthetic checks instead when any of the following is true:

- No running Postgres/pgvector database is available for the backend under test.
- No running Redis service is available.
- Backend-to-inference or backend-to-plugin service URLs are absent, point to unavailable services, or require a deployment task first.
- Object storage settings are not configured for the intended file/image path.
- The user has not authorized service startup, database mutation, external network calls, or credential use.
- The task is only to reason about route semantics, request construction, validation errors, or object lifecycle order.
- The environment uses Python 3.11 for backend imports with pinned `aioredis==2.0.1`; switch to Python 3.10 first.

When skipped, state the skip reason and verify the requested behavior with bundled references, request/response schema checks, or synthetic payload construction rather than claiming native service coverage.

## Minimum environment for backend inspection

For import-level backend inspection or local backend development, use:

- Python 3.10.
- Backend requirements compatible with the pinned dependency set.
- `PYTHONPATH`/module layout that lets the backend package import its `app` and `tkhelper` modules.
- Environment variables sufficient for config import if importing the full FastAPI app: service mode/purpose, integration URLs, database URL, Redis URL, object storage type, volume path, project ID, and secrets.

If only schema/model classes are needed, prefer importing the narrow classes rather than starting the full FastAPI app. Full app startup runs lifespan hooks that sync model/plugin caches and initialize database/Redis connections.

## What native success should look like

A full backend native service check is only meaningful when all dependent services are available. Expected signals:

- Backend imports and starts under Python 3.10.
- Health/version routes respond on the correct prefix and auth mode.
- Database migrations/connection pool initialize successfully.
- Redis initializes and supports chat locks/cache operations.
- API-mode or web-mode service/client tests complete with passing pytest status.
- Test failures, if any, map to a specific route/object workflow rather than missing services or credentials.

## Recommended synthetic usability cases for verification planning

These are suitable difficult cases for assertion-backed skill verification without running the original service tests:

1. **Assistant + RAG + tool lifecycle mapping.** Given one text document, one chat model, one embedding model, and one OpenAPI action schema, produce the correct creation order and identify validation gates for collection capacity, text splitter, embedding model type, action schema, assistant tool/retrieval validation, chat/message creation, and generation.
2. **Python-version import diagnosis.** Given an import traceback mentioning duplicate `TimeoutError` bases from `aioredis`, explain that Python 3.11 is incompatible with the backend's pinned `aioredis==2.0.1`, choose Python 3.10, and avoid misdiagnosing the failure as a FastAPI router or Pydantic issue.
