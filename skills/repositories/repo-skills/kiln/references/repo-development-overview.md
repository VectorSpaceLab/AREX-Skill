# Kiln Repo Development Overview

## Monorepo packages

| Path | Package/surface | Use it for |
|---|---|---|
| `libs/core` | `kiln-ai`, import root `kiln_ai`, CLI `kiln_ai` | Datamodel, prompts, providers, model adapters, tools/MCP, RAG, evals, data generation, fine-tuning, utility functions. |
| `libs/server` | `kiln-server`, import root `kiln_server`, CLIs `kiln_server` and `kiln_mcp` | Public FastAPI REST API and MCP server wrapping core library capabilities. |
| `app/desktop` | Desktop/studio-server checkout source plus `kiln-studio-desktop` metadata | Desktop app, studio-server API extensions, Git sync, background jobs, chat/assistant, webhost, PyInstaller packaging. |
| `app/web_ui` | Svelte 4/TypeScript/Tailwind/DaisyUI frontend | Routes, stores, components, OpenAPI-generated client types, Vitest/Playwright tests. |
| `specs` and per-package `specs` | Architecture/implementation specs | Design context for cross-package features and large UI/server changes. |

## Skill ownership

- `project-datamodel`: object model, `.kiln` files, schemas, project/task/run/prompt/dataset/skill persistence, `kiln_ai` CLI packaging.
- `task-execution-providers-tools`: run configs, providers/models, prompts, LiteLLM adapters, tools, skills, MCP sessions, structured output and provider failures.
- `rag-documents-data`: documents, extraction, chunking, embedding, vector stores, reranking, RAG configs/search, RAG tools.
- `evals-optimization-finetuning`: evals, stats, synthetic data/data guides, repair, prompt optimization, fine-tuning.
- `server-desktop-web-api`: REST/MCP server, desktop studio server, Git sync, jobs/SSE/chat, provider/tool/skill endpoints, OpenAPI bridge, Svelte UI.
- `repo-development`: check selection, coding/test/design rules, repo-local maintenance skills, release/prerelease boundaries.

## Common command surfaces

- Python packages and tests are managed by the root uv workspace. Use `uv run` commands from a checkout.
- The canonical full repo check is `uv run ./checks.sh --agent-mode`.
- OpenAPI bridge checks live in the web UI source tree and compare generated TypeScript schema with the current server API schema.
- Web UI checks run under `app/web_ui` through npm scripts.
- Paid and prerelease tests use explicit pytest flags and are not part of ordinary safe verification.

## Public package versus checkout work

For library/server consumers, assume only `kiln_ai`, `kiln_server`, and their CLIs are installed. For desktop/studio-server/web/git-sync work, assume a full Kiln checkout because those workflows depend on monorepo source layout, generated web assets, or repository tests.

Do not write reusable instructions that require opening original source files. If a future task is to edit this repository, it is acceptable to inspect source in that checkout; if the task is package use, prefer bundled references and installed-package APIs.
