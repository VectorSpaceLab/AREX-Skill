# Honcho Maintenance Invariants

These are non-negotiable rules to preserve when editing Honcho maintenance, tests, auth, DB, LLM, migrations, and release workflows.

## Tooling and Test Invocation

- Prefix Python commands with `uv run` or use `uv` directly.
- Root pytest defaults include `--strict-markers`, `-n auto`, `--ignore=tests/alembic`, `testpaths = ["tests"]`, and `pythonpath = ["src"]`.
- Live LLM tests are opt-in only. They require `--live-llm` and provider-specific environment variables.
- Alembic tests are not part of the default pytest run; run them explicitly and usually with `-n0`.
- Do not call TypeScript SDK `bun test` directly. Use pytest orchestration for integration tests so the Honcho server/runtime fixture is available.
- Direct TypeScript SDK `bun run typecheck` and `bun run build` are allowed for type/build checks.

## Auth Scoping

- `allow_member_read=True` on `require_auth(...)` grants a peer-scoped key read access to sessions where that peer is an active member. It must only appear on intentionally read-only routes.
- Do not infer read/write behavior from HTTP method alone. Honcho uses POST for some read endpoints such as richer list/search bodies.
- Never add a mutating method or mutating handler to `EXPECTED_MEMBER_READ_ROUTES`.
- Preserve the regression test that every messages route has an auth dependency; the messages router intentionally relies on per-route dependencies.
- If a member-read route is keyed by a co-member-sensitive sub-resource, check that a peer-scoped caller only reads its own resource, e.g. compare the JWT peer field to the route peer id and raise an authentication error on mismatch.

## DB and Session Safety

- Never hold a DB session open across LLM, embedding, HTTP, provider, webhook, or other slow external calls.
- `tracked_db(..., read_only=True)`, `get_read_db`, and `ReadSessionLocal` are conventionally read-only only. They run in AUTOCOMMIT mode; database writes are not blocked and may commit immediately.
- Do not use read-only sessions for get-or-create paths, enqueue operations, vector-sync state transitions, peer-card updates, webhook writes, deletion writes, or migrations.
- Use `tracked_db` for short DB-only operations. Pass a shared session only when several DB-only calls need one connection/transaction.
- In tests, read and write DB dependencies may be overridden to the same session for visibility and isolation; do not copy this fixture shortcut into production logic.

## LLM and Model Configuration

- All provider calls should go through the Honcho LLM subsystem, not ad-hoc provider SDK calls in feature code.
- Config uses nested `MODEL_CONFIG` objects for deriver, dialectic levels, summary, dream specialists, and embeddings. Do not restore legacy flat keys such as per-agent `PROVIDER` or `MODEL` fields.
- Fallback configs are independent. Do not leak primary transport fields such as Anthropic/Gemini thinking budgets into OpenAI fallbacks, or vice versa.
- `structured_output_mode` is OpenAI-transport only and must be rejected on non-OpenAI primary or fallback configs.
- Dialectic levels must use their level-specific `MODEL_CONFIG`, `MAX_TOOL_ITERATIONS`, optional `MAX_OUTPUT_TOKENS`, and `TOOL_CHOICE`.
- The Dialectic minimal level has a reduced toolset; avoid expanding it accidentally when changing shared tool definitions.
- `AttemptPlan` pins selected provider/model/config per retry/fallback attempt. Streaming final retries must not bounce back to a primary provider after a tool loop has settled on fallback.
- Tool-loop truncation must propagate `hit_input_token_cap` based on token count, including single-message over-cap cases.

## Migrations

- Each `migrations/versions/<revision>_<description>.py` file must have `tests/alembic/revisions/test_<revision>_<description>.py`.
- Use verifier callbacks to assert before/after upgrade state, data migrations, and reversibility where applicable.
- Run `scripts/ensure_alembic_tests.py` to catch missing migration tests and `scripts/run_alembic_tests.py <changed-files>` for selective pipeline runs.
- Do not mutate a user or production database as part of ordinary code maintenance without explicit approval and a rollback plan.

## Versioning and Release Safety

- The main API, Python SDK, and TypeScript SDK can have different versions. Do not force equality unless the release plan explicitly requires it.
- Use the repo's version updater for coordinated version/changelog/doc updates. Use headless flags in automated or agent-driven work to avoid interactive editor hangs.
- After version changes, inspect the diff, run relevant API/SDK tests, refresh the lockfile when package metadata changed, and require explicit approval before tags, package publishing, or deployment.
- Preserve TypeScript SDK package behavior that prevents direct integration-test execution via `bun test`.

## Style and Static Checks

- Ruff lint selection includes pycodestyle, Pyflakes, pyupgrade, bugbear, simplify, and isort conventions; line length is intentionally ignored.
- Use explicit type hints and SQLAlchemy mapped column annotations in application code.
- Prefer absolute imports in Python code.
- Use specific Honcho exception types and logging with context; avoid print statements in application code except scripts/tests where expected.
