---
name: khoj
description: "Use Khoj as a self-hosted AI second-brain server, document
  indexing/search system, chat/agent app, automation/memory service, or Python
  repository to maintain."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Khoj

Use this repo skill when a task names Khoj or asks for a self-hosted AI second brain that combines document ingestion, semantic search, chat, agents, tools, automations, memory, and a FastAPI/Django Python service.

## Quick Routing

- Use [deployment-api](sub-skills/deployment-api/SKILL.md) for installing Khoj, starting the server, Docker/pip setup, database/auth/admin/model-provider configuration, CLI parser checks, and REST route orientation.
- Use [content-indexing](sub-skills/content-indexing/SKILL.md) for `/api/content`, file upload/sync, parser APIs, Markdown/Org/PDF/DOCX/plaintext/image/GitHub/Notion ingestion, conversion, and stale-index diagnostics.
- Use [search-retrieval](sub-skills/search-retrieval/SKILL.md) for `/api/search`, semantic retrieval, `SearchType`, `SearchResponse`, date/file/word filters, embeddings, reranking, distance thresholds, and no-results debugging.
- Use [chat-agents](sub-skills/chat-agents/SKILL.md) for `/api/chat`, WebSocket/REST chat, conversation history/share/file filters, agents, model providers, slash commands, online/webpage/code/image/diagram/research/operator tools, and voice.
- Use [automations-memory](sub-skills/automations-memory/SKILL.md) for `/api/automation`, cron normalization, scheduler leadership, `/automated_task`, `/api/memories`, memory settings, and user/agent memory scoping.
- Use [development](sub-skills/development/SKILL.md) for modifying this Khoj checkout, choosing focused tests, Django model/migration changes, local dev setup, frontend/docs awareness, and maintainer script boundaries.

## First Checks

- Public package: `khoj`; Python support from package metadata is `>=3.10,<3.13`.
- Server entry point: `khoj`, implemented by `khoj.main:run`.
- Safe parser-only CLI validation: do not assume `khoj --help` is side-effect free; use `sub-skills/deployment-api/scripts/inspect_cli.py` or import `khoj.utils.cli.cli`.
- Safe environment probe: run [check_khoj_environment.py](scripts/check_khoj_environment.py) to check package metadata, imports, CLI parser defaults, and optional Django setup without starting a server.
- Staleness check: read [repo-provenance.md](references/repo-provenance.md) before deciding whether this skill matches a current checkout.

## Common Workflows

1. For a self-hosting or API task, start with `deployment-api`, then jump to the endpoint-specific sub-skill.
2. For “my docs are not searchable,” first use `content-indexing` to validate ingestion, then `search-retrieval` to inspect filters, user isolation, embeddings, and ranking.
3. For “chat or agents are failing,” use `chat-agents`, then cross-link to `deployment-api` for provider/base URL/auth setup or to `search-retrieval` for `/notes` grounding.
4. For reminders, newsletters, repeated research, or persistent memories, use `automations-memory`, then `chat-agents` for generated chat responses.
5. For code changes, use `development` first to select focused tests and identify database/frontend/docs side effects, then use the owning user-facing sub-skill for behavior details.

## Safety Boundaries

- Do not start servers, run migrations against a real database, pull containers, install dependencies, trigger external services, or run expensive chat/eval tests unless the user explicitly asks.
- Do not treat source repo docs, tests, examples, or scripts as runtime dependencies for this skill; use the bundled references and helper scripts here.
- Keep credentials out of examples. Khoj can use OpenAI, Anthropic, Gemini, OpenAI-compatible providers, Notion, GitHub, Twilio, Resend, E2B, and other services, but those require user-provided configuration.
- If a current checkout’s commit, dirty paths, package metadata, or public route/API behavior differs from the provenance snapshot, run a skill refresh before relying on detailed claims.

## Shared References

- [package-overview.md](references/package-overview.md) summarizes Khoj’s major surfaces, package metadata, and cross-skill ownership.
- [troubleshooting.md](references/troubleshooting.md) covers cross-cutting failures that span setup, indexing, search, chat, automations, and development.
- [repo-routing-metadata.json](references/repo-routing-metadata.json) is structured metadata consumed by the managed repo-skills router during import.
