# Native Verification Candidates for Maintenance

Use these repo-owned tests, scripts, and examples as verification candidates after maintenance changes. Classify each run by the task's change surface and available local services.

## Cheap Static Candidates

| Candidate | Command | Backend / prerequisites | Use when |
|---|---|---|---|
| Ruff check | `uv run ruff check src tests scripts migrations sdks/python` | CPU; uv environment | Python source, tests, scripts, migrations, or SDK Python changed |
| Ruff format | `uv run ruff format src tests scripts migrations sdks/python` | CPU; mutates formatting | Formatting changes are acceptable |
| Basedpyright | `uv run basedpyright` | CPU; uv environment | Python types, config, routers, DB, tests, SDK Python, or scripts changed |
| Pre-commit all files | `uv run pre-commit run --all-files` | CPU; may be slow and mutate formatting | Before release or broad infrastructure changes |

## Auth and Security Candidates

| Candidate | Command | Backend / prerequisites | Expected coverage |
|---|---|---|---|
| Auth route policy | `uv run pytest tests/routes/test_auth_route_policy.py` | CPU plus test DB fixture availability | Member-read allowlist exactness, no mutating methods in allowlist, every messages route has auth |
| Route-specific auth tests | `uv run pytest tests/routes/<affected_test>.py` | CPU plus test DB fixture availability | Endpoint-specific scope enforcement and own-resource checks |

## DB, Queue, and Runtime Candidates

| Candidate | Command | Backend / prerequisites | Expected coverage |
|---|---|---|---|
| General targeted pytest | `uv run pytest tests/<area>/...` | Postgres with pgvector for many app tests | CRUD/router/queue behavior with mocked LLM/vector layers |
| Deriver tests | `uv run pytest tests/deriver` | Postgres with pgvector; mocked LLM | Queue payloads, work units, representation processing |
| Reconciler/vector tests | `uv run pytest tests/reconciler tests/vector_store` | Postgres with pgvector; mocked external vector store unless test opts out | MessageEmbedding sync state and vector namespace behavior |
| Unified JSON runner | `python -m tests.unified.run` | Running test dependencies; see README | Multi-step config/session/chat behavior when a scenario is already defined |

## LLM Config and Tool-Loop Candidates

| Candidate | Command | Backend / prerequisites | Expected coverage |
|---|---|---|---|
| Model config regression set | `uv run pytest tests/llm/test_model_config.py -n0` | CPU; provider calls mocked or absent | Nested model configs, fallback independence, env/template sync, transport-specific params |
| Tool-loop token cap | `uv run pytest tests/llm/test_tool_loop_truncation.py -n0` | CPU; mocked LLM call | Token-based `hit_input_token_cap` propagation |
| Dialectic model usage | `uv run pytest tests/dialectic/test_model_config_usage.py -n0` | CPU; mocked Dialectic prep/LLM | Dialectic uses per-level model config in streaming and non-streaming answer paths |
| Live LLM suite | `uv run pytest tests/live_llm -n 0 --live-llm --no-header -q` | Explicit user approval; provider API keys and model env vars | Real provider behavior for structured output, caching, thinking/tool replay, embeddings |

## SDK Candidates

| Candidate | Command | Backend / prerequisites | Expected coverage |
|---|---|---|---|
| TypeScript SDK integration | `uv run pytest tests/ -k typescript` | Bun plus pytest fixture that starts a real Honcho server/runtime | TypeScript SDK tests against a live test server |
| TypeScript typecheck | `cd sdks/typescript && bun run typecheck` | Bun | Type-level SDK correctness only |
| TypeScript build | `cd sdks/typescript && bun run build` | Bun | Dist/build regressions |
| Python SDK tests | `cd sdks/python && uv run pytest` if SDK tests exist | uv environment | Python SDK-only behavior |

Do not use direct `bun test` as a native integration candidate; the package intentionally fails it to prevent tests from running without server fixtures.

## Alembic Candidates

| Candidate | Command | Backend / prerequisites | Expected coverage |
|---|---|---|---|
| Migration-test coverage | `uv run python scripts/ensure_alembic_tests.py` | CPU | Every migration revision has a matching verifier file |
| Selective migration pipeline | `uv run python scripts/run_alembic_tests.py <changed-files>` | Postgres; usually `-n0` inside script | Runs target revision pipeline for changed migrations/tests |
| Full Alembic pipeline | `uv run pytest tests/alembic/test_pipeline.py -n0` or `uv run pytest tests/alembic -n0` | Postgres; no xdist | Full migration order, upgrade/downgrade, schema/data verifier set |

## Benchmarks and Harnesses

Benchmark runners under `tests/bench` are long-running and often require Docker, datasets, local services, and judge/provider keys. Treat them as optional, user-approved verification for memory-quality or performance changes, not ordinary maintenance checks.

The benchmark harness starts a Docker Postgres database, a FastAPI server, and a deriver process. Use it only when a benchmark or end-to-end runtime investigation requires a real service pair.
