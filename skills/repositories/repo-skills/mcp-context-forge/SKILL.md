---
name: mcp-context-forge
description: "Operate ContextForge (mcp-context-forge), the FastAPI
  MCP/A2A/REST/gRPC gateway, including setup, APIs, transports, auth/RBAC,
  plugins, observability, deployment, and validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ContextForge Repo Skill

Use this repo skill when the user asks about ContextForge, `mcp-context-forge`,
`mcp-contextforge-gateway`, MCP gateway/proxy/registry behavior, A2A/REST/gRPC
federation, Admin API/UI, RBAC/token scoping, plugins, observability,
deployment, or maintainer validation.

ContextForge is a FastAPI gateway and registry that federates MCP servers,
A2A agents, and REST/gRPC APIs while centralizing governance, discovery,
virtual servers, auth/RBAC, plugins, and observability.

## First checks

- Package/distribution: `mcp-contextforge-gateway`.
- Import package: `mcpgateway`.
- Supported Python: `>=3.12,<3.14`.
- Minimal install: `pip install mcp-contextforge-gateway`.
- Checkout install: `pip install -e .` from a target checkout.
- Runtime secrets: `JWT_SECRET_KEY` and `AUTH_ENCRYPTION_SECRET` must be real,
  strong values before startup.
- Minimal import check:

```bash
python - <<'PY'
import mcpgateway
print(mcpgateway.__version__)
PY
```

## Route map

| User task | Read |
| --- | --- |
| Install, `.env`, secrets, startup, Docker/Compose/Helm route choice, CLI entry points | [`sub-skills/runtime-configuration/SKILL.md`](sub-skills/runtime-configuration/SKILL.md) |
| REST/Admin API, registry entities, schemas, services, pagination, catalog/tags/import-export | [`sub-skills/registry-admin-api/SKILL.md`](sub-skills/registry-admin-api/SKILL.md) |
| MCP streamable HTTP/SSE/WebSocket/stdio, virtual servers, gateways, A2A/UAID, gRPC reflection, Rust runtime modes | [`sub-skills/mcp-transports-federation/SKILL.md`](sub-skills/mcp-transports-federation/SKILL.md) |
| JWT/session/API tokens, teams, token scoping, RBAC, SSO/OAuth, token exchange, CSRF, security invariants | [`sub-skills/auth-rbac-security/SKILL.md`](sub-skills/auth-rbac-security/SKILL.md) |
| cpex plugins, plugin bindings, external plugins, internal observability, OTEL, Prometheus, logs, SIEM | [`sub-skills/plugins-observability/SKILL.md`](sub-skills/plugins-observability/SKILL.md) |
| Maintainer edits, tests, migrations, UI bundle, docs/ADRs, Helm, Rust runtime validation, PR/review gates | [`sub-skills/development-validation/SKILL.md`](sub-skills/development-validation/SKILL.md) |

## Shared references and helpers

- [`references/package-overview.md`](references/package-overview.md) — package identity, install paths, optional extras, and top-level capabilities.
- [`references/cli-entrypoints.md`](references/cli-entrypoints.md) — verified entry points: `mcpgateway`, `mcpgateway-server`, `cforge`, and `init-secrets`.
- [`references/troubleshooting.md`](references/troubleshooting.md) — top-level startup/config triage before routing deeper.
- [`references/repo-provenance.md`](references/repo-provenance.md) — source snapshot and refresh baseline.
- [`scripts/contextforge_quick_probe.py`](scripts/contextforge_quick_probe.py) — safe import/metadata/CLI discovery helper.

## Decision rules

1. If the user is trying to run a gateway, start with runtime configuration and
   check secrets before debugging code.
2. If the user is calling or changing HTTP routes, separate registry/API state
   from MCP transport behavior and from auth/RBAC policy.
3. If the user reports `401`, `403`, empty lists, hidden team rows, or admin
   bypass confusion, use the auth/RBAC sub-skill before editing services.
4. If the user mentions `/mcp`, `/servers/{id}/mcp`, SSE, WebSocket, stdio,
   A2A, gRPC, or Rust mode headers, use the transport/federation sub-skill.
5. If a plugin changes a tool/resource/prompt result, check plugin config and
   mode before blaming the registry or transport.
6. If the user is contributing code, choose validation based on changed areas;
   do not run the full live-gateway stack unless the change requires it or the
   task asks for readiness.

## Safety rules to preserve

- Do not accept inbound auth tokens via URL query parameters.
- Do not reimplement token-team interpretation; use canonical auth helpers in
  ContextForge code changes.
- Do not trust client-provided ownership/team/session fields.
- Do not log raw tokens, OAuth secrets, passwords, or Authorization headers.
- Keep high-risk transports and optional admin surfaces feature-flagged.
- For security changes, add deny-path tests.
- For migrations, verify the current Alembic head before choosing
  `down_revision`.

## When to refresh this skill

Read [`references/repo-provenance.md`](references/repo-provenance.md) before
using this skill with a different checkout. If the commit, package version,
public entry points, or major source paths differ, refresh the repo skill before
relying on detailed routes or validation matrices.
