---
name: airweave
description: "Route Airweave tasks to the most specific sub-skill:
  local-development, backend-api, source-connectors, frontend-dashboard,
  connect-widget, mcp-search, or monke-e2e."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Airweave

Use this skill when a task is about the Airweave repository itself. It is a router, not a monolith: pick the narrowest sub-skill that matches the request, then cross-link to the others only when the task spans multiple surfaces.

Start with `scripts/check_env.py` when you need a quick repo sanity check.

## Sub-skill map

| Task family | Use | Notes |
| --- | --- | --- |
| Local Docker stack, env seeding, ports, start/restart/recreate/destroy | `sub-skills/local-development/SKILL.md` | Safe stack orchestration and health checks |
| Search, collections, source connections, webhooks, usage, browse-tree routes | `sub-skills/backend-api/SKILL.md` | API shapes, request/response contracts, stream debugging |
| Source classes, registry metadata, auth/config, browse-tree implementation, ACLs | `sub-skills/source-connectors/SKILL.md` | Connector internals only |
| Dashboard UI, auth context, collections pages, search UI, billing/admin | `sub-skills/frontend-dashboard/SKILL.md` | React/Vite client behavior |
| Connect iframe, postMessage, OAuth popup, session modes | `sub-skills/connect-widget/SKILL.md` | Widget and parent messaging only |
| MCP server, tool registration, stdio/HTTP transport, auth modes | `sub-skills/mcp-search/SKILL.md` | Streamable HTTP and CLI diagnostics |
| Monke connector discovery, configs, runner, credential resolution | `sub-skills/monke-e2e/SKILL.md` | Safe discovery helper; no credentialed test runs by default |

## Operating rules

- Prefer the narrowest sub-skill that matches the task.
- When a task spans multiple surfaces, start with the dominant one and cross-link the others.
- Keep runtime guidance inside the generated skill tree.
- Do not depend on the original checkout path when a bundled helper exists.

## Useful references

- `references/overview.md` for the repo map and package layout
- `references/troubleshooting.md` for cross-cutting failures
- `references/repo-provenance.md` for the source snapshot used to build this skill tree
- `references/repo-routing-metadata.json` for repo-skills-router placement
