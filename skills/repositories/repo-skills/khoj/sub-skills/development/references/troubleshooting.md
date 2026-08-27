# Development Troubleshooting

## PostgreSQL Or Pgvector Missing

Symptoms include connection refused on `localhost:5432`, authentication failures for `postgres`, missing `vector` extension, or tests failing before assertions with Django database setup errors.

Use a disposable development database. Khoj defaults to `POSTGRES_DB=khoj`, `POSTGRES_HOST=localhost`, `POSTGRES_PORT=5432`, `POSTGRES_USER=postgres`, and `POSTGRES_PASSWORD=postgres` unless env vars override them. CI uses a PostgreSQL service with pgvector and sets database env vars explicitly.

Do not treat parser-only tests as proof that API/search/model tests will pass. Parser tests can pass without a usable database, while route/search tests need Django and PostgreSQL. Docker Compose provides a pgvector-backed database when service-level validation is in scope.

## Admin Env Vars And Non-Interactive Setup

Docker/server examples include `KHOJ_ADMIN_EMAIL`, `KHOJ_ADMIN_PASSWORD`, `KHOJ_DJANGO_SECRET_KEY`, domain settings, and `--non-interactive`. In non-interactive automation, missing admin credentials or domain/cookie settings can cause setup or login/admin behavior to fail unexpectedly.

For development tasks, avoid starting the server merely to validate code. If server startup is required, set explicit non-secret development values, use a disposable database, and avoid leaking real provider keys or production domains into logs or committed files.

## `khoj --help` Fails Before Argparse

The console entry point resolves `khoj.main:run`. Importing `khoj.main` can initialize Django and run startup work before argparse handles `--help`, so `khoj --help` is not a safe parser-only check on an unconfigured host.

Safer alternatives:

- Run `pytest tests/test_cli.py`.
- Import and call `khoj.utils.cli.cli([...])` in a small parser-only check.
- Use deployment-api tooling for CLI inspection if available in the generated root skill.

## Static Or Frontend Builds Fail

Backend startup and Django static configuration expect generated frontend/static directories. Web development uses `src/interface/web` with Bun in contributor docs: `bun install`, `bun export`, and optionally `bun dev` for interactive frontend work. The dev server can differ from exported static behavior for streaming.

If static files are missing during server startup, decide whether the task actually needs server startup. For backend-only tests, focused pytest may be sufficient. For client-visible changes, run the relevant client build/export command only after the user approves dependency/build side effects.

## Model Provider, API Key, And Chat Test Mocks

Some tests are intentionally skipped unless provider keys exist, such as automation tests requiring a Gemini key or chat tests requiring OpenAI-compatible keys. Do not add real keys to tests. Prefer existing factories and monkeypatching patterns in `tests/helpers.py` and `tests/conftest.py`.

For chat/agent changes:

- Select specific tests rather than running all chat-quality cases first.
- Respect `pytest.mark.chatquality` as a signal that the test may be slower or quality/evaluation oriented.
- Avoid network-dependent tests unless the change targets online search or provider integration and the user approved it.

## Slow ML Dependencies

Khoj depends on torch, transformers, sentence-transformers, OCR/document parsers, and embedding/cross-encoder code. Search tests can initialize embedding models; image/PDF/OCR tests can be slower than pure parser tests. CI installs with CPU torch index settings and disables CUDA visibility.

When validating ordinary parser or router code, prefer tests that do not instantiate heavy ML models. If a search test is required, pick one or two targeted cases before escalating to broad suites. GPU availability is not required for development skill extraction or normal focused validation.

## Flaky External-Service Tests

Webpage reads, online search, provider-backed chat, automation provider calls, GitHub/Notion remote-source behavior, and sandbox/code-execution integrations may depend on network, credentials, or external services. Existing tests use `skipif` markers for several key-gated cases.

If such a test fails without relevant credentials or network stability, record it as an environment limitation instead of changing product code. Use local parser, adapter, or route tests to validate deterministic behavior whenever possible.

## Migrations Surprise Real Databases

Migrations can run at startup in Khoj workflows, and schema mistakes can break server import/startup before a route is hit. Never test a migration against a real user database. Use a disposable PostgreSQL/pgvector database and run migration commands explicitly. For data migrations, check old and new record shapes, nulls, missing JSON keys, and reverse behavior.
