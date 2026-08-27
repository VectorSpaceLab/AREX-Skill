---
name: api-server
description: "Operate the LightRAG API server, WebUI, route families, auth,
  server configuration, setup wizard outputs, and deployment troubleshooting
  without touching embedded-core, storage, or provider internals."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LightRAG API Server And WebUI

Use this sub-skill when a task involves running `lightrag-server` or `lightrag-gunicorn`, configuring server `.env` settings, authenticating API/WebUI clients, using REST or Ollama-compatible routes, building the WebUI, or debugging API deployment behavior.

## Route By Task

- Configure server startup, `.env`, auth, path prefixes, CORS, setup-wizard outputs, or console scripts with [configuration](references/configuration.md).
- Use REST route families, request patterns, auth headers, streaming behavior, and graph/document/query route boundaries with [api-routes](references/api-routes.md).
- Build or serve the React WebUI, run frontend checks, use Docker stacks, or reason about packaged WebUI assets with [webui-and-deployment](references/webui-and-deployment.md).
- Diagnose guest JWT warnings, missing API extras, auth failures, upload/scan/delete conflicts, path-prefix issues, CORS, and WebUI build failures with [troubleshooting](references/troubleshooting.md).
- Run `python scripts/check_api_entrypoints.py` from this sub-skill directory for a safe installed-package import and console-entrypoint check that does not start the server.

## Boundaries

- This sub-skill owns API server entry points, FastAPI route families, WebUI packaging/dev/build/test commands, auth/JWT/password hashing, `env.example`-style server settings, `config.ini` compatibility notes, Docker/offline deployment notes, and setup-wizard output semantics.
- For embedded Python `LightRAG`, `QueryParam`, insert/query lifecycle, custom KG insertion, or direct async library use, route to `../core-rag/SKILL.md`.
- For upload/scan/delete ingestion concurrency internals, parser routing semantics, chunking strategies, multimodal extraction, and document-status state transitions, route to `../document-pipeline/SKILL.md`.
- For storage class selection, database service requirements, migrations, workspace isolation details, vector rebuilds, and destructive backend operations, route to `../storage-backends/SKILL.md`.
- For LLM, embedding, reranker, VLM provider bindings, credentials, role-specific model routing, and provider-specific options, route to `../llm-providers/SKILL.md`.

## Non-Negotiables

- Keep `.env` in the server startup directory; OS environment variables override `.env`, so restart the process after changing configuration.
- Do not expose `AUTH_ACCOUNTS` without a non-default `TOKEN_SECRET`; use `lightrag-hash-password` for bcrypt values.
- Treat no-account guest mode as development-only unless another protection layer is intentionally responsible for access control.
- Do not run `lightrag-server` or `lightrag-gunicorn` as a validation check unless the task explicitly allows starting a long-running service.
- Do not make runtime guidance depend on source-checkout scripts, repository docs, or local paths; use installed console scripts and self-contained command patterns.
