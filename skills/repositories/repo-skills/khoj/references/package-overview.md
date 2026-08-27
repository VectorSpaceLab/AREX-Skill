# Khoj Package Overview

## Purpose

Khoj is a Python package and self-hostable AI second-brain application. It combines a FastAPI service, Django models/admin, document ingestion, semantic retrieval, chat/agent workflows, scheduled automations, memory, and clients for web/desktop/editor/mobile-style usage.

## Package Facts

- Distribution name: `khoj`.
- Console script: `khoj = khoj.main:run`.
- Python range in package metadata: `>=3.10,<3.13`.
- Base dependencies include FastAPI, Django, Pydantic, OpenAI/Anthropic/Google clients, LangChain text splitters/community, sentence-transformers, torch, transformers, OCR/PDF/DOCX/image/document libraries, APScheduler, and auth/storage/telemetry support packages.
- Optional extras in package metadata: `prod` for production services, `local` for embedded PostgreSQL support, and `dev` for tests/lint/dev tooling.

## Main Runtime Surfaces

| Surface | Owner | What to read |
| --- | --- | --- |
| Server startup, CLI, Docker/pip, DB/admin/auth/model providers | `deployment-api` | `sub-skills/deployment-api/SKILL.md` |
| Content upload, conversion, parsers, remote data sources | `content-indexing` | `sub-skills/content-indexing/SKILL.md` |
| Search API, filters, embeddings, ranking | `search-retrieval` | `sub-skills/search-retrieval/SKILL.md` |
| Chat, agents, tools, sharing, voice/image/code/research/operator | `chat-agents` | `sub-skills/chat-agents/SKILL.md` |
| Scheduled tasks, cron, memories | `automations-memory` | `sub-skills/automations-memory/SKILL.md` |
| Repository maintenance and focused tests | `development` | `sub-skills/development/SKILL.md` |

## Important Design Notes

- The console script imports `khoj.main`, and `khoj.main` initializes Django, runs migrations, collects static files, configures routes, and starts scheduler/server setup before normal service operation. Treat console-script checks as operational, not parser-only.
- Many APIs require an authenticated request user, database models, and configured chat/search model rows. Parser static methods and bundled inspection scripts are safer for isolated code understanding.
- Content parsing and semantic search are separate phases: a successful upload or parser run does not guarantee search visibility until embeddings/database state and user isolation are correct.
- Chat and agents reuse search/content surfaces but add model-provider, subscription/rate-limit, tool availability, and conversation-history constraints.
- Automations use chat-generation internals plus APScheduler/Django job storage, so scheduler and database health matter even when the endpoint request succeeds.
