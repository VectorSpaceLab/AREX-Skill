---
name: api-mcp-web
description: "Develop and troubleshoot LangBot HTTP API route groups,
  service-layer auth, API keys, MCP server tools at /mcp, web frontend
  integration, and Page Bot embed workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# API, MCP, and Web UI

Use this sub-skill for HTTP routes, permissions, service APIs, API-key auth,
LangBot's own `/mcp` server, frontend API integration, and embeddable Page Bot
widget behavior.

## Read First

- [references/http-api-and-auth.md](references/http-api-and-auth.md) for route
  groups, auth types, permissions, service-layer rules, and API keys.
- [references/mcp-server.md](references/mcp-server.md) for MCP tool surface and
  alignment rules.
- [references/web-frontend-and-embed.md](references/web-frontend-and-embed.md)
  for Vite frontend and Page Bot embed workflows.
- [references/troubleshooting.md](references/troubleshooting.md) for 401/403,
  route registration, MCP transport, CORS, and frontend failures.

## Workflow: Add or Change an Agent-Accessible Endpoint

1. Locate the owning service in the HTTP service layer.
2. Add or update the route group and declare the narrowest valid `AuthType` and
   `Permission`.
3. If an AI agent should manage the resource, update `LangBotMCPServer` with a
   curated MCP tool that calls the service layer directly.
4. Keep the web UI request shape and i18n strings aligned if the endpoint is
   user-visible.
5. Update skills/testing guidance when the public agent contract changes.
6. Verify with focused HTTP/API/MCP tests before broad gates.

## Key Commands

```bash
python scripts/extract_langbot_routes.py --repo-root /path/to/LangBot --format markdown
uv run pytest tests/unit_tests/api/http/test_authz.py tests/unit_tests/api/service/test_apikey_service.py -q --tb=short
uv run pytest tests/unit_tests/api/test_mcp_controller.py tests/unit_tests/api/test_mcp_mount_tenant_scope.py tests/unit_tests/api/service/test_mcp_service.py -q --tb=short
uv run --no-sync python tests/manual/mcp_smoke.py
cd web && pnpm lint
```

## Boundaries

- Message routing and pipeline/provider execution belong to
  `platform-pipeline-provider`.
- Plugin/Box/skills runtime endpoints and SDK boundary details belong to
  `plugin-box-skills`.
- Persistence schema/tenancy internals belong to `persistence-rag-workspaces`.
