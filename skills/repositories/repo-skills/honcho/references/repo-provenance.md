# Repo provenance

Generated skill id: `honcho`

Source repository: Plastic Labs Honcho monorepo

Source revision used for extraction:

- Branch: `main`
- Commit: `444897975c95`
- Package versions observed from installed metadata:
  - `honcho` API package: `3.0.12`
  - `honcho-ai` Python SDK: `2.3.0`
  - `honcho-cli`: `0.1.2`

Working tree note at extraction time: the source checkout was clean except for
new generated skill/review artifacts under `skills/`.

## Evidence paths

The skill was distilled from the following relative source evidence paths:

- `README.md`
- `CONTRIBUTING.md`
- `CLAUDE.md`
- `pyproject.toml`
- `docs/README.md`
- `docs/v3/guides/overview.mdx`
- `docs/v3/contributing/self-hosting.mdx`
- `docs/v3/contributing/configuration.mdx`
- `docs/v3/contributing/troubleshooting.mdx`
- `src/main.py`
- `src/config.py`
- `src/db.py`
- `src/security.py`
- `src/startup/embedding_validator.py`
- `src/routers/workspaces.py`
- `src/routers/peers.py`
- `src/routers/sessions.py`
- `src/routers/messages.py`
- `src/routers/conclusions.py`
- `src/routers/keys.py`
- `src/routers/webhooks.py`
- `src/dialectic/chat.py`
- `src/dialectic/core.py`
- `src/deriver/__main__.py`
- `src/deriver/queue_manager.py`
- `src/deriver/deriver.py`
- `src/dreamer/orchestrator.py`
- `src/dreamer/specialists.py`
- `src/llm/`
- `src/utils/agent_tools.py`
- `src/vector_store/`
- `sdks/python/README.md`
- `sdks/python/pyproject.toml`
- `sdks/typescript/README.md`
- `sdks/typescript/package.json`
- `sdks/typescript/src/client.ts`
- `sdks/typescript/src/peer.ts`
- `sdks/typescript/src/session.ts`
- `honcho-cli/README.md`
- `honcho-cli/pyproject.toml`
- `honcho-cli/tests/`
- `mcp/README.md`
- `mcp/instructions.md`
- `scripts/configure_embeddings.py`
- `scripts/generate_jwt.py`
- `scripts/generate_jwt_secret.py`
- `scripts/migrate_db.py`
- `scripts/provision_db.py`
- `scripts/run_alembic_tests.py`
- `scripts/ensure_alembic_tests.py`
- `scripts/update_version.py`
- `tests/routes/test_auth_route_policy.py`
- `tests/routes/test_scope_route_policy.py`
- `tests/routes/test_scopes.py`
- `tests/routes/test_queue_status.py`
- `tests/sdk/`
- `tests/sdk_typescript/test_sdk.py`
- `tests/llm/test_model_config.py`
- `tests/startup/test_embedding_validator.py`
- `tests/scripts/test_configure_embeddings.py`
- `tests/unified/README.md`
- `tests/live_llm/README.md`

## Staleness checks

Refresh this skill when any of these areas change materially:

- `/v3` route families, auth scopes, or public schemas.
- Python or TypeScript SDK method names or constructor behavior.
- `honcho-cli` command groups, config semantics, or output shape.
- Configuration precedence, vector-store settings, embedding dimensions, or
  startup validation logic.
- Deriver, dialectic, dreamer, summarizer, or LLM provider orchestration.
- Maintainer commands for pytest, TypeScript SDK testing, Ruff, BasedPyright,
  Alembic, or versioning.
