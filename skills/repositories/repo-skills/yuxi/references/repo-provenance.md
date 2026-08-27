# Yuxi repo provenance

Schema: `disco.repo-provenance.v1`

## Source snapshot

- Repository name: Yuxi / 语析.
- Branch: `main`.
- Commit: `c46ce7ff1c7b926fb2f32f2084129a3371d6375b`.
- Dirty state during source analysis: clean before generated skill/test artifacts were written.
- Skill id: `yuxi`.
- Generated runtime skill path in this checkout: `skills/disco/yuxi/`.
- Review/test artifact path in this checkout: `skills/tests/yuxi/`.
- Final managed import: not performed for this production run.

## Package versions verified during inspection

- Backend package: `yuxi` `0.7.2.dev0`.
- CLI package: `yuxi-cli` `0.1.3`.
- Frontend package: `yuxi-web` `0.7.2.dev0`.
- Workspace metadata: `yuxi-workspace` `0.7.2.dev0`.
- Python package constraint: `>=3.12,<3.14`.
- Live inspection imported selected backend/CLI modules and listed OCR processors from the installed package environment.

## Evidence paths used

### Product and architecture

- `README.md`
- `README.en.md`
- `ARCHITECTURE.md`
- `AGENTS.md`
- `CLAUDE.md` when present in the checkout

### Documentation

- `docs/intro/quick-start.md`
- `docs/intro/model-config.md`
- `docs/intro/knowledge-base.md`
- `docs/intro/evaluation.md`
- `docs/intro/cli.md`
- `docs/advanced/configuration.md`
- `docs/advanced/deployment.md`
- `docs/advanced/document-processing.md`
- `docs/advanced/api-key-integration.md`
- `docs/advanced/langfuse-integration.md`
- `docs/agents/agents-config.md`
- `docs/agents/agent-request-queue.md`
- `docs/agents/middleware.md`
- `docs/agents/tools-system.md`
- `docs/agents/skills-management.md`
- `docs/agents/mcp-integration.md`
- `docs/agents/subagents-management.md`
- `docs/agents/sandbox-architecture.md`
- `docs/agents/agent-evaluation.md`
- `docs/develop-guides/testing-guidelines.md`
- `docs/develop-guides/changelog.md`
- `docs/develop-guides/contributing.md` when present
- `docs/.vitepress/config.mts`

### Backend code and tests

- `backend/pyproject.toml`
- `backend/package/pyproject.toml`
- `backend/server/`
- `backend/package/yuxi/main.py`
- `backend/package/yuxi/agents/`
- `backend/package/yuxi/agents/toolkits/buildin/tools.py`
- `backend/package/yuxi/agents/toolkits/buildin/install_skill.py`
- `backend/package/yuxi/agents/toolkits/kbs/tools.py`
- `backend/package/yuxi/agents/mcp/service.py`
- `backend/package/yuxi/agents/skills/`
- `backend/package/yuxi/knowledge/`
- `backend/package/yuxi/services/ocr_service.py`
- `backend/test/unit/`
- `backend/test/integration/`
- `backend/test/e2e/`
- `backend/test/run_tests.sh`
- `backend/test/live_api_cleanup.py`

### CLI and frontend

- `packages/yuxi-cli/pyproject.toml`
- `packages/yuxi-cli/README.md`
- `packages/yuxi-cli/src/yuxi_cli/`
- `packages/yuxi-cli/tests/`
- `web/package.json`
- `web/src/`
- `web/test/unit/`

### Deployment and scripts

- `docker-compose.yml`
- `docker-compose.prod.yml`
- `docker/`
- `Makefile`
- `scripts/init.sh`
- `scripts/init.ps1`
- `scripts/pull_image.sh`
- `scripts/pull_image.ps1`
- `scripts/bump-version.sh`
- `scripts/eval/upload_langfuse_python_tasks_dataset.py`
- `backend/scripts/seed_initial_users.py`

## Staleness checks for future agents

Before using this skill on another checkout, compare:

1. Branch/commit and package versions above.
2. Major changes under `backend/package/yuxi/agents`, `backend/package/yuxi/knowledge`, `backend/server/routers`, `packages/yuxi-cli/src`, `docker-compose*.yml`, `docs/agents`, and `docs/advanced`.
3. Any changed dependency constraints for Python, Node, Docker images, OCR engines, model providers, LangGraph, FastAPI, or CLI libraries.
4. Any new or removed tests for skills, sandbox, subagents, OCR, knowledge retrieval, CLI, or service startup.

If these drift substantially, refresh the skill before relying on precise APIs or commands.
